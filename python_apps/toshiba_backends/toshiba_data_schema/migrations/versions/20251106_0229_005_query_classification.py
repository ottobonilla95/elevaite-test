"""Adding query classification columns to chat_data_final

Revision ID: eaed14383849
Revises: 004
Create Date: 2025-11-06 02:29:28.283538+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('chat_data_final', sa.Column('query_type', sa.String(255), nullable=True))
    op.add_column('chat_data_final', sa.Column('machine_type', sa.String(255), nullable=True))
    op.add_column('chat_data_final', sa.Column('machine_model', sa.String(255), nullable=True))
    op.add_column('chat_data_final', sa.Column('machine_name', sa.String(255), nullable=True))
    op.add_column('chat_data_final', sa.Column('customer_name', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('chat_data_final', 'query_type')
    op.drop_column('chat_data_final', 'machine_type')
    op.drop_column('chat_data_final', 'machine_model')
    op.drop_column('chat_data_final', 'machine_name')
    op.drop_column('chat_data_final', 'customer_name')