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

class SessionManager(SessionManagerProtocol):

    def __init__(self) -> None:
        self.all_pycaw_sessions = AudioUtilities.GetAllSessions()
        self.all_pycaw_devices = AudioUtilities.GetAllDevices()
        self.software_sessions = {}
        self._master_session: MasterSession = MasterSession()
        self._system_session: SystemSession = SystemSession()
        self.devices: dict[str, Device] = {}
        self.mapped_sessions: dict[str, bool] = {
            "master": False,
            "system": False,
        }
        self.reload_sessions_and_devices()

    @property
    def system_session(self) -> SystemSession:
        return self._system_session

    @property
    def master_session(self) -> MasterSession:
        return self._master_session

    def reload_sessions_and_devices(self):
        self.all_pycaw_sessions = AudioUtilities.GetAllSessions()
        self.all_pycaw_devices = AudioUtilities.GetAllDevices()
        self.create_software_sessions()
        self.create_device_sessions()

    def create_software_sessions(self):
        pycaw_software_sessions = filter(
            lambda x: x.Process is not None, self.all_pycaw_sessions
        )  # Filter out system sounds
        for pycaw_session in pycaw_software_sessions:
            session = SoftwareSession(pycaw_session)
            self.mapped_sessions[session.name] = False
            self.software_sessions[session.name] = session

    def get_software_session(self, session_name: str) -> Session:
        session = self.software_sessions.get(session_name, None)
        if session is None:
            raise ValueError(f"Software session {session_name} not found.")
        return session
    
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
        for index, session in mapping.items():
            volume = values[index]
            if inverted:
                volume = 1 - volume
            session.set_volume(volume)
