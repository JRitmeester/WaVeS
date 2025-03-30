import sys
import serial
from PyQt5.QtCore import QThread
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

    def reload_mapping(self):
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
        self.running = False
        self.microcontroller_manager.close()
