"""Global pytest configuration."""

import os

# Set test environment variables before any app imports
# This prevents ValueError when settings.DATABASE_URI is accessed at module load time
if not os.getenv("SQLALCHEMY_DATABASE_URL"):
    os.environ["SQLALCHEMY_DATABASE_URL"] = (
        "postgresql+asyncpg://elevaite:elevaite@localhost:5433/auth_test"
    )

# Set other required environment variables for testing
if not os.getenv("FRONTEND_URL"):
    os.environ["FRONTEND_URL"] = "http://localhost:3005"

# Apply patches for third-party libraries
