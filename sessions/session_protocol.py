from typing import Protocol
from sessions import Session


class SessionManagerProtocol(Protocol):
    """Define the interface we expect from SessionManager"""

    software_sessions: dict[str, Session]
    mapped_sessions: dict[str, bool]

    @property
    def master_session(self) -> Session: ...
    @property
    def system_session(self) -> Session: ...

    def get_device_session(self, device_name: str) -> Session: ...
