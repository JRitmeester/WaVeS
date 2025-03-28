import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'src')))

import pytest
from unittest.mock import patch, MagicMock
import serial
from microcontroller.microcontroller_manager import MicrocontrollerManager


@pytest.fixture
def microcontroller_manager():
    return MicrocontrollerManager()

def test_connect(microcontroller_manager: MicrocontrollerManager):
    # Test successful connection
    with patch('serial.Serial') as mock_serial:
        # Configure the mock to not raise any exceptions
        mock_serial.return_value = MagicMock()
        
        # Call connect with test parameters
        microcontroller_manager.connect('COM1', 9600)
        
        # Verify serial.Serial was called with correct parameters
        mock_serial.assert_called_once_with('COM1', 9600, timeout=0.1)
        
        # Verify connection state
        assert microcontroller_manager.is_connected is True

def test_connect__connection_failure(microcontroller_manager: MicrocontrollerManager):
    # Test connection failure
    with patch('serial.Serial') as mock_serial:
        # Configure the mock to raise SerialException
        mock_serial.side_effect = serial.SerialException("Connection failed")
        
        # Call connect with test parameters and expect SystemExit
        with pytest.raises(ConnectionError) as exc_info:
            microcontroller_manager.connect('COM1', 9600)


def test_connect__unknown_port(microcontroller_manager: MicrocontrollerManager):
    # Test connection with unknown port
    with pytest.raises(ConnectionError):
        microcontroller_manager.connect('unknown_port', 9600)

def test_connect__unknown_baud_rate(microcontroller_manager: MicrocontrollerManager):
    # Test connection with unknown baud rate
    with pytest.raises(ConnectionError):
        microcontroller_manager.connect('COM1', 1234567890)

def test_close(microcontroller_manager: MicrocontrollerManager):
    # Test successful disconnection
    with patch('serial.Serial') as mock_serial:
        # Configure the mock to not raise any exceptions
        mock_serial.return_value = MagicMock()
        
        # Connect first
        microcontroller_manager.connect('COM1', 9600)
        assert microcontroller_manager.is_connected is True
        
        # Then disconnect
        microcontroller_manager.close()
        assert microcontroller_manager.is_connected is False


