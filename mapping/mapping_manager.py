from sessions import SessionManagerProtocol
from config import ConfigManagerProtocol
from mapping import MappingManagerProtocol
from sessions import Session, SessionGroup


class MappingManager(MappingManagerProtocol):
    def __init__(self):
        pass

    def get_mapping(
        self,
        session_manager: SessionManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ) -> dict[int, Session]:
        """Update session mappings"""
        config_manager.load_config()
        return self.create_mappings(session_manager, config_manager)

    def create_mappings(
        self,
        session_manager: SessionManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ) -> dict[int, Session]:
        """
        Create mappings between sliders and sessions

        Args:
            session_manager: Provider of session information
            config_manager: Provider of configuration information
            target_indices: Dictionary mapping targets to slider indices
        """

        target_indices = self.get_target_indices(config_manager)

        session_dict = {}

        # Process each target mapping
        for target, idx in target_indices.items():
            if isinstance(target, str):
                self._add_single_target_mapping(
                    target.lower(), idx, session_dict, session_manager
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
        """Get mapping of targets to slider indices from config"""
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
        """Handle mapping for a single target"""
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
        """Add mapping for a software session"""
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
        """Handle mapping for a group of targets"""
        active_sessions = []

        for target_app in target_group:
            target_app = target_app.lower()
            if (
                target_app in ["master", "system", "unmapped"]
                or "device:" in target_app
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
        """Handle mapping for unmapped sessions"""
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
