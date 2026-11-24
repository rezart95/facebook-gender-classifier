"""Parse the timestamps of 2015–2017 Facebook HTML exports (Italian and English UIs).

The parsed datetime keeps the wall-clock time the export shows, with the export's
UTC offset attached. myFBr read the same wall-clock time, so hour and weekday
features stay comparable with the 2019 data.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

IT_MONTHS = {
    name: number
    for number, name in enumerate(
        [
            "gennaio",
            "febbraio",
            "marzo",
            "aprile",
            "maggio",
            "giugno",
            "luglio",
            "agosto",
            "settembre",
            "ottobre",
            "novembre",
            "dicembre",
        ],
        start=1,
    )
}
EN_MONTHS = {
    name: number
    for number, name in enumerate(
        [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ],
        start=1,
    )
}
_OFFSET = r"(?:\s*UTC(?P<offset>[+-]\d{1,2}))?"
_ITALIAN = re.compile(
    r"^\s*\S+\s+(?P<day>\d{1,2})\s+(?P<month>[^\W\d_]+)\s+(?P<year>\d{4})\s+alle ore\s+"
    r"(?P<hour>\d{1,2})[:.](?P<minute>\d{2})" + _OFFSET + r"\s*$",
    re.IGNORECASE,
)
_ENGLISH_DAY_FIRST = re.compile(
    r"^\s*[^\W\d_]+,\s+(?P<day>\d{1,2})\s+(?P<month>[^\W\d_]+)\s+(?P<year>\d{4})\s+at\s+"
    r"(?P<hour>\d{1,2}):(?P<minute>\d{2})" + _OFFSET + r"\s*$",
    re.IGNORECASE,
)
_ENGLISH_MONTH_FIRST = re.compile(
    r"^\s*[^\W\d_]+,\s+(?P<month>[^\W\d_]+)\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})\s+at\s+"
    r"(?P<hour>\d{1,2}):(?P<minute>\d{2})\s*(?P<ampm>[ap]m)" + _OFFSET + r"\s*$",
    re.IGNORECASE,
)
_FORMATS = (
    (_ITALIAN, IT_MONTHS),
    (_ENGLISH_DAY_FIRST, EN_MONTHS),
    (_ENGLISH_MONTH_FIRST, EN_MONTHS),
)


class TimestampError(ValueError):
    """The string is not a supported export timestamp."""


def parse_fb_timestamp(text: str) -> datetime:
    for pattern, months in _FORMATS:
        match = pattern.match(text)
        if match:
            return _build(match, months)
    raise TimestampError(f"unsupported timestamp format: {text[:60]!r}")


def try_parse_fb_timestamp(text: str | None) -> datetime | None:
    if not text:
        return None
    try:
        return parse_fb_timestamp(text)
    except TimestampError:
        return None


def find_trailing_timestamp(text: str) -> datetime | None:
    """The timestamp ending a sentence such as 'Scaricato da X il <timestamp>'."""
    for separator in (" il ", " on ", " - "):
        if separator in text:
            parsed = try_parse_fb_timestamp(text.rsplit(separator, 1)[-1])
            if parsed is not None:
                return parsed
    return try_parse_fb_timestamp(text)


def _build(match: re.Match[str], months: dict[str, int]) -> datetime:
    month = months.get(match["month"].lower())
    if month is None:
        raise TimestampError(f"unknown month name: {match['month']!r}")
    hour = int(match["hour"])
    ampm = match.groupdict().get("ampm")
    if ampm:
        hour = hour % 12 + (12 if ampm.lower() == "pm" else 0)
    zone = timezone(timedelta(hours=int(match["offset"]) if match["offset"] else 0))
    try:
        return datetime(
            int(match["year"]), month, int(match["day"]), hour, int(match["minute"]), tzinfo=zone
        )
    except ValueError as error:
        raise TimestampError(str(error)) from error
