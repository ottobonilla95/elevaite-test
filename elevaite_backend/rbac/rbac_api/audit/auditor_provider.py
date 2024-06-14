from .config import config as auditor_config
from .auditor import Auditor


class AuditorProvider:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            config = auditor_config
            cls._instance = Auditor(config)
        return cls._instance
