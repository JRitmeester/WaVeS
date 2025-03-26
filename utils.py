from pathlib import Path
import sys


def get_appdata_path():
    return Path.home() / "AppData/Roaming/WaVeS"


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
