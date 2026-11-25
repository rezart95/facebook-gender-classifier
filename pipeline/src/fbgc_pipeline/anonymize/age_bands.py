"""Age at the download date, and the age bands the anonymized data uses.

The birth date itself never leaves memory: only whole years at download, and only 16-60
(anything else is treated as unknown, because it is almost surely a fake birth date).
Bands form a hierarchy; unknown ages are their own band at levels 0 and 1, and fall into the
single "all" band at the coarsest level 2.
"""

from __future__ import annotations

import math
from datetime import date, datetime

AGE_MIN, AGE_MAX = 16, 60
UNKNOWN_BAND = "unknown"
# Per level, finest first: (exclusive upper bound, band). Levels 0 and 1 keep "unknown" as its own
# band; the coarsest level absorbs unknown ages into its single band.
AGE_LEVELS: tuple[tuple[tuple[float, str], ...], ...] = (
    ((20, "<20"), (21, "20"), (22, "21"), (25, "22-24"), (math.inf, "25+")),
    ((21, "<21"), (math.inf, "21+")),
    ((math.inf, "all"),),
)
ALL_AGE_BANDS = frozenset({band for level in AGE_LEVELS for _, band in level} | {UNKNOWN_BAND})


def age_at_download(birth: date | None, downloaded: datetime | None) -> int | None:
    """Whole years at the download date, or None when unknown or outside 16-60."""
    if birth is None or downloaded is None:
        return None
    day = downloaded.date()
    years = day.year - birth.year - ((day.month, day.day) < (birth.month, birth.day))
    return years if AGE_MIN <= years <= AGE_MAX else None


def age_band(age: float | None, level: int) -> str:
    """The band at a level. Unknown ages are "unknown" except at the coarsest level ("all")."""
    if age is None or math.isnan(age):
        return UNKNOWN_BAND if level < len(AGE_LEVELS) - 1 else AGE_LEVELS[level][-1][1]
    return next(band for upper, band in AGE_LEVELS[level] if age < upper)
