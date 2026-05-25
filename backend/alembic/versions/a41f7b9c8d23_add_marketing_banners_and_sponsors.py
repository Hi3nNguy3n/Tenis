"""add marketing banners and sponsors

Revision ID: a41f7b9c8d23
Revises: 7c6b18d1a2f0
Create Date: 2026-05-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a41f7b9c8d23"
down_revision: Union[str, None] = "7c6b18d1a2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(table_name)


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    indexes = sa.inspect(bind).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=False)


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    if _has_table(table_name) and _has_index(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    if not _has_table("marketing_banners"):
        op.create_table(
            "marketing_banners",
            sa.Column("id", sa.BigInteger(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("subtitle", sa.String(length=255), nullable=True),
            sa.Column("image_url", sa.String(length=500), nullable=False),
            sa.Column("link_url", sa.String(length=500), nullable=True),
            sa.Column("placement", sa.String(length=50), nullable=False, server_default="home_top"),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("open_in_new_tab", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("start_at", sa.DateTime(), nullable=True),
            sa.Column("end_at", sa.DateTime(), nullable=True),
            sa.Column("created_by", sa.BigInteger(), nullable=True),
            sa.Column("updated_by", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing(op.f("ix_marketing_banners_id"), "marketing_banners", ["id"])
    _create_index_if_missing(op.f("ix_marketing_banners_placement"), "marketing_banners", ["placement"])
    _create_index_if_missing(op.f("ix_marketing_banners_display_order"), "marketing_banners", ["display_order"])
    _create_index_if_missing(op.f("ix_marketing_banners_is_active"), "marketing_banners", ["is_active"])
    _create_index_if_missing(op.f("ix_marketing_banners_start_at"), "marketing_banners", ["start_at"])
    _create_index_if_missing(op.f("ix_marketing_banners_end_at"), "marketing_banners", ["end_at"])
    _create_index_if_missing(op.f("ix_marketing_banners_created_by"), "marketing_banners", ["created_by"])
    _create_index_if_missing(op.f("ix_marketing_banners_updated_by"), "marketing_banners", ["updated_by"])

    if not _has_table("sponsors"):
        op.create_table(
            "sponsors",
            sa.Column("id", sa.BigInteger(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("logo_url", sa.String(length=500), nullable=False),
            sa.Column("website_url", sa.String(length=500), nullable=True),
            sa.Column("tier", sa.String(length=50), nullable=False, server_default="partner"),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("start_at", sa.DateTime(), nullable=True),
            sa.Column("end_at", sa.DateTime(), nullable=True),
            sa.Column("created_by", sa.BigInteger(), nullable=True),
            sa.Column("updated_by", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing(op.f("ix_sponsors_id"), "sponsors", ["id"])
    _create_index_if_missing(op.f("ix_sponsors_tier"), "sponsors", ["tier"])
    _create_index_if_missing(op.f("ix_sponsors_display_order"), "sponsors", ["display_order"])
    _create_index_if_missing(op.f("ix_sponsors_is_active"), "sponsors", ["is_active"])
    _create_index_if_missing(op.f("ix_sponsors_start_at"), "sponsors", ["start_at"])
    _create_index_if_missing(op.f("ix_sponsors_end_at"), "sponsors", ["end_at"])
    _create_index_if_missing(op.f("ix_sponsors_created_by"), "sponsors", ["created_by"])
    _create_index_if_missing(op.f("ix_sponsors_updated_by"), "sponsors", ["updated_by"])


def downgrade() -> None:
    _drop_index_if_exists(op.f("ix_sponsors_updated_by"), "sponsors")
    _drop_index_if_exists(op.f("ix_sponsors_created_by"), "sponsors")
    _drop_index_if_exists(op.f("ix_sponsors_end_at"), "sponsors")
    _drop_index_if_exists(op.f("ix_sponsors_start_at"), "sponsors")
    _drop_index_if_exists(op.f("ix_sponsors_is_active"), "sponsors")
    _drop_index_if_exists(op.f("ix_sponsors_display_order"), "sponsors")
    _drop_index_if_exists(op.f("ix_sponsors_tier"), "sponsors")
    _drop_index_if_exists(op.f("ix_sponsors_id"), "sponsors")
    if _has_table("sponsors"):
        op.drop_table("sponsors")

    _drop_index_if_exists(op.f("ix_marketing_banners_updated_by"), "marketing_banners")
    _drop_index_if_exists(op.f("ix_marketing_banners_created_by"), "marketing_banners")
    _drop_index_if_exists(op.f("ix_marketing_banners_end_at"), "marketing_banners")
    _drop_index_if_exists(op.f("ix_marketing_banners_start_at"), "marketing_banners")
    _drop_index_if_exists(op.f("ix_marketing_banners_is_active"), "marketing_banners")
    _drop_index_if_exists(op.f("ix_marketing_banners_display_order"), "marketing_banners")
    _drop_index_if_exists(op.f("ix_marketing_banners_placement"), "marketing_banners")
    _drop_index_if_exists(op.f("ix_marketing_banners_id"), "marketing_banners")
    if _has_table("marketing_banners"):
        op.drop_table("marketing_banners")
