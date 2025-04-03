import sys
from pathlib import Path
import webbrowser
import signal
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox
import utils.utils as utils
from core.tray_icon import SystemTrayIcon
from config.config_manager import ConfigManager
from sessions.session_manager import SessionManager
from mapping.mapping_manager import MappingManager
from core.volume_thread import VolumeThread
from microcontroller.microcontroller_manager import MicrocontrollerManager
import textwrap

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
        config_path, Path.cwd() / "resources" / "default_mapping.yml"
    )

    try:
        config_manager.load_config()
    except FileNotFoundError:
        config_manager.ensure_config_exists()
        QMessageBox.information(
            None,
            "New config file created",
            textwrap.dedent(
                f"""
                It seems this is the first time you started WaVeS.

                A new configuration file was created and will be opened for you to view the settings:
                You can find it by right-clicking the tray icon, or at:
                {config_path.as_posix()}
                """
            ),
        )
        webbrowser.open(config_path)

    session_manager = SessionManager()
    mapping_manager = MappingManager()
    volume_thread = VolumeThread(
        config_manager=config_manager,
        session_manager=session_manager,
        mapping_manager=mapping_manager,
        microcontroller_manager=MicrocontrollerManager(),
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

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
