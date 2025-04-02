from sessions.sessions import (
    SessionGroup,
    MasterSession,
    Session,
    SystemSession,
    Device,
    SoftwareSession,
)
from pycaw.pycaw import AudioUtilities
from pycaw.constants import AudioDeviceState
from sessions.session_protocol import SessionManagerProtocol
from typing import Set

class SessionManager(SessionManagerProtocol):

    def __init__(self) -> None:
        self.all_pycaw_sessions = AudioUtilities.GetAllSessions()
        self.all_pycaw_devices = AudioUtilities.GetAllDevices()
        self.software_sessions = []
        self._master_session: MasterSession = MasterSession()
        self._system_session: SystemSession = SystemSession()
        self.devices: dict[str, Device] = {}
        self.mapped_sessions: dict[str, bool] = {
            "master": False,
            "system": False,
        }
        self._last_session_ids: Set[str] = set()
        self._last_device_ids: Set[str] = set()
        self.reload_sessions_and_devices()

    @property
    def system_session(self) -> SystemSession:
        return self._system_session

    @property
    def master_session(self) -> MasterSession:
        return self._master_session

    def _get_session_ids(self) -> Set[str]:
        """Get a set of unique identifiers for all current sessions"""
        return {session.Process.pid for session in self.all_pycaw_sessions if session.Process is not None}

    def _get_device_ids(self) -> Set[str]:
        """Get a set of unique identifiers for all current devices"""
        return {device.id for device in self.all_pycaw_devices if device.FriendlyName is not None}

    def check_for_changes(self) -> bool:
        """Check if there are any changes in sessions or devices"""
        # Get new sessions and devices without modifying current state
        new_sessions = AudioUtilities.GetAllSessions()
        new_devices = AudioUtilities.GetAllDevices()
        
        # Get current IDs for comparison
        current_session_ids = self._get_session_ids()
        current_device_ids = self._get_device_ids()
        
        # Get new IDs for comparison
        new_session_ids = {session.Process.pid for session in new_sessions if session.Process is not None}
        new_device_ids = {device.id for device in new_devices if device.FriendlyName is not None}
        
        # Check if there are any changes
        session_changes = new_session_ids != current_session_ids
        device_changes = new_device_ids != current_device_ids
        
        if session_changes or device_changes:
            # Update state with new sessions and devices
            self.all_pycaw_sessions = new_sessions
            self.all_pycaw_devices = new_devices
            self._last_session_ids = new_session_ids
            self._last_device_ids = new_device_ids
            return True
        return False

    def reload_sessions_and_devices(self):
        """Reload all sessions and devices"""
        # Clear existing sessions and devices
        self.software_sessions.clear()
        self.devices.clear()
        
        # Recreate sessions and devices
        self.create_software_sessions()
        self.create_device_sessions()

    def create_software_sessions(self):
        pycaw_software_sessions = filter(
            lambda x: x.Process is not None and "SystemRoot" not in x.DisplayName,
            self.all_pycaw_sessions
        )  # Filter out system sounds and sessions without Process
        for pycaw_session in pycaw_software_sessions:
            session = SoftwareSession(pycaw_session)
            # Use unique_name (with PID) for software_sessions dictionary
            self.software_sessions.append(session)
            # Use process name (without PID) for mapped_sessions dictionary
            self.mapped_sessions[session.unique_name] = False

    def get_software_session_by_name(self, session_name: str) -> Session:
        return next((s for s in self.software_sessions if s.name == session_name), None)
    
    def get_software_session_by_unique_name(self, unique_name: str) -> Session:
        return next((s for s in self.software_sessions if s.unique_name == unique_name), None)  
    
    def get_device_session(self, specified_device_name: str) -> Device:
        """
        See if the device is a substring of any device name.
        If not, raise an error.
        """
        target_name = specified_device_name.lower().strip()
        
        # Check if target is substring of any device name
        for device_name, device in self.devices.items():
            device_name_lower = device_name.lower().strip()
            if target_name in device_name_lower:
                return device
            
        raise ValueError(f"Device {specified_device_name} not found.")
        

    def create_device_sessions(self):
        for pycaw_device in self.all_pycaw_devices:
            # try:
            if (
                pycaw_device.FriendlyName == None
                or pycaw_device.state == AudioDeviceState.NotPresent
            ):
                continue
            device = Device(pycaw_device)
            self.mapped_sessions[device.name] = False
            self.devices[device.name] = device


    def apply_volumes(
        self, values: list[float], mapping: dict[int, Session], inverted: bool
    ) -> None:
        """Apply volume values to the mapped sessions"""
        for index, sessions in mapping.items():
            volume = values[index]
            if inverted:
                volume = 1 - volume
            for session in sessions:
               session.set_volume(volume)
