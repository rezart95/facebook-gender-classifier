"""Sample synthetic participants and features from a fitted copula model (fixed seed).

Gaussian draws with the model's correlation become uniforms, then values through linear
interpolation between the stored quantiles. Count features are rounded to whole numbers,
others to 4 decimals. Missing values return at the real rates, block by block.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from fbgc_pipeline.synthetic.copula_model import CATEGORY_COLUMNS, LEVELS, Shares, SyntheticModel

DECIMALS = 4


def synthetic_ids(n: int) -> list[str]:
    width = max(3, len(str(n)))
    return [f"S{rank:0{width}d}" for rank in range(1, n + 1)]


def draw_categories(shares: Shares, n: int, rng: np.random.Generator) -> list[object]:
    values, probabilities = shares
    weights = np.asarray(probabilities, dtype=float)
    picks = rng.choice(len(values), size=n, p=weights / weights.sum())
    return [values[index] for index in picks]


def with_missing(values: np.ndarray, model: SyntheticModel, rng: np.random.Generator) -> np.ndarray:
    """One uniform per row and block: a feature is missing where it falls below its rate."""
    drivers = {block: rng.random(len(values)) for block in sorted(set(model.blocks))}
    result = values.copy()
    for column, block in enumerate(model.blocks):
        result[drivers[block] < model.missing_rates[column], column] = np.nan
    return result


def sample_synthetic(model: SyntheticModel, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Synthetic (participants, features) with S001... IDs, as many rows as the real data."""
    rng = np.random.default_rng(seed)
    size = len(model.keys) + 1
    normal = rng.multivariate_normal(np.zeros(size), model.correlation, model.n_rows, method="eigh")
    uniform = np.asarray(norm.cdf(normal), dtype=float)
    values = np.column_stack(
        [np.interp(uniform[:, j], LEVELS, model.quantiles[j]) for j in range(len(model.keys))]
    )
    values = np.where(model.counts, np.round(values), np.round(values, DECIMALS))
    values = with_missing(values, model, rng)
    pids = synthetic_ids(model.n_rows)
    features = pd.DataFrame(values, columns=list(model.keys))
    survey = [key for key, block in zip(model.keys, model.blocks, strict=True) if block == "survey"]
    messages = (
        features["msg_count"] if "msg_count" in features else pd.Series(np.nan, range(len(pids)))
    )
    drawn = {
        column: draw_categories(model.categories[column], model.n_rows, rng)
        for column in CATEGORY_COLUMNS
    }
    participants = pd.DataFrame(
        {
            "pid": pids,
            "wave": drawn["wave"],
            "gender": np.where(uniform[:, -1] > 1 - model.female_share, "F", "M"),
            "age_band": drawn["age_band"],
            "relationship": drawn["relationship"],
            "has_messages": (messages.fillna(0) > 0).to_numpy(),
            "has_survey": features[survey].notna().any(axis=1).to_numpy(),
        }
    )
    features.insert(0, "pid", pids)
    return participants, features
