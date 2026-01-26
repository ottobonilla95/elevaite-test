"""add a2a_agents table

Revision ID: a2a_agents_001
Revises: 4b8967571d58
Create Date: 2025-12-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'a2a_agents_001'
down_revision: Union[str, None] = '4b8967571d58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add a2a_agents table for storing external A2A agent registrations."""
    op.create_table('a2a_agents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        
        # Connection info
        sa.Column('base_url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('agent_card_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        
        # Agent Card data (cached from remote)
        sa.Column('agent_card', sa.JSON(), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('supported_input_modes', sa.JSON(), nullable=True),
        sa.Column('supported_output_modes', sa.JSON(), nullable=True),
        
        # Protocol version
        sa.Column('protocol_version', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        
        # Authentication
        sa.Column('auth_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='none'),
        sa.Column('auth_config', sa.JSON(), nullable=True),
        
        # Health check settings
        sa.Column('health_check_interval', sa.Integer(), nullable=False, server_default='300'),
        
        # Status & Health
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='active'),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        
        # Organization/multi-tenancy
        sa.Column('organization_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('created_by', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        
        # Timestamps
        sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on base_url for faster lookups
    op.create_index('ix_a2a_agents_base_url', 'a2a_agents', ['base_url'], unique=False)
    
    # Create index on organization_id for multi-tenant queries
    op.create_index('ix_a2a_agents_organization_id', 'a2a_agents', ['organization_id'], unique=False)
    
    # Create index on status for filtering active agents
    op.create_index('ix_a2a_agents_status', 'a2a_agents', ['status'], unique=False)


def downgrade() -> None:
    """Remove a2a_agents table."""
    op.drop_index('ix_a2a_agents_status', table_name='a2a_agents')
    op.drop_index('ix_a2a_agents_organization_id', table_name='a2a_agents')
    op.drop_index('ix_a2a_agents_base_url', table_name='a2a_agents')
    op.drop_table('a2a_agents')

