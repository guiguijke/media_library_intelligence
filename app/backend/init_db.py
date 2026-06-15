"""Standalone helper to initialise / baseline the database via Alembic."""
import asyncio
import logging

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.database import engine
from app.models import Base  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _alembic_config() -> Config:
    return Config("alembic.ini")


def run_stamp_head() -> None:
    command.stamp(_alembic_config(), "head")


def run_upgrade() -> None:
    command.upgrade(_alembic_config(), "head")


async def init_db() -> None:
    async with engine.begin() as conn:
        # Create tables if they don't exist yet (no-op for existing databases).
        await conn.run_sync(Base.metadata.create_all)
        # Baseline legacy or freshly-created databases so Alembic can take over.
        has_version_table = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).has_table("alembic_version")
        )

    if not has_version_table:
        await asyncio.to_thread(run_stamp_head)

    await asyncio.to_thread(run_upgrade)
    logger.info("Database migrated to head successfully")


if __name__ == "__main__":
    asyncio.run(init_db())
