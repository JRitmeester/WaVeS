from sessions.session_protocol import SessionManagerProtocol
from config.config_protocol import ConfigManagerProtocol
from mapping.mapping_protocol import MappingManagerProtocol
from sessions.sessions import Session, Device


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

        sliders = int(config_manager.get_setting("device.sliders"))
        session_dict = {i: [] for i in range(sliders)}
        mappings = config_manager.get_setting("mappings")

        # Process each target mapping
        for idx, targets in mappings.items():
            idx_int = int(idx)  # Convert string key to integer
            for target in targets:
                self._add_single_target_mapping(
                    target, idx_int, session_dict, session_manager
                )

        # Handle unmapped sessions
        for idx, targets in mappings.items():
            idx_int = int(idx)  # Convert string key to integer
            if "unmapped" in targets:
                self._add_unmapped_sessions(
                    idx_int,
                    session_dict,
                    session_manager,
                    config_manager,
                )

        return session_dict

    def _add_single_target_mapping(
        self,
        target: str,
        idx: int,
        session_dict: dict[int, Session],
        session_manager: SessionManagerProtocol,
    ) -> None:
        if target == "master":
            session_dict[idx].append(session_manager.master_session)
            session_manager.master_session.mark_as_mapped(True)
        elif target == "system":
            session_dict[idx].append(session_manager.system_session)
            session_manager.system_session.mark_as_mapped(True)
        elif target.startswith("device:"):
            session_dict[idx].append(session_manager.get_device_session(target[7:]))
        elif target != "unmapped":
            # Find the software session that matches the target, and add it to the session_dict
            for session in session_manager.software_sessions:
                if target.lower() in session.name.lower():
                    session_dict[idx].append(session)
                    session.mark_as_mapped(True)

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
            if not session.is_mapped
        ]

        if (
            config_manager.get_setting("settings.system_in_unmapped")
            and not session_manager.system_session.is_mapped
        ):
            unmapped_sessions.append(session_manager.system_session)

        session_dict[idx].extend(unmapped_sessions)
        for session in unmapped_sessions:
            session.mark_as_mapped(True)
