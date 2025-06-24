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
    # Add missing fields to tools table
    op.add_column("tools", sa.Column("api_endpoint", sa.String(), nullable=True))
    op.add_column("tools", sa.Column("http_method", sa.String(), nullable=True))
    op.add_column("tools", sa.Column("headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("tools", sa.Column("auth_required", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("tools", sa.Column("documentation", sa.Text(), nullable=True))
    op.add_column("tools", sa.Column("examples", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Remove the added fields from tools table."""
    op.drop_column("tools", "examples")
    op.drop_column("tools", "documentation")
    op.drop_column("tools", "auth_required")
    op.drop_column("tools", "headers")
    op.drop_column("tools", "http_method")
    op.drop_column("tools", "api_endpoint")
