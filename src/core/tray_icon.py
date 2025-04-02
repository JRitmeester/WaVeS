import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton
from PyQt5.QtGui import QIcon
import utils.utils as utils
from core.volume_thread import VolumeThread
import webbrowser


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, icon: QIcon, volume_thread: VolumeThread, parent: QtWidgets.QWidget):
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

    def list_sessions_and_devices(self):
        """Show a dialog with all sessions and devices currently in the Windows Volume mixer"""
        software_sessions = self.volume_thread.session_manager.software_sessions
        devices = self.volume_thread.session_manager.devices

        messagebox_text = "Sessions:\n" + "\n".join(sorted([session.name for session in software_sessions]))
        messagebox_text += "\n\nDevices:\n" + "\n".join(sorted(devices.keys()))

        if self.info_dialog is None:
            self.info_dialog = QDialog(QtWidgets.QApplication.activeWindow())
            self.info_dialog.setWindowTitle("Sessions and Devices")
            self.info_dialog.setMinimumWidth(400)
            self.info_dialog.setMinimumHeight(300)
            self.info_dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
            
            layout = QVBoxLayout()
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            close_button = QPushButton("Close")
            close_button.clicked.connect(self.info_dialog.hide)
            layout.addWidget(close_button)
            
            self.info_dialog.setLayout(layout)
            self.info_dialog.text_edit = text_edit
            
            # Connect the close event to hide instead of close
            self.info_dialog.closeEvent = lambda e: self.info_dialog.hide()

        self.info_dialog.text_edit.setText(messagebox_text)
        self.info_dialog.show()
