"""
Control module for WaVeS application.

This module handles the core functionality of the Windows Volume Slider application,
managing audio sessions, device communication, and volume control mapping.

The module provides a Control class that serves as the main interface between
the Arduino hardware and Windows audio system, handling configuration parsing
and volume control operations.
"""

from pathlib import Path
from typing import Union, Dict, Any

from PyQt5.QtWidgets import QMessageBox
from pycaw.pycaw import AudioUtilities
from serial.tools import list_ports

import utils
from sessions import SessionGroup, Session
from session_manager import SessionManager
import webbrowser
import re
from pprint import pprint
from mapping_manager import MappingManager
from config_manager import ConfigManager


class Control:
    """
    Main controller class for audio session management and hardware integration.

    This class handles all audio session control operations, including:
    - Configuration file parsing and management
    - Audio session discovery and mapping
    - Communication with Arduino hardware
    - Volume control operations

    Attributes:
        path (Path): Path to the configuration file
        mapping_dir (Path): Directory containing mapping configurations
        sessions (list): List of active audio sessions
        port (str): Serial port for Arduino communication
        baudrate (int): Serial communication baudrate
        inverted (bool): Whether slider values should be inverted
        sliders (int): Number of physical sliders connected
    """

    def __init__(self):
        """
        Initialize the Control instance.
        """

        # Initialize managers
        self.config_manager = ConfigManager(
            Path.home() / "AppData/Roaming" / "WaVeS" / "mapping.txt"
        )
        self.session_manager = SessionManager()
        self.mapping_manager = MappingManager(
            n_sliders=int(self.config_manager.get_setting("sliders"))
        )

        # Initialize control parameters
        self.port = self.config_manager.get_serial_port()
        self.baudrate = self.config_manager.get_setting("baudrate")
        self.inverted = self.config_manager.get_setting("inverted").lower() == "true"
        self.reload_interval = int(
            self.config_manager.get_setting("session reload interval")
        )

        # Get initial mappings
        self.sessions = self.get_mapping()

    def get_mapping(self):
        """Update session mappings"""
        self.config_manager.load_config()
        return self.mapping_manager.create_mappings(
            self.session_manager, self.config_manager
        )


    def get_sessions(self) -> list:
        """
        Returns all the currently mapped audio sessions.
        :return: List of all sessions that are currently mapped.
        """
        return list(self.sessions.values())

    def set_volume(self, values: list):
        if len(values) != int(self.config_manager.get_setting("sliders")):
            return
        for index, app in self.sessions.items():
            volume = values[index] / 1023
            if self.inverted:
                volume = 1 - volume
            app.set_volume(volume)

    @staticmethod
    def get_config_file_path():
        """
        Returns a parent directory path where persistent application data can be stored.
        https://stackoverflow.com/questions/19078969/python-getting-appdata-folder-in-a-cross-platform-way
        """

        return Path.home() / "AppData/Roaming"
