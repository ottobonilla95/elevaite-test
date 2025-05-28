import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    max_connections: int = 10
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    connection_timeout: int = 5
    socket_timeout: int = 5
    decode_responses: bool = True

    default_stream_max_len: int = 1000
    default_consumer_group: str = "agent_group"
    default_block_ms: int = 2000
    default_count: int = 10
    default_claim_min_idle_time: int = 30000

    max_connections_per_pool: int = 50
    retry_on_error: list = field(default_factory=lambda: [])

    @classmethod
    def from_env(cls, env_prefix: str = "REDIS_") -> "RedisConfig":
        load_dotenv()

        def get_env_bool(key: str, default: bool) -> bool:
            value = os.getenv(key, str(default)).lower()
            return value in ("true", "1", "yes", "on")

        def get_env_int(key: str, default: int) -> int:
            try:
                return int(os.getenv(key, str(default)))
            except ValueError:
                logger.warning(
                    f"Invalid integer value for {key}, using default: {default}"
                )
                return default

        def get_env_str(key: str, default: Optional[str] = None) -> Optional[str]:
            value = os.getenv(key, default)
            return value if value and value.strip() else None

        config = cls(
            host=get_env_str(f"{env_prefix}HOST", "localhost") or "localhost",
            port=get_env_int(f"{env_prefix}PORT", 6379),
            db=get_env_int(f"{env_prefix}DB", 0),
            username=get_env_str(f"{env_prefix}USERNAME"),
            password=get_env_str(f"{env_prefix}PASSWORD"),
            max_connections=get_env_int(f"{env_prefix}MAX_CONNECTIONS", 10),
            retry_on_timeout=get_env_bool(f"{env_prefix}RETRY_ON_TIMEOUT", True),
            health_check_interval=get_env_int(f"{env_prefix}HEALTH_CHECK_INTERVAL", 30),
            connection_timeout=get_env_int(f"{env_prefix}CONNECTION_TIMEOUT", 5),
            socket_timeout=get_env_int(f"{env_prefix}SOCKET_TIMEOUT", 5),
        )

        config.validate()
        return config

    def validate(self) -> None:
        if not self.host:
            raise ValueError("Redis host cannot be empty")

        if not (1 <= self.port <= 65535):
            raise ValueError(
                f"Redis port must be between 1 and 65535, got: {self.port}"
            )

        if not (0 <= self.db <= 15):
            raise ValueError(f"Redis database must be between 0 and 15, got: {self.db}")

        if self.max_connections < 1:
            raise ValueError(
                f"Max connections must be at least 1, got: {self.max_connections}"
            )

        if self.connection_timeout < 1:
            raise ValueError(
                f"Connection timeout must be at least 1 second, got: {self.connection_timeout}"
            )

        if self.socket_timeout < 1:
            raise ValueError(
                f"Socket timeout must be at least 1 second, got: {self.socket_timeout}"
            )

    def to_redis_kwargs(self) -> Dict[str, Any]:
        kwargs = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "decode_responses": self.decode_responses,
            "retry_on_timeout": self.retry_on_timeout,
            "health_check_interval": self.health_check_interval,
            "socket_connect_timeout": self.connection_timeout,
            "socket_timeout": self.socket_timeout,
        }

        if self.username:
            kwargs["username"] = self.username
        if self.password:
            kwargs["password"] = self.password

        return kwargs

    def to_connection_pool_kwargs(self) -> Dict[str, Any]:
        kwargs = self.to_redis_kwargs()
        kwargs["max_connections"] = self.max_connections_per_pool
        return kwargs

    def __str__(self) -> str:
        return (
            f"RedisConfig(host={self.host}, port={self.port}, db={self.db}, "
            f"username={'***' if self.username else None}, "
            f"password={'***' if self.password else None})"
        )


_config: Optional[RedisConfig] = None


def get_redis_config() -> RedisConfig:
    global _config
    if _config is None:
        _config = RedisConfig.from_env()
    return _config


def set_redis_config(config: RedisConfig) -> None:
    global _config
    config.validate()
    _config = config


def reset_redis_config() -> None:
    global _config
    _config = None
