"""Fit a Gaussian-copula model of the anonymized data from aggregate statistics only.

Kept per feature: the 1%-99% quantiles (stored on a 101-point grid) and the missing rate.
Kept jointly: the Spearman matrix of the features plus gender (F = 1), turned into Pearson
correlations with 2 sin(pi rho / 6) and projected to the nearest positive semi-definite
matrix (optionally shrunk toward the identity). Category shares of wave, age band and
relationship are kept too. The model holds aggregates only, and its marginals are clipped to
the 1%-99% quantiles: the exact real minimum and maximum of a feature are never stored (nor,
through sampling, produced). No row of the data is kept.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from fbgc_core.catalogue_model import Catalogue, FeatureSpec

LEVELS = np.linspace(0.0, 1.0, 101)
CLIP = (0.01, 0.99)  # marginals stop here: the real min and max are the most identifying values
UNKNOWN = "unknown"
CATEGORY_COLUMNS = ("wave", "age_band", "relationship")
GENDER_COLUMN = "__gender__"

Shares = tuple[tuple[object, ...], tuple[float, ...]]


@dataclass(frozen=True)
class SyntheticModel:
    keys: tuple[str, ...]
    quantiles: np.ndarray  # (features, 101)
    missing_rates: np.ndarray  # (features,)
    counts: np.ndarray  # (features,) True where values are whole counts
    blocks: tuple[str, ...]  # features in one block go missing together
    correlation: np.ndarray  # (features + 1) square; the last variable is gender
    female_share: float
    categories: dict[str, Shares]
    n_rows: int


def spearman_to_pearson(rho: np.ndarray) -> np.ndarray:
    return 2 * np.sin(np.pi * rho / 6)


def nearest_correlation(matrix: np.ndarray, floor: float = 1e-6) -> np.ndarray:
    """Clip negative eigenvalues, then rescale back to a unit diagonal."""
    symmetric = (matrix + matrix.T) / 2
    values, vectors = np.linalg.eigh(symmetric)
    clipped = (vectors * np.clip(values, floor, None)) @ vectors.T
    scale = np.sqrt(np.diag(clipped))
    return clipped / np.outer(scale, scale)


def shrink(correlation: np.ndarray, shrinkage: float) -> np.ndarray:
    """Blend toward the identity: weaker correlations, synthetic rows further from real ones."""
    if not 0.0 <= shrinkage <= 1.0:
        raise ValueError(f"shrinkage must be between 0 and 1, not {shrinkage}")
    return (1 - shrinkage) * correlation + shrinkage * np.eye(len(correlation))


def missing_block(spec: FeatureSpec) -> str:
    return "survey" if spec.origin == "survey" else spec.key.split("_", 1)[0]


def marginal_quantiles(values: pd.Series) -> np.ndarray:
    observed = values.dropna().to_numpy(dtype=float)
    return np.quantile(observed, np.clip(LEVELS, *CLIP)) if observed.size else np.zeros(LEVELS.size)


def category_shares(values: pd.Series) -> Shares:
    shares = values.value_counts(normalize=True).sort_index()
    if shares.empty:  # an all-null column is one "unknown" category
        return (UNKNOWN,), (1.0,)
    return tuple(shares.index.tolist()), tuple(float(share) for share in shares.to_numpy())


def fit_synthetic_model(
    participants: pd.DataFrame,
    features: pd.DataFrame,
    catalogue: Catalogue,
    shrinkage: float = 0.0,
) -> SyntheticModel:
    """`features` has one row per participant (same order) and one column per feature key."""
    keys = tuple(str(column) for column in features.columns)
    specs = [catalogue.get(key) for key in keys]
    gender = (participants["gender"].astype(str) == "F").astype(float).to_numpy()
    ranks = features.assign(**{GENDER_COLUMN: gender}).rank()
    spearman = np.nan_to_num(ranks.corr().to_numpy(dtype=float), nan=0.0)
    np.fill_diagonal(spearman, 1.0)
    return SyntheticModel(
        keys=keys,
        quantiles=np.vstack([marginal_quantiles(features[key]) for key in keys]),
        missing_rates=features.isna().mean().to_numpy(dtype=float),
        counts=np.array([spec.is_count for spec in specs]),
        blocks=tuple(missing_block(spec) for spec in specs),
        correlation=shrink(nearest_correlation(spearman_to_pearson(spearman)), shrinkage),
        female_share=float(gender.mean()),
        categories={column: category_shares(participants[column]) for column in CATEGORY_COLUMNS},
        n_rows=len(participants),
    )
