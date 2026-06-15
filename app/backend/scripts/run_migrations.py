#!/usr/bin/env python3
"""Standalone helper to run Alembic migrations.

Usage:
    python scripts/run_migrations.py
"""
from alembic import command
from alembic.config import Config


def main() -> None:
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    main()
