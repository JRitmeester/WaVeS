from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QTextEdit,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import utils.utils as utils
import textwrap
from pathlib import Path


class WelcomeDialog(QDialog):
    """A dialog that displays information about the application on first launch."""

    def __init__(self, config_path: Path, parent=None):
        super().__init__(parent)

        # Set window properties
        self.setWindowTitle("Welcome to WaVeS")
        self.setWindowIcon(QIcon(utils.get_icon_path().as_posix()))
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        # Create layout
        layout = QVBoxLayout()

        main_text = textwrap.dedent(
            """
            It seems this is the first time you started WaVeS. A new configuration file was created and will be opened for you to view the settings.
            You can find it by right-clicking the tray icon, or at:
            """
        )

        label_main_text = QLabel(main_text)
        label_main_text.setWordWrap(True)
        layout.addWidget(label_main_text)

        label_config_path = QTextEdit(config_path.as_posix())

        label_config_path.setReadOnly(True)
        label_config_path.setFixedHeight(50)
        # Set horizontal scrollbar to be visible as needed
        label_config_path.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Add padding to the bottom of the label
        layout.addWidget(label_config_path)
        layout.addSpacing(10)

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
