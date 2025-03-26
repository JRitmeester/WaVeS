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

    def get_device_session(self, device_name: str) -> Device:
        device = self.devices.get(device_name, None)
        if device is None:
            raise ValueError(f"Device {device_name} not found.")
        return device
