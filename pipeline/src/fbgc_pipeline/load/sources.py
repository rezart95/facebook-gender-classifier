"""What `fbgc load` reads: participants, feature values (long) and the demo traces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

TEXT_COLUMNS = {"pid": str, "gender": str, "age_band": str, "relationship": str}


class LoadError(ValueError):
    """The inputs of a load are missing or inconsistent."""


@dataclass(frozen=True)
class LoadBundle:
    participants: pd.DataFrame
    features_long: pd.DataFrame  # pid, feature_key, value; no missing values
    traces: list[dict[str, object]]


def require(*paths: Path) -> None:
    missing = [path.name for path in paths if not path.is_file()]
    if missing:
        raise LoadError(f"missing input files: {missing}")


def read_traces(demo_dir: Path) -> list[dict[str, object]]:
    traces: list[dict[str, object]] = []
    for path in sorted(demo_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        traces.append(
            {
                "trace_id": path.stem,
                "profile_label": data["profile_label"],
                "stages": data["stages"],
            }
        )
    return traces


def private_bundle(anonymized_dir: Path, demo_dir: Path) -> LoadBundle:
    participants, values = (
        anonymized_dir / "participants.parquet",
        anonymized_dir / "features_long.parquet",
    )
    require(participants, values)
    return LoadBundle(pd.read_parquet(participants), pd.read_parquet(values), read_traces(demo_dir))


def synthetic_bundle(synthetic_dir: Path, demo_dir: Path) -> LoadBundle:
    participants, features = synthetic_dir / "participants.csv", synthetic_dir / "features.parquet"
    require(participants, features)
    wide = pd.read_parquet(features)
    long = wide.melt(id_vars="pid", var_name="feature_key", value_name="value")
    long = long.dropna(subset=["value"]).reset_index(drop=True)
    people = pd.read_csv(participants, dtype=TEXT_COLUMNS)
    return LoadBundle(people, long, read_traces(demo_dir))
