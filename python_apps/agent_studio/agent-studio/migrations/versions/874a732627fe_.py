"""Merge workflow metrics and deterministic workflow branches

Revision ID: 874a732627fe
Revises: 19543a679fca, deterministic_workflow_001
Create Date: 2025-08-08 11:29:20.403570

"""

from typing import Sequence, Union, Tuple

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "874a732627fe"
down_revision: Union[str, Tuple[str, ...], None] = (
    "19543a679fca",
    "deterministic_workflow_001",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
