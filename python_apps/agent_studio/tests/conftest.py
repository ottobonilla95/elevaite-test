import os
import sys
import pytest
import logging
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlmodel import Session
from fastapi.testclient import TestClient

# Add agent-studio directory to Python path
agent_studio_dir = Path(__file__).parent.parent / "agent-studio"
sys.path.insert(0, str(agent_studio_dir))

from db.database import Base, get_db
from main import app

# Load test environment files from agent-studio directory
# Priority: .env.test.local (gitignored, your secrets) > .env.test (committed, safe defaults)
load_dotenv(agent_studio_dir / ".env.test")  # Load safe defaults first
load_dotenv(agent_studio_dir / ".env.test.local", override=True)  # Override with local secrets if exists

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
    """
    Create a SQLModel Session for testing.

    SQLModel Session has the .exec() method required by SDK services.
    This is different from regular SQLAlchemy sessions.
    """
    session = Session(test_engine)
    yield session
    session.close()

    # Clean up all tables after each test
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
def setup_test_environment():
    """
    Set up all environment variables needed for testing.
    This includes database, Redis, API keys (mock), and other service configurations.
    """
    test_env_vars = {
        # Database
        "SQLALCHEMY_DATABASE_URL": os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://elevaite:elevaite@localhost:5433/agent_studio",
        ),
        "AGENT_STUDIO_DATABASE_URL": os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://elevaite:elevaite@localhost:5433/agent_studio",
        ),
        "DB_POOL_SIZE": "5",
        "DB_MAX_OVERFLOW": "10",
        "DB_POOL_RECYCLE": "1800",
        "DB_POOL_TIMEOUT": "30",
        # Redis
        "REDIS_HOST": os.getenv("TEST_REDIS_HOST", "localhost"),
        "REDIS_PORT": os.getenv("TEST_REDIS_PORT", "6379"),
        "REDIS_DB": os.getenv("TEST_REDIS_DB", "1"),
        "REDIS_USERNAME": os.getenv("TEST_REDIS_USERNAME", ""),
        "REDIS_PASSWORD": os.getenv("TEST_REDIS_PASSWORD", ""),
        "REDIS_MAX_CONNECTIONS": "5",
        "REDIS_CONNECTION_TIMEOUT": "2",
        "REDIS_SOCKET_TIMEOUT": "2",
        # API Keys (use test/mock keys or empty strings)
        "OPENAI_API_KEY": os.getenv("TEST_OPENAI_API_KEY", "sk-test-mock-key"),
        "ANTHROPIC_API_KEY": os.getenv("TEST_ANTHROPIC_API_KEY", ""),
        "COHERE_API_KEY": os.getenv("TEST_COHERE_API_KEY", ""),
        "CO_API_KEY": os.getenv("TEST_CO_API_KEY", ""),
        "GEMINI_API_KEY": os.getenv("TEST_GEMINI_API_KEY", ""),
        # Google Services
        "CX_ID_PERSONAL": os.getenv("TEST_CX_ID_PERSONAL", ""),
        "GOOGLE_API_PERSONAL": os.getenv("TEST_GOOGLE_API_PERSONAL", ""),
        # AWS (for Bedrock)
        "AWS_ACCESS_KEY_ID": os.getenv("TEST_AWS_ACCESS_KEY_ID", ""),
        "AWS_SECRET_ACCESS_KEY": os.getenv("TEST_AWS_SECRET_ACCESS_KEY", ""),
        "AWS_DEFAULT_REGION": os.getenv("TEST_AWS_DEFAULT_REGION", "us-west-1"),
        # Other Services
        "WEATHER_API_KEY": os.getenv("TEST_WEATHER_API_KEY", ""),
        "QDRANT_HOST": os.getenv("TEST_QDRANT_HOST", "localhost"),
        "QDRANT_PORT": os.getenv("TEST_QDRANT_PORT", "6333"),
        "QDRANT_API_KEY": os.getenv("TEST_QDRANT_API_KEY", ""),
        # Application Settings
        "HOST": "localhost",
        "PORT": "8050",
        "ENVIRONMENT": "test",
        "SQL_ECHO": "false",
        # File Upload
        "UPLOAD_DIR": "test_uploads",
        "MAX_FILE_SIZE_BYTES": "52428800",
        # Disable external services in tests
        "OTLP_ENDPOINT": "",  # Disable OpenTelemetry
        "KUBERNETES_SERVICE_HOST": "",  # Not in Kubernetes
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
def mock_openai_client(monkeypatch):
    """
    Mock OpenAI client to prevent real API calls during tests.

    Usage:
        def test_something(test_client, mock_openai_client):
            # OpenAI calls will be mocked
            response = test_client.post("/api/agents/execute", ...)
    """
    import types

    class Delta:
        def __init__(self, content=None, tool_calls=None):
            self.content = content
            self.tool_calls = tool_calls or []

    class Choice:
        def __init__(self, delta=None, finish_reason=None):
            self.delta = delta or Delta()
            self.finish_reason = finish_reason

    class Chunk:
        def __init__(self, content=None, finish_reason=None, tool_calls=None):
            self.choices = [Choice(Delta(content, tool_calls), finish_reason)]

    class StreamResponse:
        def __iter__(self):
            # Simulate a simple streaming response
            yield Chunk(content="This ")
            yield Chunk(content="is ")
            yield Chunk(content="a ")
            yield Chunk(content="mocked ")
            yield Chunk(content="response.")
            yield Chunk(finish_reason="stop")

    mock_client = types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(
                create=lambda **kwargs: StreamResponse()
                if kwargs.get("stream")
                else types.SimpleNamespace(
                    choices=[
                        types.SimpleNamespace(
                            message=types.SimpleNamespace(content="This is a mocked response.", role="assistant")
                        )
                    ]
                )
            )
        )
    )

    # Try to patch common OpenAI client locations
    try:
        import utils

        monkeypatch.setattr(utils, "client", mock_client, raising=False)
    except (ImportError, AttributeError):
        pass

    try:
        from agents import utils as agent_utils

        monkeypatch.setattr(agent_utils, "client", mock_client, raising=False)
    except (ImportError, AttributeError):
        pass

    return mock_client


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
