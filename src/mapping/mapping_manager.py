from sessions.session_protocol import SessionManagerProtocol
from config.config_protocol import ConfigManagerProtocol
from mapping.mapping_protocol import MappingManagerProtocol
from sessions.sessions import Session, SessionGroup


class MappingManager(MappingManagerProtocol):
    def __init__(self):
        pass

    def get_mapping(
        self,
        session_manager: SessionManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ) -> dict[int, Session]:

        config_manager.load_config()
        return self.create_mappings(session_manager, config_manager)

    def create_mappings(
        self,
        session_manager: SessionManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ) -> dict[int, Session]:

        target_indices = self.get_target_indices(config_manager)

        session_dict = {}

        # Process each target mapping
        for target, idx in target_indices.items():
            if isinstance(target, str):
                self._add_single_target_mapping(
                    target, idx, session_dict, session_manager
                )
            elif isinstance(target, tuple):
                self._add_group_mapping(target, idx, session_dict, session_manager)

        # Handle unmapped sessions
        if "unmapped" in target_indices:
            self._add_unmapped_sessions(
                target_indices["unmapped"],
                session_dict,
                session_manager,
                config_manager,
            )

        return session_dict

    def get_target_indices(
        self, config_manager: ConfigManagerProtocol
    ) -> dict[str, int]:
        target_indices = {}
        for idx in range(int(config_manager.get_setting("sliders"))):
            application_str = config_manager.get_setting(str(idx))
            if "," in application_str:
                application_str = tuple(
                    app.strip() for app in application_str.split(",")
                )
            target_indices[application_str] = int(idx)
        return target_indices

    def _add_single_target_mapping(
        self,
        target: str,
        idx: int,
        session_dict: dict[int, Session],
        session_manager: SessionManagerProtocol,
    ) -> None:
        if target == "master":
            session_dict[idx] = session_manager.master_session
        elif target == "system":
            session_dict[idx] = session_manager.system_session
        elif target.startswith("device:"):
            session_dict[idx] = session_manager.get_device_session(target[7:])
        elif target != "unmapped":
            self._add_software_session(target, idx, session_dict, session_manager)

    def _add_software_session(
        self,
        target: str,
        idx: int,
        session_dict: dict[int, Session],
        session_manager: SessionManagerProtocol,
    ) -> None:
        if target in session_manager.software_sessions:
            session = session_manager.software_sessions.get(target)
            if session is not None:
                session_dict[idx] = session
                session_manager.mapped_sessions[session.name] = True

    def _add_group_mapping(
        self,
        target_group: tuple[str, ...],
        idx: int,
        session_dict: dict[int, Session],
        session_manager: SessionManagerProtocol,
    ) -> None:
        active_sessions = []

        for target_app in target_group:
            target_app = target_app.lower()
            if (
                target_app.lower() in ["master", "system", "unmapped"]
                or "device:" in target_app.lower()
            ):
                continue

            session = session_manager.software_sessions.get(target_app)
            if session is not None:
                active_sessions.append(session)

        if active_sessions:
            session_dict[idx] = SessionGroup(sessions=active_sessions)
            for session in active_sessions:
                session_manager.mapped_sessions[session.name] = True

    def _add_unmapped_sessions(
        self,
        idx: int,
        session_dict: dict[int, Session],
        session_manager: SessionManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ) -> None:
        unmapped_sessions = [
            s
            for s in session_manager.software_sessions.values()
            if not session_manager.mapped_sessions[s.name]
        ]

        if (
            config_manager.get_setting("system in unmapped").lower() == "true"
            and not session_manager.mapped_sessions["system"]
        ):
            unmapped_sessions.append(session_manager.system_session)

        session_dict[idx] = SessionGroup(sessions=unmapped_sessions)
        for session in unmapped_sessions:
            session_manager.mapped_sessions[session.name] = True
