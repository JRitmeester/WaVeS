"""
Volume control thread module for WaVeS application.

Handles the continuous communication between the Arduino hardware and
the Windows audio system. Reads volume values from the serial connection
and applies them to the appropriate audio sessions.
"""

import sys
import serial
from config_manager import ConfigManager
from mapping_manager import MappingManager
from session_manager import SessionManager
from pathlib import Path
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMessageBox
from protocols.config_protocol import ConfigManagerProtocol
from protocols.session_protocol import SessionManagerProtocol
from protocols.mapping_protocol import MappingManagerProtocol


class VolumeThread(QThread):
    """
    Thread handling communication with Arduino volume sliders.

    Maintains a serial connection to the Arduino device and continuously
    reads volume values to update Windows audio sessions.
    """

    def __init__(
        self,
        config_manager: ConfigManagerProtocol,
        session_manager: SessionManagerProtocol,
        mapping_manager: MappingManagerProtocol,
    ):
        """
        Initialize volume control thread.

        Args:
            config_manager: Configuration management instance
            session_manager: Session management instance
            mapping_manager: Mapping management instance

        Raises:
            serial.SerialException: If serial connection cannot be established
        """
        super().__init__()

        self.config_manager = config_manager
        self.session_manager = session_manager
        self.mapping_manager = mapping_manager

        port = self.config_manager.get_serial_port()
        baudrate = self.config_manager.get_setting("baudrate")
        self.inverted = self.config_manager.get_setting("inverted").lower() == "true"
        self.sessions = self.mapping_manager.get_mapping(
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

    def run(self):
        while True:
            # Data is formatted as "<val>|<val>|<val>|<val>|<val>"
            data = str(self.arduino.readline()[:-2], "utf-8")  # Trim off '\r\n'.
            if data:
                values = [float(val) for val in data.split("|")]
                if len(values) != int(self.config_manager.get_setting("sliders")):
                    return
                for index, app in self.sessions.items():
                    volume = values[index] / 1023
                    if self.inverted:
                        volume = 1 - volume
                    app.set_volume(volume)
