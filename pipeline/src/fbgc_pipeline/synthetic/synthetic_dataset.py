"""Build the public synthetic dataset from the private anonymized tables.

Fit the copula model on aggregates, sample with a fixed seed, run the distance check, and
only then write data/synthetic/participants.csv and features.parquet (each under 2 MB).
"""

from __future__ import annotations

import io
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from fbgc_core.catalogue_model import Catalogue
from fbgc_pipeline.synthetic.copula_model import fit_synthetic_model
from fbgc_pipeline.synthetic.copula_sampling import sample_synthetic
from fbgc_pipeline.synthetic.privacy_check import (
    DistanceCheck,
    SyntheticPrivacyError,
    distance_to_closest_record,
)

MAX_PUBLIC_BYTES = 2 * 1024 * 1024  # the leak guard's file limit
DEFAULT_SEED = 2026


class SyntheticSizeError(ValueError):
    """A synthetic file would break the leak guard's 2 MB limit."""


@dataclass(frozen=True)
class SyntheticDataset:
    participants: pd.DataFrame
    features: pd.DataFrame
    check: DistanceCheck
    dropped_sparse: int = 0


def read_anonymized(folder: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    participants = pd.read_parquet(folder / "participants.parquet")
    return participants, pd.read_parquet(folder / "features_long.parquet")


def wide_features(long: pd.DataFrame, pids: Sequence[str], catalogue: Catalogue) -> pd.DataFrame:
    """One row per pid (in the given order), one column per feature, in catalogue order."""
    wide = long.pivot(index="pid", columns="feature_key", values="value")
    keys = [spec.key for spec in catalogue.features if spec.key in wide.columns]
    return wide.reindex(index=list(pids), columns=keys).reset_index(drop=True)


def numeric_rows(participants: pd.DataFrame, features: pd.DataFrame) -> np.ndarray:
    gender = (participants["gender"].astype(str) == "F").astype(float).to_numpy()
    return np.column_stack([features.to_numpy(dtype=float), gender])


def build_synthetic(
    participants: pd.DataFrame,
    long: pd.DataFrame,
    catalogue: Catalogue,
    seed: int,
    shrinkage: float = 0.0,
) -> SyntheticDataset:
    real = wide_features(long, participants["pid"].tolist(), catalogue)
    model = fit_synthetic_model(participants, real, catalogue, shrinkage)
    people, synthetic = sample_synthetic(model, seed)
    check = distance_to_closest_record(
        numeric_rows(participants, real[list(model.keys)]),
        numeric_rows(people, synthetic.drop(columns="pid")),
    )
    if not check.passed and check.real_p5 == 0:
        raise SyntheticPrivacyError(
            "real rows are not distinct enough for the distance check "
            "(their 5th percentile distance is 0)"
        )
    if not check.passed:
        raise SyntheticPrivacyError(
            "synthetic rows sit too close to real rows: 5th percentile "
            f"{check.synthetic_p5:.3f} < {check.real_p5:.3f}"
        )
    return SyntheticDataset(people, synthetic, check, model.dropped_sparse)


def write_synthetic(
    dataset: SyntheticDataset, out_dir: Path, max_bytes: int = MAX_PUBLIC_BYTES
) -> dict[str, int]:
    """Write both files, or nothing when either would exceed `max_bytes`."""
    buffer = io.BytesIO()
    dataset.features.to_parquet(buffer, index=False, compression="zstd")
    files = {
        "participants.csv": dataset.participants.to_csv(index=False, lineterminator="\n").encode(),
        "features.parquet": buffer.getvalue(),
    }
    too_big = sorted(name for name, data in files.items() if len(data) > max_bytes)
    if too_big:
        raise SyntheticSizeError(f"over {max_bytes} bytes: {too_big}")
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (out_dir / name).write_bytes(data)
    return {name: len(data) for name, data in files.items()}
