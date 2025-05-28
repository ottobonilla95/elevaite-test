import json
import uuid
import time
import threading
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, List
from datetime import datetime

import redis

from redis_config import get_redis_config
from redis_client import get_redis_client

logger = logging.getLogger(__name__)

T = TypeVar("T")
MessageHandler = Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]


class RedisManagerError(Exception):
    pass


class RedisManager:

    _instance: Optional["RedisManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "RedisManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RedisManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._config = get_redis_config()
        self._redis: Optional[redis.Redis] = None
        self._consumer_threads: Dict[str, threading.Thread] = {}
        self._consumer_stop_events: Dict[str, threading.Event] = {}
        self._connection_healthy = False
        self._last_connection_check = 0
        self._operation_lock = threading.Lock()

        self._initialize_connection()
        self._initialized = True

        logger.info("RedisManager initialized successfully")

    def _initialize_connection(self) -> None:
        try:
            self._redis = get_redis_client("agent_manager")
            self._test_connection()
            self._connection_healthy = True
            logger.info(
                f"Connected to Redis at {self._config.host}:{self._config.port}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            self._connection_healthy = False
            # Don't raise exception here - allow graceful degradation

    def _test_connection(self) -> None:
        try:
            if self._redis is None:
                raise RedisManagerError("Redis client not initialized")

            self._redis.ping()
            self._connection_healthy = True
            self._last_connection_check = time.time()

        except Exception as e:
            logger.warning(f"Redis connection test failed: {e}")
            self._connection_healthy = False
            raise RedisManagerError(f"Redis connection test failed: {e}")

    def _ensure_connection(self) -> redis.Redis:
        current_time = time.time()

        if (
            current_time - self._last_connection_check
        ) > self._config.health_check_interval:
            try:
                self._test_connection()
            except RedisManagerError:
                logger.info("Attempting to reconnect to Redis...")
                self._initialize_connection()

        if not self._connection_healthy or self._redis is None:
            raise RedisManagerError("Redis connection is not healthy")

        return self._redis

    @property
    def redis(self) -> redis.Redis:
        return self._ensure_connection()

    @property
    def is_connected(self) -> bool:
        try:
            self._test_connection()
            return True
        except Exception:
            return False

    def create_stream(self, stream_name: str) -> bool:
        if not stream_name or not stream_name.strip():
            logger.error("Stream name cannot be empty")
            return False

        try:
            with self._operation_lock:
                redis_client = self.redis

                if not redis_client.exists(stream_name):
                    dummy_data = {
                        "_created": datetime.now().isoformat(),
                        "_type": "stream_init",
                    }
                    redis_client.xadd(
                        stream_name,
                        dummy_data,  # type: ignore
                        maxlen=self._config.default_stream_max_len,
                    )
                    logger.info(f"Created Redis stream: {stream_name}")
                else:
                    logger.debug(f"Redis stream already exists: {stream_name}")

                return True

        except RedisManagerError as e:
            logger.error(
                f"Redis connection error while creating stream {stream_name}: {e}"
            )
            return False
        except Exception as e:
            logger.error(f"Error creating stream {stream_name}: {e}")
            return False

    def create_consumer_group(
        self, stream_name: str, group_name: Optional[str] = None
    ) -> bool:
        if not stream_name or not stream_name.strip():
            logger.error("Stream name cannot be empty")
            return False

        if group_name is None:
            group_name = self._config.default_consumer_group

        try:
            with self._operation_lock:
                if not self.create_stream(stream_name):
                    return False

                redis_client = self.redis

                try:
                    redis_client.xgroup_create(
                        stream_name,
                        group_name,
                        id="0",
                        mkstream=True,
                    )
                    logger.info(
                        f"Created consumer group '{group_name}' for stream '{stream_name}'"
                    )

                except Exception as e:
                    if "BUSYGROUP" in str(e):
                        logger.debug(
                            f"Consumer group '{group_name}' already exists for stream '{stream_name}'"
                        )
                    else:
                        logger.error(
                            f"Error creating consumer group '{group_name}': {e}"
                        )
                        return False

                return True

        except RedisManagerError as e:
            logger.error(f"Redis connection error while creating consumer group: {e}")
            return False
        except Exception as e:
            logger.error(
                f"Error creating consumer group {group_name} for stream {stream_name}: {e}"
            )
            return False

    def publish_message(
        self,
        stream_name: str,
        message: Dict[str, Any],
        priority: int = 0,
        correlation_id: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Optional[str]:
        if not stream_name or not stream_name.strip():
            logger.error("Stream name cannot be empty")
            return None

        if not isinstance(message, dict):
            logger.error("Message must be a dictionary")
            return None

        try:
            with self._operation_lock:
                if not self.create_stream(stream_name):
                    return None

                redis_client = self.redis
                msg_id = str(uuid.uuid4())
                timestamp = datetime.now().isoformat()

                full_message = {
                    "id": msg_id,
                    "timestamp": timestamp,
                    "priority": str(priority),
                    "correlation_id": correlation_id or msg_id,
                    "reply_to": reply_to or "",
                    "data": json.dumps(message, default=str),
                }

                redis_message = {
                    k: str(v) if v is not None else "" for k, v in full_message.items()
                }

                result = redis_client.xadd(
                    stream_name,
                    redis_message,  # type: ignore
                    maxlen=self._config.default_stream_max_len,
                )

                logger.debug(f"Published message {msg_id} to stream {stream_name}")
                return str(result) if result else None

        except RedisManagerError as e:
            logger.error(
                f"Redis connection error while publishing to {stream_name}: {e}"
            )
            return None
        except (TypeError, ValueError) as e:
            logger.error(f"Error serializing message data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error publishing message to stream {stream_name}: {e}")
            return None

    def consume_messages(
        self,
        stream_name: str,
        handler: MessageHandler,
        group_name: Optional[str] = None,
        consumer_name: Optional[str] = None,
        block_ms: Optional[int] = None,
        count: Optional[int] = None,
    ) -> bool:
        """
        Start consuming messages from a Redis stream.

        Args:
            stream_name: Name of the stream to consume from
            handler: Function to handle incoming messages
            group_name: Consumer group name
            consumer_name: Consumer name (auto-generated if None)
            block_ms: Blocking time in milliseconds
            count: Number of messages to read at once

        Returns:
            True if consumer started successfully, False otherwise
        """
        if not stream_name or not stream_name.strip():
            logger.error("Stream name cannot be empty")
            return False

        if not callable(handler):
            logger.error("Handler must be callable")
            return False

        if group_name is None:
            group_name = self._config.default_consumer_group
        if consumer_name is None:
            consumer_name = f"consumer_{uuid.uuid4().hex[:8]}"
        if block_ms is None:
            block_ms = self._config.default_block_ms
        if count is None:
            count = self._config.default_count

        try:
            if not self.create_consumer_group(stream_name, group_name):
                return False

            thread_key = f"{stream_name}:{group_name}:{consumer_name}"

            if (
                thread_key in self._consumer_threads
                and self._consumer_threads[thread_key].is_alive()
            ):
                logger.warning(f"Consumer {thread_key} is already running")
                return True

            stop_event = threading.Event()
            self._consumer_stop_events[thread_key] = stop_event

            thread = threading.Thread(
                target=self._consume_messages_loop,
                args=(
                    stream_name,
                    handler,
                    group_name,
                    consumer_name,
                    block_ms,
                    count,
                    stop_event,
                ),
                daemon=True,
                name=f"RedisConsumer-{thread_key}",
            )

            self._consumer_threads[thread_key] = thread
            thread.start()

            logger.info(f"Started consumer {thread_key}")
            return True

        except Exception as e:
            logger.error(f"Error starting consumer for stream {stream_name}: {e}")
            return False

    def _consume_messages_loop(
        self,
        stream_name: str,
        handler: MessageHandler,
        group_name: str,
        consumer_name: str,
        block_ms: int,
        count: int,
        stop_event: threading.Event,
    ) -> None:
        logger.info(
            f"Starting consumer loop for {stream_name}:{group_name}:{consumer_name}"
        )

        consecutive_errors = 0
        max_consecutive_errors = 5

        while not stop_event.is_set():
            try:
                if not self.is_connected:
                    logger.warning("Redis connection lost, attempting to reconnect...")
                    time.sleep(1)
                    continue

                streams = {stream_name: ">"}
                response = None

                try:
                    redis_client = self.redis
                    response = redis_client.xreadgroup(
                        groupname=group_name,
                        consumername=consumer_name,
                        streams=streams,  # type: ignore
                        count=count,
                        block=block_ms,
                    )
                    consecutive_errors = 0  # Reset error counter on success

                except RedisManagerError as e:
                    logger.warning(f"Redis connection error in consumer loop: {e}")
                    time.sleep(1)
                    continue
                except Exception as e:
                    consecutive_errors += 1
                    logger.warning(
                        f"Error reading from stream (attempt {consecutive_errors}): {e}"
                    )

                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(
                            f"Too many consecutive errors ({consecutive_errors}), stopping consumer"
                        )
                        break

                    time.sleep(min(consecutive_errors * 0.5, 5))  # Exponential backoff
                    continue

                # Process messages
                if response:
                    for stream_data in response:  # type: ignore
                        if len(stream_data) >= 2:
                            stream = stream_data[0]
                            messages = stream_data[1]

                            for message_id, message_data in messages:
                                if stop_event.is_set():
                                    break

                                try:
                                    message = {k: v for k, v in message_data.items()}

                                    if "data" in message:
                                        try:
                                            message["data"] = json.loads(
                                                message["data"]
                                            )
                                        except json.JSONDecodeError as e:
                                            logger.warning(
                                                f"Could not parse message data as JSON: {message['data']}, error: {e}"
                                            )

                                    result = handler(message)

                                    if result and message.get("reply_to"):
                                        reply_to = message.get("reply_to")
                                        if reply_to:
                                            self.publish_message(
                                                reply_to,
                                                result,
                                                correlation_id=message.get(
                                                    "correlation_id", ""
                                                ),
                                            )

                                    redis_client.xack(stream, group_name, message_id)  # type: ignore
                                    logger.debug(f"Processed message {message_id}")

                                except Exception as e:
                                    logger.error(
                                        f"Error processing message {message_id}: {e}"
                                    )

                try:
                    self._claim_pending_messages(
                        stream_name,
                        group_name,
                        consumer_name,
                        self._config.default_claim_min_idle_time,
                    )
                except Exception as e:
                    logger.warning(f"Error claiming pending messages: {e}")

            except Exception as e:
                consecutive_errors += 1
                logger.error(
                    f"Unexpected error in consumer loop (attempt {consecutive_errors}): {e}"
                )

                if consecutive_errors >= max_consecutive_errors:
                    logger.error(
                        f"Too many consecutive errors ({consecutive_errors}), stopping consumer"
                    )
                    break

                time.sleep(min(consecutive_errors, 5))

        logger.info(
            f"Consumer loop stopped for {stream_name}:{group_name}:{consumer_name}"
        )

    def _claim_pending_messages(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        min_idle_time: int,
    ) -> None:
        try:
            redis_client = self.redis

            pending = redis_client.xpending(stream_name, group_name)

            if (
                pending
                and isinstance(pending, list)
                and len(pending) > 0
                and pending[0] > 0
            ):
                pending_messages = redis_client.xpending_range(
                    stream_name, group_name, min="-", max="+", count=10
                )

                if (
                    pending_messages
                    and isinstance(pending_messages, list)
                    and len(pending_messages) > 0
                ):
                    message_ids = []
                    for msg in pending_messages:
                        if (
                            isinstance(msg, list)
                            and len(msg) >= 3
                            and msg[2] >= min_idle_time
                        ):
                            message_ids.append(msg[0])

                    if message_ids:
                        claimed = redis_client.xclaim(
                            stream_name,
                            group_name,
                            consumer_name,
                            min_idle_time,
                            message_ids,
                        )
                        if claimed:
                            try:
                                claimed_count = len(claimed)  # type: ignore
                                logger.debug(
                                    f"Claimed {claimed_count} pending messages for {consumer_name}"
                                )
                            except (TypeError, AttributeError):
                                logger.debug(
                                    f"Claimed pending messages for {consumer_name}"
                                )

        except RedisManagerError as e:
            logger.warning(
                f"Redis connection error while claiming pending messages: {e}"
            )
        except Exception as e:
            if "NOGROUP" not in str(e) and "no such key" not in str(e).lower():
                logger.warning(f"Error claiming pending messages: {e}")

    def stop_consumer(
        self,
        stream_name: str,
        group_name: Optional[str] = None,
        consumer_name: Optional[str] = None,
    ) -> bool:
        """
        Stop a specific consumer or all consumers for a stream.

        Args:
            stream_name: Name of the stream
            group_name: Consumer group name (None for all groups)
            consumer_name: Consumer name (None for all consumers in group)

        Returns:
            True if consumers were stopped, False otherwise
        """
        try:
            if group_name is None:
                group_name = self._config.default_consumer_group

            stopped_count = 0

            for thread_key, thread in list(self._consumer_threads.items()):
                key_parts = thread_key.split(":")
                if len(key_parts) >= 3:
                    t_stream, t_group, t_consumer = (
                        key_parts[0],
                        key_parts[1],
                        key_parts[2],
                    )

                    if (
                        t_stream == stream_name
                        and t_group == group_name
                        and (consumer_name is None or t_consumer == consumer_name)
                    ):
                        if thread_key in self._consumer_stop_events:
                            self._consumer_stop_events[thread_key].set()

                        if thread.is_alive():
                            thread.join(timeout=5)

                        if thread_key in self._consumer_threads:
                            del self._consumer_threads[thread_key]
                        if thread_key in self._consumer_stop_events:
                            del self._consumer_stop_events[thread_key]

                        stopped_count += 1
                        logger.info(f"Stopped consumer: {thread_key}")

            return stopped_count > 0

        except Exception as e:
            logger.error(f"Error stopping consumers: {e}")
            return False

    def stop_all_consumers(self) -> None:
        logger.info("Stopping all Redis consumers...")

        for stop_event in self._consumer_stop_events.values():
            stop_event.set()

        for thread_key, thread in list(self._consumer_threads.items()):
            if thread.is_alive():
                thread.join(timeout=5)
                if thread.is_alive():
                    logger.warning(
                        f"Consumer thread {thread_key} did not stop gracefully"
                    )

        self._consumer_threads.clear()
        self._consumer_stop_events.clear()

        logger.info("All Redis consumers stopped")

    def request_reply(
        self,
        request_stream: str,
        message: Dict[str, Any],
        timeout: int = 5,
        priority: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        Send a request message and wait for a reply using request-reply pattern.

        Args:
            request_stream: Stream to send the request to
            message: Request message data
            timeout: Timeout in seconds to wait for reply
            priority: Message priority

        Returns:
            Reply data if received within timeout, None otherwise
        """
        if not request_stream or not request_stream.strip():
            logger.error("Request stream name cannot be empty")
            return None

        if not isinstance(message, dict):
            logger.error("Message must be a dictionary")
            return None

        reply_stream = None
        try:
            correlation_id = str(uuid.uuid4())
            reply_stream = f"reply:{correlation_id}"

            if not self.create_stream(reply_stream):
                return None
            if not self.create_consumer_group(reply_stream):
                return None

            response: Optional[Dict[str, Any]] = None
            response_event = threading.Event()

            def reply_handler(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                nonlocal response
                try:
                    if msg.get("correlation_id") == correlation_id:
                        response = msg.get("data")
                        response_event.set()
                        logger.debug(
                            f"Received reply for correlation_id: {correlation_id}"
                        )
                except Exception as e:
                    logger.error(f"Error in reply handler: {e}")
                return None

            if not self.consume_messages(
                reply_stream,
                reply_handler,
                consumer_name=f"reply_consumer_{correlation_id[:8]}",
            ):
                return None

            message_id = self.publish_message(
                request_stream,
                message,
                priority=priority,
                correlation_id=correlation_id,
                reply_to=reply_stream,
            )

            if not message_id:
                logger.error("Failed to publish request message")
                return None

            logger.debug(
                f"Sent request {correlation_id} to {request_stream}, waiting for reply..."
            )

            # Wait for response
            if response_event.wait(timeout):
                logger.debug(f"Received reply for request {correlation_id}")
                return response
            else:
                logger.warning(f"Timeout waiting for reply to {correlation_id}")
                return None

        except Exception as e:
            logger.error(f"Error in request-reply: {e}")
            return None
        finally:
            try:
                if reply_stream:
                    self.stop_consumer(reply_stream)
                    redis_client = self.redis
                    redis_client.delete(reply_stream)
                    logger.debug(f"Cleaned up reply stream: {reply_stream}")
            except Exception as e:
                logger.warning(f"Error cleaning up reply stream: {e}")

    def get_stream_info(self, stream_name: str) -> Optional[Dict[str, Any]]:
        try:
            redis_client = self.redis
            info = redis_client.xinfo_stream(stream_name)
            return info  # type: ignore
        except Exception as e:
            logger.error(f"Error getting stream info for {stream_name}: {e}")
            return None

    def get_consumer_groups(self, stream_name: str) -> List[Dict[str, Any]]:
        try:
            redis_client = self.redis
            groups = redis_client.xinfo_groups(stream_name)
            return groups  # type: ignore
        except Exception as e:
            logger.error(f"Error getting consumer groups for {stream_name}: {e}")
            return []

    def cleanup(self) -> None:
        logger.info("Cleaning up RedisManager...")
        self.stop_all_consumers()


redis_manager = RedisManager()
