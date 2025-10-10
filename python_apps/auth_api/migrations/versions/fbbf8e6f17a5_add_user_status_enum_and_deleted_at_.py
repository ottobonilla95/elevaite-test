"""Add deleted_at field to users

Revision ID: fbbf8e6f17a5
Revises: 9ee4ca11d13e
Create Date: 2025-09-16 09:15:46.447174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fbbf8e6f17a5'
down_revision: Union[str, None] = '9ee4ca11d13e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add deleted_at column for soft delete functionality
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove deleted_at column
    op.drop_column('users', 'deleted_at')