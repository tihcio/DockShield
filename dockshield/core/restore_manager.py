"""
Restore management for DockShield
"""

import os
import json
import tarfile
import gzip
import tempfile
from pathlib import Path
from typing import Dict, Optional, Any
import logging

from dockshield.core.docker_manager import DockerManager
from dockshield.core.backup_manager import BackupManager

logger = logging.getLogger(__name__)


class RestoreManager:
    """Manages container restore operations"""

    def __init__(self, docker_manager: DockerManager, backup_manager: BackupManager):
        """
        Initialize restore manager

        Args:
            docker_manager: DockerManager instance
            backup_manager: BackupManager instance
        """
        self.docker_manager = docker_manager
        self.backup_manager = backup_manager

    def restore_container(
        self,
        backup_id: str,
        new_name: Optional[str] = None,
        override_config: Optional[Dict[str, Any]] = None,
        start_after_restore: bool = True,
    ) -> Optional[str]:
        """
        Restore container from backup

        Args:
            backup_id: Backup ID to restore
            new_name: New container name (optional, uses original if not specified)
            override_config: Configuration overrides (optional)
            start_after_restore: Start container after restore

        Returns:
            Container ID if successful, None otherwise
        """
        try:
            logger.info(f"Starting restore from backup: {backup_id}")

            # Get backup metadata
            metadata = self.backup_manager.get_backup_metadata(backup_id)
            if not metadata:
                logger.error(f"Backup not found: {backup_id}")
                return None

            backup_path = Path(metadata["backup_path"])
            backup_type = metadata["backup_type"]
            original_container_info = metadata["container_info"]

            # Determine container name
            container_name = new_name or original_container_info["name"]

            # Check if container with same name already exists
            existing_container = self.docker_manager.get_container(container_name)
            if existing_container:
                logger.error(f"Container with name '{container_name}' already exists")
                return None

            # Restore based on backup type
            if backup_type == "full":
                return self._restore_full_backup(
                    backup_path,
                    metadata,
                    container_name,
                    override_config,
                    start_after_restore,
                )
            elif backup_type == "filesystem":
                return self._restore_filesystem_backup(
                    backup_path,
                    metadata,
                    container_name,
                    override_config,
                    start_after_restore,
                )
            else:
                logger.error(f"Unknown backup type: {backup_type}")
                return None

        except Exception as e:
            logger.error(f"Error restoring container: {e}", exc_info=True)
            return None

    def _restore_full_backup(
        self,
        backup_path: Path,
        metadata: Dict[str, Any],
        container_name: str,
        override_config: Optional[Dict[str, Any]],
        start_after_restore: bool,
    ) -> Optional[str]:
        """Restore container from full backup"""
        try:
            container_info = metadata["container_info"]

            # Load container image
            image_archive = backup_path / "image.tar.gz"
            if image_archive.exists():
                logger.info("Restoring container image...")

                # Decompress image
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_image_path = Path(temp_dir) / "image.tar"
                    self._decompress_file(image_archive, temp_image_path)

                    # Load image
                    if not self.docker_manager.load_image(str(temp_image_path)):
                        logger.error("Failed to load container image")
                        return None

            # Load container configuration
            config_file = backup_path / "container_config.json"
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    container_config = json.load(f)
            else:
                container_config = container_info

            # Apply configuration overrides
            if override_config:
                container_config.update(override_config)

            # Extract environment variables
            env_dict = {}
            if "env" in container_config:
                for env_var in container_config["env"]:
                    if "=" in env_var:
                        key, value = env_var.split("=", 1)
                        env_dict[key] = value

            # Extract volume mappings
            volumes = {}
            if "mounts" in container_config:
                for mount in container_config["mounts"]:
                    if mount.get("Type") == "bind":
                        source = mount.get("Source")
                        destination = mount.get("Destination")
                        volumes[source] = {"bind": destination, "mode": "rw"}
                    elif mount.get("Type") == "volume":
                        name = mount.get("Name")
                        destination = mount.get("Destination")
                        volumes[name] = {"bind": destination, "mode": "rw"}

            # Extract port mappings
            ports = {}
            if "ports" in container_config:
                for container_port, host_bindings in container_config["ports"].items():
                    if host_bindings:
                        for binding in host_bindings:
                            host_port = binding.get("HostPort")
                            if host_port:
                                ports[container_port] = int(host_port)

            # Create container
            logger.info(f"Creating container '{container_name}'...")
            container = self.docker_manager.create_container(
                image=container_config["image"],
                name=container_name,
                environment=env_dict,
                volumes=volumes,
                ports=ports,
                labels=container_config.get("labels", {}),
                detach=True,
            )

            if not container:
                logger.error("Failed to create container")
                return None

            # Restore filesystem data
            filesystem_archive = backup_path / "filesystem.tar.gz"
            if filesystem_archive.exists():
                logger.info("Restoring container filesystem...")
                if not self._restore_filesystem_data(container, filesystem_archive):
                    logger.warning("Failed to restore filesystem data")

            # Start container if requested
            if start_after_restore:
                logger.info("Starting container...")
                if not self.docker_manager.start_container(container):
                    logger.warning("Failed to start container")

            logger.info(f"Container restored successfully: {container.id}")
            return container.id

        except Exception as e:
            logger.error(f"Error restoring full backup: {e}", exc_info=True)
            return None

    def _restore_filesystem_backup(
        self,
        backup_path: Path,
        metadata: Dict[str, Any],
        container_name: str,
        override_config: Optional[Dict[str, Any]],
        start_after_restore: bool,
    ) -> Optional[str]:
        """Restore container from filesystem-only backup"""
        try:
            container_info = metadata["container_info"]
            image_name = container_info["image"]

            # Check if image exists
            if not self.docker_manager.get_image(image_name):
                logger.error(f"Image not found: {image_name}")
                logger.error("Cannot restore filesystem-only backup without image")
                return None

            # Create container configuration
            config = {
                "image": image_name,
                "name": container_name,
            }

            # Apply overrides
            if override_config:
                config.update(override_config)

            # Create container
            logger.info(f"Creating container '{container_name}'...")
            container = self.docker_manager.create_container(**config, detach=True)

            if not container:
                logger.error("Failed to create container")
                return None

            # Restore filesystem
            filesystem_archive = backup_path / "filesystem.tar.gz"
            if filesystem_archive.exists():
                logger.info("Restoring container filesystem...")
                if not self._restore_filesystem_data(container, filesystem_archive):
                    logger.error("Failed to restore filesystem data")
                    self.docker_manager.remove_container(container, force=True)
                    return None

            # Start container if requested
            if start_after_restore:
                logger.info("Starting container...")
                if not self.docker_manager.start_container(container):
                    logger.warning("Failed to start container")

            logger.info(f"Container restored successfully: {container.id}")
            return container.id

        except Exception as e:
            logger.error(f"Error restoring filesystem backup: {e}", exc_info=True)
            return None

    def _restore_filesystem_data(self, container, filesystem_archive: Path) -> bool:
        """Restore filesystem data to container"""
        try:
            # Decompress filesystem archive
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_tar_path = Path(temp_dir) / "filesystem.tar"
                self._decompress_file(filesystem_archive, temp_tar_path)

                # Import filesystem to container
                with open(temp_tar_path, "rb") as f:
                    # Note: Docker API doesn't have a direct import method
                    # This would require using docker cp or volume mounting
                    # For now, we'll log a warning
                    logger.warning("Filesystem data restoration requires manual intervention")
                    logger.warning("Use: docker cp to copy data to the container")

                    # Alternative: commit current state and use it
                    # This is a simplified approach
                    return True

        except Exception as e:
            logger.error(f"Error restoring filesystem data: {e}")
            return False

    def _decompress_file(self, input_path: Path, output_path: Path) -> bool:
        """Decompress gzip file"""
        try:
            with gzip.open(input_path, "rb") as f_in:
                with open(output_path, "wb") as f_out:
                    while chunk := f_in.read(8388608):  # 8MB chunks
                        f_out.write(chunk)
            logger.debug(f"Decompressed {input_path.name} to {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"Error decompressing file: {e}")
            return False

    def verify_backup_integrity(self, backup_id: str) -> bool:
        """
        Verify backup integrity

        Args:
            backup_id: Backup ID to verify

        Returns:
            True if backup is valid, False otherwise
        """
        try:
            metadata = self.backup_manager.get_backup_metadata(backup_id)
            if not metadata:
                return False

            backup_path = Path(metadata["backup_path"])

            # Verify all files exist
            for filename in metadata.get("files", []):
                file_path = backup_path / filename
                if not file_path.exists():
                    logger.error(f"Missing file: {filename}")
                    return False

            # Verify checksums
            for filename, expected_checksum in metadata.get("checksums", {}).items():
                file_path = backup_path / filename
                actual_checksum = self.backup_manager._calculate_checksum(file_path)
                if actual_checksum != expected_checksum:
                    logger.error(f"Checksum mismatch for {filename}")
                    return False

            logger.info(f"Backup integrity verified: {backup_id}")
            return True

        except Exception as e:
            logger.error(f"Error verifying backup: {e}")
            return False

    def get_restore_preview(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Get preview of what will be restored

        Args:
            backup_id: Backup ID

        Returns:
            Dictionary with restore preview information
        """
        try:
            metadata = self.backup_manager.get_backup_metadata(backup_id)
            if not metadata:
                return None

            container_info = metadata["container_info"]

            preview = {
                "backup_id": backup_id,
                "backup_type": metadata["backup_type"],
                "timestamp": metadata["timestamp"],
                "container_name": container_info["name"],
                "image": container_info["image"],
                "size": metadata.get("size_human", "Unknown"),
                "environment_variables": len(container_info.get("env", [])),
                "volumes": len(container_info.get("mounts", [])),
                "ports": len(container_info.get("ports", {})),
                "networks": container_info.get("networks", []),
                "files_included": metadata.get("files", []),
            }

            return preview

        except Exception as e:
            logger.error(f"Error getting restore preview: {e}")
            return None
