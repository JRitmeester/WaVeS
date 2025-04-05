import sys
from pathlib import Path
import webbrowser
import signal
from PyQt5 import QtWidgets, QtGui, QtCore
import utils.utils as utils
from utils.logger import logger
from core.tray_icon import SystemTrayIcon
from config.config_manager import ConfigManager
from sessions.session_manager import SessionManager
from mapping.mapping_manager import MappingManager
from core.volume_thread import VolumeThread
from microcontroller.microcontroller_manager import MicrocontrollerManager
from ui.error_dialog import ErrorDialog
from ui.welcome_dialog import WelcomeDialog

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("Closing application...")
    QtWidgets.QApplication.quit()


def setup_gui(
    w: QtWidgets.QWidget,
    volume_thread: VolumeThread,
):
    tray_icon = SystemTrayIcon(
        icon=QtGui.QIcon(utils.get_icon_path().as_posix()),
        parent=w,
        volume_thread=volume_thread,
    )
    tray_icon.show()
    tray_icon.start_app()
    return tray_icon


def main():
    logger.info("Starting WaVeS application")
    
    # Set up signal handling for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Set up the application before the timer, because it requires a QThread instance.
    app = QtWidgets.QApplication(sys.argv)
    
    sys.excepthook = ErrorDialog._exception_hook

    # Enable processing of keyboard interrupts in the Qt event loop
    timer = QtCore.QTimer()
    timer.start(500)  # Time in ms
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms

    config_path = Path.home() / "AppData/Roaming/WaVeS"
    logger.debug(f"Using config path: {config_path}")
    config_manager = ConfigManager(
        config_path, Path.cwd() / "resources" / "default_mapping.yml"
    )

    try:
        config_manager.load_config()
        logger.info("Configuration loaded successfully")
    except FileNotFoundError:
        logger.warning("Configuration file not found, creating default configuration")
        config_manager.ensure_config_exists()
        welcome_dialog = WelcomeDialog(config_path)
        
        webbrowser.open(config_path)

    logger.info("Initializing managers and services")
    session_manager = SessionManager()
    mapping_manager = MappingManager()
    microcontroller_manager = MicrocontrollerManager()
    volume_thread = VolumeThread(
        config_manager=config_manager,
        session_manager=session_manager,
        mapping_manager=mapping_manager,
        microcontroller_manager=microcontroller_manager,
    )
    # Create a widet to persist the tray icon. Not assigning it to a variable won't crash the app,
    # but it won't show the icon in the system tray.
    widget = QtWidgets.QWidget()

    # Create tray icon variable to persist volume thread. Not assigning it to a variable
    # will cause it to be garbage collected.
    tray_icon = setup_gui(
        widget,
        volume_thread,
    )

    logger.info("Application started successfully")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
