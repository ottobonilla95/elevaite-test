import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlmodel import Session
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

load_dotenv(os.path.join(parent_dir, ".env.local"))
load_dotenv(os.path.join(parent_dir, ".env"))

# Use SQLALCHEMY_DATABASE_URL as the primary environment variable
# Fall back to AGENT_STUDIO_DATABASE_URL for backwards compatibility
SQLALCHEMY_DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    os.getenv(
        "AGENT_STUDIO_DATABASE_URL",
        "postgresql://elevaite:elevaite@localhost:5433/agent_studio",
    ),
)

# Validate database URL is set
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError(
        "Database URL not configured. Set SQLALCHEMY_DATABASE_URL environment variable."
    )

# Create engine with connection pooling - fail hard if connection fails
try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),  # 30 minutes
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
    )

    # Test the connection immediately
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    print(f"✅ Connected to PostgreSQL: {SQLALCHEMY_DATABASE_URL}")

except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")
    print(f"   Database URL: {SQLALCHEMY_DATABASE_URL}")
    print(f"   Make sure PostgreSQL is running and the database exists.")
    raise RuntimeError(f"Failed to connect to PostgreSQL database: {e}") from e

SQLAlchemyInstrumentor().instrument(engine=engine)  # OTEL

Base = declarative_base()

# Legacy SessionLocal for backwards compatibility with scripts and background tasks
# NOTE: This creates SQLAlchemy sessions, not SQLModel sessions
# Use get_db() dependency for API endpoints (returns SQLModel Session)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency that provides a SQLModel Session for API endpoints.
    SQLModel Session has the .exec() method required by SDK services.

    NOTE: This is different from SessionLocal() which creates SQLAlchemy sessions.
    """
    with Session(engine) as session:
        yield session
