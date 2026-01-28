"""Configuration settings for the Code Execution Service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
    )

    # Service settings
    service_name: str = "code-execution-service"
    service_port: int = 8007
    log_level: str = "INFO"
    debug: bool = False

    # Execution limits
    default_timeout_seconds: int = 30
    max_timeout_seconds: int = 60
    min_timeout_seconds: int = 1
    default_memory_mb: int = 256
    max_memory_mb: int = 512
    min_memory_mb: int = 64

    # Nsjail configuration
    nsjail_path: str = "/usr/bin/nsjail"
    nsjail_config_path: str = "/app/nsjail/nsjail.cfg"
    sandbox_python_path: str = "/opt/sandbox/bin/python"
    sandbox_tmp_dir: str = "/tmp/sandbox"

    # Validation settings
    max_code_length: int = 100_000  # 100KB max code size


# Global settings instance
settings = Settings()
