from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTextEdit, 
                             QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import utils.utils as utils
import sys
import traceback

class ErrorDialog(QDialog):

    @staticmethod
    def _exception_hook(exctype, value, tb):
        """Global exception handler that shows errors in an ErrorDialog"""
        # Get the full traceback as a string
        traceback_str = ''.join(traceback.format_exception(exctype, value, tb))
        
        # Create and show the error dialog
        ErrorDialog(
            str(exctype.__name__),
            str(value),
            traceback_str
        )
        
        # Also print to console for debugging
        print(''.join(traceback.format_exception(exctype, value, tb)), file=sys.stderr)

    @classmethod
    def setup_exception_handling(cls):
        """Set up global exception handling to show errors in ErrorDialog"""
        sys.excepthook = cls._exception_hook

    def __init__(self, error_title: str, error_message: str | None = None, stacktrace: str | None = None, parent=None):
        super().__init__(parent)
        
        # Set window properties
        self.setWindowTitle("WaVeS encountered an error")
        self.setWindowIcon(QIcon(utils.get_icon_path().as_posix()))
        self.setModal(True)  # Make dialog modal
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create error message layout
        message_layout = QHBoxLayout()
        
        # Add error icon
        icon_label = QLabel()
        icon_label.setPixmap(self.style().standardIcon(self.style().SP_MessageBoxCritical).pixmap(32, 32))
        message_layout.addWidget(icon_label, 0, Qt.AlignTop)
        
        # Add error messages
        message_container = QVBoxLayout()
        title_label = QLabel(error_title)
        title_label.setStyleSheet("font-weight: bold;")
        message_container.addWidget(title_label)
        
        if error_message:
            detail_label = QLabel(error_message)
            detail_label.setWordWrap(True)
            message_container.addWidget(detail_label)
            
        message_layout.addLayout(message_container, 1)
        main_layout.addLayout(message_layout)

        # Add stacktrace if provided
        if stacktrace:
            text_edit = QTextEdit()
            text_edit.setPlainText(stacktrace)
            text_edit.setReadOnly(True)
            text_edit.setFixedHeight(80)
            text_edit.setMinimumWidth(400)
            text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            main_layout.addSpacing(10)
            main_layout.addWidget(text_edit)

        # Add OK button in its own layout
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        main_layout.addLayout(button_layout)
        
        self.exec_()
