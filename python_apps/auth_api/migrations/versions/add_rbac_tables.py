"""add rbac tables for authorization

Revision ID: add_rbac_tables
Revises:
Create Date: 2025-01-XX

This migration adds RBAC (Role-Based Access Control) tables to enable
authorization alongside the existing authentication features.

Tables added:
- organizations: Top-level organizational hierarchy
- accounts: Belong to organizations
- projects: Belong to accounts
- user_role_assignments: Maps users to roles on resources

This enables OPA-based policy evaluation for fine-grained access control.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_rbac_tables"
down_revision: Union[str, None] = "fbbf8e6f17a5"  # Update this to the latest migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add RBAC tables for authorization."""

    # Enable UUID extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Organizations table (top-level hierarchy)
    op.create_table(
        "organizations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
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
    )
    op.create_index("idx_organizations_name", "organizations", ["name"])

    # Accounts table (belong to organizations)
    op.create_table(
        "accounts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
    )
    op.create_index("idx_accounts_organization_id", "accounts", ["organization_id"])
    op.create_index("idx_accounts_name", "accounts", ["name"])

    # Projects table (belong to accounts)
    op.create_table(
        "projects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
    )
    op.create_index("idx_projects_account_id", "projects", ["account_id"])
    op.create_index("idx_projects_organization_id", "projects", ["organization_id"])
    op.create_index("idx_projects_name", "projects", ["name"])

    # User role assignments table (the core of RBAC)
    # Maps users to roles on specific resources (organization, account, or project)
    op.create_table(
        "user_role_assignments",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("user_id", "resource_id"),
        sa.CheckConstraint(
            "role IN ('superadmin', 'admin', 'editor', 'viewer')",
            name="ck_user_role_assignments_role",
        ),
        sa.CheckConstraint(
            "resource_type IN ('organization', 'account', 'project')",
            name="ck_user_role_assignments_resource_type",
        ),
    )
    op.create_index(
        "idx_user_role_assignments_user_id", "user_role_assignments", ["user_id"]
    )
    op.create_index(
        "idx_user_role_assignments_resource",
        "user_role_assignments",
        ["resource_type", "resource_id"],
    )
    op.create_index("idx_user_role_assignments_role", "user_role_assignments", ["role"])

    # Add trigger to auto-update updated_at timestamp on organizations
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER update_organizations_updated_at
        BEFORE UPDATE ON organizations
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_accounts_updated_at
        BEFORE UPDATE ON accounts
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_projects_updated_at
        BEFORE UPDATE ON projects
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    # Add comments for documentation
    op.execute(
        "COMMENT ON TABLE organizations IS 'Top-level organizational hierarchy for RBAC'"
    )
    op.execute(
        "COMMENT ON TABLE accounts IS 'Accounts belong to organizations and contain projects'"
    )
    op.execute(
        "COMMENT ON TABLE projects IS 'Projects belong to accounts and are the primary resource for access control'"
    )
    op.execute(
        "COMMENT ON TABLE user_role_assignments IS 'Maps users to roles on specific resources (organization, account, or project). Used by OPA for authorization decisions.'"
    )
    op.execute(
        "COMMENT ON COLUMN user_role_assignments.role IS 'Role: superadmin (org-level), admin (account-level), editor/viewer (project-level)'"
    )
    op.execute(
        "COMMENT ON COLUMN user_role_assignments.resource_type IS 'Type of resource: organization, account, or project'"
    )
    op.execute(
        "COMMENT ON COLUMN user_role_assignments.resource_id IS 'UUID of the resource (organization.id, account.id, or project.id)'"
    )


def downgrade() -> None:
    """Remove RBAC tables."""

    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS update_projects_updated_at ON projects")
    op.execute("DROP TRIGGER IF EXISTS update_accounts_updated_at ON accounts")
    op.execute(
        "DROP TRIGGER IF EXISTS update_organizations_updated_at ON organizations"
    )
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table("user_role_assignments")
    op.drop_table("projects")
    op.drop_table("accounts")
    op.drop_table("organizations")
