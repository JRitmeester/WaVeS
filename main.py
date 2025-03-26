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
import types
from pathlib import Path
import webbrowser

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMessageBox
import utils
from tray_icon import SystemTrayIcon

logger = utils.get_logger()

try:
    default_mapping_txt = (Path.cwd() / "default_mapping.txt").read_text()
except FileNotFoundError:
    logger.error("default_mapping.txt not found")
    default_mapping_txt = ""  # Or some default configuration
except Exception as e:
    logger.error(f"Error reading default_mapping.txt: {e}")
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

    def __init__(self, parent: QObject | None = None) -> None:
        QObject.__init__(self)

    def write(self, msg: str) -> None:
        # stderr messages are sent to this method.
        self.err_msg.emit(msg)

    def flush(self) -> None:
        pass


def except_hook(
    cls: type[BaseException], exception: BaseException, traceback: types.TracebackType
) -> None:
    """
    Global exception handler that logs uncaught exceptions.

    Args:
        cls: Exception class
        exception: Exception instance
        traceback: Traceback object
    """
    logger.critical("Uncaught exception", exc_info=(cls, exception, traceback))
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
        f"""A new config file was created for you in the same directory as the app:\n\n{str(path)}.
        It will now be opened for you to view the settings.""",
    )
    webbrowser.open(path)


def get_icon_path():
    if getattr(sys, "frozen", False):
        # Running in a PyInstaller bundle
        base_path = Path(sys._MEIPASS)
        icon_dir = base_path / "icon.ico"
    else:
        icon_dir = Path.cwd() / "resources" / "icon.ico"

    if not icon_dir.is_file():
        raise FileNotFoundError("Icon not found")

    return icon_dir


if __name__ == "__main__":
    appdata_path: Path = utils.get_appdata_path()

    if not appdata_path.exists():
        initialise(appdata_path)

    ## LOGGER STUFF
    # Create the logs directory if it doesn't exist yet.
    log_path: Path = appdata_path / "logs"
    if not log_path.is_dir():
        log_path.mkdir(parents=True)

    # Delete all the logs except for the 5 most recent ones.
    all_logs: list[Path] = list(filter(Path.is_file, log_path.glob("**/*")))
    most_recent_logs: list[Path] = sorted(
        all_logs, key=lambda x: x.stat().st_ctime, reverse=True
    )[:5]
    logs_to_delete: list[Path] = [
        log for log in all_logs if log not in most_recent_logs
    ]
    for log in logs_to_delete:
        log.unlink()

    # Setup the logger
    logger: logging.Logger = utils.get_logger()
    logger.setLevel(logging.DEBUG)

    # Create the logger file handler to write the logs to file.
    handler: logging.FileHandler = logging.FileHandler(
        log_path / f'WVSM-{datetime.datetime.now().strftime("%d%m%y-%H%M%S")}.log'
    )
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)

    logger.info("=" * 50)
    logger.info("Running WaVeS...")

    ## ERROR STUFF
    old_excepthook = sys.excepthook
    sys.excepthook = except_hook

    ## APP STUFF
    app: QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w: QtWidgets.QWidget = QtWidgets.QWidget()

    icon: QtGui.QIcon = QtGui.QIcon(str(get_icon_path()))
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
        logger.critical(
            "Uncaught exception", exc_info=(type(e).__class__, e, e.__traceback__)
        )

    sys.exit(app.exec())
