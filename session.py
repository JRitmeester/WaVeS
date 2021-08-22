from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class Session:
    """
    Contains the pycaw Session, the mapping index, the session name and the SimpleAudioVolume to get/set the volume.
    """

    def __init__(self, idx: int, name: str = None, session=None):
        self.session = session
        self.idx = idx
        if session is not None and session.Process is not None:  # Filter out System sounds.
            self.name = session.Process.name()
            self.volume = self.session.SimpleAudioVolume

    def __repr__(self):
        return f"Session(name={self.name}, index={self.idx})"

    def set_volume(self, value):
        self.volume.SetMasterVolume(value, None)

    def get_volume(self):
        return self.volume.GetMasterVolume()

    def mute(self):
        self.volume.SetMute(1, None)

    def unmute(self):
        self.volume.SetMute(0, None)


class SessionGroup:
    """
    Contains the pycaw Session, the mapping index, the session name and the SimpleAudioVolume to get/set the volume.
    """

    def __init__(self, sessions, idx: int, name: str):
        self.sessions = [Session(idx, name, session) for session in sessions]
        self.idx = idx
        self.name = name

    def __repr__(self):
        return f"SessionGroup(name={self.name}, index={self.idx}, " \
               f"sessions={[session.name for session in self.sessions]})"

    def set_volume(self, value):
        for session in self.sessions:
            session.volume.SetMasterVolume(value, None)

    def get_volume(self):
        return [session.volume.GetMasterVolume() for session in self.sessions]

    def mute(self):
        for session in self.sessions:
            session.volume.SetMute(1, None)

    def unmute(self):
        for session in self.sessions:
            session.volume.SetMute(0, None)


class Master(Session):

    def __init__(self, idx: int):
        super().__init__(idx=idx)

        # Pycaw code to get the master volume interface
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))

        self.name = 'Master'

    def set_volume(self, value):
        self.volume.SetMasterVolumeLevelScalar(value, None)  # Decibels for some reason

    def get_volume(self):
        return self.volume.GetMasterVolumeLevelScalar()


class System(Session):

    def __init__(self, session, idx: int):
        super().__init__(idx=idx)
        self.volume = session.SimpleAudioVolume
        self.name = "System"