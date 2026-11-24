"""k-anonymity over (age band, gender, wave): every combination present covers k or more people."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from fbgc_pipeline.anonymize.age_bands import AGE_LEVELS, age_band

K_MIN = 5


class KAnonymityError(ValueError):
    """No age level gives every (age band, gender, wave) cell at least k people."""


def smallest_cell(age_bands: Sequence[str], genders: Sequence[str], waves: Sequence[int]) -> int:
    cells = Counter(zip(age_bands, genders, waves, strict=True))
    return min(cells.values()) if cells else 0


def choose_age_level(
    ages: Sequence[float | None], genders: Sequence[str], waves: Sequence[int], k: int = K_MIN
) -> int:
    """The finest age level whose every (age band, gender, wave) cell has at least k people."""
    for level in range(len(AGE_LEVELS)):
        bands = [age_band(age, level) for age in ages]
        if smallest_cell(bands, genders, waves) >= k:
            return level
    raise KAnonymityError(
        f"no age level gives every (age band, gender, wave) cell at least {k} people"
    )
