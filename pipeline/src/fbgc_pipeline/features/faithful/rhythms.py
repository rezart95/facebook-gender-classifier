"""Hour-of-day and day-of-week activity shares (wall-clock time, as myFBr read it).

myFBr took weekday labels from lubridate, whose weeks start on Sunday, then
renamed them Monday..Sunday: every share moved one day. R_SUNDAY_FIRST
reproduces that; the golden test shows which variant the 2019 data used.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum

HOURS = tuple(f"{hour:02d}" for hour in range(24))
WEEKDAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


class WeekdayLabels(StrEnum):
    CORRECT = "correct"
    R_SUNDAY_FIRST = "r-sunday-first"


def _known(times: Sequence[datetime | None]) -> list[datetime]:
    return [moment for moment in times if moment is not None]


def hour_shares(times: Sequence[datetime | None], prefix: str) -> dict[str, float]:
    known = _known(times)
    counts = Counter(moment.hour for moment in known)
    total = len(known)
    return {
        f"{prefix}_hour_{hour}": counts[int(hour)] / total if total else math.nan for hour in HOURS
    }


def weekday_shares(
    times: Sequence[datetime | None], prefix: str, labels: WeekdayLabels
) -> dict[str, float]:
    known = _known(times)
    counts = Counter(moment.weekday() for moment in known)  # Monday = 0
    total = len(known)
    shift = 0 if labels is WeekdayLabels.CORRECT else 1
    return {
        f"{prefix}_weekday_{key}": counts[(index - shift) % 7] / total if total else math.nan
        for index, key in enumerate(WEEKDAY_KEYS)
    }


def days_active(times: Sequence[datetime | None]) -> float:
    return float(len({moment.date() for moment in _known(times)}))
