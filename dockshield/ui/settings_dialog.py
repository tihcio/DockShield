"""
Settings dialog for DockShield
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QSpinBox, QCheckBox, QComboBox,
    QPushButton, QGroupBox, QFormLayout, QFileDialog,
    QMessageBox, QTextEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
import logging

from dockshield.core.config import Config
from dockshield.core.docker_manager import DockerManager

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Settings dialog"""

    def __init__(self, config: Config, parent=None, docker_manager: Optional[DockerManager] = None):
        """
        Initialize settings dialog

        Args:
            config: Application configuration
            parent: Parent widget
            docker_manager: Docker manager instance (optional)
        """
        super().__init__(parent)
        self.config = config
        self.docker_manager = docker_manager
        self.setWindowTitle("DockShield Settings")
        self.setMinimumSize(700, 600)
        self.setModal(True)

        # Store original values for cancel
        self.original_config = {}

        self._init_ui()
        self._load_settings()

    def _init_ui(self) -> None:
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Add tabs
        tabs.addTab(self._create_docker_tab(), "Docker")
        tabs.addTab(self._create_backup_tab(), "Backup")
        tabs.addTab(self._create_scheduler_tab(), "Scheduler")
        tabs.addTab(self._create_storage_tab(), "Storage")
        tabs.addTab(self._create_ui_tab(), "Interface")
        tabs.addTab(self._create_notifications_tab(), "Notifications")

        # Buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        button_layout.addStretch()

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.save_and_close)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

    def _create_docker_tab(self) -> QWidget:
        """Create Docker settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Docker connection settings
        group = QGroupBox("Docker Connection")
        group_layout = QFormLayout()
        group.setLayout(group_layout)
        layout.addWidget(group)

        self.docker_socket = QLineEdit()
        self.docker_socket.setPlaceholderText("unix:///var/run/docker.sock")
        group_layout.addRow("Docker Socket:", self.docker_socket)

        self.docker_timeout = QSpinBox()
        self.docker_timeout.setRange(10, 3600)
        self.docker_timeout.setSuffix(" seconds")
        group_layout.addRow("Connection Timeout:", self.docker_timeout)

        # Docker info
        info_group = QGroupBox("Docker Information")
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        self.docker_info = QLabel("Click 'Test Connection' to verify Docker connection")
        self.docker_info.setWordWrap(True)
        info_layout.addWidget(self.docker_info)

        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self._test_docker_connection)
        info_layout.addWidget(test_button)

        layout.addStretch()
        return widget

    def _create_backup_tab(self) -> QWidget:
        """Create backup settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Backup directory
        group = QGroupBox("Backup Storage")
        group_layout = QVBoxLayout()
        group.setLayout(group_layout)
        layout.addWidget(group)

        dir_layout = QHBoxLayout()
        group_layout.addLayout(dir_layout)

        dir_layout.addWidget(QLabel("Backup Directory:"))
        self.backup_dir = QLineEdit()
        dir_layout.addWidget(self.backup_dir)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_backup_dir)
        dir_layout.addWidget(browse_button)

        # Backup options
        options_group = QGroupBox("Backup Options")
        options_layout = QFormLayout()
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        self.compression_level = QSpinBox()
        self.compression_level.setRange(0, 9)
        self.compression_level.setSpecialValueText("No compression")
        options_layout.addRow("Compression Level:", self.compression_level)

        self.retention_count = QSpinBox()
        self.retention_count.setRange(1, 100)
        self.retention_count.setSpecialValueText("Keep all")
        options_layout.addRow("Keep Last N Backups:", self.retention_count)

        self.verify_checksum = QCheckBox("Verify backup integrity (SHA256)")
        options_layout.addRow("", self.verify_checksum)

        self.include_stopped = QCheckBox("Include stopped containers in auto-backup")
        options_layout.addRow("", self.include_stopped)

        layout.addStretch()
        return widget

    def _create_scheduler_tab(self) -> QWidget:
        """Create scheduler settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Scheduler enabled
        self.scheduler_enabled = QCheckBox("Enable Automatic Backups")
        self.scheduler_enabled.toggled.connect(self._on_scheduler_toggled)
        layout.addWidget(self.scheduler_enabled)

        # Schedule settings
        self.schedule_group = QGroupBox("Schedule Configuration")
        group_layout = QFormLayout()
        self.schedule_group.setLayout(group_layout)
        layout.addWidget(self.schedule_group)

        self.schedule_cron = QLineEdit()
        self.schedule_cron.setPlaceholderText("0 2 * * * (daily at 2:00 AM)")
        group_layout.addRow("Cron Expression:", self.schedule_cron)

        # Common presets
        presets_layout = QHBoxLayout()
        group_layout.addRow("Quick Presets:", presets_layout)

        daily_btn = QPushButton("Daily 2AM")
        daily_btn.clicked.connect(lambda: self.schedule_cron.setText("0 2 * * *"))
        presets_layout.addWidget(daily_btn)

        weekly_btn = QPushButton("Weekly Sunday")
        weekly_btn.clicked.connect(lambda: self.schedule_cron.setText("0 2 * * 0"))
        presets_layout.addWidget(weekly_btn)

        hourly_btn = QPushButton("Every Hour")
        hourly_btn.clicked.connect(lambda: self.schedule_cron.setText("0 * * * *"))
        presets_layout.addWidget(hourly_btn)

        presets_layout.addStretch()

        self.backup_type = QComboBox()
        self.backup_type.addItems(["Full Backup", "Filesystem Only"])
        group_layout.addRow("Default Backup Type:", self.backup_type)

        # Container selection
        container_group = QGroupBox("Auto-Backup Containers")
        container_layout = QVBoxLayout()
        container_group.setLayout(container_layout)
        layout.addWidget(container_group)

        self.auto_backup_all = QCheckBox("Backup all running containers")
        self.auto_backup_all.toggled.connect(self._on_backup_all_toggled)
        container_layout.addWidget(self.auto_backup_all)

        # Header with refresh button
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Select containers to backup:"))
        header_layout.addStretch()

        self.refresh_containers_btn = QPushButton("Refresh List")
        self.refresh_containers_btn.clicked.connect(self._load_available_containers)
        header_layout.addWidget(self.refresh_containers_btn)
        container_layout.addLayout(header_layout)

        # List of containers with checkboxes
        self.containers_list = QListWidget()
        self.containers_list.setMaximumHeight(150)
        container_layout.addWidget(self.containers_list)

        layout.addStretch()
        return widget

    def _create_storage_tab(self) -> QWidget:
        """Create storage settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Storage type
        group = QGroupBox("Default Storage Type")
        group_layout = QFormLayout()
        group.setLayout(group_layout)
        layout.addWidget(group)

        self.storage_type = QComboBox()
        self.storage_type.addItems(["Local", "NFS", "SSH/SFTP", "AWS S3"])
        self.storage_type.currentTextChanged.connect(self._on_storage_type_changed)
        group_layout.addRow("Storage Type:", self.storage_type)

        # Remote storage settings
        self.remote_group = QGroupBox("Remote Storage Configuration")
        remote_layout = QFormLayout()
        self.remote_group.setLayout(remote_layout)
        layout.addWidget(self.remote_group)

        self.remote_host = QLineEdit()
        self.remote_host.setPlaceholderText("hostname or IP address")
        remote_layout.addRow("Host:", self.remote_host)

        self.remote_port = QSpinBox()
        self.remote_port.setRange(1, 65535)
        self.remote_port.setValue(22)
        remote_layout.addRow("Port:", self.remote_port)

        self.remote_user = QLineEdit()
        remote_layout.addRow("Username:", self.remote_user)

        self.remote_path = QLineEdit()
        self.remote_path.setPlaceholderText("/path/to/backup/directory")
        remote_layout.addRow("Remote Path:", self.remote_path)

        # AWS S3 settings
        self.s3_group = QGroupBox("AWS S3 Configuration")
        s3_layout = QFormLayout()
        self.s3_group.setLayout(s3_layout)
        layout.addWidget(self.s3_group)

        self.s3_bucket = QLineEdit()
        s3_layout.addRow("S3 Bucket:", self.s3_bucket)

        self.s3_region = QLineEdit()
        self.s3_region.setPlaceholderText("us-east-1")
        s3_layout.addRow("Region:", self.s3_region)

        self.s3_prefix = QLineEdit()
        self.s3_prefix.setPlaceholderText("backups/")
        s3_layout.addRow("Prefix:", self.s3_prefix)

        layout.addStretch()
        return widget

    def _create_ui_tab(self) -> QWidget:
        """Create UI settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Appearance
        group = QGroupBox("Appearance")
        group_layout = QFormLayout()
        group.setLayout(group_layout)
        layout.addWidget(group)

        self.theme = QComboBox()
        self.theme.addItems(["Auto (System)", "Light", "Dark"])
        group_layout.addRow("Theme:", self.theme)

        # Language selector
        self.language = QComboBox()
        self.language.addItems(["Auto (System)", "English", "Italiano"])
        group_layout.addRow("Language:", self.language)

        self.show_system_tray = QCheckBox("Show system tray icon")
        group_layout.addRow("", self.show_system_tray)

        self.minimize_to_tray = QCheckBox("Minimize to system tray")
        group_layout.addRow("", self.minimize_to_tray)

        # Behavior
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QFormLayout()
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(1, 60)
        self.refresh_interval.setSuffix(" seconds")
        behavior_layout.addRow("Container List Refresh:", self.refresh_interval)

        self.confirm_actions = QCheckBox("Confirm before backup/restore")
        behavior_layout.addRow("", self.confirm_actions)

        self.auto_refresh = QCheckBox("Auto-refresh after operations")
        behavior_layout.addRow("", self.auto_refresh)

        layout.addStretch()
        return widget

    def _create_notifications_tab(self) -> QWidget:
        """Create notifications settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Enable notifications
        self.notifications_enabled = QCheckBox("Enable Desktop Notifications")
        self.notifications_enabled.toggled.connect(self._on_notifications_toggled)
        layout.addWidget(self.notifications_enabled)

        # Notification settings
        self.notif_group = QGroupBox("Notification Settings")
        group_layout = QFormLayout()
        self.notif_group.setLayout(group_layout)
        layout.addWidget(self.notif_group)

        self.notif_method = QComboBox()
        self.notif_method.addItems(["KDE (kdialog)", "notify-send", "System Default"])
        group_layout.addRow("Method:", self.notif_method)

        # Notification types
        types_group = QGroupBox("Notify On")
        types_layout = QVBoxLayout()
        types_group.setLayout(types_layout)
        layout.addWidget(types_group)

        self.notif_backup_success = QCheckBox("Backup completed successfully")
        types_layout.addWidget(self.notif_backup_success)

        self.notif_backup_error = QCheckBox("Backup failed")
        types_layout.addWidget(self.notif_backup_error)

        self.notif_restore_success = QCheckBox("Restore completed successfully")
        types_layout.addWidget(self.notif_restore_success)

        self.notif_restore_error = QCheckBox("Restore failed")
        types_layout.addWidget(self.notif_restore_error)

        self.notif_scheduled = QCheckBox("Scheduled backup started")
        types_layout.addWidget(self.notif_scheduled)

        layout.addStretch()
        return widget

    def _load_settings(self) -> None:
        """Load settings from configuration"""
        # Docker
        self.docker_socket.setText(self.config.get("docker.socket", "unix:///var/run/docker.sock"))
        self.docker_timeout.setValue(self.config.get("docker.timeout", 300))

        # Backup
        self.backup_dir.setText(str(self.config.get_backup_dir()))
        self.compression_level.setValue(self.config.get("backup.compression_level", 6))
        self.retention_count.setValue(self.config.get("backup.retention.count", 10))
        self.verify_checksum.setChecked(self.config.get("backup.verify_integrity", True))
        self.include_stopped.setChecked(self.config.get("backup.include_stopped", False))

        # Scheduler
        scheduler_config = self.config.get("scheduler", {})
        self.scheduler_enabled.setChecked(scheduler_config.get("enabled", False))
        self.schedule_cron.setText(scheduler_config.get("cron_expression", "0 2 * * *"))

        backup_type = scheduler_config.get("backup_type", "full")
        self.backup_type.setCurrentText("Full Backup" if backup_type == "full" else "Filesystem Only")

        # Load available containers first
        self._load_available_containers()

        # Load selected containers from config
        containers = scheduler_config.get("containers", [])
        self.auto_backup_all.setChecked(len(containers) == 0)

        # Check the containers that are in the config
        for i in range(self.containers_list.count()):
            item = self.containers_list.item(i)
            container_name = item.data(Qt.ItemDataRole.UserRole)
            if container_name in containers:
                item.setCheckState(Qt.CheckState.Checked)

        # Storage
        storage_config = self.config.get("storage", {})
        storage_type = storage_config.get("type", "local")
        type_map = {"local": "Local", "nfs": "NFS", "ssh": "SSH/SFTP", "s3": "AWS S3"}
        self.storage_type.setCurrentText(type_map.get(storage_type, "Local"))

        ssh_config = storage_config.get("ssh", {})
        self.remote_host.setText(ssh_config.get("host", ""))
        self.remote_port.setValue(ssh_config.get("port", 22))
        self.remote_user.setText(ssh_config.get("username", ""))
        self.remote_path.setText(ssh_config.get("remote_path", ""))

        s3_config = storage_config.get("s3", {})
        self.s3_bucket.setText(s3_config.get("bucket", ""))
        self.s3_region.setText(s3_config.get("region", "us-east-1"))
        self.s3_prefix.setText(s3_config.get("prefix", ""))

        # UI
        ui_config = self.config.get("ui", {})
        theme = ui_config.get("theme", "auto")
        theme_map = {"auto": "Auto (System)", "light": "Light", "dark": "Dark"}
        self.theme.setCurrentText(theme_map.get(theme, "Auto (System)"))

        # Language
        language = ui_config.get("language", "auto")
        language_map = {"auto": "Auto (System)", "en": "English", "it": "Italiano"}
        self.language.setCurrentText(language_map.get(language, "Auto (System)"))

        self.refresh_interval.setValue(ui_config.get("refresh_interval", 5))
        self.show_system_tray.setChecked(ui_config.get("system_tray", True))
        self.minimize_to_tray.setChecked(ui_config.get("minimize_to_tray", True))
        self.confirm_actions.setChecked(ui_config.get("confirm_actions", True))
        self.auto_refresh.setChecked(ui_config.get("auto_refresh", True))

        # Notifications
        notif_config = self.config.get("notifications", {})
        self.notifications_enabled.setChecked(notif_config.get("enabled", True))

        method = notif_config.get("method", "kdialog")
        method_map = {"kdialog": "KDE (kdialog)", "notify-send": "notify-send", "auto": "System Default"}
        self.notif_method.setCurrentText(method_map.get(method, "KDE (kdialog)"))

        self.notif_backup_success.setChecked(notif_config.get("backup_success", True))
        self.notif_backup_error.setChecked(notif_config.get("backup_error", True))
        self.notif_restore_success.setChecked(notif_config.get("restore_success", True))
        self.notif_restore_error.setChecked(notif_config.get("restore_error", True))
        self.notif_scheduled.setChecked(notif_config.get("scheduled_backup", True))

        # Update UI state
        self._on_scheduler_toggled(self.scheduler_enabled.isChecked())
        self._on_notifications_toggled(self.notifications_enabled.isChecked())
        self._on_storage_type_changed(self.storage_type.currentText())
        self._on_backup_all_toggled(self.auto_backup_all.isChecked())

    def _save_to_config(self) -> bool:
        """Save settings to configuration"""
        try:
            # Docker
            self.config.set("docker.socket", self.docker_socket.text())
            self.config.set("docker.timeout", self.docker_timeout.value())

            # Backup
            self.config.set("backup.directory", self.backup_dir.text())
            self.config.set("backup.compression_level", self.compression_level.value())
            self.config.set("backup.retention.count", self.retention_count.value())
            self.config.set("backup.verify_integrity", self.verify_checksum.isChecked())
            self.config.set("backup.include_stopped", self.include_stopped.isChecked())

            # Scheduler
            backup_type = "full" if self.backup_type.currentText() == "Full Backup" else "filesystem"

            # Get selected containers from the list
            containers = []
            if not self.auto_backup_all.isChecked():
                for i in range(self.containers_list.count()):
                    item = self.containers_list.item(i)
                    if item.checkState() == Qt.CheckState.Checked:
                        container_name = item.data(Qt.ItemDataRole.UserRole)
                        containers.append(container_name)

            self.config.set("scheduler.enabled", self.scheduler_enabled.isChecked())
            self.config.set("scheduler.cron_expression", self.schedule_cron.text())
            self.config.set("scheduler.backup_type", backup_type)
            self.config.set("scheduler.containers", containers)

            # Storage
            type_map = {"Local": "local", "NFS": "nfs", "SSH/SFTP": "ssh", "AWS S3": "s3"}
            self.config.set("storage.type", type_map.get(self.storage_type.currentText(), "local"))

            self.config.set("storage.ssh.host", self.remote_host.text())
            self.config.set("storage.ssh.port", self.remote_port.value())
            self.config.set("storage.ssh.username", self.remote_user.text())
            self.config.set("storage.ssh.remote_path", self.remote_path.text())

            self.config.set("storage.s3.bucket", self.s3_bucket.text())
            self.config.set("storage.s3.region", self.s3_region.text())
            self.config.set("storage.s3.prefix", self.s3_prefix.text())

            # UI
            theme_map = {"Auto (System)": "auto", "Light": "light", "Dark": "dark"}
            self.config.set("ui.theme", theme_map.get(self.theme.currentText(), "auto"))

            # Language
            language_map = {"Auto (System)": "auto", "English": "en", "Italiano": "it"}
            self.config.set("ui.language", language_map.get(self.language.currentText(), "auto"))

            self.config.set("ui.refresh_interval", self.refresh_interval.value())
            self.config.set("ui.system_tray", self.show_system_tray.isChecked())
            self.config.set("ui.minimize_to_tray", self.minimize_to_tray.isChecked())
            self.config.set("ui.confirm_actions", self.confirm_actions.isChecked())
            self.config.set("ui.auto_refresh", self.auto_refresh.isChecked())

            # Notifications
            method_map = {"KDE (kdialog)": "kdialog", "notify-send": "notify-send", "System Default": "auto"}
            self.config.set("notifications.enabled", self.notifications_enabled.isChecked())
            self.config.set("notifications.method", method_map.get(self.notif_method.currentText(), "kdialog"))
            self.config.set("notifications.backup_success", self.notif_backup_success.isChecked())
            self.config.set("notifications.backup_error", self.notif_backup_error.isChecked())
            self.config.set("notifications.restore_success", self.notif_restore_success.isChecked())
            self.config.set("notifications.restore_error", self.notif_restore_error.isChecked())
            self.config.set("notifications.scheduled_backup", self.notif_scheduled.isChecked())

            # Save to file
            self.config.save()
            return True

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")
            return False

    def save_and_close(self) -> None:
        """Save settings and close dialog"""
        if self._save_to_config():
            self.accept()

    def _browse_backup_dir(self) -> None:
        """Browse for backup directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Directory",
            self.backup_dir.text()
        )
        if directory:
            self.backup_dir.setText(directory)

    def _test_docker_connection(self) -> None:
        """Test Docker connection"""
        try:
            from dockshield.core.docker_manager import DockerManager

            socket_url = self.docker_socket.text()
            timeout = self.docker_timeout.value()

            manager = DockerManager(socket_url, timeout)

            if manager.is_connected():
                # Get Docker info
                info = manager.client.info()
                version = manager.client.version()

                self.docker_info.setText(
                    f"✓ Connected to Docker daemon\n\n"
                    f"Docker Version: {version.get('Version', 'Unknown')}\n"
                    f"API Version: {version.get('ApiVersion', 'Unknown')}\n"
                    f"OS/Arch: {info.get('OperatingSystem', 'Unknown')} / {info.get('Architecture', 'Unknown')}\n"
                    f"Containers: {info.get('Containers', 0)} total, "
                    f"{info.get('ContainersRunning', 0)} running\n"
                    f"Images: {info.get('Images', 0)}"
                )

                QMessageBox.information(
                    self,
                    "Connection Successful",
                    "Successfully connected to Docker daemon!"
                )
            else:
                self.docker_info.setText("✗ Failed to connect to Docker daemon")
                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    "Could not connect to Docker daemon.\n\n"
                    "Please check the socket URL and ensure Docker is running."
                )

            manager.close()

        except Exception as e:
            self.docker_info.setText(f"✗ Error: {e}")
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to connect to Docker:\n\n{e}"
            )

    def _on_scheduler_toggled(self, checked: bool) -> None:
        """Handle scheduler enabled toggle"""
        self.schedule_group.setEnabled(checked)

    def _on_notifications_toggled(self, checked: bool) -> None:
        """Handle notifications enabled toggle"""
        self.notif_group.setEnabled(checked)

    def _on_storage_type_changed(self, storage_type: str) -> None:
        """Handle storage type change"""
        self.remote_group.setVisible(storage_type in ["NFS", "SSH/SFTP"])
        self.s3_group.setVisible(storage_type == "AWS S3")

    def _on_backup_all_toggled(self, checked: bool) -> None:
        """Handle backup all containers toggle"""
        self.containers_list.setEnabled(not checked)
        self.refresh_containers_btn.setEnabled(not checked)

    def _load_available_containers(self) -> None:
        """Load available Docker containers into the list"""
        self.containers_list.clear()

        if not self.docker_manager:
            # Try to create a temporary connection
            try:
                socket_url = self.config.get("docker.socket", "unix:///var/run/docker.sock")
                timeout = self.config.get("docker.timeout", 300)
                temp_manager = DockerManager(socket_url, timeout)

                if temp_manager.is_connected():
                    containers = temp_manager.get_containers(all_containers=True)
                    temp_manager.close()
                else:
                    temp_manager.close()
                    QMessageBox.warning(
                        self,
                        "Docker Connection",
                        "Could not connect to Docker. Please check your Docker settings."
                    )
                    return
            except Exception as e:
                logger.error(f"Failed to connect to Docker: {e}")
                QMessageBox.warning(
                    self,
                    "Docker Connection Error",
                    f"Failed to load containers:\n{e}\n\nPlease check your Docker connection."
                )
                return
        else:
            try:
                containers = self.docker_manager.get_containers(all_containers=True)
            except Exception as e:
                logger.error(f"Failed to get containers: {e}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to load containers:\n{e}"
                )
                return

        # Add containers to the list with checkboxes
        for container in containers:
            item = QListWidgetItem(f"{container.name} ({container.status})")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, container.name)  # Store container name
            self.containers_list.addItem(item)
