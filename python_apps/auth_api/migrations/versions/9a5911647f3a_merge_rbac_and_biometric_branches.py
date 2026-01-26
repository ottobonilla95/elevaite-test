"""merge_rbac_and_biometric_branches

Revision ID: 9a5911647f3a
Revises: 2a407f3f7777, d7a30b8a7594
Create Date: 2026-01-14 13:11:41.494024

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '9a5911647f3a'
down_revision: Union[str, None] = ('2a407f3f7777', 'd7a30b8a7594')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
