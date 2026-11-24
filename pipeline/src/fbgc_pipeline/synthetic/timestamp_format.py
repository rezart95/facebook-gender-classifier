"""Write timestamps the way 2015–2017 Facebook exports showed them (for fake exports)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fbgc_pipeline.parse.timestamps import EN_MONTHS, IT_MONTHS

Style = Literal["it", "en_uk", "en_us"]
IT_WEEKDAYS = ("Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica")
EN_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
IT_MONTH_NAMES = tuple(IT_MONTHS)
EN_MONTH_NAMES = tuple(name.capitalize() for name in EN_MONTHS)


def format_fb_timestamp(moment: datetime, style: Style) -> str:
    offset = moment.utcoffset()
    hours = int(offset.total_seconds() // 3600) if offset else 0
    suffix = f"UTC{'+' if hours >= 0 else '-'}{abs(hours):02d}"
    weekday, month = moment.weekday(), moment.month - 1
    if style == "it":
        return (
            f"{IT_WEEKDAYS[weekday]} {moment.day} {IT_MONTH_NAMES[month]} {moment.year} "
            f"alle ore {moment.hour}:{moment.minute:02d} {suffix}"
        )
    if style == "en_uk":
        return (
            f"{EN_WEEKDAYS[weekday]}, {moment.day} {EN_MONTH_NAMES[month]} {moment.year} "
            f"at {moment.hour:02d}:{moment.minute:02d} {suffix}"
        )
    hour12 = moment.hour % 12 or 12
    ampm = "am" if moment.hour < 12 else "pm"
    return (
        f"{EN_WEEKDAYS[weekday]}, {EN_MONTH_NAMES[month]} {moment.day}, {moment.year} "
        f"at {hour12}:{moment.minute:02d}{ampm} {suffix}"
    )
