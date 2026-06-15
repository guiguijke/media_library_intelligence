"""external_classics genre_ids

Revision ID: 0004_external_classics_genre_ids
Revises: 0003_tmdb_collections
Create Date: 2026-06-15 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_external_classics_genre_ids"
down_revision: Union[str, None] = "0003_tmdb_collections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("external_classics", sa.Column("genre_ids", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("external_classics", "genre_ids")
