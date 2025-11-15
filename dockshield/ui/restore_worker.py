"""
Background worker for restore operations
"""

from typing import Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal
import logging

from dockshield.core.restore_manager import RestoreManager
from dockshield.utils.notifications import NotificationManager

logger = logging.getLogger(__name__)


class RestoreWorker(QThread):
    """Worker thread for performing restore in background"""

    # Signals
    progress_update = pyqtSignal(int)  # Progress percentage (0-100)
    status_update = pyqtSignal(str)  # Status message
    detail_update = pyqtSignal(str)  # Detail message
    operation_update = pyqtSignal(str)  # Current operation
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(
        self,
        restore_manager: RestoreManager,
        notification_manager: NotificationManager,
        options: Dict[str, Any]
    ):
        """
        Initialize restore worker

        Args:
            restore_manager: Restore manager instance
            notification_manager: Notification manager instance
            options: Restore options
        """
        super().__init__()
        self.restore_manager = restore_manager
        self.notification_manager = notification_manager
        self.options = options

    def run(self) -> None:
        """Run restore operation"""
        container_name = self.options.get("container_name", "unknown")

        try:
            self.operation_update.emit("Restoring Container")
            self.status_update.emit(f"Preparing to restore: {container_name}")
            self.detail_update.emit(f"▶ Starting restore of '{container_name}'...")
            self.progress_update.emit(10)

            backup_id = self.options.get("backup_id")
            new_name = self.options.get("new_name")
            start_after_restore = self.options.get("start_after_restore", False)

            if not backup_id:
                raise ValueError("No backup ID specified")

            # Notify restore started
            self.notification_manager.notify_restore_started(container_name)
            self.detail_update.emit(f"  • Loading backup metadata...")
            self.progress_update.emit(20)

            # Get backup metadata
            metadata = self.restore_manager.backup_manager.get_backup_metadata(backup_id)
            if not metadata:
                raise ValueError(f"Backup not found: {backup_id}")

            backup_type = metadata.get("backup_type", "full")
            self.detail_update.emit(f"  • Backup type: {backup_type}")
            self.progress_update.emit(30)

            # Perform restore
            self.status_update.emit("Restoring container data...")
            self.detail_update.emit(f"  • Restoring container...")
            self.progress_update.emit(40)

            restored_container = self.restore_manager.restore_container(
                backup_id=backup_id,
                new_container_name=new_name,
                start_container=start_after_restore,
            )

            if restored_container:
                self.progress_update.emit(90)
                self.detail_update.emit(f"  ✓ Container restored successfully")

                if start_after_restore:
                    self.status_update.emit("Starting container...")
                    self.detail_update.emit(f"  • Starting container...")

                self.progress_update.emit(100)
                self.detail_update.emit(f"  ✓ Operation completed")

                final_name = new_name or container_name
                self.notification_manager.notify_restore_completed(final_name)
                logger.info(f"Restore completed: {final_name}")

                message = f"Container '{final_name}' restored successfully"
                self.finished.emit(True, message)
            else:
                raise ValueError("Restore operation returned no container")

        except Exception as e:
            error_msg = str(e)
            self.detail_update.emit(f"  ✗ Error: {error_msg}")
            self.notification_manager.notify_restore_failed(container_name, error_msg)
            logger.error(f"Error restoring {container_name}: {e}")
            self.finished.emit(False, f"Restore failed: {error_msg}")
