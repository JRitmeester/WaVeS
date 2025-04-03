import serial
from microcontroller.microcontroller_protocol import MicrocontrollerProtocol


class MicrocontrollerManager(MicrocontrollerProtocol):
    def __init__(self) -> None:
        self.serial = None
        self._connected = False

    def connect(self, port: str, baudrate: int) -> None:
        try:
            self.serial = serial.Serial(port, baudrate, timeout=0.1)
            self._connected = True
        except serial.SerialException as e:
            self._connected = False
            raise ConnectionError(
                f"The serial connection is busy or unavailable. This may mean that the wrong COM port is specified ({port}) or that another instance of WaVeS is already running."
            ) from e

    def read_values(self, expected_count: int) -> list[float] | None:
        """Read values from the microcontroller and validate them"""
        if not self._connected or not self.serial:
            return None

        # Data is formatted as "<val>|<val>|<val>|<val>|<val>"
        data = str(self.serial.readline()[:-2], "utf-8")  # Trim off '\r\n'.
        if not data:
            return None

        try:
            values = [float(val) for val in data.split("|")]
        except ValueError:
            print(f"Invalid data: {data}")
            return None

        if len(values) != expected_count:
            return None

        # Normalize values to 0-1 range
        return [val / 1023 for val in values]

    def close(self) -> None:
        if self.serial:
            self.serial.close()
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected
