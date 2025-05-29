import os
import pytest
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from db.database import Base, get_db
from main import app

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logging.getLogger("redis").setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def test_db_url() -> str:
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://elevaite:elevaite@localhost:5433/agent_studio",
    )


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    engine = create_engine(test_db_url)

    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    yield engine


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    yield session
    session.close()

    with test_engine.connect() as connection:
        trans = connection.begin()
        try:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())
            trans.commit()
        except Exception:
            trans.rollback()
            raise


@pytest.fixture(scope="function")
def test_client(test_db_session):
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_prompt_data():
    return {
        "prompt_label": "Test Prompt",
        "prompt": "You are a test agent.",
        "unique_label": "TestPrompt",
        "app_name": "test_app",
        "version": "1.0",
        "ai_model_provider": "OpenAI",
        "ai_model_name": "gpt-4",
        "tags": ["test"],
        "hyper_parameters": {"temperature": "0.7"},
        "variables": {"test_var": "test_value"},
    }


@pytest.fixture
def sample_agent_data():
    return {
        "name": "TestAgent",
        "persona": "Helper",
        "functions": [],
        "routing_options": {"respond": "Respond directly"},
        "short_term_memory": True,
        "long_term_memory": False,
        "reasoning": False,
        "input_type": ["text"],
        "output_type": ["text"],
        "response_type": "json",
        "max_retries": 3,
        "timeout": None,
        "deployed": False,
        "status": "active",
        "priority": None,
        "failure_strategies": ["retry"],
        "collaboration_mode": "single",
        "deployment_code": "t",
        "available_for_deployment": True,
    }


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "redis: mark test as requiring Redis")
    config.addinivalue_line("markers", "slow: mark test as slow running")


@pytest.fixture(scope="session", autouse=True)
def setup_redis_test_environment():
    test_env_vars = {
        "REDIS_HOST": os.getenv("TEST_REDIS_HOST", "localhost"),
        "REDIS_PORT": os.getenv("TEST_REDIS_PORT", "6379"),
        "REDIS_DB": os.getenv("TEST_REDIS_DB", "1"),
        "REDIS_USERNAME": os.getenv("TEST_REDIS_USERNAME", ""),
        "REDIS_PASSWORD": os.getenv("TEST_REDIS_PASSWORD", ""),
        "REDIS_MAX_CONNECTIONS": "5",
        "REDIS_CONNECTION_TIMEOUT": "2",
        "REDIS_SOCKET_TIMEOUT": "2",
    }

    original_values = {}
    for key, value in test_env_vars.items():
        original_values[key] = os.getenv(key)
        os.environ[key] = value

    yield

    for key, original_value in original_values.items():
        if original_value is not None:
            os.environ[key] = original_value
        elif key in os.environ:
            del os.environ[key]


@pytest.fixture
def redis_test_config():
    from redis_config import RedisConfig

    return RedisConfig(
        host=os.getenv("TEST_REDIS_HOST", "localhost"),
        port=int(os.getenv("TEST_REDIS_PORT", "6379")),
        db=int(os.getenv("TEST_REDIS_DB", "1")),
        username=os.getenv("TEST_REDIS_USERNAME") or None,
        password=os.getenv("TEST_REDIS_PASSWORD") or None,
        max_connections=5,
        connection_timeout=2,
        socket_timeout=2,
    )


@pytest.fixture
def clean_redis_state():
    from redis_utils import RedisManager

    manager = RedisManager()

    if manager.is_connected:
        redis_client = manager.redis
        try:
            test_keys = list(redis_client.keys("test_stream_*"))  # type: ignore
            reply_keys = list(redis_client.keys("reply:*"))  # type: ignore
            test_keys.extend(reply_keys)

            if test_keys:
                redis_client.delete(*test_keys)
        except Exception:
            pass

    yield

    # Clean up after test
    if manager.is_connected:
        redis_client = manager.redis
        try:
            test_keys = list(redis_client.keys("test_stream_*"))  # type: ignore
            reply_keys = list(redis_client.keys("reply:*"))  # type: ignore
            test_keys.extend(reply_keys)

            if test_keys:
                redis_client.delete(*test_keys)
        except Exception:
            pass


def pytest_runtest_setup(item):
    if item.get_closest_marker("redis"):
        from redis_utils import RedisManager

        manager = RedisManager()
        if not manager.is_connected:
            pytest.skip("Redis is not available")


def pytest_runtest_teardown(item):
    if item.get_closest_marker("redis"):
        try:
            from redis_utils import redis_manager

            redis_manager.stop_all_consumers()
        except Exception:
            pass
