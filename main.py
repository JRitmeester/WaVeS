"""
WaVeS (Windows Volume Slider) - A PyQt5-based application for controlling Windows audio volumes using Arduino sliders.

This module serves as the main entry point for the WaVeS application. It initializes the system tray interface,
sets up logging, and handles application configuration. The application allows users to control various audio 
channels (master, system, and individual applications) using physical Arduino-based sliders.

Key Features:
- System tray integration for easy access
- Configurable audio channel mapping
- Arduino-based volume control integration
- Logging system for debugging
- Error handling and reporting
"""

import datetime
import logging
import sys
import traceback
from pathlib import Path
import webbrowser

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMessageBox

import utils
from tray_icon import SystemTrayIcon
import sys

default_mapping_txt = (Path.cwd() / "default_mapping.txt").read_text()


class StdErrHandler(QObject):
    """
    Custom stderr handler that redirects error messages to the GUI.
    
    This class intercepts standard error messages and emits them as Qt signals,
    allowing them to be displayed in the application's GUI interface.
    
    Attributes:
        err_msg (pyqtSignal): Signal emitted when an error message is received
    """

    err_msg = pyqtSignal(str)

    def __init__(self, parent=None):
        QObject.__init__(self)

    def write(self, msg):
        # stderr messages are sent to this method.
        self.err_msg.emit(msg)

    def flush(self):
        pass


def except_hook(cls, exception, traceback):
    """
    Global exception handler that logs uncaught exceptions.
    
    Args:
        cls: Exception class
        exception: Exception instance
        traceback: Traceback object
    """
    logger.critical("Uncaught exception", exc_info=(cls, exception, traceback))
    sys.excepthook(cls, exception, traceback)


def initialise(path):
    """
    Initialize the application configuration directory and create default mapping file.
    
    Args:
        path (Path): Path where configuration files should be created
        
    Creates the configuration directory and a default mapping.txt file with
    example configurations for audio channel mapping.
    """
    path.mkdir()
    mapping_file = path / "mapping.txt"
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
    appdata_path = utils.get_appdata_path()
    if not appdata_path.exists():
        initialise(appdata_path)

    ## LOGGER STUFF
    # Create the logs directory if it doesn't exist yet.
    log_path = appdata_path / "logs"
    if not log_path.is_dir():
        log_path.mkdir(parents=True)

    # Delete all the logs except for the 5 most recent ones.
    all_logs = list(filter(Path.is_file, log_path.glob("**/*")))
    most_recent_logs = sorted(all_logs, key=lambda x: x.stat().st_ctime, reverse=True)[:5]
    logs_to_delete = [log for log in all_logs if log not in most_recent_logs]
    for log in logs_to_delete:
        log.unlink()

    # Setup the logger
    logger = utils.get_logger()
    logger.setLevel(logging.DEBUG)

    # Create the logger file handler to write the logs to file.
    handler = logging.FileHandler(log_path / f'WVSM-{datetime.datetime.now().strftime("%d%m%y-%H%M%S")}.log')
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)

    logger.info("=" * 50)
    logger.info("Running WaVeS...")

    ## ERROR STUFF
    old_excepthook = sys.excepthook
    sys.excepthook = except_hook

    ## APP STUFF
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = QtWidgets.QWidget()

    icon_dir = Path.cwd() / "WaVeS/spec/icon.ico"  # For testing the compiled version in the dist folder
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

    icon = QtGui.QIcon(str(icon_dir))
    tray_icon = SystemTrayIcon(icon, w)

    # Create the stderr handler and point stderr to it
    std_err_handler = StdErrHandler()
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
        logger.critical("Uncaught exception", exc_info=(type(e).__class__, e, e.__traceback__))

    sys.exit(app.exec())
