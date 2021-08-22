from pathlib import Path
from typing import Union

from PyQt5.QtWidgets import QMessageBox
from pycaw.pycaw import AudioUtilities
from serial.tools import list_ports
from session import SessionGroup, Master, Session, System
import webbrowser

default_mapping_txt = """
# Make sure this file is placed in the same directory as vc.exe. To make this startup on boot (for Windows), create a
# shortcut and place it in the Start-up folder.

# Application is either "master" for master volume, the application name "spotify.exe" (case insensitive) for Spotify
# (for Windows, this can be found in Task Manager under the "Details" tab), "unmapped" for any and all applications
# that are currently running, but have not been explicitly assigned a slider. "unmapped" excludes the master channel.
# Finally, "system" allows you to control the system sound volume.

# Stick to the syntax:
#<number>:<application>
# Here, number is the index
0: master
1: system
2: chrome.exe
3: spotify.exe
4: unmapped

# Find the device name when the sliders are connected to USB in Device Manager, so that when you switch USB ports,
# you don't have to change the COM port.
device name: Arduino Micro

# Indicate the number of sliders you're using:
sliders: 5
# Port is only used if the device name can't be found automatically.
port:COM8

# Make sure this matches the baudrate on the Arduino's Serial.begin() call.
baudrate:9600

# You can use this to invert the sliders: top is low volume, bottom is high volume.
inverted:False
"""

class Control:
    """
    Contains all the fields necessary to control the audio sessions. It is responsible for parsing the config file,
    and harbours the sessions so that they can be accessed as needed.
    """

    def __init__(self, path=None):
        self.path = Path.cwd() / 'mapping.txt' if path is None else path

        if not self.path.is_file():
            self.path.parent.mkdir(exist_ok=True)
            self.path.touch()
            self.path.write_text(default_mapping_txt)
            QMessageBox.information(None, "New config file created", f"A new config file was created for you in the "
                                                                     f"same directory as the app:\n\n{str(self.path)}."
                                                                     f"\n\nIt will now be opened for you to view the "
                                                                     f"settings.")
            webbrowser.open(self.path)

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
        self.inverted = self.get_setting("inverted") in ["True", "true"]

        self.get_mapping()
        self.systray = None

    def set_systray(self, systray):
        self.systray = systray

    def load_config(self):
        self.lines = self.path.read_text().split('\n')

    def get_setting(self, text):
        """
        Inner method that finds a line from the config file that contains "text".
        :param text: Text that is to be found, like "port:" or "baudrate:"
        :return: The first element in the config file that contains "text", if any.
        """
        setting = list(filter(lambda x: text + ":" in x, self.lines))[0]
        return setting.split(":")[1].strip()

    def get_mapping(self):
        self.load_config()
        self.mapping_dict = {}

        # For each of the sliders, get the mapping from config.txt, if it exists, and create the mapping.
        for idx in range(self.sliders):
            application = self.get_setting(str(idx))
            self.mapping_dict[application] = int(idx)

        session_dict = {}  # Look up table for the incoming Arduino data, mapping an index to a Session object.
        self.found_pycaw_sessions = AudioUtilities.GetAllSessions()
        mapped_sessions = []

        for session in self.found_pycaw_sessions:  # For each application with an audio session,
            if session.Process is not None:  # If it has a process (System sounds doesn't, for example),
                for application in self.mapping_dict:  # For each each of the currently mapped applications,
                    if session.Process.name().lower() == application.lower():  # Check if this session is that app,
                        session_dict[self.mapping_dict[application]] = Session(session=session,
                                                                               idx=self.mapping_dict[application])
                        mapped_sessions.append(session)
            else:
                # Act as if system sounds has been mapped to prevent issues down the line.
                mapped_sessions.append(session)
        self.unmapped = [session for session in self.found_pycaw_sessions if session not in mapped_sessions]

        # Look for mapping of 'master' and 'unmapped'.
        for application, idx in self.mapping_dict.items():
            if application.lower() == 'master':
                session_dict[idx] = Master(idx=idx)

            elif application.lower() == 'unmapped':
                session_dict[idx] = SessionGroup(self.unmapped, idx, "Unmapped")

            elif application.lower() == 'system':
                session_dict[idx] = System(session=self.found_pycaw_sessions[0], idx=idx)

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