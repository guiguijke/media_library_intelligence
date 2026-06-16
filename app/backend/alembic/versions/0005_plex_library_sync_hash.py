"""plex_library sync_hash

Revision ID: 0005_plex_library_sync_hash
Revises: 0004_external_classics_genre_ids
Create Date: 2026-06-15 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_plex_library_sync_hash"
down_revision: Union[str, None] = "0004_external_classics_genre_ids"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("plex_library", sa.Column("sync_hash", sa.String(), nullable=True))
    op.create_index("ix_plex_library_sync_hash", "plex_library", ["sync_hash"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_plex_library_sync_hash", table_name="plex_library")
    op.drop_column("plex_library", "sync_hash")
