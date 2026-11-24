"""Compare recomputed faithful features with the 2019 table, column by column."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from fbgc_core.catalogue_model import Catalogue

RELATIVE_TOLERANCE = 5e-4  # absorbs float noise and R/Python rounding differences


@dataclass(frozen=True)
class ColumnComparison:
    key: str
    legacy_name: str
    family: str
    compared: int
    exact_rate: float
    pearson: float
    max_abs_diff: float


def values_match(ours: float, legacy: float) -> bool:
    if math.isnan(ours) or math.isnan(legacy):
        return math.isnan(ours) and math.isnan(legacy)
    return abs(ours - legacy) <= max(1e-9, RELATIVE_TOLERANCE * max(abs(ours), abs(legacy)))


def comparable_rows(ours: pd.DataFrame, legacy: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    usable = ours[ours["status"] == "ok"].drop_duplicates("folder_code", keep=False)
    usable = usable.set_index("folder_code")
    shared = usable.index.intersection(legacy.index)
    return usable.loc[shared], legacy.loc[shared]


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
        return math.nan
    return float(np.corrcoef(a, b)[0, 1])


def compare_columns(
    ours: pd.DataFrame, legacy: pd.DataFrame, catalogue: Catalogue
) -> list[ColumnComparison]:
    ours_rows, legacy_rows = comparable_rows(ours, legacy)
    comparisons = []
    for spec in catalogue.features:
        if spec.legacy_name is None or spec.legacy_name not in legacy_rows.columns:
            continue
        if spec.key not in ours_rows.columns:
            continue
        a = ours_rows[spec.key].to_numpy(dtype=float)
        b = legacy_rows[spec.legacy_name].to_numpy(dtype=float)
        matches = [values_match(float(x), float(y)) for x, y in zip(a, b, strict=True)]
        both = ~(np.isnan(a) | np.isnan(b))
        diffs = np.abs(a[both] - b[both])
        comparisons.append(
            ColumnComparison(
                key=spec.key,
                legacy_name=spec.legacy_name,
                family=spec.family,
                compared=len(a),
                exact_rate=float(np.mean(matches)) if matches else math.nan,
                pearson=_pearson(a[both], b[both]),
                max_abs_diff=float(diffs.max()) if diffs.size else math.nan,
            )
        )
    return comparisons


def overall_exact_rate(comparisons: Sequence[ColumnComparison]) -> float:
    pairs = [(c.exact_rate, c.compared) for c in comparisons if c.compared]
    total = sum(compared for _, compared in pairs)
    return sum(rate * compared for rate, compared in pairs) / total if total else math.nan


def gender_agreement(ours: pd.DataFrame, legacy_gender: pd.Series) -> tuple[int, float]:
    usable = ours.drop_duplicates("folder_code", keep=False).set_index("folder_code")
    shared = usable.index.intersection(legacy_gender.index)
    if len(shared) == 0:
        return 0, math.nan
    agree = usable.loc[shared, "gender"].astype(str) == legacy_gender.loc[shared]
    return len(shared), float(agree.mean())
