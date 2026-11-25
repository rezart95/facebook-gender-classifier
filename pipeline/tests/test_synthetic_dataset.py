import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from typer.testing import CliRunner

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.cli import app
from fbgc_pipeline.synthetic.privacy_check import DistanceCheck, SyntheticPrivacyError
from fbgc_pipeline.synthetic.synthetic_dataset import (
    SyntheticSizeError,
    build_synthetic,
    wide_features,
    write_synthetic,
)

CHECK = "fbgc_pipeline.synthetic.synthetic_dataset.distance_to_closest_record"


def anonymized(n: int = 60) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Invented anonymized tables in the private layout (participants + long features)."""
    rng = np.random.default_rng(5)
    pids = [f"P{rank:03d}" for rank in range(1, n + 1)]
    participants = pd.DataFrame(
        {
            "pid": pids,
            "wave": rng.choice([1, 2], size=n),
            "gender": rng.choice(["F", "M"], size=n),
            "age_band": rng.choice(["20", "21"], size=n),
            "relationship": rng.choice(["single", "unknown"], size=n),
            "has_messages": True,
            "has_survey": True,
        }
    )
    wide = pd.DataFrame(
        {
            "pid": pids,
            "msg_count": rng.poisson(40, size=n).astype(float),
            "gpius_total": rng.uniform(1, 8, size=n),
        }
    )
    long = wide.melt(id_vars="pid", var_name="feature_key", value_name="value")
    return participants, long


def test_wide_features_follow_the_pids_and_the_catalogue_order() -> None:
    participants, long = anonymized()
    pids = participants["pid"].tolist()[::-1]
    wide = wide_features(long, pids, default_catalogue())
    assert list(wide.columns) == ["msg_count", "gpius_total"]
    first = long[(long["pid"] == pids[0]) & (long["feature_key"] == "msg_count")]["value"]
    assert wide.loc[0, "msg_count"] == first.item()


def test_build_synthetic_returns_synthetic_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CHECK, lambda real, synthetic: DistanceCheck(2.0, 1.0))
    dataset = build_synthetic(*anonymized(), default_catalogue(), seed=1)
    assert dataset.participants["pid"].tolist()[:2] == ["S001", "S002"]
    assert list(dataset.features.columns) == ["pid", "msg_count", "gpius_total"]
    assert len(dataset.features) == 60


def test_a_failed_distance_check_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CHECK, lambda real, synthetic: DistanceCheck(0.5, 1.0))
    with pytest.raises(SyntheticPrivacyError, match="too close"):
        build_synthetic(*anonymized(), default_catalogue(), seed=1)


def test_real_rows_that_are_not_distinct_raise_a_distinct_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(CHECK, lambda real, synthetic: DistanceCheck(5.0, 0.0))
    with pytest.raises(SyntheticPrivacyError, match="not distinct enough"):
        build_synthetic(*anonymized(), default_catalogue(), seed=1)


def test_write_synthetic_writes_lf_csv_and_parquet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(CHECK, lambda real, synthetic: DistanceCheck(2.0, 1.0))
    dataset = build_synthetic(*anonymized(), default_catalogue(), seed=1)
    sizes = write_synthetic(dataset, tmp_path / "out")
    assert set(sizes) == {"participants.csv", "features.parquet"}
    assert b"\r\n" not in (tmp_path / "out" / "participants.csv").read_bytes()
    back = pd.read_parquet(tmp_path / "out" / "features.parquet")
    assert back.shape == (60, 3)
    with pytest.raises(SyntheticSizeError):
        write_synthetic(dataset, tmp_path / "small", max_bytes=100)
    assert not (tmp_path / "small").exists()


def private_anonymized(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    folder = tmp_path / "private" / "anonymized"
    folder.mkdir(parents=True)
    participants, long = anonymized()
    participants.to_parquet(folder / "participants.parquet", index=False)
    long.to_parquet(folder / "features_long.parquet", index=False)
    (tmp_path / "raw").mkdir()
    monkeypatch.setenv("FBGC_RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("FBGC_PRIVATE_DIR", str(tmp_path / "private"))


def test_cli_synth_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    private_anonymized(tmp_path, monkeypatch)
    monkeypatch.setattr(CHECK, lambda real, synthetic: DistanceCheck(2.0, 1.0))
    args = ["synth-data", "--out", str(tmp_path / "public"), "--shrinkage", "0.25"]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    summary = json.loads(result.output)
    assert (summary["rows"], summary["features"], summary["shrinkage"]) == (60, 2, 0.25)
    assert summary["features_dropped_sparse"] == 0
    people = pd.read_csv(tmp_path / "public" / "participants.csv")
    assert not people["pid"].str.startswith("P").any()


def test_cli_synth_data_writes_nothing_when_the_check_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private_anonymized(tmp_path, monkeypatch)
    monkeypatch.setattr(CHECK, lambda real, synthetic: DistanceCheck(0.5, 1.0))
    result = CliRunner().invoke(app, ["synth-data", "--out", str(tmp_path / "public")])
    assert result.exit_code == 1
    assert "too close" in result.output
    assert not (tmp_path / "public").exists()
