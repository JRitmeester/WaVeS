import pytest
from unittest.mock import Mock, patch
from sessions.session_manager import SessionManager
from sessions.sessions import (
    MasterSession,
    SystemSession,
    Device,
    SoftwareSession,
)
from pycaw.pycaw import AudioDevice
from pycaw.constants import AudioDeviceState


class MockAudioSession:
    def __init__(self, name: str, display_name: str = None, pid: int = 1234):
        self.Process = Mock()
        self.Process.name.return_value = name
        self.Process.pid = pid
        self.DisplayName = display_name or name
        self.SimpleAudioVolume = Mock()
        self.SimpleAudioVolume.GetMasterVolume.return_value = 0.5
        self.SimpleAudioVolume.SetMasterVolume = Mock()
        self.id = f"session_{name}_{pid}"


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
        # Don't call parent's __init__ to avoid COM interface calls
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
        # Don't call parent's __init__ to avoid COM interface calls
        self.session = MockAudioSession(
            "System Sounds", "SystemRoot\\System32\\SystemSounds"
        )
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

    # Create a mock system sounds session
    mock_system_session = MockAudioSession(
        "System Sounds", "SystemRoot\\System32\\SystemSounds"
    )
    mock_audio_utilities.GetAllSessions.return_value = [mock_system_session]
    mock_audio_utilities.GetAllDevices.return_value = []

    # Create a simple mock for the speakers device
    mock_speakers = Mock()
    mock_speakers.FriendlyName = "Speakers"
    mock_speakers.state = AudioDeviceState.Active
    mock_speakers.id = "test_device_speakers"
    mock_speakers.properties = {}
    mock_speakers._dev = Mock()
    mock_speakers.volume = Mock()
    mock_speakers.volume.GetMasterVolumeLevelScalar.return_value = 0.5
    mock_speakers.volume.SetMasterVolumeLevelScalar = Mock()
    mock_audio_utilities.GetSpeakers.return_value = mock_speakers

    # Mock COM interface calls with a simple mock
    mock_device_enumerator = Mock()
    mock_device_enumerator.GetDevice.return_value = Mock()
    mock_device_enumerator.GetDefaultAudioEndpoint.return_value = Mock()

    # Mock the cast function to return a mock volume interface
    mock_volume_interface = Mock()
    mock_volume_interface.GetMasterVolumeLevelScalar.return_value = 0.5
    mock_volume_interface.SetMasterVolumeLevelScalar = Mock()
    mock_cast = Mock(return_value=mock_volume_interface)

    # Create patches for all the necessary components
    patches = [
        patch("sessions.session_manager.AudioUtilities", mock_audio_utilities),
        patch("sessions.sessions.MasterSession", MockMasterSession),
        patch("sessions.sessions.SystemSession", MockSystemSession),
        patch("sessions.sessions.Device", MockDevice),
        patch(
            "sessions.sessions.comtypes.CoCreateInstance",
            return_value=mock_device_enumerator,
        ),
        patch("sessions.sessions.AudioUtilities", mock_audio_utilities),
        patch("sessions.sessions.cast", mock_cast),
    ]

    # Apply all patches
    for p in patches:
        p.start()

    # Create the session manager
    manager = SessionManager()

    # Clean up patches after the test
    yield manager

    for p in patches:
        p.stop()


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
        MockAudioSession("chrome.exe", pid=1234),
        MockAudioSession("spotify.exe", pid=5678),
    ]

    # Mock the AudioUtilities methods to return our mock data
    with patch(
        "sessions.session_manager.AudioUtilities.GetAllSessions",
        return_value=mock_sessions,
    ):
        session_manager.all_pycaw_sessions = mock_sessions
        session_manager.reload_sessions_and_devices()

        # Test successful retrieval
        session = session_manager.get_software_session("chrome.exe")
        assert isinstance(session, SoftwareSession)
        assert session.name == "chrome.exe (1234)"

        # Test non-existent session
        with pytest.raises(
            ValueError, match="Software session nonexistent.exe not found."
        ):
            session_manager.get_software_session("nonexistent.exe")


def test_apply_volumes(session_manager: SessionManager):
    """Test applying volumes to mapped sessions"""
    # Setup mock data
    mock_sessions = [MockAudioSession("chrome.exe")]

    # Mock the AudioUtilities methods to return our mock data
    with patch(
        "sessions.session_manager.AudioUtilities.GetAllSessions",
        return_value=mock_sessions,
    ):
        session_manager.all_pycaw_sessions = mock_sessions
        session_manager.reload_sessions_and_devices()

        # Create test mapping
        mapping = {0: session_manager.get_software_session("chrome.exe")}
        values = [0.75]

        # Test normal volume application
        session_manager.apply_volumes(values, mapping, inverted=False)
        session_manager.software_sessions[
            "chrome.exe"
        ].session.SimpleAudioVolume.SetMasterVolume.assert_called_once_with(0.75, None)

        # Test inverted volume application
        session_manager.software_sessions[
            "chrome.exe"
        ].session.SimpleAudioVolume.SetMasterVolume.reset_mock()
        session_manager.apply_volumes(values, mapping, inverted=True)
        session_manager.software_sessions[
            "chrome.exe"
        ].session.SimpleAudioVolume.SetMasterVolume.assert_called_once_with(0.25, None)


def test_session_addition(session_manager: SessionManager):
    """Test that the session manager correctly detects and handles new sessions"""
    # Initial setup with one session
    initial_sessions = [MockAudioSession("chrome.exe", pid=1234)]
    session_manager.all_pycaw_sessions = initial_sessions
    session_manager.reload_sessions_and_devices()

    # Verify initial state
    assert len(session_manager.software_sessions) == 1
    assert "chrome.exe" in session_manager.software_sessions
    assert "spotify.exe" not in session_manager.software_sessions

    # Mock AudioUtilities to simulate a new session being added
    new_sessions = [
        MockAudioSession("chrome.exe", pid=1234),
        MockAudioSession("spotify.exe", pid=5678),
    ]

    with patch(
        "sessions.session_manager.AudioUtilities.GetAllSessions",
        return_value=new_sessions,
    ):
        # Check for changes - this should detect the new session
        assert session_manager.check_for_changes() is True

        # Reload sessions and verify the new session is added
        session_manager.reload_sessions_and_devices()
        assert len(session_manager.software_sessions) == 2
        assert "chrome.exe" in session_manager.software_sessions
        assert "spotify.exe" in session_manager.software_sessions

        # Verify the new session is properly initialized
        spotify_session = session_manager.software_sessions["spotify.exe"]
        assert isinstance(spotify_session, SoftwareSession)
        assert spotify_session.name == "spotify.exe (5678)"
        assert spotify_session.session.Process.name() == "spotify.exe"

        # Verify the existing session remains unchanged
        chrome_session = session_manager.software_sessions["chrome.exe"]
        assert isinstance(chrome_session, SoftwareSession)
        assert chrome_session.name == "chrome.exe (1234)"
        assert chrome_session.session.Process.name() == "chrome.exe"

        # Verify mapped_sessions is updated
        assert "spotify.exe" in session_manager.mapped_sessions
        assert session_manager.mapped_sessions["spotify.exe"] is False


def test_no_changes_detected(session_manager: SessionManager):
    """Test that no changes are detected when sessions remain the same"""
    # Initial setup
    initial_sessions = [MockAudioSession("chrome.exe")]
    session_manager.all_pycaw_sessions = initial_sessions
    session_manager.reload_sessions_and_devices()

    # Mock AudioUtilities to return the same sessions
    with patch(
        "sessions.session_manager.AudioUtilities.GetAllSessions",
        return_value=initial_sessions,
    ):
        # Check for changes - this should not detect any changes
        assert session_manager.check_for_changes() is False

        # Verify sessions remain unchanged
        assert len(session_manager.software_sessions) == 1
        assert "chrome.exe" in session_manager.software_sessions


def test_multiple_sessions_same_name(session_manager: SessionManager):
    """Test that multiple sessions with the same process name but different PIDs are handled correctly"""
    # Setup mock data with two Discord sessions
    mock_sessions = [
        MockAudioSession("discord.exe", pid=1234),
        MockAudioSession("discord.exe", pid=5678),
    ]

    # Mock the AudioUtilities methods to return our mock data
    with patch(
        "sessions.session_manager.AudioUtilities.GetAllSessions",
        return_value=mock_sessions,
    ):
        session_manager.all_pycaw_sessions = mock_sessions
        session_manager.reload_sessions_and_devices()

        # Verify only one entry exists in software_sessions for discord.exe
        assert len(session_manager.software_sessions) == 1
        assert "discord.exe" in session_manager.software_sessions

        # Get the session and verify it's a SoftwareSession
        session = session_manager.get_software_session("discord.exe")
        assert isinstance(session, SoftwareSession)
        assert (
            session.name == "discord.exe (1234)"
        )  # First session's name should be used

        # Test volume application affects all sessions with the same name
        mapping = {0: session}
        values = [0.75]

        session_manager.apply_volumes(values, mapping, inverted=False)

        # Verify volume was set for both sessions
        for mock_session in mock_sessions:
            mock_session.SimpleAudioVolume.SetMasterVolume.assert_called_with(
                0.75, None
            )

        # Verify that both sessions are part of the same group
        assert len(session_manager.software_sessions["discord.exe"].sessions) == 2
        session_names = [
            s.name for s in session_manager.software_sessions["discord.exe"].sessions
        ]
        assert "discord.exe (1234)" in session_names
        assert "discord.exe (5678)" in session_names
