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


import sys
import types
from pathlib import Path
import webbrowser

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QMessageBox
import utils
from tray_icon import SystemTrayIcon
from config_manager import ConfigManager
from session_manager import SessionManager
from mapping_manager import MappingManager
from volume_thread import VolumeThread

logger = utils.get_logger()


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


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()

    # Create configuration manager
    config_path = Path.home() / "AppData/Roaming/WaVeS"
    config_manager = ConfigManager(config_path, Path.cwd() / "resources" / "default_mapping.txt")

    # Ensure config exists
    try:
        config_manager.load_config()
    except FileNotFoundError:
        config_manager.ensure_config_exists()
        show_config_created_dialog(config_path)
        webbrowser.open(config_path)

    # Create other managers
    session_manager = SessionManager()
    mapping_manager = MappingManager()

    # Create volume thread with injected dependencies
    volume_thread = VolumeThread(
        config_manager=config_manager,
        session_manager=session_manager,
        mapping_manager=mapping_manager
    )

    # Create and show tray icon
    tray_icon = SystemTrayIcon(
        icon=QtGui.QIcon(get_icon_path().as_posix()),
        parent=w,
        volume_thread=volume_thread
    )
    tray_icon.show()
    tray_icon.start_app()

    sys.exit(app.exec_())


def show_config_created_dialog(config_path: Path) -> None:
    QMessageBox.information(
        None,
        "New config file created",
        f"""A new config file was created for you in the same directory as the app:
        
        {str(config_path)}
        
        It will now be opened for you to view the settings."""
    )
    webbrowser.open(config_path)

if __name__ == "__main__":
    main()
