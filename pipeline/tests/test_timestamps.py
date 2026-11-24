from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from fbgc_pipeline.parse.timestamps import (
    TimestampError,
    find_trailing_timestamp,
    parse_fb_timestamp,
    try_parse_fb_timestamp,
)
from fbgc_pipeline.synthetic.timestamp_format import format_fb_timestamp


def offset(hours: int) -> timezone:
    return timezone(timedelta(hours=hours))


def test_italian_timestamp() -> None:
    parsed = parse_fb_timestamp("Domenica 12 ottobre 2014 alle ore 14:05 UTC+02")
    assert parsed == datetime(2014, 10, 12, 14, 5, tzinfo=offset(2))
    assert parsed.hour == 14  # wall-clock hour, as myFBr read it


def test_italian_single_digit_hour_and_offset() -> None:
    parsed = parse_fb_timestamp("Venerdì 4 dicembre 2015 alle ore 9:07 UTC+1")
    assert parsed == datetime(2015, 12, 4, 9, 7, tzinfo=offset(1))


def test_mangled_weekday_still_parses() -> None:
    parsed = parse_fb_timestamp("Venerd� 4 dicembre 2015 alle ore 9:07 UTC+01")
    assert parsed.day == 4


def test_english_day_first() -> None:
    parsed = parse_fb_timestamp("Tuesday, 12 January 2016 at 14:05 UTC+01")
    assert parsed == datetime(2016, 1, 12, 14, 5, tzinfo=offset(1))


def test_english_month_first_with_pm() -> None:
    parsed = parse_fb_timestamp("Sunday, December 13, 2015 at 2:05pm UTC+01")
    assert parsed == datetime(2015, 12, 13, 14, 5, tzinfo=offset(1))


def test_english_half_past_midnight() -> None:
    parsed = parse_fb_timestamp("Sunday, December 13, 2015 at 12:30am UTC+01")
    assert parsed.hour == 0


def test_missing_offset_means_utc() -> None:
    parsed = parse_fb_timestamp("Domenica 12 ottobre 2014 alle ore 14:05")
    assert parsed.utcoffset() == timedelta(0)


def test_unsupported_language_raises() -> None:
    with pytest.raises(TimestampError):
        parse_fb_timestamp("Sábado, 12 de diciembre de 2015 a la(s) 14:05")
    assert try_parse_fb_timestamp("not a date") is None
    assert try_parse_fb_timestamp(None) is None


def test_impossible_date_raises() -> None:
    with pytest.raises(TimestampError):
        parse_fb_timestamp("Lunedì 30 febbraio 2015 alle ore 10:00 UTC+01")


def test_trailing_timestamp_in_footers() -> None:
    italian = "Scaricato da Nome Finto il Venerdì 20 novembre 2015 alle ore 10:00 UTC+01"
    english = "Downloaded by Fake Name on Friday, 20 November 2015 at 10:00 UTC+01"
    expected = datetime(2015, 11, 20, 10, 0, tzinfo=offset(1))
    assert find_trailing_timestamp(italian) == expected
    assert find_trailing_timestamp(english) == expected


moments = st.datetimes(
    min_value=datetime(2004, 2, 1),
    max_value=datetime(2017, 12, 31),
    timezones=st.sampled_from([offset(0), offset(1), offset(2)]),
).map(lambda moment: moment.replace(second=0, microsecond=0))


@given(moment=moments, style=st.sampled_from(["it", "en_uk", "en_us"]))
def test_format_then_parse_round_trips(moment: datetime, style: str) -> None:
    assert parse_fb_timestamp(format_fb_timestamp(moment, style)) == moment  # type: ignore[arg-type]
