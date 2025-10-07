"""Machine Classification System, Indexes, and Sequences.

This forms part of the initial post-hoc migration setup for the Toshiba Data Schema, reflecting the existing state of the database as of October 2025.
It includes four versions.

Revision ID: 004
Revises: 003
Create Date: 2025-10-06 11:14:17.523470+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables in proper dependency order"""
    
    # 10. Toshiba Machine Types
    op.create_table('toshiba_machine_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('machine_number', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('classification', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('machine_number')
    )
    op.create_index('idx_toshiba_machine_number', 'toshiba_machine_types', ['machine_number'])
    
    # 11. Machine Type Models
    op.create_table('machine_type_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('machine_number', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('classification', sa.String(length=100), nullable=True),
        sa.Column('machine_type', sa.String(length=10), nullable=True),
        sa.Column('machine_model', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('machine_number')
    )
    op.create_index('idx_machine_type', 'machine_type_models', ['machine_type'])
    op.create_index('idx_machine_model', 'machine_type_models', ['machine_model'])
    op.create_index('idx_classification', 'machine_type_models', ['classification'])
    
    # 12. Machine Type Lookup (fast classification)
    op.create_table('machine_type_lookup',
        sa.Column('machine_type', sa.String(length=50), nullable=False),
        sa.Column('product_category', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('machine_type')
    )
    

def downgrade() -> None:
    """Drop all tables in reverse dependency order"""

    # Drop machine classification tables
    op.drop_table('machine_type_lookup')
    
    op.drop_index('idx_classification', table_name='machine_type_models')
    op.drop_index('idx_machine_model', table_name='machine_type_models')
    op.drop_index('idx_machine_type', table_name='machine_type_models')
    op.drop_table('machine_type_models')
    
    op.drop_index('idx_toshiba_machine_number', table_name='toshiba_machine_types')
    op.drop_table('toshiba_machine_types')