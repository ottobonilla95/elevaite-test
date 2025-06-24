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
    # Add analytics fields to tools table
    op.add_column("tools", sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tools", sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tools", sa.Column("average_execution_time_ms", sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove analytics fields from tools table."""
    op.drop_column("tools", "average_execution_time_ms")
    op.drop_column("tools", "error_count")
    op.drop_column("tools", "success_count")
