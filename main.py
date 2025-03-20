"""
WaVeS (Windows Volume Slider) - A PyQt5-based application for controlling Windows audio volumes using Arduino sliders.

This module serves as the main entry point for the WaVeS application. It initializes the system tray interface,
and handles application configuration. The application allows users to control various audio 
channels (master, system, and individual applications) using physical Arduino-based sliders.

Key Features:
- System tray integration for easy access
- Configurable audio channel mapping
- Arduino-based volume control integration
- Error handling and reporting
"""

import datetime
import sys
import traceback
import types
from pathlib import Path
import webbrowser
from typing import Optional, NoReturn, Callable

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMessageBox
import utils
from tray_icon import SystemTrayIcon

try:
    default_mapping_txt = (Path.cwd() / "default_mapping.txt").read_text()
except FileNotFoundError:
    default_mapping_txt = ""  # Or some default configuration
except Exception as e:
    default_mapping_txt = ""


class StdErrHandler(QObject):
    """
    Custom stderr handler that redirects error messages to the GUI.
    
    This class intercepts standard error messages and emits them as Qt signals,
    allowing them to be displayed in the application's GUI interface.
    
    Attributes:
        err_msg (pyqtSignal): Signal emitted when an error message is received
    """

    err_msg = pyqtSignal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        QObject.__init__(self)

    def write(self, msg: str) -> None:
        # stderr messages are sent to this method.
        self.err_msg.emit(msg)

    def flush(self) -> None:
        pass


def except_hook(cls: type[BaseException], 
                exception: BaseException, 
                traceback: types.TracebackType) -> None:
    """
    Global exception handler.
    
    Args:
        cls: Exception class
        exception: Exception instance
        traceback: Traceback object
    """
    sys.excepthook(cls, exception, traceback)


def initialise(path: Path) -> None:
    """
    Initialize the application configuration directory and create default mapping file.
    
    Args:
        path (Path): Path where configuration files should be created
        
    Creates the configuration directory and a default mapping.txt file with
    example configurations for audio channel mapping.
    """
    path.mkdir()
    mapping_file: Path = path / "mapping.txt"
    mapping_file.touch()
    mapping_file.write_text(default_mapping_txt)
    QMessageBox.information(
        None,
        "New config file created",
        f"A new config file was created for you in the same directory as the app:\n\n{str(path)}."
        f"\n\nIt will now be opened for you to view the settings.\n\nUse the system tray icon > "
        f'"Show sound devices" to see the sound device names if needed.',
    )
    webbrowser.open(path)


if __name__ == "__main__":
    appdata_path: Path = utils.get_appdata_path()

    if not appdata_path.exists():
        initialise(appdata_path)

    ## ERROR STUFF
    old_excepthook = sys.excepthook
    sys.excepthook = except_hook

    ## APP STUFF
    app: QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w: QtWidgets.QWidget = QtWidgets.QWidget()

    icon_dir: Path = Path.cwd() / "WaVeS/spec/icon.ico"  # For testing the compiled version in the dist folder
    if not icon_dir.is_file():
        icon_dir = Path.cwd() / "icon.ico"
    if not icon_dir.is_file():
        QMessageBox.critical(
            None,
            "Icon not found",
            "Could not find the icon for the system tray. Please make sure "
            'there is a file "icon.ico" in the same directory as the '
            "executable.",
        )
        sys.exit(0)
        

    icon: QtGui.QIcon = QtGui.QIcon(str(icon_dir))
    tray_icon: SystemTrayIcon = SystemTrayIcon(icon, w)

    # Create the stderr handler and point stderr to it
    std_err_handler: StdErrHandler = StdErrHandler()
    sys.stderr = std_err_handler

    # Connect err_msg signal to message box method in main window
    std_err_handler.err_msg.connect(tray_icon.std_err_post)

    # Errors that occur in the init phase aren't caught by the stderr.
    try:
        tray_icon.show()
        tray_icon.start_app()
    except Exception as e:
        QMessageBox.critical(
            None,
            "Error during start-up",
            f"An error occurred during start-up:\n\n{traceback.format_exc()}",
        )

    sys.exit(app.exec())
