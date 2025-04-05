import sys
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
import utils.utils as utils
from core.volume_thread import VolumeThread
import webbrowser
from ui.listing_dialog import ListingDialog


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(
        self, icon: QIcon, volume_thread: VolumeThread, parent: QtWidgets.QWidget
    ):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.icon = icon
        self.volume_thread = volume_thread  # Injected dependency
        self.setToolTip("WaVeS")

        # Setup the error window
        self.err_box = None
        self.info_dialog = None

        # Setup the context menu when you right click the tray icon.
        menu = QtWidgets.QMenu(parent)

        reload_ = menu.addAction("Reload mapping")
        reload_.triggered.connect(self.volume_thread.reload_mapping)

        list_apps = menu.addAction("List sessions and devices")
        list_apps.triggered.connect(self.list_sessions_and_devices)

        open_config = menu.addAction("Open configuration file")
        open_config.triggered.connect(
            lambda: webbrowser.open(utils.get_appdata_path() / "mapping.yml")
        )

        exit_ = menu.addAction("Exit")
        exit_.triggered.connect(self.exit)

        self.setContextMenu(menu)

        # When the tray icon is clicked, reload the mapping.
        self.activated.connect(self.on_click)

    def on_click(self, reason):
        if reason == self.Trigger:  # LMB
            self.volume_thread.reload_mapping()

    def exit(self):
        self.volume_thread.stop()
        self.volume_thread.wait()
        sys.exit(0)

    def start_app(self):
        self.volume_thread.start()

    def list_sessions_and_devices(self):
        """Show a dialog with all sessions and devices currently in the Windows Volume mixer"""
        software_sessions = self.volume_thread.session_manager.software_sessions
        devices = self.volume_thread.session_manager.devices

        # Create and show the dialog
        dialog = ListingDialog(software_sessions, devices)
        dialog.exec_()
