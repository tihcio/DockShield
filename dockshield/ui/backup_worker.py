"""
Background worker for backup operations
"""

from typing import List, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal
import logging

from dockshield.core.docker_manager import DockerManager
from dockshield.core.backup_manager import BackupManager
from dockshield.utils.notifications import NotificationManager

logger = logging.getLogger(__name__)


class BackupWorker(QThread):
    """Worker thread for performing backups in background"""

    # Signals
    progress_update = pyqtSignal(int)  # Progress percentage (0-100)
    status_update = pyqtSignal(str)  # Status message
    detail_update = pyqtSignal(str)  # Detail message
    operation_update = pyqtSignal(str)  # Current operation
    finished = pyqtSignal(bool, str, list)  # success, message, results

    def __init__(
        self,
        docker_manager: DockerManager,
        backup_manager: BackupManager,
        notification_manager: NotificationManager,
        container_names: List[str],
        options: Dict[str, Any]
    ):
        """
        Initialize backup worker

        Args:
            docker_manager: Docker manager instance
            backup_manager: Backup manager instance
            notification_manager: Notification manager instance
            container_names: List of container names to backup
            options: Backup options
        """
        super().__init__()
        self.docker_manager = docker_manager
        self.backup_manager = backup_manager
        self.notification_manager = notification_manager
        self.container_names = container_names
        self.options = options

    def run(self) -> None:
        """Run backup operation"""
        total_containers = len(self.container_names)
        success_count = 0
        results = []

        try:
            for i, name in enumerate(self.container_names):
                # Update progress
                base_progress = int((i / total_containers) * 100)
                self.progress_update.emit(base_progress)
                self.operation_update.emit(f"Backing up container {i + 1}/{total_containers}")
                self.status_update.emit(f"Processing: {name}")
                self.detail_update.emit(f"\n▶ Starting backup of '{name}'...")

                try:
                    # Get container
                    container = self.docker_manager.get_container(name)
                    if not container:
                        self.detail_update.emit(f"  ✗ Container not found: {name}")
                        results.append({"name": name, "success": False, "error": "Container not found"})
                        continue

                    # Notify backup started
                    self.notification_manager.notify_backup_started(name)

                    # Get custom backup directory if specified
                    backup_dir = None
                    if self.options.get("backup_dir"):
                        from pathlib import Path
                        backup_dir = Path(self.options.get("backup_dir"))

                    # Perform backup
                    self.detail_update.emit(f"  • Creating backup...")
                    metadata = self.backup_manager.create_backup(
                        container=container,
                        backup_type=self.options.get("backup_type", "full"),
                        compression_level=self.options.get("compression_level", 6),
                        include_logs=self.options.get("include_logs", True),
                        verify=self.options.get("verify", True),
                        destination=backup_dir,
                    )

                    if metadata:
                        size = metadata.get("size_human", "Unknown")
                        self.detail_update.emit(f"  ✓ Backup completed: {size}")
                        self.notification_manager.notify_backup_completed(name, size)
                        success_count += 1
                        results.append({"name": name, "success": True, "size": size})
                        logger.info(f"Backup completed: {name}")
                    else:
                        self.detail_update.emit(f"  ✗ Backup failed: Unknown error")
                        self.notification_manager.notify_backup_failed(name, "Unknown error")
                        results.append({"name": name, "success": False, "error": "Unknown error"})
                        logger.error(f"Backup failed: {name}")

                except Exception as e:
                    error_msg = str(e)
                    self.detail_update.emit(f"  ✗ Error: {error_msg}")
                    self.notification_manager.notify_backup_failed(name, error_msg)
                    results.append({"name": name, "success": False, "error": error_msg})
                    logger.error(f"Error backing up {name}: {e}")

            # Final progress
            self.progress_update.emit(100)

            # Send completion signal
            if success_count == total_containers:
                message = f"All {total_containers} container(s) backed up successfully"
                self.finished.emit(True, message, results)
            elif success_count > 0:
                failed_count = total_containers - success_count
                message = f"{success_count} succeeded, {failed_count} failed"
                self.finished.emit(True, message, results)
            else:
                message = f"All {total_containers} backup(s) failed"
                self.finished.emit(False, message, results)

        except Exception as e:
            logger.error(f"Fatal error in backup worker: {e}")
            self.finished.emit(False, f"Fatal error: {str(e)}", results)
