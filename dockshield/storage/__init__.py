"""
Storage backends for DockShield
"""

from dockshield.storage.base import StorageBackend
from dockshield.storage.local import LocalStorage
from dockshield.storage.ssh import SSHStorage
from dockshield.storage.nfs import NFSStorage

__all__ = [
    "StorageBackend",
    "LocalStorage",
    "SSHStorage",
    "NFSStorage",
]
