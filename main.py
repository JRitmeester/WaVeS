import sys
from pathlib import Path
import webbrowser
import signal
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox
import utils
from core.tray_icon import SystemTrayIcon
from config.config_manager import ConfigManager
from sessions.session_manager import SessionManager
from mapping.mapping_manager import MappingManager
from core.volume_thread import VolumeThread

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nClosing application...")
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
    # Set up signal handling for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Set up the application before the timer, because it requires a QThread instance.
    app = QtWidgets.QApplication(sys.argv)
    
    # Enable processing of keyboard interrupts in the Qt event loop
    timer = QtCore.QTimer()
    timer.start(500)  # Time in ms
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms

    config_path = Path.home() / "AppData/Roaming/WaVeS"
    config_manager = ConfigManager(
        config_path, Path.cwd() / "resources" / "default_mapping.txt"
    )

    try:
        config_manager.load_config()
    except FileNotFoundError:
        config_manager.ensure_config_exists()
        QMessageBox.information(
            None,
            "New config file created",
            f"""A new config file was created for you in the same directory as the app:
            
            {config_path.as_posix()}
            
            It will now be opened for you to view the settings.""",
        )
        webbrowser.open(config_path)

    session_manager = SessionManager()
    mapping_manager = MappingManager()

    # Create tray icon variable to persist volume thread. Not assigning it to a variable
    # will cause it to be garbage collected.
    tray_icon = setup_gui(
        QtWidgets.QWidget(),
        VolumeThread(
            config_manager=config_manager,
            session_manager=session_manager,
            mapping_manager=mapping_manager,
        ),
    )

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
