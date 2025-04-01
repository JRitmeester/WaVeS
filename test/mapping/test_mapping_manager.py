import pytest
from unittest.mock import Mock
from mapping.mapping_manager import MappingManager
from sessions.sessions import (
    SessionGroup,
    SoftwareSession,
    MasterSession,
    SystemSession,
    Device,
)
from sessions.session_protocol import SessionManagerProtocol
from config.config_protocol import ConfigManagerProtocol
from mapping.mapping_protocol import MappingManagerProtocol


class MockSessionManager(SessionManagerProtocol):
    def __init__(self):
        # Create mock sessions with proper types
        self._master_session = MasterSession()
        self._system_session = SystemSession()

        # Create mock sessions with proper names
        chrome_mock = Mock()
        chrome_mock.Process.name.return_value = "chrome.exe"
        brave_mock = Mock()
        brave_mock.Process.name.return_value = "brave.exe"
        spotify_mock = Mock()
        spotify_mock.Process.name.return_value = "spotify.exe"

        self.software_sessions = {
            "chrome.exe": SoftwareSession(chrome_mock),
            "brave.exe": SoftwareSession(brave_mock),
            "spotify.exe": SoftwareSession(spotify_mock),
        }
        self.mapped_sessions = {
            "master": False,
            "system": False,
            "chrome.exe": False,
            "brave.exe": False,
            "spotify.exe": False,
        }

    @property
    def master_session(self) -> MasterSession:
        return self._master_session

    @property
    def system_session(self) -> SystemSession:
        return self._system_session

    def get_device_session(self, device_name: str) -> Device:
        # Create a mock device with all required attributes and methods
        mock_device = Mock(spec=Device)
        mock_device.name = device_name
        mock_device.set_volume = Mock()
        mock_device.get_volume = Mock(return_value=0.5)
        return mock_device


class MockConfigManager(ConfigManagerProtocol):
    def __init__(self):
        self.config = {
            "device.sliders": 5,
            "mappings": [
                "master",
                "system",
                "chrome.exe,brave.exe",
                "unmapped",
                "spotify.exe",
            ],
            "settings.system_in_unmapped": True,
        }

    def load_config(self):
        pass

    def get_setting(self, key: str):
        return self.config.get(key)


@pytest.fixture
def mapping_manager():
    return MappingManager()


@pytest.fixture
def session_manager():
    return MockSessionManager()


@pytest.fixture
def config_manager():
    return MockConfigManager()


def test_get_mapping(
    mapping_manager: MappingManagerProtocol,
    session_manager: SessionManagerProtocol,
    config_manager: ConfigManagerProtocol,
):
    result = mapping_manager.get_mapping(session_manager, config_manager)

    assert isinstance(result, dict)
    assert len(result) == 5  # Number of sliders
    assert result[0] == session_manager.master_session
    assert result[1] == session_manager.system_session
    assert isinstance(result[2], SessionGroup)
    assert len(result[2].sessions) == 2
    assert result[2].sessions[0] == session_manager.software_sessions["chrome.exe"]
    assert result[2].sessions[1] == session_manager.software_sessions["brave.exe"]
    assert isinstance(result[3], SessionGroup)
    assert len(result[3].sessions) == 1  # Only spotify should be unmapped
    assert result[4] == session_manager.software_sessions["spotify.exe"]


def test_get_target_indices(
    mapping_manager: MappingManagerProtocol, config_manager: ConfigManagerProtocol
):
    result = mapping_manager.get_target_indices(config_manager)

    assert isinstance(result, dict)
    assert result["master"] == 0
    assert result["system"] == 1
    assert isinstance(result[("chrome.exe", "brave.exe")], int)
    assert result[("chrome.exe", "brave.exe")] == 2
    assert result["unmapped"] == 3
    assert result["spotify.exe"] == 4


def test_add_single_target_mapping(
    mapping_manager: MappingManagerProtocol, session_manager: SessionManagerProtocol
):
    session_dict = {}

    # Test master mapping
    mapping_manager._add_single_target_mapping(
        "master", 0, session_dict, session_manager
    )
    assert session_dict[0] == session_manager.master_session

    # Test system mapping
    mapping_manager._add_single_target_mapping(
        "system", 1, session_dict, session_manager
    )
    assert session_dict[1] == session_manager.system_session

    # Test device mapping
    mapping_manager._add_single_target_mapping(
        "device:mic", 2, session_dict, session_manager
    )
    assert session_dict[2].name == "mic"

    # Test software session mapping
    mapping_manager._add_single_target_mapping(
        "chrome.exe", 3, session_dict, session_manager
    )
    assert session_dict[3] == session_manager.software_sessions["chrome.exe"]


def test_add_software_session(
    mapping_manager: MappingManagerProtocol, session_manager: SessionManagerProtocol
):
    session_dict = {}

    # Test existing software session
    mapping_manager._add_software_session(
        "chrome.exe", 0, session_dict, session_manager
    )
    assert session_dict[0] == session_manager.software_sessions["chrome.exe"]
    assert session_manager.mapped_sessions["chrome.exe"] is True

    # Test non-existing software session
    mapping_manager._add_software_session(
        "nonexistent", 1, session_dict, session_manager
    )
    assert 1 not in session_dict


def test_add_group_mapping(
    mapping_manager: MappingManagerProtocol, session_manager: SessionManagerProtocol
):
    session_dict = {}
    target_group = ("chrome.exe", "brave.exe")

    mapping_manager._add_group_mapping(target_group, 0, session_dict, session_manager)

    assert isinstance(session_dict[0], SessionGroup)
    assert len(session_dict[0].sessions) == 2
    assert (
        session_dict[0].sessions[0] == session_manager.software_sessions["chrome.exe"]
    )
    assert session_dict[0].sessions[1] == session_manager.software_sessions["brave.exe"]
    assert session_manager.mapped_sessions["chrome.exe"] is True
    assert session_manager.mapped_sessions["brave.exe"] is True


def test_add_unmapped_sessions(
    mapping_manager: MappingManagerProtocol,
    session_manager: SessionManagerProtocol,
    config_manager: ConfigManagerProtocol,
):
    session_dict = {}

    # First map some sessions
    mapping_manager._add_single_target_mapping(
        "chrome.exe", 0, session_dict, session_manager
    )
    mapping_manager._add_single_target_mapping(
        "brave.exe", 1, session_dict, session_manager
    )

    # Add unmapped sessions
    mapping_manager._add_unmapped_sessions(
        2, session_dict, session_manager, config_manager
    )

    assert isinstance(session_dict[2], SessionGroup)
    assert len(session_dict[2].sessions) == 2  # spotify and system
    assert (
        session_dict[2].sessions[0] == session_manager.software_sessions["spotify.exe"]
    )
    assert session_dict[2].sessions[1] == session_manager.system_session
    assert session_manager.mapped_sessions["spotify.exe"] is True
    assert session_manager.mapped_sessions["system"] is True
