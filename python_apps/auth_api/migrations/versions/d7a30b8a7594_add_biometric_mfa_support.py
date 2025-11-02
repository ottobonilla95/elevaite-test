"""add_biometric_mfa_support

Revision ID: d7a30b8a7594
Revises: fbbf8e6f17a5Create Date: 2025-10-27 13:24:17.546624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7a30b8a7594'
down_revision: Union[str, None] = 'fbbf8e6f17a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add biometric_mfa_enabled column to users table
    op.add_column('users', 
        sa.Column('biometric_mfa_enabled', sa.Boolean(), nullable=False, server_default='false')
    )
    
    # Create biometric_devices table
    op.create_table('biometric_devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_fingerprint', sa.String(length=255), nullable=False),
        sa.Column('device_name', sa.String(length=255), nullable=False),
        sa.Column('device_model', sa.String(length=255), nullable=True),
        sa.Column('public_key', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address_at_registration', sa.String(length=255), nullable=True),
        sa.Column('user_agent_at_registration', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_fingerprint')
    )
    op.create_index('ix_biometric_devices_id', 'biometric_devices', ['id'])
    op.create_index('ix_biometric_devices_user_id', 'biometric_devices', ['user_id'])
    op.create_index('ix_biometric_devices_device_fingerprint', 'biometric_devices', ['device_fingerprint'])


def downgrade() -> None:
    # Remove biometric_devices table
    op.drop_index('ix_biometric_devices_device_fingerprint', table_name='biometric_devices')
    op.drop_index('ix_biometric_devices_user_id', table_name='biometric_devices')
    op.drop_index('ix_biometric_devices_id', table_name='biometric_devices')
    op.drop_table('biometric_devices')
    
    # Remove biometric_mfa_enabled column
    op.drop_column('users', 'biometric_mfa_enabled')
