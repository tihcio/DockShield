"""
Progress dialog for long-running operations
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont


class ProgressDialog(QDialog):
    """Progress dialog with progress bar and status updates"""

    def __init__(self, parent=None, title="Operation in Progress"):
        """
        Initialize progress dialog

        Args:
            parent: Parent widget
            title: Dialog title
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(500, 300)

        # Prevent closing with X button during operation
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Operation label
        self.operation_label = QLabel("Preparing...")
        self.operation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.operation_label.setFont(font)
        layout.addWidget(self.operation_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(self.status_label)

        # Details text area (collapsible)
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                color: #2c3e50;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                font-family: monospace;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.details_text)

        layout.addStretch()

        # Close button (initially hidden)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setVisible(False)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    @pyqtSlot(str)
    def set_operation(self, text: str) -> None:
        """Set operation text"""
        self.operation_label.setText(text)

    @pyqtSlot(int)
    def set_progress(self, value: int) -> None:
        """Set progress value (0-100)"""
        self.progress_bar.setValue(value)

    @pyqtSlot(str)
    def set_status(self, text: str) -> None:
        """Set status text"""
        self.status_label.setText(text)

    @pyqtSlot(str)
    def add_detail(self, text: str) -> None:
        """Add detail line to text area"""
        self.details_text.append(text)
        # Auto-scroll to bottom
        scrollbar = self.details_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @pyqtSlot(bool, str)
    def operation_finished(self, success: bool, message: str = "") -> None:
        """
        Called when operation finishes

        Args:
            success: Whether operation succeeded
            message: Optional final message
        """
        if success:
            self.progress_bar.setValue(100)
            self.operation_label.setText("✓ Operation Completed")
            self.operation_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.status_label.setText(message or "Successfully completed")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 10pt;")
        else:
            self.operation_label.setText("✗ Operation Failed")
            self.operation_label.setStyleSheet("color: #f44336; font-weight: bold;")
            self.status_label.setText(message or "Operation failed")
            self.status_label.setStyleSheet("color: #f44336; font-size: 10pt;")

        # Show close button
        self.close_button.setVisible(True)

        # Allow closing with X button now
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.show()  # Refresh window flags
