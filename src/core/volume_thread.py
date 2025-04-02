import sys
import serial
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QMessageBox
from sessions.session_manager import SessionManagerProtocol
from config.config_manager import ConfigManagerProtocol
from mapping.mapping_manager import MappingManagerProtocol
from microcontroller.microcontroller_protocol import MicrocontrollerProtocol


class VolumeThread(QThread):

    def __init__(
        self,
        config_manager: ConfigManagerProtocol,
        session_manager: SessionManagerProtocol,
        mapping_manager: MappingManagerProtocol,
        microcontroller_manager: MicrocontrollerProtocol,
    ):

        super().__init__()

        self.running = True
        self.config_manager = config_manager
        self.session_manager = session_manager
        self.mapping_manager = mapping_manager
        self.microcontroller_manager = microcontroller_manager

        # Connect to microcontroller
        port = self.config_manager.get_serial_port()
        baudrate = self.config_manager.get_setting("device.baudrate")
        self.microcontroller_manager.connect(port, baudrate)

        # Setup mapping and settings
        self.inverted = self.config_manager.get_setting("settings.inverted")
        self.mapping = self.mapping_manager.get_mapping(
            self.session_manager, self.config_manager
        )

        # Setup session change monitoring
        session_reload_interval = self.config_manager.get_setting("settings.session_reload_interval")
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_for_changes)
        self._check_timer.start(session_reload_interval * 1000)

    def _check_for_changes(self):
        """Periodically check for session changes"""
        if self.running and self.session_manager.check_for_changes():
            self.session_manager.reload_sessions_and_devices()
            self.reload_mapping()

    def reload_mapping(self):
        """Reload the mapping when sessions change"""
        self.mapping = self.mapping_manager.get_mapping(
            self.session_manager, self.config_manager
        )

    def run(self):
        sliders = int(self.config_manager.get_setting("device.sliders"))
        while self.running:
            values = self.microcontroller_manager.read_values(sliders)
            if not values:
                continue

            self.session_manager.apply_volumes(
                values=values, mapping=self.mapping, inverted=self.inverted
            )

    def stop(self):
        """Stop the thread and clean up resources"""
        self.running = False
        self._check_timer.stop()
        self.microcontroller_manager.close()
