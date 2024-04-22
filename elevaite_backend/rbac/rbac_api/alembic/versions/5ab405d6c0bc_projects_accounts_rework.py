"""projects_accounts_rework

Revision ID: 5ab405d6c0bc
Revises: 7b1e3447f223
Create Date: 2024-04-04 18:05:18.060692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, select

# revision identifiers, used by Alembic.
revision: str = '5ab405d6c0bc'
down_revision: Union[str, None] = '7b1e3447f223'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # Remove is_disabled columns from "projects" and "accounts"
    op.drop_column('projects', 'is_disabled')
    op.drop_column('accounts', 'is_disabled')
    
    # Add the `is_admin` column as nullable initially
    op.add_column('user_project', sa.Column('is_admin', sa.Boolean(), nullable=True, server_default=sa.false())) 
    
    # Add creator column to 'projects' with String type and nullable initially
    op.add_column('projects', sa.Column('creator', sa.String(254), nullable=True))

    # Prepare to populate `is_admin`
    user_project_table = table('user_project',
        sa.column('id', sa.Uuid()),
        sa.column('user_id', sa.Uuid()),
        sa.column('project_id', sa.Uuid()),
        sa.column('is_admin', sa.Boolean()) 
    )
    # Define minimal metadata for `project`
    project_table = table('projects',
        sa.column('id', sa.Uuid()),
        sa.column('project_owner_id', sa.Uuid()),
        sa.column('creator', sa.String())
    )
    # Define minimal metadata for `user`
    user_table = table('users',
        sa.column('id', sa.Uuid()),
        sa.column('email', sa.String())
    )
    # Step 2: Populate `is_admin`
    conn = op.get_bind()
    projects = conn.execute(select(project_table)).fetchall()
    for project in projects:
        # Update `user_project` entries to set `is_admin = True` for matching conditions
        conn.execute(
            user_project_table.update().
            where(sa.and_(
                user_project_table.c.project_id == project.id,
                user_project_table.c.user_id == project.project_owner_id
            )).
            values(is_admin=True)
        )
    # Make `is_admin` non-nullable after populating
    op.alter_column('user_project', 'is_admin', nullable=False)
    
    # Populate `creator` with the email of the project owner by querying the `User` table
    projects = conn.execute(select(project_table.c.id, project_table.c.project_owner_id)).fetchall()
    for project in projects:
        result = conn.execute(
            select(user_table.c.email).
            where(user_table.c.id == project.project_owner_id)
        ).fetchone()

        # Check if a user was found; if not, set a default value or handle as appropriate
        owner_email = result[0] if result is not None else 'default@email.com'

        conn.execute(
            project_table.update().
            where(project_table.c.id == project.id).
            values(creator=owner_email)
        )
    
    # dropping the `project_owner_id` column, handled after populating `creator`
    op.drop_column('projects', 'project_owner_id')

    # Make `creator` non-nullable after populating
    op.alter_column('projects', 'creator', nullable=False)

    # Make 'is_admin' field of User_Account non-nullable as well
    op.alter_column('user_account', 'is_admin', nullable=False)
def downgrade() -> None:
    # Define minimal metadata for `project` and `user`
    project_table = table('projects',
        sa.column('id', sa.Uuid()),
        sa.column('creator', sa.String()),  # Column to be dropped later
        sa.column('project_owner_id', sa.Uuid())  # Column to be added and populated
    )
    user_table = table('users',
        sa.column('id', sa.Uuid()),
        sa.column('email', sa.String())
    )

    conn = op.get_bind()

    # Step 1: Add `project_owner_id` column to `Project`, nullable initially
    op.add_column('projects', sa.Column('project_owner_id', sa.Uuid(), nullable=True))

    # Step 2: Populate `project_owner_id` by iterating through projects
    projects = conn.execute(select(project_table.c.id, project_table.c.creator)).fetchall()
    for project in projects:
        user_id_result = conn.execute(
            select(user_table.c.id).
            where(user_table.c.email == project.creator)
        ).fetchone()

        # If a matching user is found, update `project_owner_id` with the user's ID
        if user_id_result:
            conn.execute(
                project_table.update().
                where(project_table.c.id == project.id).
                values(project_owner_id=user_id_result[0])
            )

    # Step 3: Make `project_owner_id` non-nullable
    op.alter_column('projects', 'project_owner_id', nullable=False)

    # Step 4: Drop `creator` column from `Project`
    op.drop_column('projects', 'creator')

    # Step 5: Drop `is_admin` column from `User_Project`
    op.drop_column('user_project', 'is_admin')

    op.alter_column('user_account', 'is_admin', nullable=True)
