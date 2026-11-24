from pathlib import Path

from fbgc_pipeline.parse.messages_page import parse_messages_page
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.fake_records import FakeMessage, FakeThread
from fbgc_pipeline.synthetic.samples import SAMPLE_OWNER, at, sample_profile


def test_threads_participants_and_messages(tmp_path: Path) -> None:
    root = write_fake_export(tmp_path / "alpha", sample_profile())
    threads = parse_messages_page(root / "html" / "messages.htm")
    assert [thread.participants for thread in threads] == [
        (SAMPLE_OWNER, "Marco Verdi"),
        (SAMPLE_OWNER, "Marco Verdi", "Sara Neri"),
    ]
    assert [thread.is_group for thread in threads] == [False, True]
    first = threads[0].messages[0]
    assert (first.sender, first.text, first.sent_at) == (
        SAMPLE_OWNER,
        "Ciao Marco :) come stai?",
        at(2, 9),
    )
    assert threads[1].messages[1].text.endswith("\N{GRINNING FACE}")


def test_page_that_is_not_xml_is_still_read(tmp_path: Path) -> None:
    thread = FakeThread(
        (SAMPLE_OWNER, "Marco Verdi"), (FakeMessage("Marco Verdi", at(2, 10), "pane & vino"),)
    )
    profile = sample_profile(threads=(thread,), break_messages_xml=True)
    root = write_fake_export(tmp_path / "alpha", profile)
    assert parse_messages_page(root / "html" / "messages.htm")[0].messages[0].text == "pane & vino"


def test_header_without_body_gets_empty_text(tmp_path: Path) -> None:
    page = tmp_path / "messages.htm"
    page.write_text(
        '<html><body><div class="contents"><div><div class="thread">A, B'
        '<div class="message"><div class="message_header"><span class="user">A</span>'
        '<span class="meta">Domenica 12 ottobre 2014 alle ore 14:05 UTC+02</span></div></div>'
        "</div></div></div></body></html>",
        encoding="utf-8",
    )
    message = parse_messages_page(page)[0].messages[0]
    assert (message.sender, message.text) == ("A", "")
