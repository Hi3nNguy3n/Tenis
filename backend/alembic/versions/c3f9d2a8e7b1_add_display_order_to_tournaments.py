"""add display order to tournaments

Revision ID: c3f9d2a8e7b1
Revises: 57535b602a1b
Create Date: 2026-05-30 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3f9d2a8e7b1"
down_revision: Union[str, Sequence[str], None] = "57535b602a1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(table_name)


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    columns = sa.inspect(bind).get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    indexes = sa.inspect(bind).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def upgrade() -> None:
    if not _has_table("tournaments"):
        return

    if not _has_column("tournaments", "display_order"):
        op.add_column(
            "tournaments",
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        )

    if not _has_index("tournaments", "ix_tournaments_display_order"):
        op.create_index("ix_tournaments_display_order", "tournaments", ["display_order"], unique=False)


def downgrade() -> None:
    if not _has_table("tournaments"):
        return

    if _has_index("tournaments", "ix_tournaments_display_order"):
        op.drop_index("ix_tournaments_display_order", table_name="tournaments")

    if _has_column("tournaments", "display_order"):
        op.drop_column("tournaments", "display_order")
