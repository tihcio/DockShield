"""
Backup history dialog for DockShield
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QTextEdit,
    QSplitter, QGroupBox, QLabel
)
from PyQt6.QtCore import Qt
from datetime import datetime
import json

from dockshield.core.backup_manager import BackupManager


class HistoryDialog(QDialog):
    """Dialog for viewing backup history"""

    def __init__(self, parent, backup_manager: BackupManager):
        """
        Initialize history dialog

        Args:
            parent: Parent widget
            backup_manager: BackupManager instance
        """
        super().__init__(parent)

        self.backup_manager = backup_manager

        self.backup_table: QTableWidget = None
        self.details_text: QTextEdit = None

        self.selected_backup: Optional[Dict[str, Any]] = None

        self._init_ui()
        self._load_history()

    def _init_ui(self) -> None:
        """Initialize user interface"""
        self.setWindowTitle("Backup History")
        self.setModal(True)
        self.resize(1000, 700)

        layout = QVBoxLayout()

        # Info label
        info_label = QLabel("Backup History")
        info_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(info_label)

        # Splitter for table and details
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Backup list table
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(6)
        self.backup_table.setHorizontalHeaderLabels([
            "Container", "Type", "Date", "Size", "Files", "Backup ID"
        ])
        self.backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backup_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.backup_table.setAlternatingRowColors(True)
        self.backup_table.itemSelectionChanged.connect(self._on_backup_selected)

        # Stretch columns
        header = self.backup_table.horizontalHeader()
        header.setStretchLastSection(True)

        splitter.addWidget(self.backup_table)

        # Details group
        details_group = QGroupBox("Backup Details")
        details_layout = QVBoxLayout()

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Select a backup to view details")
        details_layout.addWidget(self.details_text)

        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)

        # Set splitter sizes (70% table, 30% details)
        splitter.setSizes([500, 200])

        layout.addWidget(splitter)

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_history)
        button_layout.addWidget(refresh_btn)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self._delete_selected)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_history(self) -> None:
        """Load backup history"""
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

                # Number of files
                files_count = len(backup.get("files", []))
                self.backup_table.setItem(i, 4, QTableWidgetItem(str(files_count)))

                # Backup ID
                self.backup_table.setItem(
                    i, 5, QTableWidgetItem(backup.get("backup_id", "N/A"))
                )

            # Update info label
            info_text = f"Total backups: {len(backups)}"
            if backups:
                total_size = sum(b.get("size_bytes", 0) for b in backups)
                info_text += f" | Total size: {self._format_size(total_size)}"

            self.findChild(QLabel).setText(f"Backup History - {info_text}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load history: {e}")

    def _on_backup_selected(self) -> None:
        """Handle backup selection"""
        selected_rows = self.backup_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            backup_id = self.backup_table.item(row, 5).text()
            self.selected_backup = self.backup_manager.get_backup_metadata(backup_id)

            if self.selected_backup:
                self._display_backup_details()

    def _display_backup_details(self) -> None:
        """Display backup details"""
        if not self.selected_backup:
            return

        details = []
        details.append("=" * 60)
        details.append("BACKUP DETAILS")
        details.append("=" * 60)
        details.append("")

        # Basic info
        details.append(f"Backup ID: {self.selected_backup.get('backup_id')}")
        details.append(f"Container: {self.selected_backup.get('container_name')}")
        details.append(f"Type: {self.selected_backup.get('backup_type')}")
        details.append(f"Size: {self.selected_backup.get('size_human', 'N/A')}")

        timestamp = self.selected_backup.get('timestamp')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                date_str = timestamp
            details.append(f"Created: {date_str}")

        details.append("")

        # Files
        files = self.selected_backup.get('files', [])
        details.append(f"Files ({len(files)}):")
        for file in files:
            details.append(f"  • {file}")

        details.append("")

        # Container info
        container_info = self.selected_backup.get('container_info', {})
        if container_info:
            details.append("Container Information:")
            details.append(f"  Image: {container_info.get('image', 'N/A')}")
            details.append(f"  Status: {container_info.get('status', 'N/A')}")

            env_count = len(container_info.get('env', []))
            details.append(f"  Environment variables: {env_count}")

            mounts = container_info.get('mounts', [])
            details.append(f"  Volumes: {len(mounts)}")

            networks = container_info.get('networks', [])
            if networks:
                details.append(f"  Networks: {', '.join(networks)}")

        # Path
        details.append("")
        details.append(f"Location: {self.selected_backup.get('backup_path', 'N/A')}")

        self.details_text.setPlainText("\n".join(details))

    def _delete_selected(self) -> None:
        """Delete selected backup"""
        if not self.selected_backup:
            QMessageBox.warning(self, "No Selection", "Please select a backup to delete")
            return

        backup_id = self.selected_backup.get("backup_id")
        container_name = self.selected_backup.get("container_name")

        result = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete backup for '{container_name}'?\n\n"
            f"Backup ID: {backup_id}\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if result == QMessageBox.StandardButton.Yes:
            try:
                if self.backup_manager.delete_backup(backup_id):
                    QMessageBox.information(self, "Success", "Backup deleted successfully")
                    self.selected_backup = None
                    self.details_text.clear()
                    self._load_history()
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete backup")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting backup: {e}")

    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
