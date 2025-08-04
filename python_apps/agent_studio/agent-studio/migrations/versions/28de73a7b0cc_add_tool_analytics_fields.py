"""add_tool_analytics_fields

Revision ID: 28de73a7b0cc
Revises: 2ff05d1141a2
Create Date: 2025-06-24 17:50:44.808648

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "28de73a7b0cc"
down_revision: Union[str, None] = "2ff05d1141a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add analytics fields to tools table."""
    # Check if columns already exist before adding them
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("tools")]

    # Add analytics fields to tools table only if they don't exist
    if "success_count" not in existing_columns:
        op.add_column(
            "tools",
            sa.Column(
                "success_count", sa.Integer(), nullable=False, server_default="0"
            ),
        )

    if "error_count" not in existing_columns:
        op.add_column(
            "tools",
            sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        )

    if "average_execution_time_ms" not in existing_columns:
        op.add_column(
            "tools", sa.Column("average_execution_time_ms", sa.Float(), nullable=True)
        )


def downgrade() -> None:
    """Remove analytics fields from tools table."""
    # Check if columns exist before dropping them
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("tools")]

    # Remove analytics fields from tools table only if they exist
    if "average_execution_time_ms" in existing_columns:
        op.drop_column("tools", "average_execution_time_ms")

    if "error_count" in existing_columns:
        op.drop_column("tools", "error_count")

    if "success_count" in existing_columns:
        op.drop_column("tools", "success_count")
