from pathlib import Path
import re
from serial.tools import list_ports
from .config_protocol import ConfigManagerProtocol


class ConfigManager(ConfigManagerProtocol):
    def __init__(self, config_path: Path, default_mapping_path: Path):
        self.config_path = config_path
        self.config_file_path = config_path / "mapping.txt"
        self.default_mapping_path = default_mapping_path
        self.lines: list[str] = []

    def ensure_config_exists(self) -> Path:
        """
        Ensure the config file exists. If it doesn't, create it and write the default mapping to it.
        """
        if not self.config_file_path.exists():
            self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_file_path.touch(exist_ok=True)
            self.config_file_path.write_text(self.default_mapping_path.read_text())

    def load_config(self) -> None:
        """
        Load the config file and store the lines in the lines attribute.
        """
        self.lines = self.config_file_path.read_text().strip().split("\n")

    def get_setting(self, text: str) -> str:
        """
        Get the value of a setting from the config file.
        """
        matching_settings = list(filter(lambda x: text + ":" in x, self.lines))
        if len(matching_settings) == 0:
            raise ValueError(f"Setting {text} is not found in the configuration file.")

        value = re.search(r"^[^:]*:[ \t]*(.*?)[ \t]*$", matching_settings[0])
        if value.group(1) == "":
            raise ValueError(f"Setting {text} is present but empty.")
        return value.group(1)

    def get_serial_port(self) -> str:
        """
        Try to find the serial port from the config file, first by device name.
        If the device name cannot be matched to a port, return the port specified in the config file.        
        Note that if there a multiple devices with the same name, the first one found will be returned.
        """
        device_name = self.get_setting("device name")
        ports = list_ports.comports()

        # Try to find port by device name first
        for port, desc, _ in sorted(ports):
            if device_name in desc:
                return port

        # Fall back to explicit port setting if device not found
        try:
            return self.get_setting("port")
        except ValueError:
            raise ValueError("The config file does not contain the right device name or an appropriate port.")

    @staticmethod
    def get_default_config_path() -> Path:
        return Path.home() / "AppData/Roaming"
