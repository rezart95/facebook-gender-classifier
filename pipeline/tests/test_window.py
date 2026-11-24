from datetime import UTC, datetime

from fbgc_pipeline.parse.records import Message, Thread, WallItem
from fbgc_pipeline.window.observation import (
    WindowPolicy,
    filter_threads,
    filter_wall,
    in_window,
    subtract_months,
    window_bounds,
)
from fbgc_pipeline.window.owner import find_owner

END = datetime(2015, 11, 20, 10, tzinfo=UTC)


def thread(*participants: str, messages: int = 1) -> Thread:
    return Thread(participants, tuple(Message(participants[0], None, "x") for _ in range(messages)))


def test_owner_is_most_frequent_across_personal_threads() -> None:
    threads = [thread("Owner", "A"), thread("Owner", "B"), thread("Owner", "A", "B")]
    assert find_owner(threads) == "Owner"


def test_owner_ties_go_to_the_alphabetically_first_name() -> None:
    assert find_owner([thread("Zoe", "Anna")]) == "Anna"


def test_no_personal_thread_with_messages_means_no_owner() -> None:
    assert find_owner([thread("A", "B", "C")]) is None
    assert find_owner([thread("A", "B", messages=0)]) is None


def test_subtract_months_clamps_the_day() -> None:
    assert subtract_months(datetime(2015, 8, 31, 10, tzinfo=UTC), 6) == datetime(
        2015, 2, 28, 10, tzinfo=UTC
    )


def test_six_month_window() -> None:
    bounds = window_bounds(END, WindowPolicy.LAST_6_MONTHS)
    assert bounds == (datetime(2015, 5, 20, 10, tzinfo=UTC), END)
    assert in_window(datetime(2015, 6, 1, tzinfo=UTC), bounds)
    assert not in_window(datetime(2015, 5, 1, tzinfo=UTC), bounds)
    assert not in_window(None, bounds)


def test_all_policy_and_missing_download_date_keep_everything() -> None:
    assert window_bounds(END, WindowPolicy.ALL) is None
    assert window_bounds(None, WindowPolicy.LAST_6_MONTHS) is None
    assert in_window(None, None)


def test_filters_drop_messages_and_wall_items_outside_the_window() -> None:
    inside, outside = datetime(2015, 10, 1, tzinfo=UTC), datetime(2014, 1, 1, tzinfo=UTC)
    threads = [Thread(("A", "B"), (Message("A", inside, "in"), Message("B", outside, "out")))]
    bounds = window_bounds(END, WindowPolicy.LAST_6_MONTHS)
    assert [m.text for m in filter_threads(threads, bounds)[0].messages] == ["in"]
    wall = [WallItem(inside, "a", None), WallItem(outside, "b", None)]
    assert [item.action for item in filter_wall(wall, bounds)] == ["a"]


def test_twelve_month_window() -> None:
    assert window_bounds(END, WindowPolicy.LAST_12_MONTHS) == (
        datetime(2014, 11, 20, 10, tzinfo=UTC),
        END,
    )


def test_twelve_month_policy_parses_from_its_cli_value() -> None:
    assert WindowPolicy("12m") is WindowPolicy.LAST_12_MONTHS
