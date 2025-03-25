"""
Volume control thread module for WaVeS application.

Handles the continuous communication between the Arduino hardware and
the Windows audio system. Reads volume values from the serial connection
and applies them to the appropriate audio sessions.
"""

import sys
import serial
import utils
from pathlib import Path
from control import Control

from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QMessageBox

logger = utils.get_logger()


class VolumeThread(QThread):
    """
    Thread handling communication with Arduino volume sliders.

    Maintains a serial connection to the Arduino device and continuously
    reads volume values to update Windows audio sessions.

    Attributes:
        running (bool): Thread control flag
        control (Control): Audio control interface
        arduino (serial.Serial): Serial connection to Arduino
    """

    def __init__(self, mapping_dir=None):
        """
        Initialize volume control thread.

        Args:
            mapping_dir (Path, optional): Custom mapping directory path

        Raises:
            serial.SerialException: If serial connection cannot be established
        """
        super().__init__()
        logger.info("Creating volume thread.")
        self.running = True
        self.control = Control()
        logger.info("Setting up serial communication.")
        try:
            self.arduino = serial.Serial(
                self.control.port, self.control.baudrate, timeout=0.1
            )
            logger.info(self.arduino)
        except serial.SerialException:
            QMessageBox.critical(
                None,
                "Application already running",
                "The application crashed because the serial connection is busy. This may mean "
                "that another instance is already running. Please check the system tray or the "
                "task manager.",
            )
            sys.exit(0)

    def reload_sessions(self):
        self.control.get_sessions()

    def run(self):
        logger.info("Entering thread loop.")
        while self.running:
            if self.control.sessions is not None:
                # Data is formatted as "<val>|<val>|<val>|<val>|<val>"
                data = str(self.arduino.readline()[:-2], "utf-8")  # Trim off '\r\n'.
                if data:
                    values = [float(val) for val in data.split("|")]
                    self.control.set_volume(values)
