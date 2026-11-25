"""What `fbgc load` reads: participants, feature values (long) and the demo traces."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

import pandas as pd

SYNTHETIC_ID = r"S\d{3,}"
PRIVATE_ID = r"P\d{3,}"
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


def require_ids(bundle: LoadBundle, pattern: str, kind: str) -> None:
    """Refuse ids of the wrong kind, in participants and values; say how many, never which."""
    pids = pd.concat([bundle.participants["pid"], bundle.features_long["pid"]]).astype(str)
    wrong = int((~pids.drop_duplicates().str.fullmatch(pattern)).sum())
    if wrong:
        raise LoadError(f"{wrong} participant ids are not {kind}")


def read_traces(demo_dir: Path) -> list[dict[str, object]]:
    traces: list[dict[str, object]] = []
    for path in sorted(demo_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("fake") is not True:
            raise LoadError(f"trace {path.stem} is not marked as a fake profile")
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
    bundle = LoadBundle(pd.read_parquet(participants), pd.read_parquet(values), [])
    require_ids(bundle, PRIVATE_ID, "private P-IDs")
    return replace(bundle, traces=read_traces(demo_dir))


def synthetic_bundle(synthetic_dir: Path, demo_dir: Path) -> LoadBundle:
    participants, features = synthetic_dir / "participants.csv", synthetic_dir / "features.parquet"
    require(participants, features)
    wide = pd.read_parquet(features)
    long = wide.melt(id_vars="pid", var_name="feature_key", value_name="value")
    long = long.dropna(subset=["value"]).reset_index(drop=True)
    people = pd.read_csv(participants, dtype=TEXT_COLUMNS)
    bundle = LoadBundle(people, long, [])
    require_ids(bundle, SYNTHETIC_ID, "synthetic S-IDs")
    return replace(bundle, traces=read_traces(demo_dir))
