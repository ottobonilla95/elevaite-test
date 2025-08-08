"""Add workflow tables

Revision ID: add_workflow_tables
Revises: d2d4d2e688c4
Create Date: 2024-01-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_workflow_tables"
down_revision = "d2d4d2e688c4"
branch_labels = None
depends_on = None


def upgrade():
    # Create workflows table
    op.create_table(
        "workflows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("version", sa.String(), nullable=True),
        sa.Column(
            "configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_deployed", sa.Boolean(), nullable=True),
        sa.Column("deployed_at", sa.DateTime(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "version", name="uix_workflow_name_version"),
        sa.UniqueConstraint("workflow_id"),
    )

    # Create workflow_agents table
    op.create_table(
        "workflow_agents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_x", sa.Integer(), nullable=True),
        sa.Column("position_y", sa.Integer(), nullable=True),
        sa.Column("node_id", sa.String(), nullable=False),
        sa.Column(
            "agent_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("added_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.agent_id"],
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["workflows.workflow_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_id", "agent_id", name="uix_workflow_agent"),
        sa.UniqueConstraint("workflow_id", "node_id", name="uix_workflow_node_id"),
    )

    # Create workflow_connections table
    op.create_table(
        "workflow_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_type", sa.String(), nullable=True),
        sa.Column("conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("source_handle", sa.String(), nullable=True),
        sa.Column("target_handle", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_agent_id"],
            ["agents.agent_id"],
        ),
        sa.ForeignKeyConstraint(
            ["target_agent_id"],
            ["agents.agent_id"],
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["workflows.workflow_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workflow_id",
            "source_agent_id",
            "target_agent_id",
            name="uix_workflow_connection",
        ),
    )

    # Create workflow_deployments table
    op.create_table(
        "workflow_deployments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("deployment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("environment", sa.String(), nullable=True),
        sa.Column("deployment_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("deployed_by", sa.String(), nullable=True),
        sa.Column("deployed_at", sa.DateTime(), nullable=True),
        sa.Column("stopped_at", sa.DateTime(), nullable=True),
        sa.Column(
            "runtime_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("last_executed", sa.DateTime(), nullable=True),
        sa.Column("execution_count", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["workflows.workflow_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deployment_id"),
        sa.UniqueConstraint(
            "deployment_name", "environment", name="uix_deployment_name_env"
        ),
    )

    # Create workflow_executions table
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("input_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "output_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_type", sa.String(), nullable=True),
        sa.Column(
            "error_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("retry_count", sa.Integer(), server_default="0"),
        sa.Column("max_retries", sa.Integer(), server_default="3"),
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("current_step_index", sa.Integer(), server_default="0"),
        sa.Column("total_steps", sa.Integer(), server_default="0"),
        sa.Column(
            "execution_path", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "branch_decisions", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["workflows.workflow_id"],
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.agent_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_id", name="uix_workflow_execution_id"),
    )

    # Create workflow_execution_steps table
    op.create_table(
        "workflow_execution_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("step_id", sa.String(), nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("step_name", sa.String(), nullable=True),
        sa.Column("step_type", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("input_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "output_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0"),
        sa.Column(
            "step_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["workflow_executions.execution_id"],
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.agent_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_id", "step_id", name="uix_execution_step_id"),
    )


def downgrade():
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table("workflow_execution_steps")
    op.drop_table("workflow_executions")
    op.drop_table("workflow_deployments")
    op.drop_table("workflow_connections")
    op.drop_table("workflow_agents")
    op.drop_table("workflows")
