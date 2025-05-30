import pytest
from unittest.mock import patch
import yaml
from config.config_manager import ConfigManager
from pathlib import Path
from config.config_exceptions import ConfigValidationError, ConfigFileEmptyError



@pytest.fixture
def default_mapping_path(tmp_path):
    # Create a default mapping file with test content
    mapping_path = tmp_path / "default_mapping.yml"
    default_content = {
        "mappings": {"0": "master"},
        "device": {"name": "Test Device"},
        "settings": {"inverted": False},
    }
    mapping_path.write_text(yaml.dump(default_content))
    return mapping_path


@pytest.fixture
def config_manager(tmp_path, default_mapping_path) -> ConfigManager:
    return ConfigManager(
        config_path=tmp_path, default_mapping_path=default_mapping_path
    )


def test_ensure_config_exists__already_exists(config_manager: ConfigManager):
    # Create the config file with some content
    existing_content = {
        "mappings": {"0": "master"},
        "device": {"name": "Existing Device"},
    }
    config_manager.config_file_path.parent.mkdir(parents=True, exist_ok=True)
    config_manager.config_file_path.write_text(yaml.dump(existing_content))

    # Call ensure_config_exists
    config_manager.ensure_config_exists()

    # Verify the file still exists and content is unchanged
    assert config_manager.config_file_path.exists()
    assert (
        yaml.safe_load(config_manager.config_file_path.read_text()) == existing_content
    )


def test_ensure_config_exists__does_not_exist(config_manager: ConfigManager):
    # Ensure the config file doesn't exist
    if config_manager.config_file_path.exists():
        config_manager.config_file_path.unlink()

    # Call ensure_config_exists
    config_manager.ensure_config_exists()

    # Verify the file was created with default content
    assert config_manager.config_file_path.exists()
    assert yaml.safe_load(
        config_manager.config_file_path.read_text()
    ) == yaml.safe_load(config_manager.default_mapping_path.read_text())


def test_load_config__successful_load(config_manager: ConfigManager):
    # Arrange: Set up a config file with known content
    test_content = {
        "mappings": {0:  ["master"], 1: ["system"]},
        "device": {"name": "Test Device", "port": "COM1", "baudrate": 9600, "sliders": 2},
        "settings": {"inverted": False, "system_in_unmapped": True, "session_reload_interval": 10},
    }
    config_manager.config_file_path.parent.mkdir(parents=True, exist_ok=True)
    config_manager.config_file_path.write_text(yaml.dump(test_content))

    # Act
    config_manager.load_config()

    # Assert: Verify internal state was set correctly
    assert config_manager.config_data == test_content


def test_load_config__file_not_found(config_manager: ConfigManager):
    # Arrange: Ensure the config file doesn't exist
    if config_manager.config_file_path.exists():
        config_manager.config_file_path.unlink()

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        config_manager.load_config()


def test_load_config__empty_file(config_manager: ConfigManager):
    # Arrange: Create an empty config file
    config_manager.config_file_path.parent.mkdir(parents=True, exist_ok=True)
    config_manager.config_file_path.write_text("")

    # Act & Assert
    with pytest.raises(ConfigFileEmptyError):
        config_manager.load_config()


def test_get_setting__successful_retrieval(config_manager: ConfigManager):
    # Arrange: Set up internal state directly
    config_manager.config_data = {
        "mappings": {"0": "master"},
        "device": {"name": "Test Device", "baudrate": 9600},
        "settings": {"inverted": False},
    }

    # Act & Assert
    assert config_manager.get_setting("device.name") == "Test Device"
    assert config_manager.get_setting("mappings").get("0") == "master"
    assert config_manager.get_setting("settings.inverted") == False


def test_get_setting__nested_setting_not_found(config_manager: ConfigManager):
    # Arrange: Set up internal state
    config_manager.config_data = {"device": {"name": "Test Device"}}

    # Act & Assert
    with pytest.raises(
        ValueError,
        match="Setting device.nonexistent is not found in the configuration file.",
    ):
        config_manager.get_setting("device.nonexistent")


def test_get_setting__invalid_path(config_manager: ConfigManager):
    # Arrange: Set up internal state
    config_manager.config_data = {"device": "not_a_dict"}

    # Act & Assert
    with pytest.raises(
        ValueError,
        match="Cannot access name in device.name as parent is not a dictionary",
    ):
        config_manager.get_setting("device.name")


def test_get_setting__empty_value(config_manager: ConfigManager):
    # Arrange: Set up internal state with an empty setting
    config_manager.config_data = {"device": {"name": None}}

    # Act & Assert
    with pytest.raises(ValueError, match="Setting device.name is present but empty."):
        config_manager.get_setting("device.name")


def test_get_serial_port__device_name_found(config_manager: ConfigManager):
    """Test when the device name is found in the available ports."""
    # Setup config with device name
    config_manager.config_data = {"device": {"name": "Test Device"}}

    # Mock the list_ports.comports() to return controlled test data
    mock_ports = [
        ("COM1", "Other Device", "hwid1"),
        ("COM2", "Test Device", "hwid2"),
        ("COM3", "Another Device", "hwid3"),
    ]

    with patch("serial.tools.list_ports.comports", return_value=mock_ports):
        assert config_manager.get_serial_port() == "COM2"


def test_get_serial_port__device_not_found_fallback_to_port(
    config_manager: ConfigManager,
):
    """Test when device name isn't found but port setting exists as fallback."""
    # Setup config with device name and port
    config_manager.config_data = {
        "device": {"name": "Nonexistent Device", "port": "COM4"}
    }

    # Mock empty ports list
    with patch("serial.tools.list_ports.comports", return_value=[]):
        assert config_manager.get_serial_port() == "COM4"


def test_get_serial_port__no_device_no_port(config_manager: ConfigManager):
    """Test when neither device is found nor port setting exists."""
    # Setup config with only device name
    config_manager.config_data = {"device": {"name": "Nonexistent Device"}}

    # Mock empty ports list
    with patch("serial.tools.list_ports.comports", return_value=[]):
        with pytest.raises(
            ValueError,
            match="The config file does not contain the right device name or an appropriate port.",
        ):
            config_manager.get_serial_port()


def test_get_serial_port__multiple_matching_devices(config_manager: ConfigManager):
    """Test when multiple devices match the device name - should return first match."""
    # Setup config with device name
    config_manager.config_data = {"device": {"name": "Test Device"}}

    # Mock multiple matching devices
    mock_ports = [
        ("COM1", "Other Device", "hwid1"),
        ("COM2", "Test Device First", "hwid2"),
        ("COM3", "Test Device Second", "hwid3"),
    ]

    with patch("serial.tools.list_ports.comports", return_value=mock_ports):
        assert config_manager.get_serial_port() == "COM2"


def test_get_serial_port__no_device_name_in_config(config_manager: ConfigManager):
    """Test when device name setting is missing but port is available."""
    # Setup config with only port
    config_manager.config_data = {"device": {"port": "COM5"}}

    with patch(
        "serial.tools.list_ports.comports",
        return_value=[("COM1", "Some Device", "hwid1")],
    ):
        with pytest.raises(
            ValueError,
            match="Setting device.name is not found in the configuration file.",
        ):
            config_manager.get_serial_port()


def test_get_serial_port__empty_ports_list(config_manager: ConfigManager):
    """Test when no serial ports are available but port setting exists."""
    # Setup config with device name and port
    config_manager.config_data = {"device": {"name": "Test Device", "port": "COM6"}}

    # Mock empty ports list
    with patch("serial.tools.list_ports.comports", return_value=[]):
        assert config_manager.get_serial_port() == "COM6"


def test_get_default_config_path():
    """Test that the default config path is correctly constructed."""
    expected_path = Path.home() / "AppData/Roaming"
    assert ConfigManager.get_default_config_path() == expected_path


def test_load_config__invalid_schema(config_manager: ConfigManager):
    """Test loading config with invalid schema raises ConfigValidationError."""
    # Create invalid config (missing required fields)
    invalid_content = {
        "mappings": {"0": ["master"]},
        "device": {"name": "Test Device"},  # Missing required fields
        "settings": {"inverted": False}  # Missing required fields
    }
    config_manager.config_file_path.parent.mkdir(parents=True, exist_ok=True)
    config_manager.config_file_path.write_text(yaml.dump(invalid_content))

    # Act & Assert
    with pytest.raises(ConfigValidationError):
        config_manager.load_config()


def test_get_setting__invalid_path_format(config_manager: ConfigManager):
    """Test that invalid path formats raise appropriate errors."""
    config_manager.config_data = {"device": {"name": "Test Device"}}
    
    # Test empty path
    with pytest.raises(ValueError):
        config_manager.get_setting("")
    
    # Test path with leading/trailing dots
    with pytest.raises(ValueError):
        config_manager.get_setting(".device.name")
    with pytest.raises(ValueError):
        config_manager.get_setting("device.name.")


def test_get_setting__non_string_path(config_manager: ConfigManager):
    """Test that non-string paths raise TypeError."""
    config_manager.config_data = {"device": {"name": "Test Device"}}
    
    with pytest.raises(AttributeError):
        config_manager.get_setting(None)
    with pytest.raises(AttributeError):
        config_manager.get_setting(123)


def test_get_serial_port__invalid_port_format(config_manager: ConfigManager):
    """Test that invalid port formats are handled appropriately."""
    # Setup config with invalid port format
    config_manager.config_data = {
        "device": {
            "name": "Nonexistent Device",
            "port": "INVALID_PORT"
        }
    }

    # Mock empty ports list
    with patch("serial.tools.list_ports.comports", return_value=[]):
        # Should still return the port even if it's invalid format
        assert config_manager.get_serial_port() == "INVALID_PORT"


def test_get_serial_port__multiple_ports_same_device(config_manager: ConfigManager):
    """Test behavior when multiple ports have the same device name."""
    # Setup config with device name
    config_manager.config_data = {"device": {"name": "Test Device"}}

    # Mock multiple ports with same device name
    mock_ports = [
        ("COM1", "Test Device", "hwid1"),
        ("COM2", "Test Device", "hwid2"),
        ("COM3", "Other Device", "hwid3"),
    ]

    with patch("serial.tools.list_ports.comports", return_value=mock_ports):
        # Should return the first matching port
        assert config_manager.get_serial_port() == "COM1"


def test_ensure_config_exists__permission_error(config_manager: ConfigManager):
    """Test handling of permission errors when creating config."""
    # Mock Path.mkdir to raise PermissionError
    with patch.object(Path, 'mkdir', side_effect=PermissionError("Access denied")):
        with pytest.raises(PermissionError):
            config_manager.ensure_config_exists()
