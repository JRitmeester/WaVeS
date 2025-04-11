import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import serial
from microcontroller.microcontroller_manager import MicrocontrollerManager


@pytest.fixture
def microcontroller_manager():
    return MicrocontrollerManager(n_sliders=4)


def test_connect(microcontroller_manager: MicrocontrollerManager):
    # Test successful connection
    with patch("serial.Serial") as mock_serial:
        # Configure the mock to not raise any exceptions
        mock_serial.return_value = MagicMock()

        # Call connect with test parameters
        microcontroller_manager.connect("COM1", 9600)

        # Verify serial.Serial was called with correct parameters
        mock_serial.assert_called_once_with("COM1", 9600, timeout=0.1)

        # Verify connection state
        assert microcontroller_manager.is_connected is True


def test_connect__connection_failure(microcontroller_manager: MicrocontrollerManager):
    # Test connection failure
    with patch("serial.Serial") as mock_serial:
        # Configure the mock to raise SerialException
        mock_serial.side_effect = serial.SerialException("Connection failed")

        # Call connect with test parameters and expect SystemExit
        with pytest.raises(ConnectionError) as exc_info:
            microcontroller_manager.connect("COM1", 9600)


def test_connect__unknown_port(microcontroller_manager: MicrocontrollerManager):
    # Test connection with unknown port
    with pytest.raises(ConnectionError):
        microcontroller_manager.connect("unknown_port", 9600)


def test_connect__unknown_baud_rate(microcontroller_manager: MicrocontrollerManager):
    # Test connection with unknown baud rate
    with pytest.raises(ConnectionError):
        microcontroller_manager.connect("COM1", 1234567890)


def test_close(microcontroller_manager: MicrocontrollerManager):
    # Test successful disconnection
    with patch("serial.Serial") as mock_serial:
        # Configure the mock to not raise any exceptions
        mock_serial.return_value = MagicMock()

        # Connect first
        microcontroller_manager.connect("COM1", 9600)
        assert microcontroller_manager.is_connected is True

        # Then disconnect
        microcontroller_manager.close()
        assert microcontroller_manager.is_connected is False


def test_send_sync_message(microcontroller_manager: MicrocontrollerManager):
    """Test sending sync messages to the microcontroller"""
    with patch("serial.Serial") as mock_serial:
        # Setup mock serial connection
        mock_serial_instance = MagicMock()
        mock_serial.return_value = mock_serial_instance
        microcontroller_manager.connect("COM1", 9600)

        # Test case 1: Normal values
        values = [0.5, 0.25, 0.75, 1.0]  # 4 sliders with different values
        microcontroller_manager.send_sync_message(values)
        mock_serial_instance.write.assert_called_with("<50|25|75|100>".encode('utf-8'))

        # Test case 2: All zeros
        values = [0.0, 0.0, 0.0, 0.0]
        microcontroller_manager.send_sync_message(values)
        mock_serial_instance.write.assert_called_with("<0|0|0|0>".encode('utf-8'))

        # Test case 3: All ones
        values = [1.0, 1.0, 1.0, 1.0]
        microcontroller_manager.send_sync_message(values)
        mock_serial_instance.write.assert_called_with("<100|100|100|100>".encode('utf-8'))

        # Test case 4: Values that need rounding
        values = [0.333, 0.667, 0.123, 0.789]
        microcontroller_manager.send_sync_message(values)
        mock_serial_instance.write.assert_called_with("<33|66|12|78>".encode('utf-8'))


def test_send_sync_message__validation(microcontroller_manager: MicrocontrollerManager):
    """Test validation of sync message inputs"""
    with patch("serial.Serial") as mock_serial:
        mock_serial_instance = MagicMock()
        mock_serial.return_value = mock_serial_instance
        microcontroller_manager.connect("COM1", 9600)

        # Test case 1: Wrong number of values
        with pytest.raises(ValueError, match=r"Expected 4 values, got 3"):
            microcontroller_manager.send_sync_message([0.5, 0.5, 0.5])

        # Test case 2: Values out of range (below 0)
        with pytest.raises(ValueError, match=r"Values must be between 0 and 1"):
            microcontroller_manager.send_sync_message([-0.1, 0.5, 0.5, 0.5])

        # Test case 3: Values out of range (above 1)
        with pytest.raises(ValueError, match=r"Values must be between 0 and 1"):
            microcontroller_manager.send_sync_message([0.5, 1.1, 0.5, 0.5])


def test_send_sync_message__not_connected(microcontroller_manager: MicrocontrollerManager):
    """Test sending sync message when not connected"""
    # Try to send message without connecting first
    values = [0.5, 0.5, 0.5, 0.5]
    microcontroller_manager.send_sync_message(values)  # Should silently return without error

    # Verify no serial communication was attempted
    assert microcontroller_manager.serial is None

