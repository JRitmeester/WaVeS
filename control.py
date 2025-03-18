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
from sessions import SessionGroup, Master, Session, System, Device
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

        print(self.mapping_dir)
        self.sessions = None
        self.port = None
        self.baudrate = None
        self.inverted = False
        self.unmapped = []
        self.found_pycaw_sessions = None

        self.load_config()  # Read the mappings from mapping.txt

        self.sliders = int(self.get_setting("sliders"))
        self.port = self.get_port()
        self.baudrate = self.get_setting("baudrate")
        self.inverted = self.get_setting("inverted").lower() == "true"
        self.reload_interval = int(self.get_setting("session reload interval"))

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
        setting = list(filter(lambda x: text + ":" in x, self.lines))[0]
        return re.sub(r"^[a-zA-Z0-9]*: *", "", setting)

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

        # Look up table for the incoming Arduino data, mapping an index to a Session object.
        self.found_pycaw_sessions = AudioUtilities.GetAllSessions()

        active_sessions = {
            session.Process.name().lower(): session
            for session in self.found_pycaw_sessions
            if session.Process is not None
        }

        mapped_sessions = []
        system_session = [session for session in self.found_pycaw_sessions if "SystemRoot" in session.DisplayName][0]

        # Loop through all the targets and the slider indices they are suppposed to map to.
        # A target is the second part of the mapping string, after the first colon (:).
        for target, idx in self.target_idxs.items():

            # If the target is a string, it is a single target.
            if type(target) == str:
                target = target.lower()

                # If indicated with "master", create a Master volume session.
                if target == "master":
                    session_dict[idx] = Master(idx=idx)

                # If indicated with "system", create a System volume session.
                elif target == "system":
                    session_dict[idx] = System(idx=idx, session=system_session)

                    # System sounds are considered a Session by Pycaw, so add it so that it is not picked up
                    # at the end by an eventual "unmapped" category.
                    mapped_sessions.append(system_session)

                # If indicated by "device:", try to make a Device session, controlling an audio output device.
                elif "device:" in target:
                    session_dict[idx] = Device(target[7:])

                # If not indicated by "master", "system", "system", or "device:", then consider it an application name,
                # and map only that application to the slider.
                elif target != "unmapped":  # Can be any application

                    # Check if the application name is found in the current active sessions.
                    if target in active_sessions:
                        session = active_sessions.get(target, None)
                        if session is not None:  # If there is a session that matches, create a custom Session for it.
                            session_dict[idx] = Session(idx, session)
                        mapped_sessions.append(session)

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
                    session = active_sessions.get(target_app, None)
                    if session is not None:
                        active_sessions_in_group.append(session)
                        mapped_sessions.append(session)

                # If one or more of the targeted applications are active, add a SessionGroup with them.
                if len(active_sessions_in_group) > 0:
                    session_dict[idx] = SessionGroup(group_idx=idx, sessions=active_sessions_in_group)

        # Finally, if indicated with "unmapped", create a SessionGroup for all active audio session that haven't
        # been mapped before.
        if "unmapped" in self.target_idxs.keys():
            unmapped_idx = self.target_idxs["unmapped"]
            unmapped_sessions = [ses for ses in active_sessions.values() if ses not in mapped_sessions]
            if self.get_setting("system in unmapped").lower() == "false" and system_session in unmapped_sessions:
                unmapped_sessions.remove(system_session)

            session_dict[unmapped_idx] = SessionGroup(unmapped_idx, sessions=unmapped_sessions)

        self.sessions = session_dict

    def find_session(self, session_name: str, case_sensitive: bool = False) -> Union[Session, None]:
        """
        Finds a session with "session_name", if it exists. Can be searched for with case sensitivity if needed.
        :param session_name: Name of the Process object of the session, like "chrome.exe" or "Spotify.exe".
        Case insensitive by default.
        :param case_sensitive: Boolean flag to search for "session_name" with case sensitivity.
        :return: The Session with name "session_name" if it exists, None otherwise.
        """
        for idx, session in self.sessions.items():
            if not case_sensitive:
                if session.name.lower() == session_name.lower():
                    return session
            else:
                if session.name == session_name:
                    return session
        else:
            return None

    def get_sessions(self) -> list:
        """
        Returns all the currently mapped audio sessions.
        :return: List of all sessions that are currently mapped.
        """
        return list(self.sessions.values())

    def set_volume(self, values: list):
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

