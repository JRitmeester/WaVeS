from pathlib import Path
import yaml
from serial.tools import list_ports
from .config_protocol import ConfigManagerProtocol
from .config_validator import ConfigValidator
from pydantic import ValidationError
from .config_exceptions import ConfigValidationError


class ConfigManager(ConfigManagerProtocol):
    def __init__(self, config_path: Path, default_mapping_path: Path):
        self.config_path = config_path
        self.config_file_path = config_path / "mapping.yml"
        self.default_mapping_path = default_mapping_path
        self.config_data = {}
        self.validator = ConfigValidator(self.config_file_path)

    def ensure_config_exists(self) -> Path:
        """
        Ensure the config file exists. If it doesn't, create it and write the default mapping to it.
        """
        if not self.config_file_path.exists():
            self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_file_path.touch(exist_ok=True)
            self.config_file_path.write_text(self.default_mapping_path.read_text())

    def load_config(self ) -> None:
        """
        Load and validate the YAML config file.
        Raises ConfigValidationError if the configuration is invalid.
        """
        try:
            validated_config = self.validator.validate()
            self.config_data = validated_config.model_dump()
        except ValidationError as e:
            raise ConfigValidationError(e)

    def get_setting(self, path: str) -> str:
        """
        Get the value of a setting from the config file using dot notation.
        Example: 'device.baudrate' will return the baudrate under the device section
        """
        keys = path.split(".")
        value = self.config_data
        for key in keys:
            if isinstance(value, dict):
                if key not in value:
                    raise ValueError(
                        f"Setting {path} is not found in the configuration file."
                    )
                value = value[key]
            else:
                raise ValueError(
                    f"Cannot access {key} in {path} as parent is not a dictionary"
                )

        if value is None:
            raise ValueError(f"Setting {path} is present but empty.")
        return value

    def get_serial_port(self) -> str:
        """
        Try to find the serial port from the config file, first by device name.
        If the device name cannot be matched to a port, return the port specified in the config file.
        """
        device_name = self.get_setting("device.name")
        ports = list_ports.comports()

        # Try to find port by device name first
        for port, desc, _ in sorted(ports):
            if device_name in desc:
                return port

        # Fall back to explicit port setting if device not found
        try:
            return self.get_setting("device.port")
        except ValueError:
            raise ValueError(
                "The config file does not contain the right device name or an appropriate port."
            )

    @staticmethod
    def get_default_config_path() -> Path:
        return Path.home() / "AppData/Roaming"
