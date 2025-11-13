"""
Base storage backend interface for DockShield
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize storage backend

        Args:
            config: Storage backend configuration
        """
        self.config = config
        self.enabled = config.get("enabled", False)

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to storage backend

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from storage backend"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connected to storage backend

        Returns:
            True if connected, False otherwise
        """
        pass

    @abstractmethod
    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """
        Upload file to storage backend

        Args:
            local_path: Local file path
            remote_path: Remote file path

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """
        Download file from storage backend

        Args:
            remote_path: Remote file path
            local_path: Local file path

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """
        Delete file from storage backend

        Args:
            remote_path: Remote file path

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def list_files(self, remote_path: str = "") -> List[str]:
        """
        List files in storage backend

        Args:
            remote_path: Remote directory path

        Returns:
            List of file paths
        """
        pass

    @abstractmethod
    def file_exists(self, remote_path: str) -> bool:
        """
        Check if file exists in storage backend

        Args:
            remote_path: Remote file path

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information

        Args:
            remote_path: Remote file path

        Returns:
            Dictionary with file information or None if not found
        """
        pass

    def upload_directory(self, local_dir: Path, remote_dir: str) -> bool:
        """
        Upload entire directory to storage backend

        Args:
            local_dir: Local directory path
            remote_dir: Remote directory path

        Returns:
            True if successful, False otherwise
        """
        try:
            for item in local_dir.rglob("*"):
                if item.is_file():
                    relative_path = item.relative_to(local_dir)
                    remote_path = f"{remote_dir}/{relative_path}".replace("\\", "/")

                    if not self.upload_file(item, remote_path):
                        logger.error(f"Failed to upload {item}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error uploading directory: {e}")
            return False

    def download_directory(self, remote_dir: str, local_dir: Path) -> bool:
        """
        Download entire directory from storage backend

        Args:
            remote_dir: Remote directory path
            local_dir: Local directory path

        Returns:
            True if successful, False otherwise
        """
        try:
            local_dir.mkdir(parents=True, exist_ok=True)
            files = self.list_files(remote_dir)

            for remote_file in files:
                # Calculate local path
                relative_path = remote_file.replace(remote_dir, "").lstrip("/")
                local_file = local_dir / relative_path

                # Create parent directory if needed
                local_file.parent.mkdir(parents=True, exist_ok=True)

                if not self.download_file(remote_file, local_file):
                    logger.error(f"Failed to download {remote_file}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error downloading directory: {e}")
            return False

    def get_available_space(self) -> Optional[int]:
        """
        Get available space in bytes

        Returns:
            Available space in bytes or None if not supported
        """
        return None

    def test_connection(self) -> bool:
        """
        Test connection to storage backend

        Returns:
            True if connection successful, False otherwise
        """
        try:
            return self.connect() and self.is_connected()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
