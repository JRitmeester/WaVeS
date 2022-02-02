from pycaw.pycaw import AudioUtilities
from pathlib import Path
import logging
import re


def get_devices():
    return [re.sub("AudioDevice: ", "", str(x)) for x in AudioUtilities.GetAllDevices() if x]


def get_appdata_path():
    return Path.home() / "AppData/Roaming/WaVeS"


def get_logger():
    return logging.getLogger("root")
