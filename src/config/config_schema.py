
from pydantic import BaseModel


class Device(BaseModel):
    name: str
    port: str
    baudrate: int
    sliders: int

class Settings(BaseModel):
    inverted: bool
    system_in_unmapped: bool
    session_reload_interval: int

class ConfigSchema(BaseModel):
    mappings: dict[int, list[str]]
    device: Device
    settings: Settings
