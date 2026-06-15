"""wishlist external ids

Revision ID: 0002_wishlist_external_ids
Revises: 0001_initial
Create Date: 2026-06-15 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_wishlist_external_ids"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("wishlist", sa.Column("tmdb_id", sa.Integer(), nullable=True))
    op.add_column("wishlist", sa.Column("tvdb_id", sa.Integer(), nullable=True))
    op.add_column("wishlist", sa.Column("anilist_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_wishlist_tmdb_id"), "wishlist", ["tmdb_id"], unique=False
    )
    op.create_index(
        op.f("ix_wishlist_tvdb_id"), "wishlist", ["tvdb_id"], unique=False
    )
    op.create_index(
        op.f("ix_wishlist_anilist_id"), "wishlist", ["anilist_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_wishlist_anilist_id"), table_name="wishlist")
    op.drop_index(op.f("ix_wishlist_tvdb_id"), table_name="wishlist")
    op.drop_index(op.f("ix_wishlist_tmdb_id"), table_name="wishlist")
    op.drop_column("wishlist", "anilist_id")
    op.drop_column("wishlist", "tvdb_id")
    op.drop_column("wishlist", "tmdb_id")
