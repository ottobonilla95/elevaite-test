import pytest
import uuid
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional

from redis_utils import RedisManager


@pytest.fixture(scope="module")
def redis_manager():
    manager = RedisManager()

    if not manager.is_connected:
        pytest.skip("Redis is not available for integration tests")

    yield manager

    manager.cleanup()


@pytest.mark.integration
@pytest.mark.redis
class TestRedisIntegration:
    def test_redis_connection(self, redis_manager):
        assert redis_manager.is_connected is True
        redis_client = redis_manager.redis
        assert redis_client.ping() is True

    def test_stream_lifecycle(self, redis_manager):
        stream_name = f"test_stream_{uuid.uuid4().hex}"

        try:
            assert redis_manager.create_stream(stream_name) is True
            assert redis_manager.redis.exists(stream_name) == 1

            group_name = "test_group"
            assert redis_manager.create_consumer_group(stream_name, group_name) is True

            groups = redis_manager.get_consumer_groups(stream_name)
            assert len(groups) >= 1
            group_names = [group["name"] for group in groups]
            assert group_name in group_names

            stream_info = redis_manager.get_stream_info(stream_name)
            assert stream_info is not None
            assert "length" in stream_info

        finally:
            redis_manager.stop_all_consumers()
            redis_manager.redis.delete(stream_name)

    def test_message_publishing_and_reading(self, redis_manager):
        stream_name = f"test_stream_{uuid.uuid4().hex}"

        try:
            message = {
                "type": "test",
                "content": "Hello, world!",
                "timestamp": datetime.now().isoformat(),
                "number": 42,
                "boolean": True,
            }
            message_id = redis_manager.publish_message(stream_name, message)
            assert message_id is not None

            messages = redis_manager.redis.xread({stream_name: "0"}, block=1000)
            assert len(messages) == 1
            assert len(messages[0][1]) >= 1

            stream_data = messages[0][1]
            published_message = stream_data[-1][1]
            assert "data" in published_message

            import json

            decoded_data = json.loads(published_message["data"])
            assert decoded_data["type"] == "test"
            assert decoded_data["content"] == "Hello, world!"
            assert decoded_data["number"] == 42
            assert decoded_data["boolean"] is True

        finally:
            redis_manager.redis.delete(stream_name)

    def test_consumer_message_processing(self, redis_manager):
        stream_name = f"test_stream_{uuid.uuid4().hex}"
        group_name = "test_group"

        received_messages = []
        message_event = threading.Event()

        def message_handler(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            received_messages.append(message)
            message_event.set()
            return {"status": "processed", "original_id": message.get("id")}

        try:
            assert redis_manager.consume_messages(
                stream_name, message_handler, group_name, consumer_name="test_consumer"
            )

            time.sleep(0.1)

            test_message = {
                "type": "test_consumer",
                "content": "Consumer test message",
                "test_id": str(uuid.uuid4()),
            }
            message_id = redis_manager.publish_message(stream_name, test_message)
            assert message_id is not None

            assert message_event.wait(timeout=5) is True

            assert len(received_messages) == 1
            received = received_messages[0]
            assert "data" in received
            assert received["data"]["type"] == "test_consumer"
            assert received["data"]["content"] == "Consumer test message"

        finally:
            redis_manager.stop_consumer(stream_name, group_name, "test_consumer")
            redis_manager.redis.delete(stream_name)

    def test_request_reply_pattern(self, redis_manager):
        request_stream = f"request_stream_{uuid.uuid4().hex}"

        def request_handler(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            data = message.get("data", {})
            if data.get("type") == "ping":
                return {
                    "type": "pong",
                    "original_message": data.get("message", ""),
                    "timestamp": datetime.now().isoformat(),
                }
            return None

        try:
            assert redis_manager.consume_messages(
                request_stream,
                request_handler,
                "request_group",
                consumer_name="responder",
            )

            time.sleep(0.1)

            request_message = {
                "type": "ping",
                "message": "Hello from test",
                "request_id": str(uuid.uuid4()),
            }

            reply = redis_manager.request_reply(
                request_stream, request_message, timeout=5
            )

            assert reply is not None
            assert reply["type"] == "pong"
            assert reply["original_message"] == "Hello from test"
            assert "timestamp" in reply

        finally:
            redis_manager.stop_consumer(request_stream, "request_group", "responder")
            redis_manager.redis.delete(request_stream)

    def test_multiple_consumers(self, redis_manager):
        stream_name = f"test_stream_{uuid.uuid4().hex}"
        group_name = "multi_consumer_group"

        consumer1_messages = []
        consumer2_messages = []

        def consumer1_handler(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            consumer1_messages.append(message)
            return None

        def consumer2_handler(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            consumer2_messages.append(message)
            return None

        try:
            assert redis_manager.consume_messages(
                stream_name, consumer1_handler, group_name, consumer_name="consumer1"
            )

            assert redis_manager.consume_messages(
                stream_name, consumer2_handler, group_name, consumer_name="consumer2"
            )

            time.sleep(0.1)

            num_messages = 10
            for i in range(num_messages):
                message = {
                    "type": "multi_test",
                    "message_number": i,
                    "content": f"Message {i}",
                }
                redis_manager.publish_message(stream_name, message)

            time.sleep(2)

            total_received = len(consumer1_messages) + len(consumer2_messages)
            assert total_received == num_messages
            assert len(consumer1_messages) > 0 or len(consumer2_messages) > 0

        finally:
            redis_manager.stop_consumer(stream_name, group_name, "consumer1")
            redis_manager.stop_consumer(stream_name, group_name, "consumer2")
            redis_manager.redis.delete(stream_name)

    def test_error_handling_and_recovery(self, redis_manager):
        stream_name = f"test_stream_{uuid.uuid4().hex}"
        group_name = "error_test_group"

        error_count = 0
        processed_count = 0

        def error_prone_handler(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            nonlocal error_count, processed_count
            data = message.get("data", {})
            if data.get("should_error", False):
                error_count += 1
                raise Exception("Simulated processing error")
            else:
                processed_count += 1
                return {"status": "success"}

        try:
            assert redis_manager.consume_messages(
                stream_name,
                error_prone_handler,
                group_name,
                consumer_name="error_consumer",
            )

            time.sleep(0.1)

            for i in range(3):
                redis_manager.publish_message(
                    stream_name, {"should_error": True, "id": i}
                )

            for i in range(3):
                redis_manager.publish_message(
                    stream_name, {"should_error": False, "id": i}
                )

            time.sleep(2)

            assert processed_count == 3

        finally:
            redis_manager.stop_consumer(stream_name, group_name, "error_consumer")
            redis_manager.redis.delete(stream_name)
