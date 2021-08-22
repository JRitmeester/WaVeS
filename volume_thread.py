from pathlib import Path

import serial
from PyQt5.QtCore import QThread
import logging

from control import Control

logger = logging.getLogger('root')

class VolumeThread(QThread):

    def __init__(self):
        super().__init__()
        logger.info("Creating volume thread.")
        self.running = True
        self.control = Control(Path.cwd() / 'mapping.txt')
        logger.info("Setting up serial communication.")
        self.arduino = serial.Serial(self.control.port, self.control.baudrate, timeout=.1)

    def run(self):
        logger.info("Entering thread loop.")
        while self.running:
            if self.control.sessions is not None:
                # Data is formatted as "<val>|<val>|<val>|<val>|<val>"
                data = str(self.arduino.readline()[:-2], 'utf-8')  # Trim off '\r\n'.
                if data:
                    values = [float(val) for val in data.split('|')]
                    self.control.set_volume(values)