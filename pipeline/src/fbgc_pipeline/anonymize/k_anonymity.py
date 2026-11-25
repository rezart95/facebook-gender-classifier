"""k-anonymity over (age band, gender, wave, relationship): every combination present covers
k or more people."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from fbgc_pipeline.anonymize.age_bands import AGE_LEVELS, age_band
from fbgc_pipeline.anonymize.relationship import RELATIONSHIP_LEVELS, generalize_relationship

K_MIN = 5


class KAnonymityError(ValueError):
    """No generalisation level gives every (age band, gender, wave, relationship) cell k people."""


def smallest_cell(*columns: Sequence[object]) -> int:
    """The size of the smallest group of rows that share one value in every column."""
    cells = Counter(zip(*columns, strict=True))
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


def choose_levels(
    ages: Sequence[float | None],
    genders: Sequence[str],
    waves: Sequence[int],
    relationships: Sequence[str],
    k: int = K_MIN,
) -> tuple[int, int]:
    """The (age level, relationship level) that makes every four-column cell hold k people.

    Age detail is preferred over relationship detail: all relationship levels are tried at the
    finest age level before the age is coarsened.
    """
    for age_level in range(len(AGE_LEVELS)):
        bands = [age_band(age, age_level) for age in ages]
        for relationship_level in range(RELATIONSHIP_LEVELS):
            categories = [generalize_relationship(r, relationship_level) for r in relationships]
            if smallest_cell(bands, genders, waves, categories) >= k:
                return age_level, relationship_level
    raise KAnonymityError(
        f"no combination of age and relationship levels gives every cell at least {k} people"
    )
