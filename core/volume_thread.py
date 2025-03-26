import sys
import serial
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMessageBox
from sessions import SessionManagerProtocol
from config import ConfigManagerProtocol
from mapping import MappingManagerProtocol


class VolumeThread(QThread):

    def __init__(
        self,
        config_manager: ConfigManagerProtocol,
        session_manager: SessionManagerProtocol,
        mapping_manager: MappingManagerProtocol,
    ):

        super().__init__()

        self.config_manager = config_manager
        self.session_manager = session_manager
        self.mapping_manager = mapping_manager

        port = self.config_manager.get_serial_port()
        baudrate = self.config_manager.get_setting("baudrate")
        self.inverted = self.config_manager.get_setting("inverted").lower() == "true"
        self.mapping = self.mapping_manager.get_mapping(
            self.session_manager, self.config_manager
        )

        try:
            self.arduino = serial.Serial(port, baudrate, timeout=0.1)
        except serial.SerialException:
            QMessageBox.critical(
                None,
                "Application already running",
                "The application crashed because the serial connection is busy. This may mean "
                "that another instance is already running. Please check the system tray or the "
                "task manager.",
            )
            sys.exit(0)

    def reload_mapping(self):
        self.mapping = self.mapping_manager.get_mapping(
            self.session_manager, self.config_manager
        )

    def run(self):
        while True:
            # Data is formatted as "<val>|<val>|<val>|<val>|<val>"
            data = str(self.arduino.readline()[:-2], "utf-8")  # Trim off '\r\n'.
            if data:
                values = [float(val) for val in data.split("|")]
                if len(values) != int(self.config_manager.get_setting("sliders")):
                    return
                for index, app in self.mapping.items():
                    volume = values[index] / 1023
                    if self.inverted:
                        volume = 1 - volume
                    app.set_volume(volume)
