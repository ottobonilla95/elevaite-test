import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from db.database import Base, get_db
from main import app


@pytest.fixture(scope="session")
def test_db_url() -> str:
    return "sqlite:///./test_agent_studio.db"


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    try:
        os.remove("./test_agent_studio.db")
    except FileNotFoundError:
        pass


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    yield session
    session.close()
    for table in reversed(Base.metadata.sorted_tables):
        test_engine.execute(table.delete())


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
