import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
import utils.utils as utils
from core.volume_thread import VolumeThread
import webbrowser


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, icon, volume_thread: VolumeThread, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.icon = icon
        self.volume_thread = volume_thread  # Injected dependency
        self.setToolTip("WaVeS")

        # Setup the error window
        self.err_box = None

        # Setup the context menu when you right click the tray icon.
        menu = QtWidgets.QMenu(parent)

        reload_ = menu.addAction("Reload mapping")
        reload_.triggered.connect(self.volume_thread.reload_mapping)

        open_config = menu.addAction("Open configuration file")
        open_config.triggered.connect(
            lambda: webbrowser.open(utils.get_appdata_path() / "mapping.txt")
        )

        exit_ = menu.addAction("Exit")
        exit_.triggered.connect(self.exit)

        self.setContextMenu(menu)

        # When the tray icon is clicked, reload the mapping.
        self.activated.connect(self.on_click)

    def std_err_post(self, msg):
        if self.err_box is None:
            self.err_box = QMessageBox()
            # Both OK and window delete fire the 'finished' signal
            self.err_box.finished.connect(lambda: self.err_box.setText(""))

        self.err_box.setWindowTitle("Runtime Error")
        self.err_box.setIcon(QMessageBox.Critical)
        self.err_box.setText(self.err_box.text() + msg)

        # .show() is used here because .exec() or .exec_() create multiple
        # MessageBoxes.
        self.err_box.show()

    def on_click(self, reason):
        if reason == self.Trigger:  # LMB
            self.volume_thread.reload_mapping()

    def exit(self):
        self.volume_thread.stop()
        self.volume_thread.wait()
        sys.exit(0)

    def start_app(self):
        self.volume_thread.start()
