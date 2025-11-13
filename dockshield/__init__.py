"""
DockShield - Docker Container Backup and Restore for KDE Plasma
"""

__version__ = "1.0.0"
__author__ = "DockShield Team"
__license__ = "GPL-3.0"

from dockshield.core.config import Config
from dockshield.core.docker_manager import DockerManager
from dockshield.core.backup_manager import BackupManager
from dockshield.core.restore_manager import RestoreManager

__all__ = [
    "Config",
    "DockerManager",
    "BackupManager",
    "RestoreManager",
]
