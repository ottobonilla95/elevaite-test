from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_is_password_temporary"
down_revision: Union[str, None] = "f650f484e244"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_password_temporary column with default value False
    op.add_column(
        "users",
        sa.Column(
            "is_password_temporary",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    # Drop is_password_temporary column
    op.drop_column("users", "is_password_temporary")
