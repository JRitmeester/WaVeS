import datetime
import logging
import os
import sys
import traceback
from pathlib import Path

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMessageBox

import utils
from tray_icon import SystemTrayIcon

default_mapping_txt = """
# Make sure this file is placed in the same directory as vc.exe. To make this startup on boot (for Windows), create a
# shortcut and place it in the Start-up folder.

# Application is either "master" for master volume, the application name "spotify.exe" (case insensitive) for Spotify
# (for Windows, this can be found in Task Manager under the "Details" tab), "unmapped" for any and all applications
# that are currently running, but have not been explicitly assigned a slider. "unmapped" excludes the master channel.
# Finally, "system" allows you to control the system sound volume.

# Stick to the syntax:
#<number>:<application>
# Here, number is the index
0: master
1: system
2: chrome.exe
3: spotify.exe
4: unmapped

# Find the device name when the sliders are connected to USB in Device Manager, so that when you switch USB ports,
# you don't have to change the COM port.
device name: Arduino Micro

# Indicate the number of sliders you're using:
sliders: 5
# Port is only used if the device name can't be found automatically.
port:COM7

# Make sure this matches the baudrate on the Arduino's Serial.begin() call.
baudrate:9600

# You can use this to invert the sliders: top is low volume, bottom is high volume.
inverted:False

# Set this to true if you want system sounds included in 'unmapped' if system sounds aren't assigned anywhere else.
system in unmapped:True
"""


class StdErrHandler(QObject):
    """
    This class provides an alternate write() method for stderr messages.
    Messages are sent by pyqtSignal to the pyqtSlot in the main window.
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
    logger.critical("Uncaught exception", exc_info=(cls, exception, traceback))
    sys.excepthook(cls, exception, traceback)


def initialise(path):
    path.mkdir()
    mapping_file = path / 'mapping.txt'
    mapping_file.touch()
    mapping_file.write_text(default_mapping_txt)
    QMessageBox.information(None, "New config file created",
                            f"A new config file was created for you in the same directory as the app:\n\n{str(path)}."
                            f"\n\nIt will now be opened for you to view the settings.\n\nUse the system tray icon > "
                            f"\"Show sound devices\" to see the sound device names if needed.")
    webbrowser.open(path)

if __name__ == "__main__":
    appdata_path = utils.get_appdata_path()
    if not appdata_path.exists():
        initialise(appdata_path)

    ## LOGGER STUFF
    # Create the logs directory if it doesn't exist yet.
    log_path = Path(os.getenv("APPDATA")) / 'WaVeS' / 'logs'
    if not log_path.is_dir():
        log_path.mkdir(parents=True)

    # Delete all the logs except for the 5 most recent ones.
    all_logs = list(filter(Path.is_file, log_path.glob('**/*')))
    most_recent_logs = sorted(all_logs, key=lambda x: x.stat().st_ctime, reverse=True)[:5]
    logs_to_delete = [log for log in all_logs if log not in most_recent_logs]
    for log in logs_to_delete:
        log.unlink()

    # Setup the logger
    logger = utils.get_logger()
    logger.setLevel(logging.DEBUG)

    # Create the logger file handler to write the logs to file.
    handler = logging.FileHandler(log_path / f'WVSM-{datetime.datetime.now().strftime("%d%m%y-%H%M%S")}.log')
    handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
    logger.addHandler(handler)

    logger.info("="*50)
    logger.info("Running WaVeS...")

    ## ERROR STUFF
    old_excepthook = sys.excepthook
    sys.excepthook = except_hook

    ## APP STUFF
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = QtWidgets.QWidget()

    icon_dir = Path.cwd() / 'WaVeS/spec/icon.ico'  # For testing the compiled version in the dist folder
    if not icon_dir.is_file():
        icon_dir = Path.cwd() / 'icon.ico'
    if not icon_dir.is_file():
        QMessageBox.critical(None, "Icon not found", "Could not find the icon for the system tray. Please make sure "
                                                     "there is a file \"icon.ico\" in the same directory as the "
                                                     "executable.")
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
        QMessageBox.critical(None, "Error during start-up", f"An error occurred during start-up:\n\n{traceback.format_exc()}")
        logger.critical("Uncaught exception", exc_info=(type(e).__class__, e, e.__traceback__))

    app.exec()
