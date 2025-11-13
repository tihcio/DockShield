"""
Restore dialog for DockShield
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QGroupBox, QFormLayout, QLineEdit,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt
from datetime import datetime

from dockshield.core.config import Config
from dockshield.core.backup_manager import BackupManager


class RestoreDialog(QDialog):
    """Dialog for restoring containers from backups"""

    def __init__(self, parent, backup_manager: BackupManager, config: Config):
        """
        Initialize restore dialog

        Args:
            parent: Parent widget
            backup_manager: BackupManager instance
            config: Application configuration
        """
        super().__init__(parent)

        self.backup_manager = backup_manager
        self.config = config

        self.backup_table: QTableWidget = None
        self.new_name_edit: QLineEdit = None
        self.start_after_check: QCheckBox = None

        self.selected_backup: Optional[Dict[str, Any]] = None

        self._init_ui()
        self._load_backups()

    def _init_ui(self) -> None:
        """Initialize user interface"""
        self.setWindowTitle("Restore from Backup")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout()

        # Info label
        info_label = QLabel("Select a backup to restore:")
        layout.addWidget(info_label)

        # Backup list table
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(5)
        self.backup_table.setHorizontalHeaderLabels([
            "Container", "Type", "Date", "Size", "Backup ID"
        ])
        self.backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backup_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.backup_table.setAlternatingRowColors(True)
        self.backup_table.itemSelectionChanged.connect(self._on_backup_selected)

        # Stretch columns
        header = self.backup_table.horizontalHeader()
        header.setStretchLastSection(True)

        layout.addWidget(self.backup_table)

        # Restore options group
        options_group = QGroupBox("Restore Options")
        options_layout = QFormLayout()

        # New container name
        self.new_name_edit = QLineEdit()
        self.new_name_edit.setPlaceholderText("Leave empty to use original name")
        options_layout.addRow("New Container Name:", self.new_name_edit)

        # Start after restore
        self.start_after_check = QCheckBox("Start container after restore")
        self.start_after_check.setChecked(True)
        options_layout.addRow("", self.start_after_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_backups)
        button_layout.addWidget(refresh_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        restore_btn = QPushButton("Restore")
        restore_btn.clicked.connect(self._on_restore_clicked)
        restore_btn.setDefault(True)
        button_layout.addWidget(restore_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_backups(self) -> None:
        """Load available backups"""
        try:
            backups = self.backup_manager.list_backups()

            self.backup_table.setRowCount(len(backups))

            for i, backup in enumerate(backups):
                # Container name
                self.backup_table.setItem(
                    i, 0, QTableWidgetItem(backup.get("container_name", "N/A"))
                )

                # Backup type
                self.backup_table.setItem(
                    i, 1, QTableWidgetItem(backup.get("backup_type", "N/A"))
                )

                # Date
                timestamp = backup.get("timestamp")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        date_str = timestamp
                else:
                    date_str = "N/A"
                self.backup_table.setItem(i, 2, QTableWidgetItem(date_str))

                # Size
                self.backup_table.setItem(
                    i, 3, QTableWidgetItem(backup.get("size_human", "N/A"))
                )

                # Backup ID
                self.backup_table.setItem(
                    i, 4, QTableWidgetItem(backup.get("backup_id", "N/A"))
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load backups: {e}")

    def _on_backup_selected(self) -> None:
        """Handle backup selection"""
        selected_rows = self.backup_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            backup_id = self.backup_table.item(row, 4).text()
            self.selected_backup = self.backup_manager.get_backup_metadata(backup_id)

            # Set default container name
            if self.selected_backup:
                original_name = self.selected_backup.get("container_name", "")
                self.new_name_edit.setPlaceholderText(f"Original: {original_name}")

    def _on_restore_clicked(self) -> None:
        """Handle restore button click"""
        if not self.selected_backup:
            QMessageBox.warning(self, "No Selection", "Please select a backup to restore")
            return

        # Confirm restore
        container_name = self.selected_backup.get("container_name")
        result = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Are you sure you want to restore container '{container_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if result == QMessageBox.StandardButton.Yes:
            self.accept()

    def get_options(self) -> Dict[str, Any]:
        """
        Get selected restore options

        Returns:
            Dictionary with restore options
        """
        new_name = self.new_name_edit.text().strip()

        return {
            "backup_id": self.selected_backup.get("backup_id"),
            "container_name": self.selected_backup.get("container_name"),
            "new_name": new_name if new_name else None,
            "start_after_restore": self.start_after_check.isChecked(),
        }
