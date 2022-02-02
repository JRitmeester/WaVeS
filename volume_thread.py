import sys
import time
import serial
import logging
import utils
from pathlib import Path
from control import Control

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMessageBox

logger = utils.get_logger()


class VolumeThread(QThread):
    def __init__(self, mapping_dir=None):
        super().__init__()
        logger.info("Creating volume thread.")
        self.running = True


        self.control = Control()

        logger.info("Setting up serial communication.")
        try:
            self.arduino = serial.Serial(self.control.port, self.control.baudrate, timeout=0.1)
            logger.info(self.arduino)
        except serial.SerialException:
            QMessageBox.critical(
                None,
                "Application already running",
                "The application crashed because the serial connection is busy. This may mean "
                "that another instance is already running. Please check the system tray or the "
                "task manager.",
            )
            raise

    def run(self):
        logger.info("Entering thread loop.")
        while self.running:
            if self.control.sessions is not None:
                # Data is formatted as "<val>|<val>|<val>|<val>|<val>"
                data = str(self.arduino.readline()[:-2], "utf-8")  # Trim off '\r\n'.
                if data:
                    values = [float(val) for val in data.split("|")]
                    self.control.set_volume(values)
