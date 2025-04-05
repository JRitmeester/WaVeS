from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import utils.utils as utils


class InfoDialog(QDialog):
    """A dialog that displays information about the application."""

    def __init__(self, info_title: str, info_message: str | None = None, parent=None):
        super().__init__(parent)

        # Set window properties
        self.setWindowTitle(info_title)
        self.setWindowIcon(QIcon(utils.get_icon_path().as_posix()))
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        # Create layout
        layout = QVBoxLayout()

        # Add message if provided
        if info_message:
            message_label = QLabel(info_message)
            message_label.setWordWrap(True)
            layout.addWidget(message_label)

        # Create close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        # Add button in horizontal layout for centering
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Set dialog layout
        self.setLayout(layout)

        self.exec_()
