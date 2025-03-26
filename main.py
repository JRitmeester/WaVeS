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
from pathlib import Path
import webbrowser
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QMessageBox
import utils
from tray_icon import SystemTrayIcon
from config_manager import ConfigManager
from session_manager import SessionManager
from mapping_manager import MappingManager
from volume_thread import VolumeThread

logger = utils.get_logger()


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


def setup_gui(
    w: QtWidgets.QWidget,
    volume_thread: VolumeThread,
):
    tray_icon = SystemTrayIcon(
        icon=QtGui.QIcon(get_icon_path().as_posix()),
        parent=w,
        volume_thread=volume_thread,
    )
    tray_icon.show()
    tray_icon.start_app()
    return tray_icon


def main():
    app = QtWidgets.QApplication(sys.argv)

    # Create configuration manager
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

    # Create other managers
    session_manager = SessionManager()
    mapping_manager = MappingManager()

    setup_gui(
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
