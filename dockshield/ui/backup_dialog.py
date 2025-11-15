"""
Backup dialog for DockShield
"""

from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QSpinBox, QPushButton, QGroupBox, QFormLayout,
    QLineEdit, QFileDialog
)
from PyQt6.QtCore import Qt

from dockshield.core.config import Config


class BackupDialog(QDialog):
    """Dialog for configuring backup options"""

    def __init__(self, parent, container_names: List[str], config: Config):
        """
        Initialize backup dialog

        Args:
            parent: Parent widget
            container_names: List of container names to backup
            config: Application configuration
        """
        super().__init__(parent)

        self.container_names = container_names
        self.config = config

        self.backup_dir_edit: QLineEdit = None
        self.backup_type_combo: QComboBox = None
        self.compression_spin: QSpinBox = None
        self.include_logs_check: QCheckBox = None
        self.verify_check: QCheckBox = None

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize user interface"""
        self.setWindowTitle("Backup Configuration")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout()

        # Container info
        info_label = QLabel(f"Backing up {len(self.container_names)} container(s):")
        layout.addWidget(info_label)

        container_list = QLabel("\n".join(f"  • {name}" for name in self.container_names))
        container_list.setStyleSheet("padding-left: 20px;")
        layout.addWidget(container_list)

        # Backup directory selection
        dir_group = QGroupBox("Backup Location")
        dir_layout = QHBoxLayout()

        dir_label = QLabel("Save to:")
        dir_layout.addWidget(dir_label)

        self.backup_dir_edit = QLineEdit()
        self.backup_dir_edit.setText(str(self.config.get_backup_dir()))
        self.backup_dir_edit.setPlaceholderText("Select backup directory...")
        dir_layout.addWidget(self.backup_dir_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_backup_dir)
        dir_layout.addWidget(browse_btn)

        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        # Backup options group
        options_group = QGroupBox("Backup Options")
        options_layout = QFormLayout()

        # Backup type
        self.backup_type_combo = QComboBox()
        self.backup_type_combo.addItems(["full", "filesystem"])
        self.backup_type_combo.setCurrentText(
            self.config.get("backup.default_type", "full")
        )
        self.backup_type_combo.setToolTip(
            "Full: Backup image, configuration, and filesystem\n"
            "Filesystem: Backup only container filesystem"
        )
        options_layout.addRow("Backup Type:", self.backup_type_combo)

        # Compression level
        self.compression_spin = QSpinBox()
        self.compression_spin.setRange(0, 9)
        self.compression_spin.setValue(
            self.config.get("backup.compression_level", 6)
        )
        self.compression_spin.setToolTip(
            "Compression level (0=none, 9=maximum)\n"
            "Higher levels = smaller size but slower"
        )
        options_layout.addRow("Compression Level:", self.compression_spin)

        # Include logs
        self.include_logs_check = QCheckBox("Include container logs")
        self.include_logs_check.setChecked(
            self.config.get("backup.include_logs", True)
        )
        options_layout.addRow("", self.include_logs_check)

        # Verify backup
        self.verify_check = QCheckBox("Verify backup integrity")
        self.verify_check.setChecked(
            self.config.get("backup.verify_integrity", True)
        )
        self.verify_check.setToolTip("Verify checksums after backup creation")
        options_layout.addRow("", self.verify_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        backup_btn = QPushButton("Start Backup")
        backup_btn.clicked.connect(self.accept)
        backup_btn.setDefault(True)
        button_layout.addWidget(backup_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _browse_backup_dir(self) -> None:
        """Browse for backup directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Directory",
            self.backup_dir_edit.text()
        )
        if directory:
            self.backup_dir_edit.setText(directory)

    def get_options(self) -> Dict[str, Any]:
        """
        Get selected backup options

        Returns:
            Dictionary with backup options
        """
        # Only include backup_dir if it's different from the default
        backup_dir = self.backup_dir_edit.text()
        default_dir = str(self.config.get_backup_dir())

        return {
            "backup_dir": backup_dir if backup_dir and backup_dir != default_dir else None,
            "backup_type": self.backup_type_combo.currentText(),
            "compression_level": self.compression_spin.value(),
            "include_logs": self.include_logs_check.isChecked(),
            "verify": self.verify_check.isChecked(),
        }
