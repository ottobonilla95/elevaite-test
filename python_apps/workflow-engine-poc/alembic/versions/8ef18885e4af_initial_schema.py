"""initial_schema

Initial migration for workflow-engine database schema.

This migration establishes the baseline schema for the workflow engine.
Tables are created automatically when running migrations for the first time.

To generate the actual schema, run:
  ALEMBIC_SCHEMA=workflow_default uv run alembic revision --autogenerate -m "populate_initial_schema"

Revision ID: 8ef18885e4af
Revises:
Create Date: 2026-01-26 10:25:07.652668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ef18885e4af'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is a placeholder migration that marks the initial state.
    # The actual schema should already exist from previous deployments.
    # If starting fresh, tables will be created by subsequent migrations.
    pass


def downgrade() -> None:
    # Cannot downgrade from initial state
    pass
