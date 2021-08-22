import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from volume_thread import VolumeThread
import logging

logger = logging.getLogger('root')

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.icon = icon
        self.setToolTip("Windows Volume Slider Manager")

        # Setup the error window
        self.err_box = None

        # Setup the context menu when you right click the tray icon.
        menu = QtWidgets.QMenu(parent)
        exit_ = menu.addAction("Exit")
        exit_.triggered.connect(self.exit)
        reload_ = menu.addAction("Reload mapping")
        reload_.triggered.connect(self.reload)
        self.setContextMenu(menu)

        self.activated.connect(self.onClick)
        self.thread = VolumeThread()

    def std_err_post(self, msg):
        """
        This method receives stderr text strings as a pyqtSlot.
        """
        if self.err_box is None:
            self.err_box = QMessageBox()
            # Both OK and window delete fire the 'finished' signal
            self.err_box.finished.connect(self.clear_err_box)
        # A single error is sent as a string of separate stderr .write() messages,
        # so concatenate them.
        self.err_box.setWindowTitle("Runtime Error")
        self.err_box.setIcon(QMessageBox.Critical)
        self.err_box.setText(self.err_box.text() + msg)
        # .show() is used here because .exec() or .exec_() create multiple
        # MessageBoxes.
        self.err_box.show()

    def clear_err_box(self):
        self.err_box.setText("")

    def onClick(self, reason):
        if reason == self.Trigger:  # LMB
            self.reload()

    def reload(self):
        self.showMessage("Volume Slider Manager", "Reloading slider mappings...", self.icon)
        self.thread.control.get_mapping()

    def exit(self):
        logger.info("Quitting application.")
        sys.exit(0)

    def start_app(self):
        """
        Create a global volume control object "vc" and a systray object to control the system tray in other places.
        Start the event loop to parse incoming data from the volume sliders. Stops the vc thread and systray thread once
        :return:
        """
        logger.info("Starting application.")
        self.thread.start()