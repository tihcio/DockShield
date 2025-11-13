"""
SSH/SFTP storage backend for DockShield
"""

import paramiko
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import stat

from dockshield.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class SSHStorage(StorageBackend):
    """SSH/SFTP storage backend"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SSH storage

        Args:
            config: Storage configuration
        """
        super().__init__(config)
        self.host = config.get("host")
        self.port = config.get("port", 22)
        self.username = config.get("username")
        self.password = config.get("password")
        self.key_file = config.get("key_file")
        self.remote_path = config.get("remote_path", "/backups/dockshield")

        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.sftp_client: Optional[paramiko.SFTPClient] = None

    def connect(self) -> bool:
        """
        Connect to SSH server

        Returns:
            True if successful, False otherwise
        """
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect using key or password
            if self.key_file:
                key_path = Path(self.key_file).expanduser()
                self.ssh_client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=str(key_path),
                    timeout=30,
                )
            elif self.password:
                self.ssh_client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=30,
                )
            else:
                logger.error("No authentication method provided (key_file or password)")
                return False

            # Open SFTP session
            self.sftp_client = self.ssh_client.open_sftp()

            # Create remote directory if it doesn't exist
            self._mkdir_p(self.remote_path)

            logger.info(f"Connected to SSH storage: {self.username}@{self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to SSH storage: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from SSH server"""
        try:
            if self.sftp_client:
                self.sftp_client.close()
                self.sftp_client = None

            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None

            logger.info("Disconnected from SSH storage")

        except Exception as e:
            logger.error(f"Error disconnecting from SSH storage: {e}")

    def is_connected(self) -> bool:
        """
        Check if connected to SSH server

        Returns:
            True if connected, False otherwise
        """
        try:
            if self.ssh_client and self.sftp_client:
                # Try a simple operation to check connection
                self.sftp_client.listdir(".")
                return True
        except Exception:
            pass
        return False

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """
        Upload file via SFTP

        Args:
            local_path: Local file path
            remote_path: Remote file path (relative to remote_path)

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.sftp_client:
                logger.error("Not connected to SSH storage")
                return False

            full_remote_path = f"{self.remote_path}/{remote_path}"

            # Create remote directory if needed
            remote_dir = str(Path(full_remote_path).parent)
            self._mkdir_p(remote_dir)

            # Upload file
            self.sftp_client.put(str(local_path), full_remote_path)
            logger.debug(f"Uploaded {local_path} to {full_remote_path}")
            return True

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """
        Download file via SFTP

        Args:
            remote_path: Remote file path (relative to remote_path)
            local_path: Local file path

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.sftp_client:
                logger.error("Not connected to SSH storage")
                return False

            full_remote_path = f"{self.remote_path}/{remote_path}"

            # Create local directory if needed
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Download file
            self.sftp_client.get(full_remote_path, str(local_path))
            logger.debug(f"Downloaded {full_remote_path} to {local_path}")
            return True

        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        """
        Delete file via SFTP

        Args:
            remote_path: Remote file path (relative to remote_path)

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.sftp_client:
                logger.error("Not connected to SSH storage")
                return False

            full_remote_path = f"{self.remote_path}/{remote_path}"
            self.sftp_client.remove(full_remote_path)
            logger.debug(f"Deleted {full_remote_path}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

    def list_files(self, remote_path: str = "") -> List[str]:
        """
        List files via SFTP

        Args:
            remote_path: Remote directory path (relative to remote_path)

        Returns:
            List of file paths
        """
        try:
            if not self.sftp_client:
                logger.error("Not connected to SSH storage")
                return []

            full_remote_path = f"{self.remote_path}/{remote_path}" if remote_path else self.remote_path
            files = []

            def list_recursive(path: str):
                try:
                    for item in self.sftp_client.listdir_attr(path):
                        item_path = f"{path}/{item.filename}"
                        if stat.S_ISDIR(item.st_mode):
                            list_recursive(item_path)
                        else:
                            relative = item_path.replace(self.remote_path + "/", "")
                            files.append(relative)
                except Exception as e:
                    logger.warning(f"Error listing directory {path}: {e}")

            list_recursive(full_remote_path)
            return files

        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []

    def file_exists(self, remote_path: str) -> bool:
        """
        Check if file exists via SFTP

        Args:
            remote_path: Remote file path (relative to remote_path)

        Returns:
            True if file exists, False otherwise
        """
        try:
            if not self.sftp_client:
                return False

            full_remote_path = f"{self.remote_path}/{remote_path}"
            self.sftp_client.stat(full_remote_path)
            return True

        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False

    def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information via SFTP

        Args:
            remote_path: Remote file path (relative to remote_path)

        Returns:
            Dictionary with file information or None
        """
        try:
            if not self.sftp_client:
                return None

            full_remote_path = f"{self.remote_path}/{remote_path}"
            file_stat = self.sftp_client.stat(full_remote_path)

            return {
                "path": full_remote_path,
                "size": file_stat.st_size,
                "modified": file_stat.st_mtime,
                "is_directory": stat.S_ISDIR(file_stat.st_mode),
            }

        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None

    def _mkdir_p(self, remote_path: str) -> None:
        """Create directory recursively (like mkdir -p)"""
        try:
            dirs = []
            path = remote_path

            while path and path != "/":
                dirs.append(path)
                path = str(Path(path).parent)

            dirs.reverse()

            for directory in dirs:
                try:
                    self.sftp_client.stat(directory)
                except FileNotFoundError:
                    self.sftp_client.mkdir(directory)

        except Exception as e:
            logger.debug(f"Error creating directory {remote_path}: {e}")
