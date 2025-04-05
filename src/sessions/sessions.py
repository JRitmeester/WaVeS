from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, AudioSession, AudioDevice
from abc import ABC, abstractmethod
from _ctypes import COMError
import warnings
import comtypes
from pycaw.pycaw import (
    AudioUtilities,
    IMMDeviceEnumerator,
    EDataFlow,
    ERole,
)
from pycaw.api.mmdeviceapi import IMMDeviceEnumerator
from pycaw.constants import CLSID_MMDeviceEnumerator

warnings.filterwarnings("ignore", message="COMError attempting to get property.*")


class Session(ABC):

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def unique_name(self):
        pass

    @property
    @abstractmethod
    def is_mapped(self):
        pass

    @abstractmethod
    def set_volume(self, value):
        pass

    @abstractmethod
    def get_volume(self):
        pass

    @abstractmethod
    def mark_as_mapped(self, value: bool):
        pass


class SoftwareSession(Session):

    def __init__(self, session: AudioSession):
        self.session = session
        self.volume = self.session.SimpleAudioVolume
        self._is_mapped = False

    @property
    def name(self) -> str:
        """The unique identifier combining process name and PID"""
        return self.session.Process.name()

    @property
    def unique_name(self) -> str:
        """The display name including PID, used for UI purposes"""
        return self.session.Process.name() + f" ({self.session.Process.pid})"

    @property
    def is_mapped(self) -> bool:
        return self._is_mapped

    def __repr__(self):
        return f"Session(unique_name={self.unique_name})"

    def set_volume(self, value):
        self.volume.SetMasterVolume(value, None)

    def get_volume(self):
        return self.volume.GetMasterVolume()

    def mark_as_mapped(self, value: bool):
        self._is_mapped = value


class MasterSession(Session):

    def __init__(self):
        # Pycaw code to get the master volume interface
        self.volume = cast(
            AudioUtilities.GetSpeakers().Activate(
                IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None
            ),
            POINTER(IAudioEndpointVolume),
        )
        self._is_mapped = False

    @property
    def name(self) -> str:
        return "master"

    @property
    def unique_name(self) -> str:
        return "master"

    @property
    def is_mapped(self) -> bool:
        return self._is_mapped

    def set_volume(self, value):
        self.volume.SetMasterVolumeLevelScalar(value, None)  # Decibels for some reason

    def get_volume(self):
        return self.volume.GetMasterVolumeLevelScalar()

    def mark_as_mapped(self, value: bool):
        self._is_mapped = value


class SystemSession(Session):

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
        self.session = system_pycaw_session
        self.volume = self.session.SimpleAudioVolume
        self._is_mapped = False

    @property
    def name(self) -> str:
        return "system"

    @property
    def unique_name(self) -> str:
        return "system"

    @property
    def is_mapped(self) -> bool:
        return self._is_mapped

    def set_volume(self, value):
        self.volume.SetMasterVolume(value, None)

    def get_volume(self):
        return self.volume.GetMasterVolume()

    def mark_as_mapped(self, value: bool):
        self._is_mapped = value


class Device(AudioDevice, Session):

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
        self.volume = self._get_volume_interface()
        self._is_mapped = False

    def _get_volume_interface(self):
        device_enumerator = comtypes.CoCreateInstance(
            CLSID_MMDeviceEnumerator, IMMDeviceEnumerator, comtypes.CLSCTX_INPROC_SERVER
        )

        speaker = (
            device_enumerator.GetDevice(self.pycaw_device.id)
            if self.pycaw_device.id is not None
            else device_enumerator.GetDefaultAudioEndpoint(
                EDataFlow.eRender.value, ERole.eMultimedia.value
            )
        )

        if not speaker:
            raise RuntimeError(
                f"Could not get speaker interface for device: {self.pycaw_device}"
            )

        try:
            return cast(
                speaker.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None),
                POINTER(IAudioEndpointVolume),
            )
        except COMError:
            pass  # If the device is not active, the COMError will be raised

    def __repr__(self):
        return f"{self.pycaw_device.FriendlyName} - {self.pycaw_device.state}"

    @property
    def name(self) -> str:
        return self.pycaw_device.FriendlyName

    @property
    def unique_name(self) -> str:
        return self.name

    @property
    def is_mapped(self) -> bool:
        return self._is_mapped

    def set_volume(self, value):
        self.volume.SetMasterVolumeLevelScalar(value, None)  # Decibels for some reason

    def get_volume(self):
        return self.volume.GetMasterVolumeLevelScalar()

    def mark_as_mapped(self, value: bool):
        self._is_mapped = value
