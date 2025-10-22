import pytest
from unittest.mock import Mock, patch
from redis_utils import RedisManager


@pytest.mark.unit
class TestRedisManager:
    def test_redis_manager_singleton(self):
        manager1 = RedisManager()
        manager2 = RedisManager()
        assert manager1 is manager2

    @patch("redis_utils.get_redis_client")
    def test_redis_manager_initialization(self, mock_get_client):
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_get_client.return_value = mock_redis

        manager = RedisManager()
        assert manager is not None
        assert hasattr(manager, "_redis")

    @patch("redis_utils.get_redis_client")
    def test_connection_health_check(self, mock_get_client):
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_get_client.return_value = mock_redis

        manager = RedisManager()
        assert manager.is_connected is True

        mock_redis.ping.side_effect = Exception("Connection failed")
        assert manager.is_connected is False

    @patch("redis_utils.get_redis_client")
    def test_create_stream_success(self, mock_get_client):
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.exists.return_value = False
        mock_redis.xadd.return_value = "1234567890-0"
        mock_get_client.return_value = mock_redis

        manager = RedisManager()
        result = manager.create_stream("test_stream")

        assert result is True
        mock_redis.exists.assert_called_once_with("test_stream")
        mock_redis.xadd.assert_called_once()

    @patch("redis_utils.get_redis_client")
    def test_create_stream_already_exists(self, mock_get_client):
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.exists.return_value = True
        mock_get_client.return_value = mock_redis

        manager = RedisManager()
        result = manager.create_stream("existing_stream")

        assert result is True
        mock_redis.exists.assert_called_once_with("existing_stream")
        mock_redis.xadd.assert_not_called()

    @patch("redis_utils.get_redis_client")
    def test_create_stream_invalid_name(self, mock_get_client):
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_get_client.return_value = mock_redis

        manager = RedisManager()

        assert manager.create_stream("") is False
        assert manager.create_stream("   ") is False
        assert manager.create_stream("") is False

    @patch("redis_utils.get_redis_client")
    def test_create_consumer_group_success(self, mock_get_client):
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.exists.return_value = True
        mock_redis.xgroup_create.return_value = True
        mock_get_client.return_value = mock_redis

        manager = RedisManager()
        result = manager.create_consumer_group("test_stream", "test_group")

        assert result is True
        mock_redis.xgroup_create.assert_called_once()

    @patch("redis_utils.get_redis_client")
    def test_create_consumer_group_already_exists(self, mock_get_client):
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.exists.return_value = True
        mock_redis.xgroup_create.side_effect = Exception(
            "BUSYGROUP Consumer Group name already exists"
        )
        mock_get_client.return_value = mock_redis

        manager = RedisManager()
        result = manager.create_consumer_group("test_stream", "existing_group")

        assert result is True  # Should succeed even if group exists

    @patch("redis_utils.get_redis_client")
    def test_publish_message_success(self, mock_get_client):
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.exists.return_value = True
        mock_redis.xadd.return_value = "1234567890-0"
        mock_get_client.return_value = mock_redis

        manager = RedisManager()
        message = {"type": "test", "content": "hello"}
        result = manager.publish_message("test_stream", message)

        assert result is not None
        mock_redis.xadd.assert_called_once()

    @patch("redis_utils.get_redis_client")
    def test_publish_message_invalid_input(self, mock_get_client):
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_get_client.return_value = mock_redis

        manager = RedisManager()

        assert manager.publish_message("", {"test": "data"}) is None
        assert manager.publish_message("test_stream", {}) is None
