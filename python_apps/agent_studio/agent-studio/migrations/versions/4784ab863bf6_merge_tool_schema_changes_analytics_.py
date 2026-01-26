"""merge tool schema changes - analytics moved to dedicated table

Revision ID: 4784ab863bf6
Revises: 252104e9a26b, 28de73a7b0cc
Create Date: 2025-06-25 18:03:19.006032

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '4784ab863bf6'
down_revision: Union[str, None] = ('252104e9a26b', '28de73a7b0cc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
