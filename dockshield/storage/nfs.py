"""
NFS storage backend for DockShield
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from dockshield.storage.local import LocalStorage

logger = logging.getLogger(__name__)


class NFSStorage(LocalStorage):
    """
    NFS storage backend

    Inherits from LocalStorage since NFS is mounted locally
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize NFS storage

        Args:
            config: Storage configuration
        """
        self.nfs_server = config.get("server")
        self.export_path = config.get("export_path")
        self.mount_point = Path(config.get("mount_point", "/mnt/nfs_backups"))
        self.mount_options = config.get("mount_options", "vers=4,rw")
        self.is_mounted = False

        # Initialize with mount point as base path
        config_with_mount = config.copy()
        config_with_mount["path"] = str(self.mount_point)
        super().__init__(config_with_mount)

    def connect(self) -> bool:
        """
        Mount NFS share

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if already mounted
            if self._check_mount():
                logger.info(f"NFS share already mounted at {self.mount_point}")
                self.is_mounted = True
                self.connected = True
                return True

            # Create mount point
            self.mount_point.mkdir(parents=True, exist_ok=True)

            # Mount NFS share
            mount_cmd = [
                "mount",
                "-t", "nfs",
                "-o", self.mount_options,
                f"{self.nfs_server}:{self.export_path}",
                str(self.mount_point)
            ]

            logger.info(f"Mounting NFS share: {' '.join(mount_cmd)}")

            result = subprocess.run(
                mount_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"Failed to mount NFS share: {result.stderr}")
                return False

            self.is_mounted = True
            self.connected = True
            logger.info(f"Successfully mounted NFS share at {self.mount_point}")
            return True

        except Exception as e:
            logger.error(f"Error mounting NFS share: {e}")
            return False

    def disconnect(self) -> None:
        """Unmount NFS share"""
        try:
            if not self.is_mounted:
                return

            # Unmount
            result = subprocess.run(
                ["umount", str(self.mount_point)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"Failed to unmount NFS share: {result.stderr}")
                # Try force unmount
                subprocess.run(
                    ["umount", "-f", str(self.mount_point)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

            self.is_mounted = False
            self.connected = False
            logger.info(f"Unmounted NFS share from {self.mount_point}")

        except Exception as e:
            logger.error(f"Error unmounting NFS share: {e}")

    def is_connected(self) -> bool:
        """
        Check if NFS share is mounted

        Returns:
            True if mounted, False otherwise
        """
        return self._check_mount()

    def _check_mount(self) -> bool:
        """Check if NFS share is currently mounted"""
        try:
            result = subprocess.run(
                ["mount"],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Check if mount point is in mount output
            mount_str = f"{self.nfs_server}:{self.export_path}"
            return mount_str in result.stdout and str(self.mount_point) in result.stdout

        except Exception as e:
            logger.error(f"Error checking mount status: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test NFS connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to mount
            if not self.connect():
                return False

            # Try to write a test file
            test_file = self.mount_point / ".dockshield_test"
            test_file.write_text("test")
            test_file.unlink()

            return True

        except Exception as e:
            logger.error(f"NFS connection test failed: {e}")
            return False
