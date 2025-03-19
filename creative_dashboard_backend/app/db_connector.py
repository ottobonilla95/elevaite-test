import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
Base = declarative_base()

class DatabaseConnector:
    """
    Database connection manager for PostgreSQL using SQLAlchemy.
    Handles connection initialization and session management.
    """
    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one database connection is created."""
        if cls._instance is None:
            cls._instance = super(DatabaseConnector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the database connection if not already initialized."""
        if not getattr(self, '_initialized', False):
            self._load_config()
            self._setup_engine()
            self._initialized = True

    def _load_config(self):
        """Load database configuration from environment variables."""
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", 5432))
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.database = os.getenv("DB_NAME")
        self.echo = os.getenv("DB_ECHO", "False").lower() == "true"

        # Validate required configuration
        if not all([self.username, self.password, self.database]):
            logger.error("Missing required database configuration")
            raise ValueError("Database configuration incomplete. Check environment variables.")

    def _setup_engine(self):
        """Set up the SQLAlchemy engine and session factory."""
        try:
            connection_string = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
            self.engine = create_engine(connection_string, echo=self.echo, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info(f"Database engine initialized for {self.host}:{self.port}/{self.database}")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    def create_tables(self):
        """Create all tables defined in SQLAlchemy models."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    def get_session(self):
        """
        Get a database session.
        Returns:
            Session: SQLAlchemy database session
        """
        return self.SessionLocal()

# Create a singleton instance
db_connector = DatabaseConnector()
