import sys
from urllib.parse import urlsplit, urlunsplit, unquote

from alembic import command
from alembic.config import Config

# Reuse app settings (.env loaded by Settings)
from app.core.config import settings


def derive_test_db_url(db_url: str) -> str:
    """
    Derive a test database URL from the provided database URL by suffixing
    the database name with "_test" in a robust, provider-agnostic way.

    Examples:
      postgresql+asyncpg://u:p@localhost:5432/auth -> postgresql+asyncpg://u:p@localhost:5432/auth_test
      postgresql+psycopg2://u:p@localhost/auth_db -> postgresql+psycopg2://u:p@localhost/auth_db_test
    """
    # Strip any wrapping quotes that may come from env files
    db_url = db_url.strip().strip('"').strip("'")

    parts = urlsplit(db_url)
    # parts.path starts with '/dbname'
    if not parts.path or parts.path == "/":
        raise ValueError(f"Could not derive DB name from URL: {db_url}")

    # Path may contain percent-escaped characters; normalise db name
    dbname = unquote(parts.path.lstrip("/"))
    if not dbname.endswith("_test"):
        dbname = f"{dbname}_test"

    new_path = f"/{dbname}"
    return urlunsplit(
        (parts.scheme, parts.netloc, new_path, parts.query, parts.fragment)
    )


def migrate(url: str) -> None:
    """Run Alembic upgrade head against the given SQLAlchemy URL."""
    # Point Alembic at the local alembic.ini in this package
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)

    # Run migrations
    command.upgrade(cfg, "head")


def main() -> int:
    try:
        base_url = settings.DATABASE_URI  # pulled from env via Settings
    except Exception as e:
        print(f"ERROR: Unable to read SQLALCHEMY_DATABASE_URL from environment: {e}")
        return 1

    test_url = derive_test_db_url(base_url)
    print(f"Running Alembic migrations for test DB: {test_url}")

    try:
        migrate(test_url)
    except Exception as e:
        print(f"ERROR: Alembic migration failed: {e}")
        return 2

    print("Alembic migration completed for test DB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
