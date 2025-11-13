"""
Local storage backend for DockShield
"""

import shutil
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from dockshield.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class LocalStorage(StorageBackend):
    """Local filesystem storage backend"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize local storage

        Args:
            config: Storage configuration
        """
        super().__init__(config)
        self.base_path = Path(config.get("path", "/var/backups/dockshield"))
        self.connected = False

    def connect(self) -> bool:
        """
        Connect to local storage (create directory if needed)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.connected = True
            logger.info(f"Connected to local storage: {self.base_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to local storage: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from local storage"""
        self.connected = False

    def is_connected(self) -> bool:
        """
        Check if connected

        Returns:
            True if connected, False otherwise
        """
        return self.connected and self.base_path.exists()

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """
        Copy file to local storage

        Args:
            local_path: Source file path
            remote_path: Destination file path (relative to base_path)

        Returns:
            True if successful, False otherwise
        """
        try:
            dest_path = self.base_path / remote_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(local_path, dest_path)
            logger.debug(f"Copied {local_path} to {dest_path}")
            return True

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """
        Copy file from local storage

        Args:
            remote_path: Source file path (relative to base_path)
            local_path: Destination file path

        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = self.base_path / remote_path

            if not source_path.exists():
                logger.error(f"File not found: {source_path}")
                return False

            local_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, local_path)
            logger.debug(f"Copied {source_path} to {local_path}")
            return True

        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        """
        Delete file from local storage

        Args:
            remote_path: File path (relative to base_path)

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self.base_path / remote_path

            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return False

            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()

            logger.debug(f"Deleted {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

    def list_files(self, remote_path: str = "") -> List[str]:
        """
        List files in local storage

        Args:
            remote_path: Directory path (relative to base_path)

        Returns:
            List of file paths
        """
        try:
            search_path = self.base_path / remote_path if remote_path else self.base_path

            if not search_path.exists():
                return []

            files = []
            for item in search_path.rglob("*"):
                if item.is_file():
                    relative_path = item.relative_to(self.base_path)
                    files.append(str(relative_path))

            return files

        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []

    def file_exists(self, remote_path: str) -> bool:
        """
        Check if file exists

        Args:
            remote_path: File path (relative to base_path)

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.base_path / remote_path
        return file_path.exists()

    def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information

        Args:
            remote_path: File path (relative to base_path)

        Returns:
            Dictionary with file information or None
        """
        try:
            file_path = self.base_path / remote_path

            if not file_path.exists():
                return None

            stat = file_path.stat()

            return {
                "path": str(file_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "is_directory": file_path.is_dir(),
            }

        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None

    def get_available_space(self) -> Optional[int]:
        """
        Get available disk space

        Returns:
            Available space in bytes
        """
        try:
            stat = shutil.disk_usage(self.base_path)
            return stat.free
        except Exception as e:
            logger.error(f"Error getting available space: {e}")
            return None
