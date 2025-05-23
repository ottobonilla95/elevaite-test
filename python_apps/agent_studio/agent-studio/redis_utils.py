import os
import json
import uuid
import time
import threading
from typing import Any, Callable, Dict, Optional, TypeVar
from datetime import datetime

import redis
from dotenv import load_dotenv

T = TypeVar("T")
MessageHandler = Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]

# Constants for Redis Streams
DEFAULT_STREAM_MAX_LEN = 1000  # Maximum number of messages in a stream
DEFAULT_STREAM_GROUP = "agent_group"  # Default consumer group
DEFAULT_CONSUMER_NAME = "agent_consumer"  # Default consumer name
DEFAULT_BLOCK_MS = 2000  # Default blocking time in milliseconds
DEFAULT_COUNT = 10  # Default number of messages to read at once
DEFAULT_CLAIM_MIN_IDLE_TIME = (
    30000  # Default minimum idle time for claiming messages (ms)
)


class RedisManager:
    """
    Manages Redis connections and provides methods for agent communication.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RedisManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        load_dotenv()

        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_username = os.getenv("REDIS_USERNAME", "elevaite")
        redis_password = os.getenv("REDIS_PASSWORD", "")

        try:
            # Try with username/password first
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                username=redis_username,
                password=redis_password,
                decode_responses=True,
            )
            self.redis.ping()
            print(f"Connected to Redis at {redis_host}:{redis_port} with username")
        except Exception as e:
            print(f"Error connecting with username: {e}")
            # Try again without username/password
            try:
                self.redis = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                )
                self.redis.ping()
                print(
                    f"Connected to Redis at {redis_host}:{redis_port} without username"
                )
            except Exception as e:
                print(f"Error connecting without username: {e}")
                print(
                    "WARNING: Could not connect to Redis. Agent communication will not work."
                )

        self.consumer_threads = {}
        self._initialized = True

    def create_stream(self, stream_name: str) -> bool:
        """
        Creates a stream if it doesn't exist by adding a dummy message.
        Returns True if successful, False otherwise.
        """
        try:
            # Check if stream exists
            if not self.redis.exists(stream_name):
                # Add a dummy message to create the stream
                dummy_data = {"_created": datetime.now().isoformat()}
                self.redis.xadd(
                    stream_name,
                    dummy_data,  # type: ignore
                    maxlen=DEFAULT_STREAM_MAX_LEN,
                )
            return True
        except Exception as e:
            print(f"Error creating stream {stream_name}: {e}")
            return False

    def create_consumer_group(
        self, stream_name: str, group_name: str = DEFAULT_STREAM_GROUP
    ) -> bool:
        try:
            self.create_stream(stream_name)

            try:
                self.redis.xgroup_create(
                    stream_name,
                    group_name,
                    id="0",
                    mkstream=True,
                )
            except Exception as e:
                if "BUSYGROUP" not in str(e):
                    print(f"Error creating consumer group: {e}")
                    return False

            return True
        except Exception as e:
            print(
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
        try:
            self.create_stream(stream_name)

            msg_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            full_message = {
                "id": msg_id,
                "timestamp": timestamp,
                "priority": str(priority),
                "correlation_id": correlation_id or msg_id,
                "reply_to": reply_to or "",
                "data": json.dumps(message),
            }

            # Convert all values to strings for Redis compatibility
            redis_message = {
                k: str(v) if v is not None else "" for k, v in full_message.items()
            }

            result = self.redis.xadd(
                stream_name,
                redis_message,  # type: ignore
                maxlen=DEFAULT_STREAM_MAX_LEN,
            )

            return str(result) if result else None
        except Exception as e:
            print(f"Error publishing message to stream {stream_name}: {e}")
            return None

    def consume_messages(
        self,
        stream_name: str,
        handler: MessageHandler,
        group_name: str = DEFAULT_STREAM_GROUP,
        consumer_name: Optional[str] = None,
        block_ms: int = DEFAULT_BLOCK_MS,
        count: int = DEFAULT_COUNT,
    ) -> None:
        if consumer_name is None:
            consumer_name = f"{DEFAULT_CONSUMER_NAME}_{uuid.uuid4().hex[:8]}"

        self.create_consumer_group(stream_name, group_name)

        thread_key = f"{stream_name}:{group_name}:{consumer_name}"
        if (
            thread_key in self.consumer_threads
            and self.consumer_threads[thread_key].is_alive()
        ):
            print(f"Consumer {thread_key} is already running")
            return

        thread = threading.Thread(
            target=self._consume_messages_loop,
            args=(stream_name, handler, group_name, consumer_name, block_ms, count),
            daemon=True,
        )
        self.consumer_threads[thread_key] = thread
        thread.start()

    def _consume_messages_loop(
        self,
        stream_name: str,
        handler: MessageHandler,
        group_name: str,
        consumer_name: str,
        block_ms: int,
        count: int,
    ) -> None:
        while True:
            try:
                streams = {stream_name: ">"}
                response = None

                try:
                    response = self.redis.xreadgroup(
                        groupname=group_name,
                        consumername=consumer_name,
                        streams=streams,  # type: ignore
                        count=count,
                        block=block_ms,
                    )
                except Exception:
                    time.sleep(0.1)
                    continue

                # Cast response to Any to avoid type checking issues
                if response:
                    for stream_data in response:  # type: ignore
                        if len(stream_data) >= 2:
                            stream = stream_data[0]
                            messages = stream_data[1]

                            for message_id, message_data in messages:
                                try:
                                    message = {k: v for k, v in message_data.items()}
                                    if "data" in message:
                                        try:
                                            message["data"] = json.loads(
                                                message["data"]
                                            )
                                        except json.JSONDecodeError:
                                            print(
                                                f"Warning: Could not parse message data as JSON: {message['data']}"
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

                                    self.redis.xack(stream, group_name, message_id)  # type: ignore
                                except Exception as e:
                                    print(f"Error processing message {message_id}: {e}")

                self._claim_pending_messages(
                    stream_name, group_name, consumer_name, DEFAULT_CLAIM_MIN_IDLE_TIME
                )

            except Exception as e:
                pass
                time.sleep(1)

    def _claim_pending_messages(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        min_idle_time: int,
    ) -> None:
        try:
            try:
                pending = self.redis.xpending(stream_name, group_name)

                if (
                    pending
                    and isinstance(pending, list)
                    and len(pending) > 0
                    and pending[0] > 0
                ):
                    pending_messages = self.redis.xpending_range(
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
                            self.redis.xclaim(
                                stream_name,
                                group_name,
                                consumer_name,
                                min_idle_time,
                                message_ids,
                            )
            except Exception as e:
                pass
        except Exception as e:
            if "NOGROUP" not in str(e) and "no such key" not in str(e).lower():
                print(f"Error claiming pending messages: {e}")

    def request_reply(
        self,
        request_stream: str,
        message: Dict[str, Any],
        timeout: int = 5,
        priority: int = 0,
    ) -> Optional[Dict[str, Any]]:
        reply_stream = None
        try:
            correlation_id = str(uuid.uuid4())
            reply_stream = f"reply:{correlation_id}"

            self.create_stream(reply_stream)
            self.create_consumer_group(reply_stream)

            response: Optional[Dict[str, Any]] = None
            response_event = threading.Event()

            def reply_handler(msg):
                nonlocal response
                if msg.get("correlation_id") == correlation_id:
                    response = msg.get("data")
                    response_event.set()
                return None

            self.consume_messages(
                reply_stream,
                reply_handler,
                consumer_name=f"reply_consumer_{correlation_id[:8]}",
            )

            self.publish_message(
                request_stream,
                message,
                priority=priority,
                correlation_id=correlation_id,
                reply_to=reply_stream,
            )

            if response_event.wait(timeout):
                return response
            else:
                print(f"Timeout waiting for reply to {correlation_id}")
                return None

        except Exception as e:
            print(f"Error in request-reply: {e}")
            return None
        finally:
            try:
                if reply_stream:
                    self.redis.delete(reply_stream)
            except Exception:
                pass


redis_manager = RedisManager()
