"""
Main window for DockShield
"""

import sys
from typing import Optional, List
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QGroupBox, QMessageBox,
    QSystemTrayIcon, QMenu, QStatusBar, QToolBar, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
import logging

from dockshield.core.config import Config
from dockshield.core.docker_manager import DockerManager
from dockshield.core.backup_manager import BackupManager
from dockshield.core.restore_manager import RestoreManager
from dockshield.scheduler.scheduler import BackupScheduler
from dockshield.utils.notifications import NotificationManager
from dockshield.utils.translations import get_translator, tr
from dockshield.ui.backup_dialog import BackupDialog
from dockshield.ui.restore_dialog import RestoreDialog
from dockshield.ui.history_dialog import HistoryDialog
from dockshield.ui.settings_dialog import SettingsDialog
from dockshield.ui.progress_dialog import ProgressDialog
from dockshield.ui.backup_worker import BackupWorker
from dockshield.ui.restore_worker import RestoreWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""

    # Signals
    backup_completed = pyqtSignal(dict)
    restore_completed = pyqtSignal(str)

    def __init__(self, config: Config):
        """
        Initialize main window

        Args:
            config: Application configuration
        """
        super().__init__()

        self.config = config
        self.docker_manager: Optional[DockerManager] = None
        self.backup_manager: Optional[BackupManager] = None
        self.restore_manager: Optional[RestoreManager] = None
        self.scheduler: Optional[BackupScheduler] = None
        self.notification_manager: Optional[NotificationManager] = None

        # UI components
        self.container_table: Optional[QTableWidget] = None
        self.status_label: Optional[QLabel] = None
        self.system_tray: Optional[QSystemTrayIcon] = None

        # Refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_containers)

        # Initialize translator
        self._init_translator()

        # Initialize managers
        self._init_managers()

        # Setup UI
        self._init_ui()
        self._setup_system_tray()
        self._apply_theme()

        # Start refresh timer
        refresh_interval = self.config.get("ui.refresh_interval", 5) * 1000
        self.refresh_timer.start(refresh_interval)

        # Initial refresh
        self.refresh_containers()

    def _init_translator(self) -> None:
        """Initialize translation system"""
        translator = get_translator()

        # Get configured language
        language = self.config.get("ui.language", "auto")

        if language == "auto":
            # Detect system language
            language = translator.detect_system_language()

        # Set language
        translator.set_language(language)
        logger.info(f"Language set to: {translator.get_current_language_name()}")

    def _init_managers(self) -> None:
        """Initialize application managers"""
        try:
            # Docker manager
            docker_socket = self.config.get("docker.socket")
            docker_timeout = self.config.get("docker.timeout", 300)
            self.docker_manager = DockerManager(docker_socket, docker_timeout)

            # Backup manager
            backup_dir = self.config.get_backup_dir()
            self.backup_manager = BackupManager(self.docker_manager, backup_dir)

            # Restore manager
            self.restore_manager = RestoreManager(self.docker_manager, self.backup_manager)

            # Scheduler
            scheduler_config = self.config.get("scheduler", {})
            self.scheduler = BackupScheduler(scheduler_config)

            if scheduler_config.get("enabled"):
                self.scheduler.setup_jobs(self._scheduled_backup_callback)
                self.scheduler.start()

            # Notification manager
            notif_config = self.config.get("notifications", {})
            self.notification_manager = NotificationManager(
                enabled=notif_config.get("desktop_enabled", True),
                sound_enabled=notif_config.get("sound_enabled", True)
            )

            logger.info("Application managers initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing managers: {e}")
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize application:\n{e}"
            )
            sys.exit(1)

    def _init_ui(self) -> None:
        """Initialize user interface"""
        # Window properties
        window_config = self.config.get("ui.window", {})
        self.setWindowTitle(tr("app_title", "DockShield - Docker Backup Manager"))
        self.resize(
            window_config.get("width", 1200),
            window_config.get("height", 800)
        )

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Toolbar
        self._create_toolbar()

        # Create splitter for containers and info
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Container list group
        container_group = self._create_container_list()
        splitter.addWidget(container_group)

        # Action buttons
        button_layout = self._create_action_buttons()
        main_layout.addLayout(button_layout)

        main_layout.addWidget(splitter)

        # Status bar
        self._create_status_bar()

    def _create_toolbar(self) -> None:
        """Create application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_containers)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)

        # History action
        history_action = QAction("History", self)
        history_action.triggered.connect(self.show_history)
        toolbar.addAction(history_action)

        toolbar.addSeparator()

        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)

    def _create_container_list(self) -> QGroupBox:
        """Create container list widget"""
        group = QGroupBox(tr("docker_containers", "Docker Containers"))
        layout = QVBoxLayout()

        # Container table
        self.container_table = QTableWidget()
        self.container_table.setColumnCount(5)
        self.container_table.setHorizontalHeaderLabels([
            "Name", "Status", "Image", "Created", "ID"
        ])
        self.container_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.container_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.container_table.setAlternatingRowColors(True)

        # Stretch columns
        header = self.container_table.horizontalHeader()
        header.setStretchLastSection(True)

        layout.addWidget(self.container_table)
        group.setLayout(layout)

        return group

    def _create_action_buttons(self) -> QHBoxLayout:
        """Create action buttons layout"""
        layout = QHBoxLayout()

        # Container management section
        container_label = QLabel(f"<b>{tr('container_label', 'Container:')}</b>")
        layout.addWidget(container_label)

        # Start button
        self.start_btn = QPushButton(tr("btn_start", "▶ Start"))
        self.start_btn.setToolTip(tr("tooltip_start", "Start selected containers"))
        self.start_btn.clicked.connect(self.start_selected_containers)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        layout.addWidget(self.start_btn)

        # Stop button
        self.stop_btn = QPushButton(tr("btn_stop", "⏹ Stop"))
        self.stop_btn.setToolTip(tr("tooltip_stop", "Stop selected containers"))
        self.stop_btn.clicked.connect(self.stop_selected_containers)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        layout.addWidget(self.stop_btn)

        # Restart button
        self.restart_btn = QPushButton(tr("btn_restart", "⟳ Restart"))
        self.restart_btn.setToolTip(tr("tooltip_restart", "Restart selected containers"))
        self.restart_btn.clicked.connect(self.restart_selected_containers)
        self.restart_btn.setEnabled(False)
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        layout.addWidget(self.restart_btn)

        # Separator
        layout.addSpacing(20)
        separator1 = QLabel("|")
        separator1.setStyleSheet("color: #888;")
        layout.addWidget(separator1)
        layout.addSpacing(20)

        # Backup section
        backup_label = QLabel(f"<b>{tr('backup_label', 'Backup:')}</b>")
        layout.addWidget(backup_label)

        # Backup button
        self.backup_btn = QPushButton(tr("btn_backup", "💾 Backup"))
        self.backup_btn.setToolTip(tr("tooltip_backup", "Backup selected containers"))
        self.backup_btn.clicked.connect(self.backup_selected_containers)
        self.backup_btn.setEnabled(False)
        layout.addWidget(self.backup_btn)

        # Restore button
        restore_btn = QPushButton(tr("btn_restore", "📥 Restore"))
        restore_btn.setToolTip(tr("tooltip_restore", "Restore container from backup"))
        restore_btn.clicked.connect(self.restore_container)
        layout.addWidget(restore_btn)

        # History button
        history_btn = QPushButton(tr("btn_history", "📜 History"))
        history_btn.setToolTip(tr("tooltip_history", "View backup history"))
        history_btn.clicked.connect(self.show_history)
        layout.addWidget(history_btn)

        layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton(tr("btn_refresh", "🔄 Refresh"))
        refresh_btn.setToolTip(tr("tooltip_refresh", "Refresh container list"))
        refresh_btn.clicked.connect(self.refresh_containers)
        layout.addWidget(refresh_btn)

        # Connect selection change to update button states
        self.container_table.itemSelectionChanged.connect(self._update_button_states)

        return layout

    def _create_status_bar(self) -> None:
        """Create status bar"""
        self.status_label = QLabel("Ready")
        self.statusBar().addPermanentWidget(self.status_label)

    def _setup_system_tray(self) -> None:
        """Setup system tray icon"""
        if not self.config.get("ui.system_tray", True):
            return

        try:
            self.system_tray = QSystemTrayIcon(self)
            # Set icon (would need actual icon file)
            # self.system_tray.setIcon(QIcon(":/icons/dockshield.png"))

            # Tray menu
            tray_menu = QMenu()

            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)

            hide_action = QAction("Hide", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)

            tray_menu.addSeparator()

            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)

            self.system_tray.setContextMenu(tray_menu)
            self.system_tray.show()

        except Exception as e:
            logger.warning(f"Could not setup system tray: {e}")

    def _apply_theme(self) -> None:
        """Apply theme based on configuration"""
        theme = self.config.get("ui.theme", "auto")

        if theme == "dark":
            # Apply dark theme stylesheet
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #2b2b2b;
                    color: #f0f0f0;
                }
                QTableWidget {
                    background-color: #353535;
                    alternate-background-color: #2b2b2b;
                }
                QPushButton {
                    background-color: #454545;
                    border: 1px solid #555;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
            """)
        # Auto and light themes use system default

    def refresh_containers(self) -> None:
        """Refresh container list"""
        try:
            if not self.docker_manager or not self.docker_manager.is_connected():
                self.status_label.setText("Docker: Disconnected")
                return

            containers = self.docker_manager.get_containers(all_containers=True)

            # Update table
            self.container_table.setRowCount(len(containers))

            for i, container in enumerate(containers):
                info = self.docker_manager.get_container_info(container)

                self.container_table.setItem(i, 0, QTableWidgetItem(info.get("name", "N/A")))
                self.container_table.setItem(i, 1, QTableWidgetItem(info.get("status", "N/A")))
                self.container_table.setItem(i, 2, QTableWidgetItem(info.get("image", "N/A")))
                self.container_table.setItem(i, 3, QTableWidgetItem(info.get("created", "N/A")))
                self.container_table.setItem(i, 4, QTableWidgetItem(info.get("short_id", "N/A")))

            self.status_label.setText(f"Docker: Connected | Containers: {len(containers)}")

        except Exception as e:
            logger.error(f"Error refreshing containers: {e}")
            self.status_label.setText(f"Error: {e}")

    def backup_selected_containers(self) -> None:
        """Backup selected containers"""
        selected_rows = self.container_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select containers to backup")
            return

        container_names = []
        for row in selected_rows:
            name = self.container_table.item(row.row(), 0).text()
            container_names.append(name)

        # Show backup dialog
        dialog = BackupDialog(self, container_names, self.config)
        if dialog.exec():
            backup_options = dialog.get_options()
            self._perform_backup(container_names, backup_options)

    def _perform_backup(self, container_names: List[str], options: dict) -> None:
        """Perform backup operation using background worker"""
        # Create progress dialog
        progress_dialog = ProgressDialog(self, "Backup in Progress")
        progress_dialog.set_operation("Preparing backup...")

        # Create worker thread
        self.backup_worker = BackupWorker(
            self.docker_manager,
            self.backup_manager,
            self.notification_manager,
            container_names,
            options
        )

        # Connect signals
        self.backup_worker.progress_update.connect(progress_dialog.set_progress)
        self.backup_worker.status_update.connect(progress_dialog.set_status)
        self.backup_worker.detail_update.connect(progress_dialog.add_detail)
        self.backup_worker.operation_update.connect(progress_dialog.set_operation)
        self.backup_worker.finished.connect(
            lambda success, msg, results: self._on_backup_finished(progress_dialog, success, msg, results)
        )

        # Start worker
        self.backup_worker.start()

        # Show progress dialog (blocks until finished)
        progress_dialog.exec()

    def _on_backup_finished(self, dialog: ProgressDialog, success: bool, message: str, results: list) -> None:
        """Handle backup completion"""
        dialog.operation_finished(success, message)
        self.status_label.setText("Backup completed")
        self.refresh_containers()

    def start_selected_containers(self) -> None:
        """Start selected containers"""
        selected_rows = self.container_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select containers to start")
            return

        container_names = []
        for row in selected_rows:
            name = self.container_table.item(row.row(), 0).text()
            container_names.append(name)

        # Confirm action
        reply = QMessageBox.question(
            self,
            "Start Containers",
            f"Start {len(container_names)} container(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Start containers
        success_count = 0
        failed = []

        for name in container_names:
            try:
                container = self.docker_manager.get_container(name)
                if not container:
                    failed.append(f"{name} (not found)")
                    continue

                self.status_label.setText(f"Starting {name}...")

                if self.docker_manager.start_container(container):
                    success_count += 1
                    logger.info(f"Container started: {name}")
                else:
                    failed.append(f"{name} (failed to start)")
                    logger.error(f"Failed to start container: {name}")

            except Exception as e:
                failed.append(f"{name} ({str(e)})")
                logger.error(f"Error starting {name}: {e}")

        # Refresh container list
        self.refresh_containers()

        # Show result
        message = f"Successfully started {success_count} container(s)"
        if failed:
            message += f"\n\nFailed:\n" + "\n".join(failed)
            QMessageBox.warning(self, "Start Completed", message)
        else:
            self.status_label.setText(f"Started {success_count} container(s)")
            QMessageBox.information(self, "Success", message)

    def stop_selected_containers(self) -> None:
        """Stop selected containers"""
        selected_rows = self.container_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select containers to stop")
            return

        container_names = []
        for row in selected_rows:
            name = self.container_table.item(row.row(), 0).text()
            container_names.append(name)

        # Confirm action
        reply = QMessageBox.question(
            self,
            "Stop Containers",
            f"Stop {len(container_names)} container(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Stop containers
        success_count = 0
        failed = []

        for name in container_names:
            try:
                container = self.docker_manager.get_container(name)
                if not container:
                    failed.append(f"{name} (not found)")
                    continue

                self.status_label.setText(f"Stopping {name}...")

                if self.docker_manager.stop_container(container):
                    success_count += 1
                    logger.info(f"Container stopped: {name}")
                else:
                    failed.append(f"{name} (failed to stop)")
                    logger.error(f"Failed to stop container: {name}")

            except Exception as e:
                failed.append(f"{name} ({str(e)})")
                logger.error(f"Error stopping {name}: {e}")

        # Refresh container list
        self.refresh_containers()

        # Show result
        message = f"Successfully stopped {success_count} container(s)"
        if failed:
            message += f"\n\nFailed:\n" + "\n".join(failed)
            QMessageBox.warning(self, "Stop Completed", message)
        else:
            self.status_label.setText(f"Stopped {success_count} container(s)")
            QMessageBox.information(self, "Success", message)

    def restart_selected_containers(self) -> None:
        """Restart selected containers"""
        selected_rows = self.container_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select containers to restart")
            return

        container_names = []
        for row in selected_rows:
            name = self.container_table.item(row.row(), 0).text()
            container_names.append(name)

        # Confirm action
        reply = QMessageBox.question(
            self,
            "Restart Containers",
            f"Restart {len(container_names)} container(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Restart containers (stop then start)
        success_count = 0
        failed = []

        for name in container_names:
            try:
                container = self.docker_manager.get_container(name)
                if not container:
                    failed.append(f"{name} (not found)")
                    continue

                self.status_label.setText(f"Restarting {name}...")

                # Stop first
                if not self.docker_manager.stop_container(container):
                    failed.append(f"{name} (failed to stop)")
                    continue

                # Then start
                if self.docker_manager.start_container(container):
                    success_count += 1
                    logger.info(f"Container restarted: {name}")
                else:
                    failed.append(f"{name} (failed to start)")
                    logger.error(f"Failed to restart container: {name}")

            except Exception as e:
                failed.append(f"{name} ({str(e)})")
                logger.error(f"Error restarting {name}: {e}")

        # Refresh container list
        self.refresh_containers()

        # Show result
        message = f"Successfully restarted {success_count} container(s)"
        if failed:
            message += f"\n\nFailed:\n" + "\n".join(failed)
            QMessageBox.warning(self, "Restart Completed", message)
        else:
            self.status_label.setText(f"Restarted {success_count} container(s)")
            QMessageBox.information(self, "Success", message)

    def _update_button_states(self) -> None:
        """Update button states based on selection"""
        selected_rows = self.container_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0

        # Enable/disable buttons based on selection
        self.start_btn.setEnabled(has_selection)
        self.stop_btn.setEnabled(has_selection)
        self.restart_btn.setEnabled(has_selection)
        self.backup_btn.setEnabled(has_selection)

    def restore_container(self) -> None:
        """Restore container from backup"""
        dialog = RestoreDialog(self, self.backup_manager, self.config)
        if dialog.exec():
            restore_options = dialog.get_options()
            self._perform_restore(restore_options)

    def _perform_restore(self, options: dict) -> None:
        """Perform restore operation using background worker"""
        # Create progress dialog
        progress_dialog = ProgressDialog(self, "Restore in Progress")
        progress_dialog.set_operation("Preparing restore...")

        # Create worker thread
        self.restore_worker = RestoreWorker(
            self.restore_manager,
            self.notification_manager,
            options
        )

        # Connect signals
        self.restore_worker.progress_update.connect(progress_dialog.set_progress)
        self.restore_worker.status_update.connect(progress_dialog.set_status)
        self.restore_worker.detail_update.connect(progress_dialog.add_detail)
        self.restore_worker.operation_update.connect(progress_dialog.set_operation)
        self.restore_worker.finished.connect(
            lambda success, msg: self._on_restore_finished(progress_dialog, success, msg)
        )

        # Start worker
        self.restore_worker.start()

        # Show progress dialog (blocks until finished)
        progress_dialog.exec()

    def _on_restore_finished(self, dialog: ProgressDialog, success: bool, message: str) -> None:
        """Handle restore completion"""
        dialog.operation_finished(success, message)
        self.status_label.setText("Restore completed")
        self.refresh_containers()

    def show_history(self) -> None:
        """Show backup history"""
        dialog = HistoryDialog(self, self.backup_manager)
        dialog.exec()

    def show_settings(self) -> None:
        """Show settings dialog"""
        dialog = SettingsDialog(self.config, self, self.docker_manager)
        if dialog.exec():
            # Settings were saved
            # Note: Some settings may require a restart to take effect
            pass

    def show_about(self) -> None:
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About DockShield",
            "<h2>DockShield 0.6.0 Beta</h2>"
            "<p>Docker Container Backup and Restore for KDE Plasma</p>"
            "<p><b>This is a beta version - use with caution!</b></p>"
            "<p>Copyright © 2025 Tiziano Angeli</p>"
            "<p>Licensed under GPL-3.0</p>"
        )

    def _scheduled_backup_callback(self, job_config: dict) -> None:
        """Callback for scheduled backups"""
        try:
            container_names = job_config.get("containers", [])
            if container_names == "all":
                containers = self.docker_manager.get_containers()
                container_names = [c.name for c in containers]

            backup_options = {
                "backup_type": job_config.get("backup_type", "full"),
                "compression_level": self.config.get("backup.compression_level", 6),
                "include_logs": self.config.get("backup.include_logs", True),
                "verify": self.config.get("backup.verify_integrity", True),
            }

            self._perform_backup(container_names, backup_options)

        except Exception as e:
            logger.error(f"Error in scheduled backup: {e}")

    def closeEvent(self, event) -> None:
        """Handle window close event"""
        if self.config.get("ui.minimize_to_tray", True) and self.system_tray:
            event.ignore()
            self.hide()
        else:
            self.quit_application()

    def quit_application(self) -> None:
        """Quit application"""
        # Stop scheduler
        if self.scheduler:
            self.scheduler.stop()

        # Close Docker connection
        if self.docker_manager:
            self.docker_manager.close()

        # Save configuration
        try:
            self.config.save()
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

        # Quit
        sys.exit(0)
