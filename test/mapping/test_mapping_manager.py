import pytest
from unittest.mock import Mock, patch
from mapping.mapping_manager import MappingManager
from sessions.sessions import (
    Session,
    Device,
    SoftwareSession,
    MasterSession,
    SystemSession,
    SessionGroup,
)
from sessions.session_protocol import SessionManagerProtocol
from config.config_protocol import ConfigManagerProtocol


class MockSessionManager(SessionManagerProtocol):
    def __init__(self):
        self._master_session = Mock(spec=MasterSession)
        self._master_session.name = "master"
        self._master_session.is_mapped = False
        self._master_session.mark_as_mapped = Mock(
            side_effect=lambda x: setattr(self._master_session, "is_mapped", x)
        )

        self._system_session = Mock(spec=SystemSession)
        self._system_session.name = "system"
        self._system_session.unique_name = "system"
        self._system_session.is_mapped = False
        self._system_session.mark_as_mapped = Mock(
            side_effect=lambda x: setattr(self._system_session, "is_mapped", x)
        )

        self.software_sessions = []

    @property
    def master_session(self) -> MasterSession:
        return self._master_session

    @property
    def system_session(self) -> SystemSession:
        return self._system_session

    def get_device_session(self, device_name: str) -> Device:
        mock_device = Mock(spec=Device)
        mock_device.name = device_name
        return mock_device

    def get_software_session(self, session_name: str) -> SoftwareSession:
        for session in self.software_sessions:
            if session_name.lower() in session.name.lower():
                return session
        raise ValueError(f"Software session {session_name} not found.")


class MockConfigManager(ConfigManagerProtocol):
    def __init__(self):
        self.config_data = {
            "device": {"sliders": 4},
            "mappings": {
                "0": ["master"],
                "1": ["system"],
                "2": ["device:speakers"],
                "3": ["chrome.exe", "unmapped"],
            },
            "settings": {"system_in_unmapped": True},
        }

    def load_config(self):
        pass

    def get_setting(self, setting_path: str):
        if setting_path == "device.sliders":
            return self.config_data["device"]["sliders"]
        elif setting_path == "mappings":
            return self.config_data["mappings"]
        elif setting_path == "settings.system_in_unmapped":
            return self.config_data["settings"]["system_in_unmapped"]
        return None


@pytest.fixture
def session_manager():
    manager = MockSessionManager()
    # Add some mock software sessions
    mock_session1 = Mock(spec=SoftwareSession)
    mock_session1.name = "chrome.exe"
    mock_session1.unique_name = "chrome.exe (1234)"
    mock_session1.is_mapped = False
    mock_session1.mark_as_mapped = Mock(
        side_effect=lambda x: setattr(mock_session1, "is_mapped", x)
    )

    mock_session2 = Mock(spec=SoftwareSession)
    mock_session2.name = "spotify.exe"
    mock_session2.unique_name = "spotify.exe (5678)"
    mock_session2.is_mapped = False
    mock_session2.mark_as_mapped = Mock(
        side_effect=lambda x: setattr(mock_session2, "is_mapped", x)
    )

    manager.software_sessions = [mock_session1, mock_session2]
    return manager


@pytest.fixture
def config_manager():
    return MockConfigManager()


@pytest.fixture
def mapping_manager():
    return MappingManager()


def test_get_mapping(mapping_manager, session_manager, config_manager):
    """Test the main get_mapping function"""
    result = mapping_manager.get_mapping(session_manager, config_manager)

    assert isinstance(result, dict)
    assert len(result) == 4  # 4 sliders from config
    assert all(isinstance(key, int) for key in result.keys())
    assert all(isinstance(value, SessionGroup) for value in result.values())


def test_create_mappings(mapping_manager, session_manager, config_manager):
    """Test creating mappings with different target types"""
    result = mapping_manager.create_mappings(session_manager, config_manager)

    # Test master mapping
    assert session_manager.master_session in result[0].sessions
    assert session_manager.master_session.is_mapped is True

    # Test system mapping
    assert session_manager.system_session in result[1].sessions
    assert session_manager.system_session.is_mapped is True

    # Test device mapping
    assert any(isinstance(session, Device) for session in result[2].sessions)

    # Test software session mapping
    assert any(session.name == "chrome.exe" for session in result[3].sessions)


def test_add_single_target_mapping(mapping_manager, session_manager):
    """Test adding individual target mappings"""
    session_dict = {0: []}

    # Test master target
    mapping_manager._add_single_target_mapping(
        "master", 0, session_dict, session_manager
    )
    assert session_manager.master_session in session_dict[0]
    assert session_manager.master_session.is_mapped is True

    # Test system target
    session_dict = {0: []}
    mapping_manager._add_single_target_mapping(
        "system", 0, session_dict, session_manager
    )
    assert session_manager.system_session in session_dict[0]
    assert session_manager.system_session.is_mapped is True

    # Test device target
    session_dict = {0: []}
    mapping_manager._add_single_target_mapping(
        "device:speakers", 0, session_dict, session_manager
    )
    assert any(isinstance(session, Device) for session in session_dict[0])

    # Test software session target
    session_dict = {0: []}
    mapping_manager._add_single_target_mapping(
        "chrome.exe", 0, session_dict, session_manager
    )
    assert any(session.name == "chrome.exe" for session in session_dict[0])


def test_add_unmapped_sessions(mapping_manager, session_manager, config_manager):
    """Test handling of unmapped sessions"""
    session_dict = {0: []}

    # First mark some sessions as mapped
    session_manager.get_software_session("chrome.exe").mark_as_mapped(True)
    # Add unmapped sessions
    mapping_manager._add_unmapped_sessions(
        0, session_dict, session_manager, config_manager
    )

    # Verify spotify.exe is added (since it's unmapped)
    assert any(session.name == "spotify.exe" for session in session_dict[0])

    # Verify system session is added when system_in_unmapped is True
    assert session_manager.system_session in session_dict[0]


def test_add_unmapped_sessions_without_system(
    mapping_manager, session_manager, config_manager
):
    """Test unmapped sessions when system_in_unmapped is False"""
    # Set system_in_unmapped to False
    config_manager.config_data["settings"]["system_in_unmapped"] = False
    session_dict = {0: []}

    # Add unmapped sessions
    mapping_manager._add_unmapped_sessions(
        0, session_dict, session_manager, config_manager
    )

    # Verify system session is not added
    assert session_manager.system_session not in session_dict[0]


def test_mapping_with_no_sessions(mapping_manager, session_manager, config_manager):
    """Test mapping when there are no software sessions"""
    session_manager.software_sessions = []
    result = mapping_manager.create_mappings(session_manager, config_manager)

    # Verify basic structure is maintained
    assert isinstance(result, dict)
    assert len(result) == 4
    # Verify master and system mappings still work
    assert session_manager.master_session in result[0].sessions
    assert session_manager.system_session in result[1].sessions
