import math
from pathlib import Path

from fbgc_pipeline.features.faithful.rhythms import WeekdayLabels
from fbgc_pipeline.features.faithful.wall_features import friends_events_features, wall_features
from fbgc_pipeline.parse.export_pages import ExportPages
from fbgc_pipeline.parse.records import EventStats, FriendStats, WallItem
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import sample_profile


def test_wall_features_on_the_sample(tmp_path: Path) -> None:
    items = ExportPages.read(write_fake_export(tmp_path / "alpha", sample_profile())).wall
    features = wall_features(items, WeekdayLabels.CORRECT)
    assert len(features) == 43
    assert (features["wall_links_by_owner"], features["wall_items_total"]) == (1, 2)
    assert features["wall_friendships"] == 0
    assert (features["wall_hour_18"], features["wall_hour_20"]) == (0.5, 0.5)
    assert (features["wall_weekday_wed"], features["wall_weekday_thu"]) == (0.5, 0.5)
    assert features["wall_days_active"] == 2


def test_wall_patterns_are_regexes_like_r_grep() -> None:
    items = [WallItem(None, "Anna ha pubblicato un link sul tuo diario!", None)]
    assert (
        wall_features(items, WeekdayLabels.CORRECT)["wall_links_by_others"] == 1
    )  # '.' is any char


def test_friends_and_events_features() -> None:
    features = friends_events_features(FriendStats(3, 1, 2, 1), EventStats(1, 0, 0, 2))
    assert features == {
        "friends_accepted": 3,
        "friends_requests_sent": 1,
        "friends_requests_received": 2,
        "friends_removed": 1,
        "events_going": 1,
        "events_maybe": 0,
        "events_declined": 0,
        "events_no_reply": 2,
    }
    assert all(math.isnan(value) for value in friends_events_features(None, None).values())
