from sessions.session_protocol import SessionManagerProtocol
from config.config_protocol import ConfigManagerProtocol
from mapping.mapping_protocol import MappingManagerProtocol
from sessions.sessions import Session, SessionGroup, Device


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
    ) -> dict[int, list[Session | Device]]:

        target_indices = self.get_target_indices(config_manager)

        sliders = int(config_manager.get_setting("device.sliders"))
        session_dict = {i: [] for i in range(sliders)}

        # Process each target mapping
        for idx, targets in target_indices.items():
            for target in targets:
                self._add_single_target_mapping(
                    target, idx, session_dict, session_manager
                )
            # elif isinstance(target, tuple):
            #     self._add_group_mapping(target, idx, session_dict, session_manager)

        # Handle unmapped sessions
        for idx, targets in target_indices.items(): 
            if "unmapped" in targets:
                self._add_unmapped_sessions(
                    idx,
                    session_dict,
                    session_manager,
                    config_manager,
            )

        return session_dict

    def get_target_indices(
        self, config_manager: ConfigManagerProtocol
    ) -> dict[int, str]:
        mappings = config_manager.get_setting("mappings")
        return mappings

        # for idx in range(sliders):
        #     application_str = mappings[idx]
        #     if application_str:
        #         if isinstance(application_str, str) and "," in application_str:
        #             application_str = tuple(
        #                 app.strip() for app in application_str.split(",")
        #             )
        #         target_indices[application_str] = int(idx)
        # return target_indices

    def _add_single_target_mapping(
        self,
        target: str,
        idx: int,
        session_dict: dict[int, Session],
        session_manager: SessionManagerProtocol,
    ) -> None:
        if target == "master":
            session_dict[idx].append(session_manager.master_session)
            session_manager.mapped_sessions["master"] = True
        elif target == "system":
            session_dict[idx].append(session_manager.system_session)
            session_manager.mapped_sessions["system"] = True
        elif target.startswith("device:"):
            session_dict[idx].append(session_manager.get_device_session(target[7:]))
        elif target != "unmapped":
            self._add_software_session(target, idx, session_dict, session_manager)

    def _add_software_session(
        self,
        target: str,
        idx: int,
        session_dict: dict[int, Session],
        session_manager: SessionManagerProtocol,
    ) -> None:
        for session in session_manager.software_sessions:
            if target.lower() in session.name.lower():
                session_dict[idx].append(session)
                session_manager.mapped_sessions[session.unique_name] = True


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

            session = session_manager.get_software_session_by_name(target_app)
            if session is not None:
                active_sessions.append(session)

        if active_sessions:
            session_dict[idx] = SessionGroup(sessions=active_sessions)
            for session in active_sessions:
                session_manager.mapped_sessions[session.unique_name] = True

    def _add_unmapped_sessions(
        self,
        idx: int,
        session_dict: dict[int, Session],
        session_manager: SessionManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ) -> None:
        unmapped_sessions = [
            session
            for session in session_manager.software_sessions
            if not session_manager.mapped_sessions[session.unique_name]
        ]

        if (
            config_manager.get_setting("settings.system_in_unmapped")
            and not session_manager.mapped_sessions["system"]
        ):
            unmapped_sessions.append(session_manager.system_session)

        session_dict[idx].extend(unmapped_sessions)
        for session in unmapped_sessions:
            session_manager.mapped_sessions[session.unique_name] = True
