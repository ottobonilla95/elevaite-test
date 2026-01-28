"""empty message

Revision ID: ea4815f57379
Revises: add_workflow_tables, aec8c69ea633
Create Date: 2025-06-02 15:21:36.025261

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = 'ea4815f57379'
down_revision: Union[str, None] = ('add_workflow_tables', 'aec8c69ea633')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
