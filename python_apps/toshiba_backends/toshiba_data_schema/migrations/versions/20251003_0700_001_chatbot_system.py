"""ChatBot System Tables, Indexes, and Sequences.

This forms part of the initial post-hoc migration setup for the Toshiba Data Schema, reflecting the existing state of the database as of October 2025.
It includes four versions.

Revision ID: 001
Revises: 
Create Date: 2025-10-03 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables in proper dependency order"""

    # 13. Chat Data Final (main chat table)
    op.create_table('chat_data_final',
        sa.Column('qid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sr_ticket_id', sa.String(), nullable=True),
        sa.Column('original_request', sa.String(), nullable=True),
        sa.Column('request', sa.String(), nullable=True),
        sa.Column('request_timestamp', sa.DateTime(), nullable=True),
        sa.Column('response', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('response_timestamp', sa.DateTime(), nullable=True),
        sa.Column('vote', sa.Integer(), server_default='0', nullable=True),
        sa.Column('vote_timestamp', sa.DateTime(), nullable=True),
        sa.Column('feedback', sa.String(), server_default='', nullable=True),
        sa.Column('feedback_timestamp', sa.DateTime(), nullable=True),
        sa.Column('agent_flow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('qid')
    )
    op.create_index('idx_chat_session_id', 'chat_data_final', ['session_id'])
    op.create_index('idx_chat_user_id', 'chat_data_final', ['user_id'])
    
    # 14. Agent Flow Data
    op.create_table('agent_flow_data',
        sa.Column('agent_flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('qid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('request', sa.String(), nullable=True),
        sa.Column('response', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('tries', sa.Integer(), server_default='0', nullable=True),
        sa.Column('tool_calls', sa.String(), nullable=True),
        sa.Column('chat_history', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('agent_flow_id')
    )
    op.create_index('idx_agent_session_id', 'agent_flow_data', ['session_id'])
    op.create_index('idx_agent_qid', 'agent_flow_data', ['qid'])
    
    # 15. SR Number Data
    op.create_table('sr_number_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sr_number', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sr_number_session', 'sr_number_data', ['session_id'])


def downgrade() -> None:
    """Drop all tables in reverse dependency order"""
    
    # Drop chatbot tables
    op.drop_index('idx_sr_number_session', table_name='sr_number_data')
    op.drop_table('sr_number_data')
    
    op.drop_index('idx_agent_qid', table_name='agent_flow_data')
    op.drop_index('idx_agent_session_id', table_name='agent_flow_data')
    op.drop_table('agent_flow_data')
    
    op.drop_index('idx_chat_user_id', table_name='chat_data_final')
    op.drop_index('idx_chat_session_id', table_name='chat_data_final')
    op.drop_table('chat_data_final')
