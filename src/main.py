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

import sys
import traceback
from pathlib import Path
import webbrowser

from PyQt5.QtWidgets import QApplication, QMessageBox
import utils as utils
from tray_icon import SystemTrayIcon

try:
    default_mapping_txt = (Path.cwd() / "default_mapping.txt").read_text()
except FileNotFoundError:
    default_mapping_txt = ""  # Or some default configuration
except Exception as e:
    default_mapping_txt = ""

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

    app: QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    tray_icon: SystemTrayIcon = SystemTrayIcon()
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
