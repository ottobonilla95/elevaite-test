"""Add support for deterministic workflows

Revision ID: deterministic_workflow_001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "deterministic_workflow_001"
down_revision: Union[str, None] = "add_workflow_tables"  # Depends on workflow tables
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Add new table for deterministic workflow steps
    op.create_table(
        "deterministic_workflow_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "step_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_name", sa.String(), nullable=False),
        sa.Column("step_type", sa.String(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "dependencies", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("execution_pattern", sa.String(), server_default="sequential"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("input_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "output_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "input_mapping", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("total_items", sa.Integer(), nullable=True),
        sa.Column("processed_items", sa.Integer(), nullable=True),
        sa.Column("successful_items", sa.Integer(), nullable=True),
        sa.Column("failed_items", sa.Integer(), nullable=True),
        sa.Column("current_batch", sa.Integer(), nullable=True),
        sa.Column("total_batches", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "rollback_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("rollback_attempted", sa.Boolean(), server_default="false"),
        sa.Column("rollback_successful", sa.Boolean(), nullable=True),
        sa.Column(
            "step_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "step_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("progress_percentage", sa.Float(), nullable=True),
        sa.Column("estimated_completion", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["workflow_executions.execution_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("step_id"),
    )

    # Add indexes for performance
    op.create_index(
        op.f("ix_deterministic_workflow_steps_execution_id"),
        "deterministic_workflow_steps",
        ["execution_id"],
    )
    op.create_index(
        op.f("ix_deterministic_workflow_steps_step_type"),
        "deterministic_workflow_steps",
        ["step_type"],
    )
    op.create_index(
        op.f("ix_deterministic_workflow_steps_status"),
        "deterministic_workflow_steps",
        ["status"],
    )
    op.create_index(
        op.f("ix_deterministic_workflow_steps_start_time"),
        "deterministic_workflow_steps",
        ["start_time"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        op.f("ix_deterministic_workflow_steps_start_time"),
        table_name="deterministic_workflow_steps",
    )
    op.drop_index(
        op.f("ix_deterministic_workflow_steps_status"),
        table_name="deterministic_workflow_steps",
    )
    op.drop_index(
        op.f("ix_deterministic_workflow_steps_step_type"),
        table_name="deterministic_workflow_steps",
    )
    op.drop_index(
        op.f("ix_deterministic_workflow_steps_execution_id"),
        table_name="deterministic_workflow_steps",
    )

    # Drop table
    op.drop_table("deterministic_workflow_steps")
