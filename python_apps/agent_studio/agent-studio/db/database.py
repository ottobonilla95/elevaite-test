import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Load environment variables
load_dotenv(os.path.join(parent_dir, ".env.local"))
load_dotenv(os.path.join(parent_dir, ".env"))

# Get database URL from environment variable or use a default for development
SQLALCHEMY_DATABASE_URL = os.getenv(
    "AGENT_STUDIO_DATABASE_URL",
    "postgresql://elevaite:elevaite@localhost:5433/agent_studio",
)

# Create SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for SQLAlchemy models
Base = declarative_base()


# Dependency to get DB session
def get_db():
    """
    Get a database session.

    Yields:
        SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
