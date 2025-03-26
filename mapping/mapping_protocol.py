from typing import Protocol
from sessions.sessions import Session
from sessions.session_protocol import SessionManagerProtocol
from config.config_protocol import ConfigManagerProtocol


class MappingManagerProtocol(Protocol):

    def get_mapping(
        self,
        session_manager: SessionManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ) -> dict[int, Session]: ...
