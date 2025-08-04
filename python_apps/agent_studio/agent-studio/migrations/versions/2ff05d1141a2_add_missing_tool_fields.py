"""add_missing_tool_fields

Revision ID: 2ff05d1141a2
Revises: b6589798221d
Create Date: 2025-06-24 17:35:13.048856

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2ff05d1141a2"
down_revision: Union[str, None] = "b6589798221d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing fields to tools table."""
    # Check if columns already exist before adding them
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("tools")]

    # Add missing fields to tools table only if they don't exist
    if "api_endpoint" not in existing_columns:
        op.add_column("tools", sa.Column("api_endpoint", sa.String(), nullable=True))

    if "http_method" not in existing_columns:
        op.add_column("tools", sa.Column("http_method", sa.String(), nullable=True))

    if "headers" not in existing_columns:
        op.add_column(
            "tools",
            sa.Column(
                "headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True
            ),
        )

    if "auth_required" not in existing_columns:
        op.add_column(
            "tools",
            sa.Column(
                "auth_required", sa.Boolean(), nullable=False, server_default="false"
            ),
        )

    if "documentation" not in existing_columns:
        op.add_column("tools", sa.Column("documentation", sa.Text(), nullable=True))

    if "examples" not in existing_columns:
        op.add_column(
            "tools",
            sa.Column(
                "examples", postgresql.JSONB(astext_type=sa.Text()), nullable=True
            ),
        )


def downgrade() -> None:
    """Remove the added fields from tools table."""
    # Check if columns exist before dropping them
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("tools")]

    # Drop columns only if they exist
    columns_to_drop = [
        "examples",
        "documentation",
        "auth_required",
        "headers",
        "http_method",
        "api_endpoint",
    ]

    for column_name in columns_to_drop:
        if column_name in existing_columns:
            op.drop_column("tools", column_name)
