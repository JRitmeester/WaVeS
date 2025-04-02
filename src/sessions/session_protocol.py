from typing import Protocol
from sessions.sessions import Session


class SessionManagerProtocol(Protocol):

    software_sessions: dict[str, Session]
    mapped_sessions: dict[str, bool]
    devices: dict[str, Session]

    @property
    def master_session(self) -> Session: ...
    @property
    def system_session(self) -> Session: ...

    def reload_sessions_and_devices(self) -> None: ...

    def check_for_changes(self) -> bool: ...

    def apply_volumes(
        self, values: list[float], mapping: dict[int, Session], inverted: bool
    ) -> None: ...


    def get_software_session(self, session_name: str) -> Session: ...

    def get_device_session(self, device_name: str) -> Session: ...

    def create_software_sessions(self) -> None: ...

    def create_device_sessions(self) -> None: ...