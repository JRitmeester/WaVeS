"""
System tray interface module for WaVeS application.

Provides a system tray icon with context menu for controlling the application,
including options to reload mappings, view devices, and access configuration.
The module handles user interaction through the system tray and manages
the volume control thread.
"""

import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
import utils
from volume_thread import VolumeThread
import logging
import webbrowser

logger = logging.getLogger("root")


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    """
    System tray icon implementation with volume control functionality.
    
    Provides user interface elements in the system tray, including context menu
    options and error reporting capabilities.
    
    Attributes:
        icon: The icon displayed in the system tray
        err_box: Error message dialog box
        thread (VolumeThread): Thread handling volume control operations
    """
    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.icon = icon
        self.setToolTip("Windows Volume Slider Manager")

        # Setup the error window
        self.err_box = None

        # Setup the context menu when you right click the tray icon.
        menu = QtWidgets.QMenu(parent)

        reload_ = menu.addAction("Reload mapping")
        reload_.triggered.connect(self.reload)

        showdevices = menu.addAction("Show sound devices")
        showdevices.triggered.connect(self.show_devices)

        open_config = menu.addAction("Open configuration file")
        open_config.triggered.connect(lambda: webbrowser.open(utils.get_appdata_path() / "mapping.txt"))

        exit_ = menu.addAction("Exit")
        exit_.triggered.connect(self.exit)

        self.setContextMenu(menu)
        self.activated.connect(self.on_click)
        self.thread = VolumeThread()

    def std_err_post(self, msg):
        """
        This method receives stderr text strings as a pyqtSlot.
        """
        if self.err_box is None:
            self.err_box = QMessageBox()
            # Both OK and window delete fire the 'finished' signal
            self.err_box.finished.connect(lambda: self.err_box.setText(""))
            
        # A single error is sent as a string of separate stderr .write() messages,
        # so concatenate them.
        self.err_box.setWindowTitle("Runtime Error")
        self.err_box.setIcon(QMessageBox.Critical)
        self.err_box.setText(self.err_box.text() + msg)

        # .show() is used here because .exec() or .exec_() create multiple
        # MessageBoxes.
        self.err_box.show()

    def on_click(self, reason):
        if reason == self.Trigger:  # LMB
            self.reload()

    def reload(self):
        self.showMessage("Volume Slider Manager", "Reloading slider mappings...", self.icon)
        self.thread.control.get_mapping()

    def exit(self):
        logger.info("Quitting application.")
        sys.exit(0)

    def show_devices(self):
        sound_devices = utils.get_devices()
        text = "Note that these are both input and output devices!\n\n" + "\n".join(sorted(set(sound_devices)))
        QMessageBox.information(None, "Sound devices", text)

    def start_app(self):
        """
        Create a global volume control object "vc" and a systray object to control the system tray in other places.
        Start the event loop to parse incoming data from the volume sliders. Stops the vc thread and systray thread once
        :return:
        """
        logger.info("Starting application.")
        self.thread.start()
