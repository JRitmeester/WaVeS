import serial
from microcontroller.microcontroller_protocol import MicrocontrollerProtocol
from utils.logger import logger
class MicrocontrollerManager(MicrocontrollerProtocol):
    def __init__(self, n_sliders: int) -> None:
        self.serial = None
        self.n_sliders = n_sliders
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
        logger.info(f"Connected to {port} at {baudrate} baud")

    def read_values(self) -> list[float] | None:
        """Read values from the microcontroller and validate them"""
        if not self._connected or not self.serial:
            return None

        # Data is formatted as "<val>|<val>|<val>|<val>|<val>"
        # Creating a QMessageBox can disrupt the data flow and cause UnicodeDecodeError.
        try:
            data = str(self.serial.readline()[:-2], "utf-8")  # Trim off '\r\n'.
        except UnicodeDecodeError:
            return None
        if not data:
            return None

        try:
            values = [float(val) for val in data.split("|")]
        except ValueError:
            logger.warning(f"Invalid data: {data}")
            return None

        if len(values) != self.n_sliders:
            return None

        # Normalize values to 0-1 range
        return [val / 1023 for val in values]

    def write_values(self, values: list[float]) -> None:
        """Write values to the microcontroller
        
        Values are normalized to 0-100 and sent as integers. This avoids having to use floats, while still using a normalized range.
        """
        if not self._connected or not self.serial:
            return

        # Validate the number of values
        if len(values) != self.n_sliders:
            raise ValueError(f"Expected {self.n_sliders} values, got {len(values)}")
        
        values = [str(int(val * 100)) for val in values]
        payload = "|".join(values).encode('utf-8')
        try:
            self.serial.write(payload)
        except serial.SerialException as e:
            logger.error(f"Error writing values to microcontroller: {e}")

    def close(self) -> None:
        if self.serial:
            self.serial.close()
            self._connected = False
            logger.info("Disconnected from microcontroller")

    @property
    def is_connected(self) -> bool:
        return self._connected
