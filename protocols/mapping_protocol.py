from typing import Protocol
from sessions import Session
from .session_protocol import SessionManagerProtocol
from .config_protocol import ConfigManagerProtocol


class MappingManagerProtocol(Protocol):
    """Define the interface we expect from MappingManager"""

    def get_mapping(
        self,
        session_manager: SessionManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ) -> dict[int, Session]: ...
