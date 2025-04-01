import pytest
from unittest.mock import Mock, patch
from sessions.session_manager import SessionManager
from sessions.sessions import (
    SessionGroup,
    MasterSession,
    Session,
    SystemSession,
    Device,
    SoftwareSession,
)
from pycaw.pycaw import AudioUtilities, AudioSession, AudioDevice
from pycaw.constants import AudioDeviceState


class MockAudioSession:
    def __init__(self, name: str, display_name: str = None):
        self.Process = Mock()
        self.Process.name.return_value = name
        self.DisplayName = display_name or name
        self.SimpleAudioVolume = Mock()
        self.SimpleAudioVolume.GetMasterVolume.return_value = 0.5
        self.SimpleAudioVolume.SetMasterVolume = Mock()


class MockAudioDevice:
    def __init__(self, name: str, state: AudioDeviceState = AudioDeviceState.Active):
        self.FriendlyName = name
        self.state = state
        self.id = f"test_device_{name}"
        self.properties = {}
        self._dev = Mock()
        self.volume = Mock()
        self.volume.GetMasterVolumeLevelScalar.return_value = 0.5
        self.volume.SetMasterVolumeLevelScalar = Mock()

    @property
    def name(self) -> str:
        return self.FriendlyName

    def set_volume(self, value):
        self.volume.SetMasterVolumeLevelScalar(value, None)

    def get_volume(self):
        return self.volume.GetMasterVolumeLevelScalar()


class MockMasterSession(MasterSession):
    def __init__(self):
        self.volume = Mock()
        self.volume.GetMasterVolumeLevelScalar.return_value = 0.5
        self.volume.SetMasterVolumeLevelScalar = Mock()

    @property
    def name(self) -> str:
        return "master"

    def set_volume(self, value):
        self.volume.SetMasterVolumeLevelScalar(value, None)

    def get_volume(self):
        return self.volume.GetMasterVolumeLevelScalar()


class MockSystemSession(SystemSession):
    def __init__(self):
        self.session = MockAudioSession("System Sounds", "SystemRoot\\System32\\SystemSounds")
        self.volume = self.session.SimpleAudioVolume

    @property
    def name(self) -> str:
        return "system"

    def set_volume(self, value):
        self.volume.SetMasterVolume(value, None)

    def get_volume(self):
        return self.volume.GetMasterVolume()


class MockDevice(Device):
    def __init__(self, pycaw_device: AudioDevice):
        # Don't call parent's __init__ to avoid COM interface calls
        self.pycaw_device = pycaw_device
        self.volume = Mock()
        self.volume.GetMasterVolumeLevelScalar.return_value = 0.5
        self.volume.SetMasterVolumeLevelScalar = Mock()
        self.id = pycaw_device.id
        self.state = pycaw_device.state
        self.properties = pycaw_device.properties
        self._dev = pycaw_device._dev

    def _get_volume_interface(self):
        return self.volume

    @property
    def name(self) -> str:
        return self.pycaw_device.FriendlyName

    def set_volume(self, value):
        self.volume.SetMasterVolumeLevelScalar(value, None)

    def get_volume(self):
        return self.volume.GetMasterVolumeLevelScalar()

    def __repr__(self):
        return f"{self.pycaw_device.FriendlyName} - {self.pycaw_device.state}"


@pytest.fixture
def session_manager():
    # Mock AudioUtilities
    mock_audio_utilities = Mock()
    mock_audio_utilities.GetAllSessions.return_value = []
    mock_audio_utilities.GetAllDevices.return_value = []
    mock_audio_utilities.GetSpeakers.return_value = Mock()
    
    # Mock COM interface calls
    mock_device_enumerator = Mock()
    mock_device_enumerator.GetDevice.return_value = Mock()
    mock_device_enumerator.GetDefaultAudioEndpoint.return_value = Mock()
    
    with patch('sessions.session_manager.AudioUtilities', mock_audio_utilities), \
         patch('sessions.sessions.MasterSession', MockMasterSession), \
         patch('sessions.sessions.SystemSession', MockSystemSession), \
         patch('sessions.sessions.Device', MockDevice), \
         patch('sessions.sessions.comtypes.CoCreateInstance', return_value=mock_device_enumerator):
        return SessionManager()


def test_initialization(session_manager: SessionManager):
    """Test if SessionManager initializes correctly with default values"""
    assert isinstance(session_manager._master_session, MasterSession)
    assert isinstance(session_manager._system_session, SystemSession)
    assert session_manager.software_sessions == {}
    assert session_manager.devices == {}
    assert session_manager.mapped_sessions == {"master": False, "system": False}


def test_get_software_session(session_manager: SessionManager):
    """Test getting a software session"""
    # Setup mock data
    mock_sessions = [
        MockAudioSession("chrome.exe"),
        MockAudioSession("spotify.exe"),
    ]
    
    # Mock the AudioUtilities methods to return our mock data
    with patch('sessions.session_manager.AudioUtilities.GetAllSessions', return_value=mock_sessions):
        session_manager.all_pycaw_sessions = mock_sessions
        session_manager.reload_sessions_and_devices()
        
        # Test successful retrieval
        session = session_manager.get_software_session("chrome.exe")
        assert isinstance(session, SoftwareSession)
        assert session.name == "chrome.exe"
        
        # Test non-existent session
        with pytest.raises(ValueError, match="Software session nonexistent.exe not found."):
            session_manager.get_software_session("nonexistent.exe")

def test_apply_volumes(session_manager: SessionManager):
    """Test applying volumes to mapped sessions"""
    # Setup mock data
    mock_sessions = [MockAudioSession("chrome.exe")]
    
    # Mock the AudioUtilities methods to return our mock data
    with patch('sessions.session_manager.AudioUtilities.GetAllSessions', return_value=mock_sessions):
        session_manager.all_pycaw_sessions = mock_sessions
        session_manager.reload_sessions_and_devices()
        
        # Create test mapping
        mapping = {0: session_manager.get_software_session("chrome.exe")}
        values = [0.75]
        
        # Test normal volume application
        session_manager.apply_volumes(values, mapping, inverted=False)
        session_manager.software_sessions["chrome.exe"].session.SimpleAudioVolume.SetMasterVolume.assert_called_once_with(0.75, None)
        
        # Test inverted volume application
        session_manager.software_sessions["chrome.exe"].session.SimpleAudioVolume.SetMasterVolume.reset_mock()
        session_manager.apply_volumes(values, mapping, inverted=True)
        session_manager.software_sessions["chrome.exe"].session.SimpleAudioVolume.SetMasterVolume.assert_called_once_with(0.25, None)
