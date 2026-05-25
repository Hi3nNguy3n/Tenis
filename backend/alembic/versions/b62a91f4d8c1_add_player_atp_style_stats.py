"""add player atp style stats

Revision ID: b62a91f4d8c1
Revises: a41f7b9c8d23
Create Date: 2026-05-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b62a91f4d8c1"
down_revision: Union[str, None] = "a41f7b9c8d23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COUNT_COLUMNS = [
    "aces",
    "double_faults",
    "break_points_faced",
    "service_games_played",
    "break_points_opportunities",
    "return_games_played",
]

PERCENT_COLUMNS = [
    "first_serve_pct",
    "first_serve_points_won_pct",
    "second_serve_points_won_pct",
    "break_points_saved_pct",
    "service_games_won_pct",
    "total_service_points_won_pct",
    "first_serve_return_points_won_pct",
    "second_serve_return_points_won_pct",
    "break_points_converted_pct",
    "return_games_won_pct",
    "return_points_won_pct",
    "total_points_won_pct",
]


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return any(column["name"] == column_name for column in sa.inspect(bind).get_columns(table_name))


def upgrade() -> None:
    for column_name in COUNT_COLUMNS:
        if not _has_column("players", column_name):
            op.add_column(
                "players",
                sa.Column(column_name, sa.Integer(), nullable=False, server_default="0"),
            )

    for column_name in PERCENT_COLUMNS:
        if not _has_column("players", column_name):
            op.add_column(
                "players",
                sa.Column(column_name, sa.Numeric(5, 2), nullable=False, server_default="0"),
            )


def downgrade() -> None:
    for column_name in reversed(PERCENT_COLUMNS):
        if _has_column("players", column_name):
            op.drop_column("players", column_name)

    for column_name in reversed(COUNT_COLUMNS):
        if _has_column("players", column_name):
            op.drop_column("players", column_name)
