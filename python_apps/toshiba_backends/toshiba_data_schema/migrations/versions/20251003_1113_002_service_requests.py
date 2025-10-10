"""Service Request System (Core ETL Tables), Indexes, and Sequences.

This forms part of the initial post-hoc migration setup for the Toshiba Data Schema, reflecting the existing state of the database as of October 2025.
It includes four versions.

Revision ID: 002
Revises: 001
Create Date: 2025-10-06 11:13:10.889614+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables in proper dependency order"""
    
    # 1. Service Requests (parent table, no dependencies)
    op.create_table('service_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sr_number', sa.String(length=255), nullable=False),
        sa.Column('customer_account_number', sa.String(length=255), nullable=True),
        sa.Column('service_address', sa.Text(), nullable=True),
        sa.Column('service_city', sa.String(length=255), nullable=True),
        sa.Column('service_state', sa.String(length=100), nullable=True),
        sa.Column('service_postal_code', sa.String(length=50), nullable=True),
        sa.Column('incident_date', sa.DateTime(), nullable=True),
        sa.Column('closed_date', sa.DateTime(), nullable=True),
        sa.Column('severity', sa.String(length=100), nullable=True),
        sa.Column('machine_type', sa.String(length=255), nullable=True),
        sa.Column('machine_model', sa.String(length=255), nullable=True),
        sa.Column('machine_serial_number', sa.String(length=255), nullable=True),
        sa.Column('barrier_code', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sr_number')
    )
    op.create_index('idx_sr_customer_account', 'service_requests', ['customer_account_number'])
    op.create_index('idx_sr_incident_date', 'service_requests', ['incident_date'])
    op.create_index('idx_sr_country', 'service_requests', ['country'])
    op.create_index('idx_sr_service_state', 'service_requests', ['service_state'])
    op.create_index('idx_sr_service_city', 'service_requests', ['service_city'])
    
    # 2. Customers (independent table)
    op.create_table('customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_account_number', sa.String(length=255), nullable=False),
        sa.Column('customer_name', sa.Text(), nullable=True),
        sa.Column('address_line1', sa.Text(), nullable=True),
        sa.Column('address_line2', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=255), nullable=True),
        sa.Column('state', sa.String(length=255), nullable=True),
        sa.Column('postal_code', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_account_number')
    )
    
    # 3. Tasks (depends on service_requests)
    op.create_table('tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_number', sa.String(length=255), nullable=False),
        sa.Column('sr_number', sa.String(length=255), nullable=True),
        sa.Column('task_assignee_id', sa.String(length=255), nullable=True),
        sa.Column('assignee_name', sa.Text(), nullable=True),
        sa.Column('task_notes', sa.Text(), nullable=True),
        sa.Column('travel_time_hours', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('actual_time_hours', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['sr_number'], ['service_requests.sr_number'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_number')
    )
    op.create_index('idx_tasks_sr_number', 'tasks', ['sr_number'])
    op.create_index('idx_tasks_assignee', 'tasks', ['task_assignee_id'])
    
    # 4. Parts Used (depends on tasks)
    op.create_table('parts_used',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_number', sa.String(length=255), nullable=True),
        sa.Column('part_number', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('unit_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['task_number'], ['tasks.task_number'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_parts_task_number', 'parts_used', ['task_number'])
    
    # 5. SR Notes (depends on service_requests)
    op.create_table('sr_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sr_number', sa.String(length=255), nullable=True),
        sa.Column('customer_problem_summary', sa.Text(), nullable=True),
        sa.Column('sr_notes', sa.Text(), nullable=True),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('concat_comments', sa.Text(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['sr_number'], ['service_requests.sr_number'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notes_sr_number', 'sr_notes', ['sr_number'])



def downgrade() -> None:
    """Drop all tables in reverse dependency order"""

    # Drop service request tables
    op.drop_index('idx_notes_sr_number', table_name='sr_notes')
    op.drop_table('sr_notes')
    
    op.drop_index('idx_parts_task_number', table_name='parts_used')
    op.drop_table('parts_used')
    
    op.drop_index('idx_tasks_assignee', table_name='tasks')
    op.drop_index('idx_tasks_sr_number', table_name='tasks')
    op.drop_table('tasks')
    
    op.drop_table('customers')
    
    op.drop_index('idx_sr_service_city', table_name='service_requests')
    op.drop_index('idx_sr_service_state', table_name='service_requests')
    op.drop_index('idx_sr_country', table_name='service_requests')
    op.drop_index('idx_sr_incident_date', table_name='service_requests')
    op.drop_index('idx_sr_customer_account', table_name='service_requests')
    op.drop_table('service_requests')