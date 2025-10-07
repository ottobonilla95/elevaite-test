"""Technician/Manager System Tables, Indexes, and Sequences.

This forms part of the initial post-hoc migration setup for the Toshiba Data Schema, reflecting the existing state of the database as of October 2025.
It includes four versions.

Revision ID: 003
Revises: 002
Create Date: 2025-10-06 11:14:01.368193+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables in proper dependency order"""
    
    # 6. FST Technicians (independent)
    op.create_table('fst_technicians',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fst_email', sa.String(length=255), nullable=False),
        sa.Column('fst_first_name', sa.String(length=255), nullable=True),
        sa.Column('fst_last_name', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fst_email')
    )
    op.create_index('idx_fst_email', 'fst_technicians', ['fst_email'])
    
    # 7. Manager Groups (independent)
    op.create_table('manager_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('manager_name', sa.String(length=255), nullable=False),
        sa.Column('manager_email', sa.String(length=255), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('group_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('manager_name')
    )
    op.create_index('idx_manager_name', 'manager_groups', ['manager_name'])
    
    # 8. FST Manager Assignments (junction table)
    op.create_table('fst_manager_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fst_id', sa.Integer(), nullable=True),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['fst_id'], ['fst_technicians.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['manager_id'], ['manager_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fst_id', 'manager_id', name='uq_fst_manager')
    )
    op.create_index('idx_fst_assignments', 'fst_manager_assignments', ['manager_id'])
    
    # 9. FST Manager Mapping (raw import data)
    op.create_table('fst_manager_mapping',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fst_email', sa.String(length=255), nullable=True),
        sa.Column('fst_first_name', sa.String(length=255), nullable=True),
        sa.Column('fst_last_name', sa.String(length=255), nullable=True),
        sa.Column('manager_name', sa.String(length=255), nullable=True),
        sa.Column('manager_email', sa.String(length=255), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fst_email', 'manager_name', name='uq_fst_manager_mapping')
    )
    op.create_index('idx_fst_mapping_email', 'fst_manager_mapping', ['fst_email'])
    op.create_index('idx_fst_mapping_manager', 'fst_manager_mapping', ['manager_name'])


def downgrade() -> None:
    """Drop all tables in reverse dependency order"""

   # Drop technician/manager tables
    op.drop_index('idx_fst_mapping_manager', table_name='fst_manager_mapping')
    op.drop_index('idx_fst_mapping_email', table_name='fst_manager_mapping')
    op.drop_table('fst_manager_mapping')
    
    op.drop_index('idx_fst_assignments', table_name='fst_manager_assignments')
    op.drop_table('fst_manager_assignments')
    
    op.drop_index('idx_manager_name', table_name='manager_groups')
    op.drop_table('manager_groups')
    
    op.drop_index('idx_fst_email', table_name='fst_technicians')
    op.drop_table('fst_technicians')
    
