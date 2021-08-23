import sys
from pathlib import Path

import serial
from PyQt5.QtCore import QThread
import logging

from PyQt5.QtWidgets import QMessageBox

from control import Control

logger = logging.getLogger('root')


class VolumeThread(QThread):

    def __init__(self):
        super().__init__()
        logger.info("Creating volume thread.")
        self.running = True
        self.control = Control(Path.cwd() / 'mapping.txt')
        logger.info("Setting up serial communication.")
        try:
            self.arduino = serial.Serial(self.control.port, self.control.baudrate, timeout=.1)
        except serial.SerialException as e:
            msg = QMessageBox.critical(None, "Application already running",
                                       "The application crashed because the serial "
                                       "connection is busy. This may mean that another "
                                       "instance is already running. Please check the "
                                       "system tray or the task manager.")

            raise

    def run(self):
        logger.info("Entering thread loop.")
        while self.running:
            if self.control.sessions is not None:
                # Data is formatted as "<val>|<val>|<val>|<val>|<val>"
                data = str(self.arduino.readline()[:-2], 'utf-8')  # Trim off '\r\n'.
                if data:
                    values = [float(val) for val in data.split('|')]
                    self.control.set_volume(values)
