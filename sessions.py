from ctypes import cast, POINTER
from typing import List

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, AudioSession, AudioDevice
from abc import ABC, abstractmethod
from _ctypes import COMError
import utils
from MyAudioUtilities import MyAudioUtilities
import warnings

warnings.filterwarnings("ignore", message="COMError attempting to get property.*")


class Session(ABC):

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def set_volume(self, value):
        pass

    @abstractmethod
    def get_volume(self):
        pass


class SoftwareSession(Session):
    """
    Base class for managing individual audio sessions.

    Attributes:
        idx (int): Index for mapping to physical slider
        session (AudioSession): pycaw audio session object
        name (str): Process name of the audio session
        volume (SimpleAudioVolume): Volume control interface
    """

    def __init__(self, session: AudioSession):
        self.session = session
        self.volume = self.session.SimpleAudioVolume

    @property
    def name(self) -> str:
        return self.session.Process.name()

    def __repr__(self):
        return f"Session(name={self.name})"

    def set_volume(self, value):
        self.volume.SetMasterVolume(value, None)

    def get_volume(self):
        return self.volume.GetMasterVolume()


class SessionGroup:
    """
    Groups multiple audio sessions for collective volume control.

    Useful for controlling volume of multiple instances of the same application
    or related audio sessions together.

    Attributes:
        sessions (List[Session]): List of audio sessions in this group
    """

    def __init__(self, sessions: List[Session]):
        self.sessions = sessions

    def __repr__(self):
        return f"SessionGroup(sessions={[session.name for session in self.sessions]})"

    def __contains__(self, item: AudioSession):
        if type(item) == AudioSession:
            return any([s.session == item for s in self.sessions])

    def set_volume(self, value):
        for session in self.sessions:
            session.set_volume(value)

    def get_volume(self):
        return [session.get_volume() for session in self.sessions]


class MasterSession(Session):
    """
    Controls the system master volume.

    Provides interface to control the overall system volume level
    using the Windows audio endpoint volume interface.
    """

    def __init__(self):
        # Pycaw code to get the master volume interface
        self.volume = cast(
            AudioUtilities.GetSpeakers().Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None
            ),
            POINTER(IAudioEndpointVolume),
        )

    def set_volume(self, value):
        self.volume.SetMasterVolumeLevelScalar(value, None)  # Decibels for some reason

    def get_volume(self):
        return self.volume.GetMasterVolumeLevelScalar()

    @property
    def name(self) -> str:
        return "master"


class SystemSession(SoftwareSession):
    """
    Controls system sound effects volume.

    Manages volume for Windows system sounds like notifications,
    alerts, and other system audio events.
    """

    def __init__(self):
        available_pycaw_sessions = AudioUtilities.GetAllSessions()
        system_pycaw_session = next(
            (
                session
                for session in available_pycaw_sessions
                if "SystemRoot" in session.DisplayName
            ),
            None,
        )
        if system_pycaw_session is None:
            raise RuntimeError("System sounds session could not be found.")
        else:
            print(f"System sounds session found: {system_pycaw_session}")
        self.session = system_pycaw_session

        self.volume = self.session.SimpleAudioVolume

    @property
    def name(self) -> str:
        return "system"

    def set_volume(self, value):
        super().set_volume(value)

    def get_volume(self):
        return super().get_volume()

    def __repr__(self):
        return self.name


class Device(AudioDevice, Session):
    """
    Controls specific audio output devices.

    Allows direct control of individual audio devices like speakers,
    headphones, or other audio outputs.

    Attributes:
        device_name: The specific audio device being controlled
    """

    def __init__(self, pycaw_device: AudioDevice):
        # Initialize AudioDevice with all the required fields from the source device
        AudioDevice.__init__(
            self,
            id=pycaw_device.id,
            state=pycaw_device.state,
            properties=pycaw_device.properties,
            dev=pycaw_device._dev,
        )
        self.pycaw_device = pycaw_device

        try:
            speaker = MyAudioUtilities.GetSpeaker(pycaw_device.id)
            if speaker:
                try:
                    self.volume = cast(
                        speaker.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None),
                        POINTER(IAudioEndpointVolume),
                    )
                except COMError as e:
                    pass
            else:
                raise RuntimeError(
                    f"Could not get speaker interface for device: {pycaw_device}"
                )
        except Exception as e:
            raise

    def __repr__(self):
        return f"{self.pycaw_device.FriendlyName} - {self.pycaw_device.state}"

    @property
    def name(self) -> str:
        return self.pycaw_device.FriendlyName

    def set_volume(self, value):
        self.volume.SetMasterVolumeLevelScalar(value, None)  # Decibels for some reason

    def get_volume(self):
        return self.volume.GetMasterVolumeLevelScalar()
