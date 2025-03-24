"""
Control module for WaVeS application.

This module handles the core functionality of the Windows Volume Slider application,
managing audio sessions, device communication, and volume control mapping.

The module provides a Control class that serves as the main interface between
the Arduino hardware and Windows audio system, handling configuration parsing
and volume control operations.
"""

from pathlib import Path
from typing import Union

from PyQt5.QtWidgets import QMessageBox
from pycaw.pycaw import AudioUtilities
from serial.tools import list_ports

import utils
from sessions import SessionGroup, Session
from session_manager import SessionManager
import webbrowser
import re
from pprint import pprint


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

    def __init__(self, path=None):
        """
        Initialize the Control instance.
        
        Args:
            path (Path, optional): Custom path to configuration file.
                                 If None, uses default location.
        """
        self.path = (self.get_config_file_path() / 'WaVeS' / 'mapping.txt') if path is None else path

        # Check if there is a custom mapping directory specified in config.yaml. If not, use %appdata%.
        mapping_dir = utils.get_mapping_dir()
        if mapping_dir is None or mapping_dir == "":
            self.mapping_dir = utils.get_appdata_path() / "mapping.txt"
            utils.save_mapping_dir(self.mapping_dir.as_posix())
        else:
            self.mapping_dir = Path(mapping_dir)

        self.sessions = None
        self.port = None
        self.baudrate = None
        self.inverted = False
        self.unmapped = []

        self.load_config()  # Read the mappings from mapping.txt

        self.sliders = int(self.get_setting("sliders"))
        self.port = self.get_port()
        self.baudrate = self.get_setting("baudrate")
        self.inverted = self.get_setting("inverted").lower() == "true"
        self.reload_interval = int(self.get_setting("session reload interval"))

        self.session_manager = SessionManager()
        self.get_mapping()

    def load_config(self):
        """
        Load and parse the configuration file.
        
        Reads the mapping.txt file and extracts settings for:
        - Audio channel mappings
        - Device configuration
        - Slider settings
        
        Raises:
            FileNotFoundError: If mapping.txt cannot be found
        """
        self.lines = self.mapping_dir.read_text().split("\n")

    def get_setting(self, text: str) -> str:
        """
        Extract a specific setting from the configuration file.
        
        Args:
            text (str): The setting name to search for
            
        Returns:
            str: The value of the requested setting
            
        Raises:
            ValueError: If the setting is not found
        """
        matching_settings = list(filter(lambda x: text + ":" in x, self.lines))
        if len(matching_settings) == 0:
            raise ValueError(f"Setting {text} is not found in the configuration file.")
        # Use .*: ?(.*) to get the value of the setting
        value = re.search(r"^.*: ?(.*)", matching_settings[0])
        if value.group(1) == "":
            raise ValueError(f"Setting {text} is not found in the configuration file.")
        return value.group(1)

    def get_mapping(self):
        self.load_config()
        self.target_idxs = {}

        # For each of the sliders, get the mapping from config.txt, if it exists, and create the mapping.
        for idx in range(self.sliders):
            application_str = self.get_setting(str(idx))  # Get the settings from the config for each index.
            if "," in application_str:
                application_str = tuple(app.strip() for app in application_str.split(","))
            self.target_idxs[application_str] = int(idx)  # Store the settings in a dictionary.

        session_dict = {}

        
        # Loop through all the targets and the slider indices they are suppposed to map to.
        # A target is the second part of the mapping string, after the first colon (:).
        for target, idx in self.target_idxs.items():

            # If the target is a string, it is a single target.
            if type(target) == str:
                target = target.lower()

                # If indicated with "master", create a Master volume session.
                if target == "master":
                    session_dict[idx] = self.session_manager.master_session

                # If indicated with "system", create a System volume session.
                elif target == "system":
                    session_dict[idx] = self.session_manager.system_session


                # If indicated by "device:", try to make a Device session, controlling an audio output device.
                elif "device:" in target:
                    # TODO: Currently device sessions are only created when they are first requested.
                    # This means that if a device is not selected, it will not be available.
                    # This may be desirable, but not sure.
                    session_dict[idx] = self.session_manager.get_device_session(target[7:])

                # If not indicated by "master", "system", "system", or "device:", then consider it an application name,
                # and map only that application to the slider.
                elif target != "unmapped":  # Can be any application

                    # Check if the application name is found in the current active sessions.
                    if target in self.session_manager.software_sessions:
                        session = self.session_manager._software_sessions.get(target, None)
                        if session is not None:  # If there is a session that matches, create a custom Session for it.
                            session_dict[idx] = Session(session)

            # If the target is a tuple, it is a group.
            elif type(target) == tuple:
                active_sessions_in_group = []  # fmt: skip

                # Check for each application that is part of the group, if it's "master", "system" or "unmapped"
                for target_app in target:
                    target_app = target_app.lower()

                    # Exclude the other categories. Might change in the future.
                    if target_app in ["master", "system", "unmapped"] or "device:" in target_app:
                        continue

                    # Check if the target app is active.
                    session = self.session_manager.software_sessions.get(target_app, None)
                    if session is not None:
                        active_sessions_in_group.append(session)


                # If one or more of the targeted applications are active, add a SessionGroup with them.
                if len(active_sessions_in_group) > 0:
                    session_dict[idx] = SessionGroup(sessions=active_sessions_in_group)
                    # Mark all sessions in the group as mapped
                    for session in active_sessions_in_group:
                        self.session_manager.mapped_sessions[session.name] = True

        # Finally, if indicated with "unmapped", create a SessionGroup for all active audio session that haven't
        # been mapped before.
        if "unmapped" in self.target_idxs.keys():
            unmapped_idx = self.target_idxs["unmapped"]
            unmapped_sessions = [s for s in self.session_manager.software_sessions.values() if not self.session_manager.mapped_sessions[s.name]]
            if self.get_setting("system in unmapped").lower() == "true" and not self.session_manager.mapped_sessions["system"]:
                unmapped_sessions.append(self.session_manager.system_session)

            session_dict[unmapped_idx] = SessionGroup(sessions=unmapped_sessions)
            # Mark all unmapped sessions as now mapped
            for session in unmapped_sessions:
                self.session_manager.mapped_sessions[session.name] = True

        self.sessions = session_dict


    def get_sessions(self) -> list:
        """
        Returns all the currently mapped audio sessions.
        :return: List of all sessions that are currently mapped.
        """
        return list(self.sessions.values())

    def set_volume(self, values: list):
        if len(values) != self.sliders:
            return
        for index, app in self.sessions.items():
            volume = values[index] / 1023
            if self.inverted:
                volume = 1 - volume
            app.set_volume(volume)

    def get_port(self):
        ports = list_ports.comports()
        device_name = self.get_setting("device name")
        for port, desc, hwid in sorted(ports):
            if device_name in desc:
                return port
        else:
            try:
                return self.get_setting("port")
            except:
                raise ValueError("The config file does not contain the right device name or an appropriate port.")

    @staticmethod
    def get_config_file_path():
        """
        Returns a parent directory path where persistent application data can be stored.
        https://stackoverflow.com/questions/19078969/python-getting-appdata-folder-in-a-cross-platform-way
        """

        return Path.home() / "AppData/Roaming"

