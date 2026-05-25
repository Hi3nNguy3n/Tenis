"""add_player_body_metrics

Revision ID: 7c6b18d1a2f0
Revises: 1f26b7c2c32e
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c6b18d1a2f0"
down_revision: Union[str, Sequence[str], None] = "1f26b7c2c32e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("players", sa.Column("height_cm", sa.Integer(), nullable=True))
    op.add_column("players", sa.Column("weight_kg", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("players", "weight_kg")
    op.drop_column("players", "height_cm")
