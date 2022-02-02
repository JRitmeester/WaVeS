import yaml
from pycaw.pycaw import AudioUtilities
from pathlib import Path
import logging
import re
import utils


def get_yaml_dir():
    return get_appdata_path() / 'config.yaml'

def get_mapping_dir():
    config = get_config()
    if config is not None:
        return config['mapping_dir']
    else:
        create_config()

def create_config():
    yaml_dir = get_yaml_dir()
    yaml_dir.touch()
    yaml_dir.write_text("mapping_dir: \"\"")

def get_config():
    yaml_dir = get_yaml_dir()

    if yaml_dir.exists():
        with open(yaml_dir, 'r') as file:
            config = yaml.safe_load(file)
        return config

def save_mapping_dir(mapping_dir):
    yaml_dir = get_yaml_dir()
    if yaml_dir.exists():
        config = get_config()
        config['mapping_dir'] = mapping_dir
        with yaml_dir.open(mode='w') as file:
            yaml.dump(config, file)

def get_devices():
    return [re.sub("AudioDevice: ", "", str(x)) for x in AudioUtilities.GetAllDevices() if x]

def get_appdata_path():
    return Path.home() / "AppData/Roaming/WaVeS"

def get_logger():
    return logging.getLogger("root")
