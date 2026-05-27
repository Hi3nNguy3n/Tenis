"""add_banner_url_to_tournaments

Revision ID: 57535b602a1b
Revises: 6c57d82979f8
Create Date: 2026-05-27 15:21:35.847732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57535b602a1b'
down_revision: Union[str, Sequence[str], None] = '6c57d82979f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tournaments', sa.Column('banner_url', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tournaments', 'banner_url')
