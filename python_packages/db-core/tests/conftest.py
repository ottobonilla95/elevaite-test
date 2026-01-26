"""
Test fixtures for db-core package tests.
"""

import asyncio
import logging
import os

import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from starlette.testclient import TestClient

from db_core import Base, MultitenancySettings, TenantMiddleware, init_db
from db_core.utils import (
    async_create_tenant_schema,
    create_tenant_schema,
    get_schema_name,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sync and async database URLs for testing
SYNC_TEST_DB_URL = os.environ.get(
    "TEST_DB_URL", "postgresql://postgres:postgres@localhost:5433/db_core_test"
)
ASYNC_TEST_DB_URL = os.environ.get(
    "TEST_ASYNC_DB_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/db_core_test",
)

# Log the database URLs being used
logger.info(f"Using sync database URL: {SYNC_TEST_DB_URL}")
logger.info(f"Using async database URL: {ASYNC_TEST_DB_URL}")

# Test tenant IDs
TEST_TENANTS = ["tenant1", "tenant2", "admin"]


# Define test models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def multitenancy_settings() -> MultitenancySettings:
    """Create multitenancy settings for testing."""
    return MultitenancySettings(
        db_url=SYNC_TEST_DB_URL,
        tenant_id_header="X-Tenant-ID",
        schema_prefix="test_tenant_",
        default_tenant_id=None,
        admin_tenant_id="admin",
        auto_create_tenant_schema=True,
        case_sensitive_tenant_id=False,
        tenant_id_validation_pattern=r"^[a-zA-Z0-9_-]+$",
        db_pool_size=2,
        db_max_overflow=5,
        db_pool_timeout=10,
        db_pool_recycle=300,
    )


# Removed row-level strategy fixture as we only support schema-level multitenancy


@pytest.fixture(scope="function")
def db_engine():
    """Create a database engine for testing."""
    engine = create_engine(
        SYNC_TEST_DB_URL,
        poolclass=NullPool,  # Use NullPool to avoid hanging connections between tests
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def db_engine_session():
    """Create a database engine for session-scoped tests."""
    engine = create_engine(
        SYNC_TEST_DB_URL,
        poolclass=NullPool,
    )
    yield engine
    engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_db_engine():
    """Create an async database engine for testing."""
    engine = create_async_engine(
        ASYNC_TEST_DB_URL,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
def setup_db(db_engine, multitenancy_settings):
    """Setup the database for testing."""
    # Create tables in public schema
    Base.metadata.create_all(db_engine)

    # Create tenant schemas
    for tenant_id in TEST_TENANTS:
        schema_name = get_schema_name(tenant_id, multitenancy_settings)
        create_tenant_schema(db_engine, schema_name)

        # Create tables in tenant schema
        with db_engine.connect() as conn:
            conn.execute(text(f'SET search_path TO "{schema_name}"'))
            Base.metadata.create_all(conn)

    yield

    # Drop tenant schemas
    for tenant_id in TEST_TENANTS:
        schema_name = get_schema_name(tenant_id, multitenancy_settings)
        with db_engine.connect() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))

    # Drop tables in public schema
    Base.metadata.drop_all(db_engine)


@pytest_asyncio.fixture(scope="function")
async def setup_async_db(async_db_engine, multitenancy_settings):
    """Setup the database for async testing."""
    # Create tables in public schema (need to use sync engine for this)
    sync_engine = create_engine(SYNC_TEST_DB_URL, poolclass=NullPool)
    Base.metadata.create_all(sync_engine)

    # Create tenant schemas
    for tenant_id in TEST_TENANTS:
        schema_name = get_schema_name(tenant_id, multitenancy_settings)
        await async_create_tenant_schema(async_db_engine, schema_name)

        # Create tables in tenant schema (need to use sync engine for this)
        with sync_engine.connect() as conn:
            conn.execute(text(f'SET search_path TO "{schema_name}"'))
            Base.metadata.create_all(conn)

    yield

    # Drop tenant schemas
    for tenant_id in TEST_TENANTS:
        schema_name = get_schema_name(tenant_id, multitenancy_settings)
        async with async_db_engine.connect() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))

    # Drop tables in public schema
    Base.metadata.drop_all(sync_engine)
    sync_engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Create a SQLAlchemy session for testing."""
    connection = db_engine.connect()
    transaction = connection.begin()

    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest_asyncio.fixture
async def async_db_session(async_db_engine):
    """Create an async SQLAlchemy session for testing."""
    async with async_db_engine.connect() as connection:
        transaction = await connection.begin()

        async_session = AsyncSession(bind=connection, expire_on_commit=False)

        yield async_session

        await async_session.close()
        await transaction.rollback()


@pytest.fixture
def init_db_config(multitenancy_settings, db_engine):
    """Initialize the database configuration for testing."""
    result = init_db(
        settings=multitenancy_settings,
        db_url=SYNC_TEST_DB_URL,
        create_schemas=True,
        base_model_class=Base,
        tenant_ids=TEST_TENANTS,
        is_async=False,
    )
    yield result


@pytest_asyncio.fixture
async def init_async_db_config(multitenancy_settings, async_db_engine):
    """Initialize the async database configuration for testing."""
    result = init_db(
        settings=multitenancy_settings,
        db_url=ASYNC_TEST_DB_URL,
        create_schemas=True,
        base_model_class=Base,
        tenant_ids=TEST_TENANTS,
        is_async=True,
    )
    yield result


@pytest.fixture
def fastapi_app(multitenancy_settings):
    """Create a FastAPI app for testing."""
    app = FastAPI()
    app.add_middleware(TenantMiddleware, settings=multitenancy_settings)
    return app


@pytest.fixture
def test_client(fastapi_app):
    """Create a test client for the FastAPI app."""
    return TestClient(fastapi_app)


@pytest.fixture
def tenant_headers():
    """Create headers with tenant ID for testing."""
    return {"X-Tenant-ID": "tenant1"}


@pytest.fixture
def admin_headers():
    """Create headers with admin tenant ID for testing."""
    return {"X-Tenant-ID": "admin"}


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return {
        "users": [
            {"name": "User 1", "email": "user1@example.com"},
            {"name": "User 2", "email": "user2@example.com"},
        ],
        "products": [
            {"name": "Product 1", "price": 100},
            {"name": "Product 2", "price": 200},
        ],
    }


@pytest.fixture
def tenant_specific_settings():
    """Create tenant-specific settings for testing."""
    return {
        "tenant1": {
            "db_pool_size": 10,
            "db_max_overflow": 20,
        },
        "tenant2": {
            "db_pool_size": 5,
            "db_max_overflow": 15,
        },
    }
