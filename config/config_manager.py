from pathlib import Path
import re
from serial.tools import list_ports
from config.config_protocol import ConfigManagerProtocol
from PyQt5.QtWidgets import QMessageBox
import webbrowser


class ConfigManager(ConfigManagerProtocol):
    def __init__(self, config_path: Path, default_mapping_path: Path):
        self.config_path = config_path
        self.config_file_path = config_path / "mapping.txt"
        self.default_mapping_path = default_mapping_path
        self.lines: list[str] = []
        self.load_config()

    def ensure_config_exists(self) -> Path:
        if not self.config_file_path.exists():
            self.config_file_path.touch(exist_ok=True, parents=True)
            self.config_file_path.write_text(self.default_mapping_path.read_text())

    def load_config(self) -> None:
        """Load configuration file contents"""
        self.lines = self.config_file_path.read_text().split("\n")

    def get_setting(self, text: str) -> str:
        """
        Extract a specific setting from the configuration file.

        Args:
            text (str): The setting name to search for

        Returns:
            str: The value of the requested setting

        Raises:
            ValueError: If the setting is not found
        """
        matching_settings = list(filter(lambda x: text + ":" in x, self.lines))
        if len(matching_settings) == 0:
            raise ValueError(f"Setting {text} is not found in the configuration file.")

        value = re.search(r"^.*: ?(.*)", matching_settings[0])
        if value.group(1) == "":
            raise ValueError(f"Setting {text} is not found in the configuration file.")
        return value.group(1)

    def get_serial_port(self) -> str:
        """Get the appropriate serial port based on config settings"""
        ports = list_ports.comports()
        device_name = self.get_setting("device name")

        for port, desc, _ in sorted(ports):
            if device_name in desc:
                return port

        try:
            return self.get_setting("port")
        except:
            raise ValueError(
                "The config file does not contain the right device name or an appropriate port."
            )

    @staticmethod
    def get_default_config_path() -> Path:
        """Returns default configuration directory path"""
        return Path.home() / "AppData/Roaming"
