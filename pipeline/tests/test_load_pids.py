from pathlib import Path

import pandas as pd
import pytest

from fbgc_pipeline.load.sources import LoadError, private_bundle, synthetic_bundle


def synthetic_folder(
    tmp_path: Path, pids: list[str], feature_pids: list[str] | None = None
) -> Path:
    folder = tmp_path / "synthetic"
    folder.mkdir()
    pd.DataFrame({"pid": pids, "gender": "F"}).to_csv(folder / "participants.csv", index=False)
    pd.DataFrame({"pid": feature_pids or pids, "msg_count": 1.0}).to_parquet(
        folder / "features.parquet", index=False
    )
    return folder


def private_folder(tmp_path: Path, pids: list[str], feature_pids: list[str] | None = None) -> Path:
    folder = tmp_path / "anonymized"
    folder.mkdir()
    pd.DataFrame({"pid": pids, "gender": "F"}).to_parquet(folder / "participants.parquet")
    pd.DataFrame(
        {"pid": feature_pids or pids, "feature_key": "msg_count", "value": 1.0}
    ).to_parquet(folder / "features_long.parquet")
    return folder


@pytest.fixture
def no_traces(tmp_path: Path) -> Path:
    folder = tmp_path / "demo"
    folder.mkdir()
    return folder


def test_synthetic_bundle_accepts_synthetic_ids(tmp_path: Path, no_traces: Path) -> None:
    bundle = synthetic_bundle(synthetic_folder(tmp_path, ["S001", "S002"]), no_traces)
    assert len(bundle.participants) == 2


@pytest.mark.parametrize("bad", ["P001", "S01", "S001x", "xS001", "S", "s001"])
def test_synthetic_bundle_refuses_other_ids_in_participants(
    tmp_path: Path, no_traces: Path, bad: str
) -> None:
    folder = synthetic_folder(tmp_path, ["S001", bad, bad, "S002"])
    with pytest.raises(LoadError) as raised:
        synthetic_bundle(folder, no_traces)
    assert str(raised.value) == "1 participant ids are not synthetic S-IDs"


def test_synthetic_bundle_refuses_other_ids_in_the_features(
    tmp_path: Path, no_traces: Path
) -> None:
    folder = synthetic_folder(tmp_path, ["S001", "S002"], ["S001", "P002"])
    with pytest.raises(LoadError, match="1 participant ids are not synthetic S-IDs"):
        synthetic_bundle(folder, no_traces)


def test_private_bundle_accepts_private_ids(tmp_path: Path, no_traces: Path) -> None:
    bundle = private_bundle(private_folder(tmp_path, ["P001", "P1000"]), no_traces)
    assert len(bundle.participants) == 2


@pytest.mark.parametrize("bad", ["S001", "P01", "P001x", "xP001", "P"])
def test_private_bundle_refuses_other_ids(tmp_path: Path, no_traces: Path, bad: str) -> None:
    folder = private_folder(tmp_path, ["P001", bad])
    with pytest.raises(LoadError, match="1 participant ids are not private P-IDs"):
        private_bundle(folder, no_traces)


def test_private_bundle_refuses_other_ids_in_the_features(tmp_path: Path, no_traces: Path) -> None:
    folder = private_folder(tmp_path, ["P001", "P002"], ["P001", "S002"])
    with pytest.raises(LoadError, match="1 participant ids are not private P-IDs"):
        private_bundle(folder, no_traces)
