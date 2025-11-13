"""
Backup management for DockShield
"""

import os
import json
import tarfile
import gzip
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import hashlib

from dockshield.core.docker_manager import DockerManager
from docker.models.containers import Container

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages container backup operations"""

    BACKUP_METADATA_FILE = "backup_metadata.json"

    def __init__(self, docker_manager: DockerManager, backup_dir: Path):
        """
        Initialize backup manager

        Args:
            docker_manager: DockerManager instance
            backup_dir: Base directory for backups
        """
        self.docker_manager = docker_manager
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        container: Container,
        backup_type: str = "full",
        compression_level: int = 6,
        include_logs: bool = True,
        verify: bool = True,
        destination: Optional[Path] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create backup of container

        Args:
            container: Container object to backup
            backup_type: "filesystem" or "full"
            compression_level: Compression level (0-9)
            include_logs: Include container logs
            verify: Verify backup integrity
            destination: Backup destination directory (optional)

        Returns:
            Backup metadata dictionary or None if failed
        """
        try:
            logger.info(f"Starting {backup_type} backup of container {container.name}")

            # Get container info
            container_info = self.docker_manager.get_container_info(container)

            # Create backup metadata
            timestamp = datetime.now()
            backup_id = f"{container.name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

            metadata = {
                "backup_id": backup_id,
                "container_name": container.name,
                "container_id": container.id,
                "backup_type": backup_type,
                "timestamp": timestamp.isoformat(),
                "compression_level": compression_level,
                "container_info": container_info,
                "files": [],
                "checksums": {},
            }

            # Determine backup directory
            backup_path = destination or self.backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)

            # Export container filesystem
            filesystem_path = backup_path / "filesystem.tar"
            if not self._export_filesystem(container, filesystem_path):
                logger.error("Failed to export container filesystem")
                return None

            # Compress filesystem
            compressed_filesystem_path = backup_path / "filesystem.tar.gz"
            if not self._compress_file(filesystem_path, compressed_filesystem_path, compression_level):
                logger.error("Failed to compress filesystem")
                return None

            # Remove uncompressed file
            filesystem_path.unlink()

            metadata["files"].append("filesystem.tar.gz")
            metadata["checksums"]["filesystem.tar.gz"] = self._calculate_checksum(compressed_filesystem_path)

            # Full backup includes image and configuration
            if backup_type == "full":
                # Save container image
                image_name = container_info["image"]
                image_path = backup_path / "image.tar"

                if self.docker_manager.save_image(image_name, str(image_path)):
                    # Compress image
                    compressed_image_path = backup_path / "image.tar.gz"
                    if self._compress_file(image_path, compressed_image_path, compression_level):
                        image_path.unlink()
                        metadata["files"].append("image.tar.gz")
                        metadata["checksums"]["image.tar.gz"] = self._calculate_checksum(compressed_image_path)

                # Save container configuration
                config_path = backup_path / "container_config.json"
                self._save_container_config(container_info, config_path)
                metadata["files"].append("container_config.json")
                metadata["checksums"]["container_config.json"] = self._calculate_checksum(config_path)

            # Include logs if requested
            if include_logs:
                logs = self.docker_manager.get_container_logs(container)
                logs_path = backup_path / "container.log"
                logs_path.write_text(logs, encoding="utf-8")
                metadata["files"].append("container.log")
                metadata["checksums"]["container.log"] = self._calculate_checksum(logs_path)

            # Save metadata
            metadata_path = backup_path / self.BACKUP_METADATA_FILE
            self._save_metadata(metadata, metadata_path)

            # Verify backup if requested
            if verify:
                if not self._verify_backup(backup_path, metadata):
                    logger.error("Backup verification failed")
                    return None

            # Calculate total backup size
            metadata["size_bytes"] = sum(
                (backup_path / f).stat().st_size for f in metadata["files"]
            )
            metadata["size_human"] = self._format_size(metadata["size_bytes"])

            # Update metadata with final info
            self._save_metadata(metadata, metadata_path)

            logger.info(f"Backup completed successfully: {backup_id}")
            logger.info(f"Backup size: {metadata['size_human']}")

            return metadata

        except Exception as e:
            logger.error(f"Error creating backup: {e}", exc_info=True)
            return None

    def _export_filesystem(self, container: Container, output_path: Path) -> bool:
        """Export container filesystem to tar file"""
        try:
            return self.docker_manager.export_container_filesystem(container, str(output_path))
        except Exception as e:
            logger.error(f"Error exporting filesystem: {e}")
            return False

    def _compress_file(self, input_path: Path, output_path: Path, compression_level: int) -> bool:
        """Compress file using gzip"""
        try:
            with open(input_path, "rb") as f_in:
                with gzip.open(output_path, "wb", compresslevel=compression_level) as f_out:
                    while chunk := f_in.read(8388608):  # 8MB chunks
                        f_out.write(chunk)
            logger.debug(f"Compressed {input_path.name} to {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"Error compressing file: {e}")
            return False

    def _save_container_config(self, container_info: Dict[str, Any], output_path: Path) -> None:
        """Save container configuration to JSON file"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(container_info, f, indent=2, default=str)

    def _save_metadata(self, metadata: Dict[str, Any], output_path: Path) -> None:
        """Save backup metadata to JSON file"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8388608):  # 8MB chunks
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _verify_backup(self, backup_path: Path, metadata: Dict[str, Any]) -> bool:
        """Verify backup integrity using checksums"""
        try:
            for filename, expected_checksum in metadata["checksums"].items():
                file_path = backup_path / filename
                if not file_path.exists():
                    logger.error(f"Missing file in backup: {filename}")
                    return False

                actual_checksum = self._calculate_checksum(file_path)
                if actual_checksum != expected_checksum:
                    logger.error(f"Checksum mismatch for {filename}")
                    return False

            logger.debug("Backup verification successful")
            return True
        except Exception as e:
            logger.error(f"Error verifying backup: {e}")
            return False

    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def list_backups(self, container_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available backups

        Args:
            container_name: Filter by container name (optional)

        Returns:
            List of backup metadata dictionaries
        """
        backups = []

        try:
            for backup_dir in self.backup_dir.iterdir():
                if not backup_dir.is_dir():
                    continue

                metadata_path = backup_dir / self.BACKUP_METADATA_FILE
                if not metadata_path.exists():
                    continue

                try:
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)

                    # Filter by container name if specified
                    if container_name and metadata.get("container_name") != container_name:
                        continue

                    # Add backup path to metadata
                    metadata["backup_path"] = str(backup_dir)

                    backups.append(metadata)
                except Exception as e:
                    logger.warning(f"Error reading backup metadata from {backup_dir}: {e}")

            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        except Exception as e:
            logger.error(f"Error listing backups: {e}")

        return backups

    def get_backup_metadata(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for specific backup

        Args:
            backup_id: Backup ID

        Returns:
            Backup metadata dictionary or None if not found
        """
        backup_path = self.backup_dir / backup_id
        metadata_path = backup_path / self.BACKUP_METADATA_FILE

        if not metadata_path.exists():
            logger.warning(f"Backup metadata not found: {backup_id}")
            return None

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            metadata["backup_path"] = str(backup_path)
            return metadata
        except Exception as e:
            logger.error(f"Error reading backup metadata: {e}")
            return None

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete backup

        Args:
            backup_id: Backup ID

        Returns:
            True if successful, False otherwise
        """
        backup_path = self.backup_dir / backup_id

        if not backup_path.exists():
            logger.warning(f"Backup not found: {backup_id}")
            return False

        try:
            import shutil
            shutil.rmtree(backup_path)
            logger.info(f"Deleted backup: {backup_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            return False

    def cleanup_old_backups(self, retention_days: int, container_name: Optional[str] = None) -> int:
        """
        Delete backups older than retention period

        Args:
            retention_days: Number of days to keep backups
            container_name: Filter by container name (optional)

        Returns:
            Number of backups deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0

        backups = self.list_backups(container_name)

        for backup in backups:
            try:
                backup_date = datetime.fromisoformat(backup["timestamp"])
                if backup_date < cutoff_date:
                    if self.delete_backup(backup["backup_id"]):
                        deleted_count += 1
            except Exception as e:
                logger.warning(f"Error processing backup for cleanup: {e}")

        logger.info(f"Cleaned up {deleted_count} old backups")
        return deleted_count
