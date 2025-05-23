import pytest
from redis_utils import RedisManager


@pytest.mark.unit
def test_redis_manager_initialization():
    manager = RedisManager()
    assert manager is not None
    assert hasattr(manager, "redis")
