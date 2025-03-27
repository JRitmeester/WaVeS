import pytest
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from config.config_manager import ConfigManager

@pytest.fixture
def default_mapping_path(tmp_path):
    # Create a default mapping file with test content
    mapping_path = tmp_path / "default_mapping.txt"
    mapping_path.write_text("test: value\n")
    return mapping_path

@pytest.fixture
def config_manager(tmp_path, default_mapping_path) -> ConfigManager:
    return ConfigManager(config_path=tmp_path, default_mapping_path=default_mapping_path)

def test_ensure_config_exists__already_exists(config_manager: ConfigManager):
    # Create the config file with some content
    config_manager.config_file_path.touch()
    config_manager.config_file_path.write_text("existing: content\n")
    
    # Call ensure_config_exists
    config_manager.ensure_config_exists()
    
    # Verify the file still exists and content is unchanged
    assert config_manager.config_file_path.exists()
    assert config_manager.config_file_path.read_text() == "existing: content\n"

def test_ensure_config_exists__does_not_exist(config_manager: ConfigManager):
    # Ensure the config file doesn't exist
    if config_manager.config_file_path.exists():
        config_manager.config_file_path.unlink()
    
    # Call ensure_config_exists
    config_manager.ensure_config_exists()
    
    # Verify the file was created with default content
    assert config_manager.config_file_path.exists()
    assert config_manager.config_file_path.read_text() == "test: value\n"

def test_load_config__successful_load(config_manager: ConfigManager):
    # Arrange: Set up a config file with known content
    config_manager.config_file_path.parent.mkdir(parents=True, exist_ok=True)
    config_manager.config_file_path.write_text("test: value\nother: setting\n")
    
    # Act
    config_manager.load_config()
    
    # Assert: Verify internal state was set correctly
    assert config_manager.lines == ["test: value", "other: setting"]

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
    
    # Act
    config_manager.load_config()
    
    # Assert: Should have a single empty string in lines
    assert config_manager.lines == [""]

def test_get_setting__successful_retrieval(config_manager: ConfigManager):
    # Arrange: Set up internal state directly
    config_manager.lines = ["test: value", "other: setting"]
    
    # Act
    result = config_manager.get_setting("test")
    
    # Assert
    assert result == "value"

def test_get_setting__setting_not_found(config_manager: ConfigManager):
    # Arrange: Set up internal state
    config_manager.lines = ["test: value", "other: setting"]
    
    # Act & Assert
    with pytest.raises(ValueError, match="Setting nonexistent is not found in the configuration file."):
        config_manager.get_setting("nonexistent")


def test_get_setting__multiple_colons(config_manager: ConfigManager):
    # Arrange: Set up internal state with a value containing colons
    config_manager.lines = ["test: value:with:colons", "other: setting"]
    
    # Act
    result = config_manager.get_setting("test")
    
    # Assert
    assert result == "value:with:colons"

def test_get_setting__whitespace_handling(config_manager: ConfigManager):
    # Arrange: Set up internal state with various whitespace patterns
    config_manager.lines = [
        "test:value",          # no space after colon
        "spaces:   value  ",   # multiple spaces
        "tabs:\tvalue\t",      # tabs
    ]
    
    # Act
    result1 = config_manager.get_setting("test")
    result2 = config_manager.get_setting("spaces")
    result3 = config_manager.get_setting("tabs")
    
    # Assert
    assert result1 == "value"
    assert result2 == "value"  # trailing spaces preserved
    assert result3 == "value"  # trailing tab preserved

def test_get_setting__empty_setting(config_manager: ConfigManager):
    # Arrange: Set up internal state with an empty setting
    config_manager.lines = ["empty:  ", "other: setting"]
    
    # Act & Assert
    with pytest.raises(ValueError, match="Setting empty is present but empty."):
        config_manager.get_setting("empty")

def test_get_serial_port__device_name_found(config_manager: ConfigManager):
    """
    Test when the device name is found in the available ports.
    """
    # Setup config with device name
    config_manager.config_file_path.write_text("device name: Test Device\n")
    config_manager.load_config()
    
    # Mock the list_ports.comports() to return controlled test data
    mock_ports = [
        ("COM1", "Other Device", "hwid1"),
        ("COM2", "Test Device", "hwid2"),
        ("COM3", "Another Device", "hwid3")
    ]
    
    with patch('serial.tools.list_ports.comports', return_value=mock_ports):
        assert config_manager.get_serial_port() == "COM2"

def test_get_serial_port__device_not_found_fallback_to_port(config_manager: ConfigManager):
    """
    Test when device name isn't found but port setting exists as fallback.
    """
    # Setup config with device name and port
    config_manager.config_file_path.write_text(
        "device name: Nonexistent Device\n"
        "port: COM4\n"
    )
    config_manager.load_config()
    
    # Mock empty ports list
    mock_ports = []
    
    with patch('serial.tools.list_ports.comports', return_value=mock_ports):
        assert config_manager.get_serial_port() == "COM4"

def test_get_serial_port__no_device_no_port(config_manager: ConfigManager):
    """
    Test when neither device is found nor port setting exists.
    """
    # Setup config with only device name
    config_manager.config_file_path.write_text("device name: Nonexistent Device\n")
    config_manager.load_config()
    
    # Mock empty ports list
    mock_ports = []
    
    with patch('serial.tools.list_ports.comports', return_value=mock_ports):
        with pytest.raises(ValueError, match="The config file does not contain the right device name or an appropriate port."):
            config_manager.get_serial_port()

def test_get_serial_port__multiple_matching_devices(config_manager: ConfigManager):
    """
    Test when multiple devices match the device name - should return first match.
    """
    # Setup config with device name
    config_manager.config_file_path.write_text("device name: Test Device\n")
    config_manager.load_config()
    
    # Mock multiple matching devices
    mock_ports = [
        ("COM1", "Other Device", "hwid1"),
        ("COM2", "Test Device First", "hwid2"),
        ("COM3", "Test Device Second", "hwid3")
    ]
    
    with patch('serial.tools.list_ports.comports', return_value=mock_ports):
        assert config_manager.get_serial_port() == "COM2"

def test_get_serial_port__no_device_name_in_config(config_manager: ConfigManager):
    """
    Test when device name setting is missing but port is available.
    """
    # Setup config with only port
    config_manager.config_file_path.write_text("port: COM5\n")
    config_manager.load_config()
    
    mock_ports = [
        ("COM1", "Some Device", "hwid1"),
    ]
    
    with patch('serial.tools.list_ports.comports', return_value=mock_ports):
        with pytest.raises(ValueError, match="Setting device name is not found in the configuration file."):
            config_manager.get_serial_port()

def test_get_serial_port__empty_ports_list(config_manager: ConfigManager):
    """
    Test when no serial ports are available but port setting exists.
    """
    # Setup config with device name and port
    config_manager.config_file_path.write_text(
        "device name: Test Device\n"
        "port: COM6\n"
    )
    config_manager.load_config()
    
    # Mock empty ports list
    with patch('serial.tools.list_ports.comports', return_value=[]):
        assert config_manager.get_serial_port() == "COM6"

