"""empty message

Revision ID: 82806d1cb3a9
Revises: 76d0167de09d, c545eec7b0dd
Create Date: 2025-07-04 17:21:25.230232

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "82806d1cb3a9"
down_revision: Union[str, None] = ("76d0167de09d", "c545eec7b0dd")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
