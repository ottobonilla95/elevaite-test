"""Consolidated migrations for timestamp handling and SQLAlchemy 2.0

Revision ID: consolidated_migrations
Revises: 72a50a53308c
Create Date: 2025-04-11 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'consolidated_migrations'
down_revision: Union[str, None] = '72a50a53308c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    This migration consolidates several empty migrations:
    - 5a78ac8f4024_update_models_to_use_sqlalchemy_2_0_.py
    - 8634a3e9a06d_clean_up_attribute_access.py
    - ccdf8be15a49_fix_timestamp_handling.py
    - d065dc1c6b7e_fix_timestamp_handling_again.py
    - 6db0631fee6c_fix_timestamp_handling.py
    
    The actual changes were made to the models directly and didn't require
    schema changes, which is why the original migrations were empty.
    
    Changes included:
    1. Updated models to use SQLAlchemy 2.0 style with Mapped types
    2. Fixed timestamp handling to use datetime.now instead of lambda functions
    3. Improved attribute access in the ORM models
    """
    # No schema changes needed
    pass


def downgrade() -> None:
    # No schema changes to revert
    pass
