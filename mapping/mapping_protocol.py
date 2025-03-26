from typing import Protocol
from sessions.sessions import Session
from sessions.session_protocol import SessionManagerProtocol
from config.config_protocol import ConfigManagerProtocol


class MappingManagerProtocol(Protocol):
    """Define the interface we expect from MappingManager"""

    def get_mapping(
        self,
        session_manager: SessionManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ) -> dict[int, Session]: ...
