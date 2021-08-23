import datetime
import logging
import os
import sys
import traceback
from pathlib import Path

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMessageBox

from tray_icon import SystemTrayIcon


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


if __name__ == "__main__":

    ## LOGGER STUFF
    # Create the logs directory if it doesn't exist yet.
    log_path = Path(os.getenv("APPDATA")) / 'WVSM' / 'logs'
    if not log_path.is_dir():
        log_path.mkdir(parents=True)

    # Delete all the logs except for the 5 most recent ones.
    all_logs = list(filter(Path.is_file, log_path.glob('**/*')))
    most_recent_logs = sorted(all_logs, key=lambda x: x.stat().st_ctime, reverse=True)[:5]
    logs_to_delete = [log for log in all_logs if log not in most_recent_logs]
    for log in logs_to_delete:
        log.unlink()

    # Setup the logger
    logger = logging.getLogger('root')
    logger.setLevel(logging.DEBUG)

    # Create the logger file handler to write the logs to file.
    handler = logging.FileHandler(log_path / f'WVSM-{datetime.datetime.now().strftime("%d%m%y-%H%M%S")}.log')
    handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
    logger.addHandler(handler)

    logger.info("="*50)
    logger.info("Running PyWinVol...")

    ## ERROR STUFF
    old_excepthook = sys.excepthook
    sys.excepthook = except_hook

    ## APP STUFF
    app = QApplication(sys.argv)
    w = QtWidgets.QWidget()

    icon_dir = Path.cwd() / 'WaVeS/spec/icon.ico'
    if icon_dir.is_file():
        icon = QtGui.QIcon(str(icon_dir))
        tray_icon = SystemTrayIcon(icon, w)
    else:
        QMessageBox.critical(None, "Icon not found", "Could not find the icon for the system tray. Please make sure "
                                                     "there is a file \"icon.ico\" in the same directory as the "
                                                     "executable.")

    # Create the stderr handler and point stderr to it
    std_err_handler = StdErrHandler()
    sys.stderr = std_err_handler

    # Connect err_msg signal to message box method in main window
    std_err_handler.err_msg.connect(tray_icon.std_err_post)

    # Errors that occur in the init phase aren't caught by the stderr.
    tray_icon.show()
    tray_icon.start_app()
    # try:
    #
    # except Exception as e:
    #     QMessageBox.critical(None, "Error during start-up", f"An error occurred during start-up:\n\n{traceback.format_exc()}")
    #     logger.critical("Uncaught exception", exc_info=(type(e).__class__, e, e.__traceback__))

    app.exec()
    print("This should not be printed.")

