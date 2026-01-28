"""add permission_overrides table for fine-grained access control

Revision ID: add_permission_overrides
Revises: add_rbac_tables
Create Date: 2025-11-03

This migration adds the permission_overrides table to enable fine-grained
permission control beyond role-based permissions.

Permission overrides allow:
- Granting specific permissions to users (allow list)
- Denying specific permissions to users (deny list)
- Exceptions to role-based permissions

Deny takes precedence over allow (security best practice).

Example use cases:
- Grant a viewer permission to edit a specific project
- Deny an editor permission to delete a specific project
- Grant temporary access to specific actions
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_permission_overrides"
down_revision: Union[str, None] = "add_rbac_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add permission_overrides table."""

    # Permission overrides table
    # Allows fine-grained permission control beyond role-based permissions
    op.create_table(
        "permission_overrides",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=False),
        sa.Column("allow_actions", postgresql.JSONB(), nullable=True),
        sa.Column("deny_actions", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("user_id", "resource_id"),
        sa.CheckConstraint(
            "resource_type IN ('organization', 'account', 'project')",
            name="ck_permission_overrides_resource_type",
        ),
    )

    # Create indexes for efficient querying
    op.create_index(
        "idx_permission_overrides_user_id", "permission_overrides", ["user_id"]
    )
    op.create_index(
        "idx_permission_overrides_resource",
        "permission_overrides",
        ["resource_type", "resource_id"],
    )

    # Add trigger to auto-update updated_at timestamp
    op.execute("""
        CREATE TRIGGER update_permission_overrides_updated_at
        BEFORE UPDATE ON permission_overrides
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    # Add comments for documentation
    op.execute(
        "COMMENT ON TABLE permission_overrides IS 'Fine-grained permission overrides for users on specific resources. Allows granting or denying specific actions beyond role-based permissions.'"
    )
    op.execute(
        'COMMENT ON COLUMN permission_overrides.allow_actions IS \'JSONB array of actions explicitly allowed for this user on this resource (e.g., ["edit_project", "delete_workflow"])\''
    )
    op.execute(
        "COMMENT ON COLUMN permission_overrides.deny_actions IS 'JSONB array of actions explicitly denied for this user on this resource. Deny takes precedence over allow.'"
    )
    op.execute(
        "COMMENT ON COLUMN permission_overrides.resource_type IS 'Type of resource: organization, account, or project'"
    )
    op.execute(
        "COMMENT ON COLUMN permission_overrides.resource_id IS 'UUID of the resource (organization.id, account.id, or project.id)'"
    )


def downgrade() -> None:
    """Remove permission_overrides table."""

    # Drop trigger first
    op.execute(
        "DROP TRIGGER IF EXISTS update_permission_overrides_updated_at ON permission_overrides"
    )

    # Drop table
    op.drop_table("permission_overrides")
