import math
from datetime import UTC, datetime

from fbgc_pipeline.features.faithful.gini import gini_heterogeneity
from fbgc_pipeline.features.faithful.message_stats import message_summary, r_summary
from fbgc_pipeline.features.faithful.rhythms import (
    WeekdayLabels,
    days_active,
    hour_shares,
    weekday_shares,
)
from fbgc_pipeline.parse.records import Message


def moment(day: int, hour: int) -> datetime:
    return datetime(2015, 11, day, hour, tzinfo=UTC)  # 2 Nov 2015 = Monday, 8 Nov = Sunday


def test_message_summary_matches_r() -> None:
    texts = [("A", "x"), ("A", "xx"), ("A", "xxx"), ("B", "xxxx"), ("B", "x" * 100)]
    summary = message_summary([Message(sender, None, text) for sender, text in texts])
    assert (summary["msg_count"], summary["msg_n_contacts"], summary["msg_per_contact"]) == (
        5,
        2,
        2.5,
    )
    assert summary["msg_chars_total"] == 110
    keys = [
        "msg_chars_min",
        "msg_chars_q1",
        "msg_chars_median",
        "msg_chars_mean",
        "msg_chars_q3",
        "msg_chars_max",
    ]
    assert [summary[key] for key in keys] == [1, 2, 3, 22, 4, 100]
    assert (summary["msg_top1_share"], summary["msg_top2_share"]) == (0.6, 0.4)
    assert math.isnan(summary["msg_top3_share"])


def test_empty_messages_give_nan_shares() -> None:
    summary = message_summary([])
    assert summary["msg_count"] == 0
    assert summary["msg_chars_total"] == 0
    assert summary["msg_n_contacts"] == 0
    assert math.isnan(summary["msg_top1_share"])
    assert math.isnan(summary["msg_per_contact"])
    assert math.isnan(summary["msg_chars_mean"])


def test_r_summary_is_not_rounded() -> None:
    assert r_summary([1, 2, 2])[3] == 5 / 3


def test_gini_heterogeneity() -> None:
    assert gini_heterogeneity(["a", "a", "b", "b"]) == 1.0
    assert gini_heterogeneity(["a", "a", "a", "b"]) == 0.75
    assert gini_heterogeneity(["a", "a"]) == 0.0
    assert gini_heterogeneity([]) == 0.0


def test_hour_shares_ignore_unknown_times() -> None:
    shares = hour_shares([moment(2, 9), moment(2, 9), moment(8, 23), None], "msg")
    assert len(shares) == 24
    assert (shares["msg_hour_09"], shares["msg_hour_23"], shares["msg_hour_02"]) == (
        2 / 3,
        1 / 3,
        0,
    )


def test_weekday_shares_correct_and_r_sunday_first() -> None:
    times = [moment(2, 9), moment(8, 23), moment(7, 12), moment(2, 18)]  # Mon, Sun, Sat, Mon
    correct = weekday_shares(times, "msg", WeekdayLabels.CORRECT)
    assert (correct["msg_weekday_mon"], correct["msg_weekday_sat"], correct["msg_weekday_sun"]) == (
        0.5,
        0.25,
        0.25,
    )
    shifted = weekday_shares(times, "msg", WeekdayLabels.R_SUNDAY_FIRST)
    assert shifted["msg_weekday_mon"] == 0.25  # Sunday's share under R's Monday label
    assert shifted["msg_weekday_tue"] == 0.5  # Monday's share
    assert shifted["msg_weekday_sun"] == 0.25  # Saturday's share wraps onto Sunday
    assert shifted["msg_weekday_sat"] == 0.0


def test_no_times_give_nan_and_days_active_counts_dates() -> None:
    assert all(math.isnan(value) for value in hour_shares([None], "wall").values())
    assert days_active([moment(2, 9), moment(2, 10), moment(8, 23), None]) == 2
