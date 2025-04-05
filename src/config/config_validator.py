from pathlib import Path
import yaml
from pydantic import ValidationError
from .config_schema import ConfigSchema
from .config_exceptions import ConfigFileEmptyError
class ConfigValidator:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def validate(self) -> ConfigSchema:
        """
        Load and validate the configuration file.
        Returns the validated configuration if successful.
        Raises ValidationError if validation fails.
        """
        with open(self.config_path) as f:
            config_data = yaml.safe_load(f)
        if config_data is None:
            raise ConfigFileEmptyError("Configuration file is empty")
        return ConfigSchema(**config_data)