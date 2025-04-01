"""project_creator_change

Revision ID: 0a794b1322b2
Revises: 8b78c453a1ed
Create Date: 2024-05-14 20:19:46.748625

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = '0a794b1322b2'
down_revision: Union[str, None] = '8b78c453a1ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
   # Add a new column for the user ID foreign key, initially as nullable
    op.add_column('projects', sa.Column('creator_id', sa.UUID(as_uuid=True), nullable=True))

    # Assuming connection to perform data migration
    connection = op.get_bind()

    # Fetch all projects with their creator's email
    projects = connection.execute(
        text("""
            SELECT p.id, u.id AS user_id
            FROM projects p
            JOIN users u ON p.creator = u.email
        """)
    ).fetchall()

    # Update the new creator_id column with the user IDs
    for project_id, user_id in projects:
        connection.execute(
            text("""
                UPDATE projects
                SET creator_id = :user_id
                WHERE id = :project_id
            """),
            {'user_id': user_id, 'project_id': project_id}
        )

    # Now alter the creator_id column to be non-nullable
    op.alter_column('projects', 'creator_id', nullable=False)

    # Drop the old creator column
    op.drop_column('projects', 'creator')


def downgrade() -> None:
     # Add the 'creator' column back to the 'projects' table for storing emails, initially as nullable
    op.add_column('projects', sa.Column('creator', sa.String(), nullable=True))

    # Assuming connection to perform data migration
    connection = op.get_bind()

    # Fetch all project IDs and the corresponding user emails using the 'creator_id' foreign key
    projects = connection.execute(
        text("""
            SELECT p.id, u.email
            FROM projects p
            JOIN users u ON p.creator_id = u.id
        """)
    ).fetchall()

    # Update the 'creator' column with emails
    for project_id, email in projects:
        connection.execute(
            text("""
                UPDATE projects
                SET creator = :email
                WHERE id = :project_id
            """),
            {'email': email, 'project_id': project_id}
        )

    # Now alter the creator column to be non-nullable
    op.alter_column('projects', 'creator', nullable=False)

    # Drop the 'creator_id' column
    op.drop_column('projects', 'creator_id')
