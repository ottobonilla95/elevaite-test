import pytest
import uuid
from datetime import datetime

from redis_utils import RedisManager


@pytest.mark.integration
@pytest.mark.redis
def test_redis_stream_operations():
    redis_manager = RedisManager()

    stream_name = f"test_stream_{uuid.uuid4().hex}"

    try:
        # Create the stream
        redis_manager.create_stream(stream_name)

        # Check that the stream exists
        assert redis_manager.redis.exists(stream_name) == 1

        # Create a consumer group
        group_name = "test_group"
        redis_manager.create_consumer_group(stream_name, group_name)

        # Check that the consumer group exists
        groups = redis_manager.redis.xinfo_groups(stream_name)
        assert len(groups) == 1
        assert groups[0]["name"] == group_name

        # Publish a message
        message = {
            "type": "test",
            "content": "Hello, world!",
            "timestamp": datetime.now().isoformat(),
        }
        message_id = redis_manager.publish_message(stream_name, message)

        # Check that the message was published
        assert message_id is not None

        # Read the message
        messages = redis_manager.redis.xread({stream_name: "0"})
        assert len(messages) == 1
        assert len(messages[0][1]) >= 1

    finally:
        # Clean up
        redis_manager.redis.delete(stream_name)
