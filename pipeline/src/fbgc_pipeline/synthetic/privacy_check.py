"""Distance to closest record: synthetic rows must not sit closer to real rows than real rows
sit to each other (5th percentile of standardised Euclidean distances).

Columns are standardised with the real means and standard deviations; a missing value counts
as the mean (0 after standardising).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.distance import cdist

PERCENTILE = 5


class SyntheticPrivacyError(ValueError):
    """Synthetic rows sit too close to real rows."""


@dataclass(frozen=True)
class DistanceCheck:
    synthetic_p5: float
    real_p5: float

    @property
    def passed(self) -> bool:
        return self.synthetic_p5 >= self.real_p5


def column_scale(real: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Mean and standard deviation per column over observed values (1 when constant)."""
    observed = ~np.isnan(real)
    count = observed.sum(axis=0)
    zeros = np.zeros(real.shape[1])
    mean = np.divide(
        np.where(observed, real, 0.0).sum(axis=0), count, out=zeros.copy(), where=count > 0
    )
    squares = np.where(observed, real - mean, 0.0) ** 2
    std = np.sqrt(np.divide(squares.sum(axis=0), count, out=zeros.copy(), where=count > 0))
    return mean, np.where(std > 0, std, 1.0)


def standardise(values: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    return np.nan_to_num((values - mean) / scale, nan=0.0)


def distance_to_closest_record(real: np.ndarray, synthetic: np.ndarray) -> DistanceCheck:
    mean, scale = column_scale(real)
    real_z, synthetic_z = standardise(real, mean, scale), standardise(synthetic, mean, scale)
    within = cdist(real_z, real_z)
    np.fill_diagonal(within, np.inf)
    across = cdist(synthetic_z, real_z)
    return DistanceCheck(
        synthetic_p5=float(np.percentile(across.min(axis=1), PERCENTILE)),
        real_p5=float(np.percentile(within.min(axis=1), PERCENTILE)),
    )
