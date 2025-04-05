from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt5.QtGui import QIcon
import utils.utils as utils


class ListingDialog(QDialog):
    """Dialog for displaying a list of items in a text box with a close button."""

    def __init__(self, sessions=None, devices=None):
        """Initialize the dialog with the given title, content and parent.

        Args:
            title (str): The window title
            sessions (list): The list of sessions to display
            devices (dict): The dictionary of devices to display
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(QtWidgets.QApplication.activeWindow())

        if sessions is None:
            sessions = []
        if devices is None:
            devices = {}

        # Set window properties
        self.setWindowTitle("Sessions and Devices")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setModal(True)

        self.setWindowIcon(QIcon(utils.get_icon_path().as_posix()))
        layout = QVBoxLayout()

        label_sessions = QLabel("Sessions")
        layout.addWidget(label_sessions)

        # Create text edit widget
        text_edit_sessions = QTextEdit()
        text_edit_sessions.setReadOnly(True)
        text_edit_sessions.setText("\n".join(sessions))
        text_edit_sessions.setMinimumHeight(100)
        text_edit_sessions.setSizeAdjustPolicy(QTextEdit.AdjustToContents)
        layout.addWidget(text_edit_sessions)

        label_devices = QLabel("Devices")
        layout.addWidget(label_devices)
        # Create text edit widget
        text_edit_devices = QTextEdit()
        text_edit_devices.setReadOnly(True)
        text_edit_devices.setText("\n".join(devices))
        text_edit_devices.setMinimumHeight(100)
        text_edit_devices.setSizeAdjustPolicy(QTextEdit.AdjustToContents)
        layout.addWidget(text_edit_devices)

        # Create close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        # Set layout
        self.setLayout(layout)
