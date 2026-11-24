from pathlib import Path

from fbgc_pipeline.parse.events_page import parse_events_page
from fbgc_pipeline.parse.export_pages import ExportPages
from fbgc_pipeline.parse.friends_page import parse_friends_page
from fbgc_pipeline.parse.records import EventStats, FriendStats, WallItem
from fbgc_pipeline.parse.wall_page import parse_wall_page
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import SAMPLE_OWNER, at, sample_profile


def test_wall_items_follow_myfbr_children_order(tmp_path: Path) -> None:
    root = write_fake_export(tmp_path / "alpha", sample_profile())
    items = parse_wall_page(root / "html" / "wall.htm")
    assert items[0] == WallItem(at(4, 18), f"{SAMPLE_OWNER} ha condiviso un link.", "bello")
    # myFBr quirk: without an action text, the comment lands in the action slot.
    assert items[1] == WallItem(at(5, 20), "solo un commento", None)


def test_friend_sections_are_read_by_label(tmp_path: Path) -> None:
    root = write_fake_export(tmp_path / "alpha", sample_profile())
    stats = parse_friends_page(root / "html" / "friends.htm")
    assert stats == FriendStats(accepted=3, requests_sent=1, requests_received=2, removed=1)


def test_english_friend_labels(tmp_path: Path) -> None:
    sections = (("Friends", 4), ("Received Friend Requests", 2), ("Removed Friends", 0))
    profile = sample_profile(style="en_uk", friend_sections=sections)
    stats = parse_friends_page(
        write_fake_export(tmp_path / "alpha", profile) / "html" / "friends.htm"
    )
    assert stats == FriendStats(accepted=4, requests_sent=0, requests_received=2, removed=0)


def test_event_responses(tmp_path: Path) -> None:
    when = "Sabato 7 novembre 2015 alle ore 21:00 UTC+01"
    events = tuple(
        f"{name} - {when} - {answer}"
        for name, answer in [
            ("A", "Partecipazione confermata"),
            ("B", "Forse"),
            ("C", "Partecipazione rifiutata"),
            ("D", "Nessuna risposta"),
        ]
    )
    root = write_fake_export(tmp_path / "alpha", sample_profile(events=events))
    assert parse_events_page(root / "html" / "events.htm") == EventStats(1, 1, 1, 1)


def test_export_pages_reads_everything_and_tolerates_missing_pages(tmp_path: Path) -> None:
    root = write_fake_export(tmp_path / "alpha", sample_profile())
    pages = ExportPages.read(root)
    assert (len(pages.threads), len(pages.wall)) == (2, 2)
    assert pages.events == EventStats(1, 0, 0, 0)
    (root / "html" / "friends.htm").unlink()
    assert ExportPages.read(root).friends is None
