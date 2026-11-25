import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, text
from typer.testing import CliRunner

from fbgc_core.catalogue import default_catalogue
from fbgc_core.db.migrate import upgrade_to_head
from fbgc_pipeline.cli import app
from fbgc_pipeline.load.database_load import is_local_database, load_database
from fbgc_pipeline.load.sources import LoadError, synthetic_bundle


def synthetic_dir(tmp_path: Path) -> Path:
    folder = tmp_path / "synthetic"
    folder.mkdir()
    pids = ["S001", "S002", "S003"]
    pd.DataFrame(
        {
            "pid": pids,
            "wave": [1, 2, 1],
            "gender": ["F", "M", "F"],
            "age_band": ["20", "21", "20"],
            "relationship": ["single", "unknown", "single"],
            "has_messages": [True, True, False],
            "has_survey": [True, False, True],
        }
    ).to_csv(folder / "participants.csv", index=False, lineterminator="\n")
    features = pd.DataFrame(
        {"pid": pids, "msg_count": [5.0, 7.0, np.nan], "gpius_total": [2.5, np.nan, 3.0]}
    )
    features.to_parquet(folder / "features.parquet", index=False)
    return folder


def demo_dir(tmp_path: Path) -> Path:
    folder = tmp_path / "demo"
    folder.mkdir()
    trace = {"profile_label": "fake-01", "stages": [{"stage": "raw_html", "snippet": "<p>"}]}
    (folder / "trace-fake-01.json").write_text(json.dumps(trace), encoding="utf-8")
    return folder


def database(tmp_path: Path) -> str:
    url = f"sqlite:///{(tmp_path / 'fbgc.sqlite').as_posix()}"
    upgrade_to_head(url)
    return url


def count(url: str, table: str) -> int:
    with create_engine(url).connect() as connection:
        return int(connection.execute(text(f"select count(*) from {table}")).scalar_one())


def test_load_is_idempotent(tmp_path: Path) -> None:
    url = database(tmp_path)
    bundle = synthetic_bundle(synthetic_dir(tmp_path), demo_dir(tmp_path))
    first = load_database(url, bundle, default_catalogue())
    second = load_database(url, bundle, default_catalogue())
    assert (
        first
        == second
        == {
            "catalogue": 577,
            "participants": 3,
            "feature_values": 4,
            "traces": 1,
        }
    )
    assert [count(url, t) for t in ("feature_catalogue", "participants", "feature_values")] == [
        577,
        3,
        4,
    ]
    assert count(url, "pipeline_traces") == 1


def test_bands_that_look_like_numbers_stay_text(tmp_path: Path) -> None:
    bundle = synthetic_bundle(synthetic_dir(tmp_path), demo_dir(tmp_path))
    assert bundle.participants["age_band"].tolist() == ["20", "21", "20"]


def test_unknown_feature_keys_are_refused(tmp_path: Path) -> None:
    folder = synthetic_dir(tmp_path)
    wide = pd.read_parquet(folder / "features.parquet").assign(free_text=1.0)
    wide.to_parquet(folder / "features.parquet", index=False)
    bundle = synthetic_bundle(folder, demo_dir(tmp_path))
    with pytest.raises(LoadError, match="free_text"):
        load_database(database(tmp_path), bundle, default_catalogue())


def test_local_database_urls() -> None:
    assert is_local_database("sqlite:///x.sqlite")
    assert is_local_database("postgresql+psycopg://u:p@127.0.0.1:5433/fbgc")
    assert is_local_database("postgresql+psycopg://u:p@localhost/fbgc")
    assert not is_local_database("postgresql+psycopg://u:p@db.example.org/fbgc")


def test_cli_load_synthetic(tmp_path: Path) -> None:
    url = database(tmp_path)
    args = ["load", "--synthetic", "--database-url", url]
    args += ["--from", str(synthetic_dir(tmp_path)), "--traces", str(demo_dir(tmp_path))]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["participants"] == 3
    assert "sqlite" not in result.output


def test_cli_load_needs_exactly_one_source(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'x.sqlite').as_posix()}"
    for flags in ([], ["--private", "--synthetic"]):
        result = CliRunner().invoke(app, ["load", *flags, "--database-url", url])
        assert result.exit_code == 2
        assert "exactly one" in result.output


def test_cli_load_private_refuses_a_remote_database() -> None:
    url = "postgresql+psycopg://u:p@db.example.org/fbgc"
    result = CliRunner().invoke(app, ["load", "--private", "--database-url", url])
    assert result.exit_code == 1
    assert "local database" in result.output


def test_cli_load_reports_missing_inputs(tmp_path: Path) -> None:
    url = database(tmp_path)
    args = ["load", "--synthetic", "--database-url", url, "--from", str(tmp_path / "none")]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1
    assert "missing input files" in result.output
