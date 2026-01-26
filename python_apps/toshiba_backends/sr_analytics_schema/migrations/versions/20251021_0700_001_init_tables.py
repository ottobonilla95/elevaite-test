
"""create initial schema for sr_analytics

Revision ID: 001_init_schema
Revises:
Create Date: 2025-10-21

"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = '001_init_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('customer_unique_id', sa.String(255), unique=True, nullable=False),
        sa.Column('customer_account_number', sa.String(255), nullable=False),
        sa.Column('customer_name', sa.Text),
        sa.Column('address_line1', sa.Text),
        sa.Column('address_line2', sa.Text),
        sa.Column('city', sa.String(255)),
        sa.Column('state', sa.String(255)),
        sa.Column('postal_code', sa.String(50)),
        sa.Column('country', sa.String(100)),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Create service_requests table
    op.create_table(
        'service_requests',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('sr_number', sa.String(255), unique=True, nullable=False),
        sa.Column('customer_unique_id', sa.String(255), nullable=False),
        sa.Column('customer_account_number', sa.String(255)),
        sa.Column('service_address', sa.Text),
        sa.Column('service_city', sa.String(255)),
        sa.Column('service_state', sa.String(100)),
        sa.Column('service_postal_code', sa.String(50)),
        sa.Column('incident_date', sa.TIMESTAMP),
        sa.Column('closed_date', sa.TIMESTAMP),
        sa.Column('severity', sa.String(100)),
        sa.Column('machine_type', sa.String(255)),
        sa.Column('machine_model', sa.String(255)),
        sa.Column('machine_serial_number', sa.String(255)),
        sa.Column('barrier_code', sa.String(100)),
        sa.Column('country', sa.String(100)),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('task_number', sa.String(255), unique=True, nullable=False),
        sa.Column('sr_number', sa.String(255)),
        sa.Column('task_assignee_id', sa.String(255)),
        sa.Column('assignee_name', sa.Text),
        sa.Column('task_notes', sa.Text),
        sa.Column('travel_time_hours', sa.Numeric(10, 2)),
        sa.Column('actual_time_hours', sa.Numeric(10, 2)),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['sr_number'], ['service_requests.sr_number'], ondelete='CASCADE')
    )

    # Create parts_used table
    op.create_table(
        'parts_used',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('task_number', sa.String(255)),
        sa.Column('part_number', sa.String(255)),
        sa.Column('description', sa.Text),
        sa.Column('quantity', sa.Integer),
        sa.Column('unit_cost', sa.Numeric(12, 2)),
        sa.Column('total_cost', sa.Numeric(12, 2)),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['task_number'], ['tasks.task_number'], ondelete='CASCADE')
    )

    # Create sr_notes table
    op.create_table(
        'sr_notes',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('sr_number', sa.String(255)),
        sa.Column('customer_problem_summary', sa.Text),
        sa.Column('sr_notes', sa.Text),
        sa.Column('resolution_summary', sa.Text),
        sa.Column('concat_comments', sa.Text),
        sa.Column('comments', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['sr_number'], ['service_requests.sr_number'], ondelete='CASCADE')
    )

    # Create indexes
    op.create_index('idx_sr_customer_account', 'service_requests', ['customer_account_number'])
    op.create_index('idx_sr_incident_date', 'service_requests', ['incident_date'])
    op.create_index('idx_sr_country', 'service_requests', ['country'])
    op.create_index('idx_sr_service_state', 'service_requests', ['service_state'])
    op.create_index('idx_sr_service_city', 'service_requests', ['service_city'])
    op.create_index('idx_tasks_sr_number', 'tasks', ['sr_number'])
    op.create_index('idx_tasks_assignee', 'tasks', ['task_assignee_id'])
    op.create_index('idx_parts_task_number', 'parts_used', ['task_number'])
    op.create_index('idx_notes_sr_number', 'sr_notes', ['sr_number'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_notes_sr_number', table_name='sr_notes')
    op.drop_index('idx_parts_task_number', table_name='parts_used')
    op.drop_index('idx_tasks_assignee', table_name='tasks')
    op.drop_index('idx_tasks_sr_number', table_name='tasks')
    op.drop_index('idx_sr_service_city', table_name='service_requests')
    op.drop_index('idx_sr_service_state', table_name='service_requests')
    op.drop_index('idx_sr_country', table_name='service_requests')
    op.drop_index('idx_sr_incident_date', table_name='service_requests')
    op.drop_index('idx_sr_customer_account', table_name='service_requests')

    # Drop tables in reverse dependency order
    op.drop_table('sr_notes')
    op.drop_table('parts_used')
    op.drop_table('tasks')
    op.drop_table('service_requests')
    op.drop_table('customers')

