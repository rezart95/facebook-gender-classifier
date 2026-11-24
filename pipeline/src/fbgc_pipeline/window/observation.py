"""The observation window: everything, or the last N months before the download date.

The 2019 data covers the 12 months before the download date (inferred from the
data; the theses said 6 months). The other policies stay available for
comparison.
"""

from __future__ import annotations

import calendar
from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum

from fbgc_pipeline.parse.records import Thread, WallItem

Bounds = tuple[datetime, datetime] | None


class WindowPolicy(StrEnum):
    ALL = "all"
    LAST_6_MONTHS = "6m"
    LAST_12_MONTHS = "12m"


POLICY_MONTHS = {WindowPolicy.LAST_6_MONTHS: 6, WindowPolicy.LAST_12_MONTHS: 12}


def subtract_months(moment: datetime, months: int) -> datetime:
    year, month_index = divmod(moment.year * 12 + moment.month - 1 - months, 12)
    day = min(moment.day, calendar.monthrange(year, month_index + 1)[1])
    return moment.replace(year=year, month=month_index + 1, day=day)


def is_windowed(policy: WindowPolicy) -> bool:
    return policy in POLICY_MONTHS


def window_bounds(downloaded_at: datetime | None, policy: WindowPolicy) -> Bounds:
    months = POLICY_MONTHS.get(policy)
    if months is None or downloaded_at is None:
        return None
    return (subtract_months(downloaded_at, months), downloaded_at)


def in_window(moment: datetime | None, bounds: Bounds) -> bool:
    if bounds is None:
        return True
    return moment is not None and bounds[0] <= moment <= bounds[1]


def filter_threads(threads: Sequence[Thread], bounds: Bounds) -> list[Thread]:
    if bounds is None:
        return list(threads)
    return [
        Thread(
            thread.participants, tuple(m for m in thread.messages if in_window(m.sent_at, bounds))
        )
        for thread in threads
    ]


def filter_wall(items: Sequence[WallItem], bounds: Bounds) -> list[WallItem]:
    return [item for item in items if in_window(item.at, bounds)]
