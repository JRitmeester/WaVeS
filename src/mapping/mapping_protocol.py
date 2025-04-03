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

    def create_mappings(
        self,
        session_manager: SessionManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ) -> dict[int, Session]: ...

    def _add_single_target_mapping(
        self,
        target: str,
        idx: int,
        session_dict: dict[int, Session],
        session_manager: SessionManagerProtocol,
    ) -> None: ...

    def _add_unmapped_sessions(
        self,
        idx: int,
        session_dict: dict[int, Session],
        session_manager: SessionManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ) -> None: ...
