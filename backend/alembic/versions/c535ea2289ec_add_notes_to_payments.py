"""add_notes_to_payments

Revision ID: c535ea2289ec
Revises: 5d9f83afcf0b
Create Date: 2026-06-21 14:40:44.511311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c535ea2289ec'
down_revision: Union[str, Sequence[str], None] = '5d9f83afcf0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('payments', sa.Column('notes', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('payments', 'notes')
