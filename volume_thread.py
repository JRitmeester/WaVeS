"""
Volume control thread module for WaVeS application.

Handles the continuous communication between the Arduino hardware and
the Windows audio system. Reads volume values from the serial connection
and applies them to the appropriate audio sessions.
"""

import sys
import time
import serial
import logging
import utils
from pathlib import Path
from control import Control
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMessageBox

logger = utils.get_logger()


class MappingFileHandler(FileSystemEventHandler):
    """
    File system event handler for mapping file changes.
    
    Monitors the mapping file for modifications and triggers reload
    when changes are detected.
    """
    def __init__(self, control):
        self.control = control
        self.last_modified = time.time()
        # Debounce time in seconds to prevent multiple reloads
        self.debounce_seconds = 1

    def on_modified(self, event):
        if not event.is_directory:
            current_time = time.time()
            if current_time - self.last_modified > self.debounce_seconds:
                self.last_modified = current_time
                self.control.get_mapping()
                logger.info("Mapping file changed - reloading configuration")


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
        self.control = Control(Path.cwd() / 'mapping.txt')
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
        
        # Setup file watching
        self.observer = Observer()
        self.event_handler = MappingFileHandler(self.control)
        self.observer.schedule(
            self.event_handler, 
            str(self.control.mapping_dir.parent), 
            recursive=False
        )
        self.observer.start()

    def run(self):
        logger.info("Entering thread loop.")
        try:
            while self.running:
                if self.control.sessions is not None:
                    # Data is formatted as "<val>|<val>|<val>|<val>|<val>"
                    data = str(self.arduino.readline()[:-2], "utf-8")  # Trim off '\r\n'.
                    if data:
                        values = [float(val) for val in data.split("|")]
                        self.control.set_volume(values)
        finally:
            self.observer.stop()
            self.observer.join()

    def stop(self):
        """
        Cleanly stop the thread and file observer.
        """
        self.running = False
        self.observer.stop()
        self.observer.join()
