import time
import logging
import threading
from typing import Optional, Dict
from contextlib import contextmanager

import redis
from redis.connection import ConnectionPool

from redis_config import get_redis_config

logger = logging.getLogger(__name__)


class RedisConnectionError(Exception):
    pass


class RedisClientFactory:
    _instance: Optional["RedisClientFactory"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "RedisClientFactory":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._config = get_redis_config()
        self._connection_pools: Dict[str, ConnectionPool] = {}
        self._clients: Dict[str, redis.Redis] = {}
        self._health_check_thread: Optional[threading.Thread] = None
        self._health_check_running = False
        self._last_health_check = 0
        self._lock = threading.Lock()
        self._initialized = True

        self._start_health_check()

    def get_client(self, pool_name: str = "default") -> redis.Redis:
        with self._lock:
            if pool_name not in self._clients:
                self._clients[pool_name] = self._create_client(pool_name)
            return self._clients[pool_name]

    def _create_client(self, pool_name: str) -> redis.Redis:
        try:
            if pool_name not in self._connection_pools:
                pool_kwargs = self._config.to_connection_pool_kwargs()
                self._connection_pools[pool_name] = ConnectionPool(**pool_kwargs)

            client = redis.Redis(
                connection_pool=self._connection_pools[pool_name],
                **self._config.to_redis_kwargs(),
            )

            self._test_connection(client)
            logger.info(f"Created Redis client for pool: {pool_name}")
            return client

        except Exception as e:
            logger.error(f"Failed to create Redis client for pool {pool_name}: {e}")
            raise RedisConnectionError(f"Failed to create Redis client: {e}")

    def _test_connection(self, client: redis.Redis) -> None:
        try:
            client.ping()
        except Exception as e:
            raise RedisConnectionError(f"Redis connection test failed: {e}")

    def test_connection(self, pool_name: str = "default") -> bool:
        try:
            client = self.get_client(pool_name)
            self._test_connection(client)
            return True
        except Exception as e:
            logger.warning(f"Connection test failed for pool {pool_name}: {e}")
            return False

    def reconnect(self, pool_name: str = "default") -> bool:
        try:
            with self._lock:
                if pool_name in self._clients:
                    try:
                        self._clients[pool_name].close()
                    except Exception:
                        pass
                    del self._clients[pool_name]

                if pool_name in self._connection_pools:
                    try:
                        self._connection_pools[pool_name].disconnect()
                    except Exception:
                        pass
                    del self._connection_pools[pool_name]

                # Create new client
                self._clients[pool_name] = self._create_client(pool_name)
                logger.info(
                    f"Successfully reconnected Redis client for pool: {pool_name}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to reconnect Redis client for pool {pool_name}: {e}")
            return False

    def _start_health_check(self) -> None:
        if (
            self._health_check_thread is None
            or not self._health_check_thread.is_alive()
        ):
            self._health_check_running = True
            self._health_check_thread = threading.Thread(
                target=self._health_check_loop, daemon=True, name="RedisHealthCheck"
            )
            self._health_check_thread.start()
            logger.info("Started Redis health check thread")

    def _health_check_loop(self) -> None:
        while self._health_check_running:
            try:
                current_time = time.time()
                if (
                    current_time - self._last_health_check
                    >= self._config.health_check_interval
                ):
                    self._perform_health_check()
                    self._last_health_check = current_time

                time.sleep(min(5, self._config.health_check_interval))

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                time.sleep(5)

    def _perform_health_check(self) -> None:
        with self._lock:
            for pool_name in list(self._clients.keys()):
                try:
                    if not self.test_connection(pool_name):
                        logger.warning(
                            f"Health check failed for pool {pool_name}, attempting reconnection"
                        )
                        self.reconnect(pool_name)
                except Exception as e:
                    logger.error(f"Error during health check for pool {pool_name}: {e}")

    def close_all(self) -> None:
        self._health_check_running = False

        with self._lock:
            for pool_name, client in self._clients.items():
                try:
                    client.close()
                    logger.info(f"Closed Redis client for pool: {pool_name}")
                except Exception as e:
                    logger.error(
                        f"Error closing Redis client for pool {pool_name}: {e}"
                    )

            for pool_name, pool in self._connection_pools.items():
                try:
                    pool.disconnect()
                    logger.info(f"Disconnected connection pool: {pool_name}")
                except Exception as e:
                    logger.error(
                        f"Error disconnecting connection pool {pool_name}: {e}"
                    )

            self._clients.clear()
            self._connection_pools.clear()

    @contextmanager
    def get_connection(self, pool_name: str = "default"):
        client = None
        try:
            client = self.get_client(pool_name)
            yield client
        except Exception as e:
            logger.error(f"Error with Redis connection for pool {pool_name}: {e}")
            raise
        finally:
            pass


_factory: Optional[RedisClientFactory] = None


def get_redis_client(pool_name: str = "default") -> redis.Redis:
    global _factory
    if _factory is None:
        _factory = RedisClientFactory()
    return _factory.get_client(pool_name)


def test_redis_connection(pool_name: str = "default") -> bool:
    global _factory
    if _factory is None:
        _factory = RedisClientFactory()
    return _factory.test_connection(pool_name)


def close_all_redis_connections() -> None:
    global _factory
    if _factory is not None:
        _factory.close_all()
        _factory = None
