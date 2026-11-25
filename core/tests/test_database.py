from pathlib import Path

import yaml
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from fbgc_core.db.migrate import upgrade_to_head
from fbgc_core.db.models import Base

CORE = Path(__file__).resolve().parents[1]
TABLES = {
    "participants",
    "feature_catalogue",
    "feature_values",
    "model_runs",
    "model_metrics",
    "model_coefficients",
    "predictions",
    "stepwise_trace",
    "pipeline_traces",
}


def sqlite_url(tmp_path: Path) -> str:
    return f"sqlite:///{(tmp_path / 'fbgc.sqlite').as_posix()}"


def test_models_cover_the_spec_tables() -> None:
    assert set(Base.metadata.tables) == TABLES


def test_the_migration_builds_exactly_the_model_schema(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path)
    upgrade_to_head(url)
    inspector = inspect(create_engine(url))
    assert set(inspector.get_table_names()) == TABLES | {"alembic_version"}
    for name, table in Base.metadata.tables.items():
        columns = {column["name"]: column["nullable"] for column in inspector.get_columns(name)}
        assert columns == {column.name: column.nullable for column in table.columns}, name
        primary = inspector.get_pk_constraint(name)["constrained_columns"]
        assert set(primary) == {column.name for column in table.primary_key.columns}, name
        found = {
            (fk["referred_table"], tuple(fk["constrained_columns"]))
            for fk in inspector.get_foreign_keys(name)
        }
        expected = {(fk.column.table.name, (fk.parent.name,)) for fk in table.foreign_keys}
        assert found == expected, name


def test_upgrading_twice_is_a_no_op(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path)
    upgrade_to_head(url)
    upgrade_to_head(url)
    assert "participants" in inspect(create_engine(url)).get_table_names()


def test_alembic_ini_finds_the_migrations() -> None:
    script = ScriptDirectory.from_config(Config(str(CORE / "alembic.ini")))
    assert script.get_current_head() == "0001"


def test_local_postgres_is_postgres_17_bound_to_localhost() -> None:
    compose = CORE.parent / "infra" / "docker-compose.yml"
    service = yaml.safe_load(compose.read_text(encoding="utf-8"))["services"]["postgres"]
    assert service["image"] == "postgres:17"
    assert all(port.startswith("127.0.0.1:") for port in service["ports"])
