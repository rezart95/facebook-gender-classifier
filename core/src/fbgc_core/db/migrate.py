"""Run the Alembic migrations from code (shell: `alembic -c core/alembic.ini upgrade head`)."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

MIGRATIONS_DIR = Path(__file__).with_name("migrations")


def alembic_config(url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("path_separator", "os")
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))  # ini interpolation
    return config


def upgrade_to_head(url: str) -> None:
    command.upgrade(alembic_config(url), "head")
