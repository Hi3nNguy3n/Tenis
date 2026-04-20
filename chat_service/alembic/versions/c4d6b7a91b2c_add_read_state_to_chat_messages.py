"""Add read state to chat_messages

Revision ID: c4d6b7a91b2c
Revises: 01bc6b0d018f
Create Date: 2026-04-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d6b7a91b2c'
down_revision: Union[str, Sequence[str], None] = '01bc6b0d018f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_messages', sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('chat_messages', sa.Column('read_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('chat_messages', 'read_at')
    op.drop_column('chat_messages', 'is_read')
