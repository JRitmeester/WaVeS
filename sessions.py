from ctypes import cast, POINTER
from typing import List

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, AudioSession

import utils
from MyAudioUtilities import MyAudioUtilities

logger = utils.get_logger()

class Session:
    """
    Contains the pycaw Session, the mapping index, the session name and the SimpleAudioVolume to get/set the volume.
    """

    def __init__(self, idx: int, session: AudioSession = None):
        self.idx = idx
        self.session = session
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

    def __init__(self, group_idx: int, sessions: List[AudioSession]):
        self.group_idx = group_idx
        self.sessions = [Session(group_idx, session) for session in sessions]

    def __repr__(self):
        return f"SessionGroup(index={self.group_idx}, " \
               f"sessions={[session.name for session in self.sessions]})"

    def __contains__(self, item: AudioSession):
        if type(item) == AudioSession:
            return any([s.session == item for s in self.sessions])
        elif type(item) == int:
            return any([s.idx == item for s in self.sessions])

    def add_session(self, session: AudioSession):
        self.sessions.append(Session(self.group_idx, session))

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

    def __init__(self, idx: int, session):
        super().__init__(idx=idx, session=session)
        self.name = 'System Sounds'
        self.session = session
        self.volume = session.SimpleAudioVolume

    def __repr__(self):
        return self.name


class Device(Session):

    def __init__(self, device_name: str):
        super().__init__(-1)
        self.selected_device = None

        devicelist = AudioUtilities.GetAllDevices()
        for device in devicelist:
            if device_name.lower() in str(device).lower():
                self.selected_device = device
        if self.selected_device is None:
            raise RuntimeError(f"Sound device {device_name} could not be found. Please correct the name or remove it.")

        speaker = MyAudioUtilities.GetSpeaker(self.selected_device.id)
        interface = speaker.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        logger.info(f"Selected \"{self}\" for \"{device_name.strip()}\"")

    def __repr__(self):
        return str(self.selected_device)

    def set_volume(self, value):
        self.volume.SetMasterVolumeLevelScalar(value, None)  # Decibels for some reason

    def get_volume(self):
        return self.volume.GetMasterVolumeLevelScalar()