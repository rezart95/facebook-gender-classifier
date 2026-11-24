from pathlib import Path

import pytest
from lxml import etree

from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.fake_records import FakeMessage, FakeThread
from fbgc_pipeline.synthetic.samples import SAMPLE_OWNER, at, sample_profile


def test_writes_index_and_the_four_pages(tmp_path: Path) -> None:
    root = write_fake_export(tmp_path / "alpha", sample_profile())
    assert (root / "index.htm").is_file()
    names = sorted(page.name for page in (root / "html").iterdir())
    assert names == ["events.htm", "friends.htm", "messages.htm", "wall.htm"]


def test_pages_are_well_formed_xml_like_most_real_exports(tmp_path: Path) -> None:
    root = write_fake_export(tmp_path / "alpha", sample_profile())
    for page in [root / "index.htm", *(root / "html").iterdir()]:
        etree.fromstring(page.read_bytes())


def test_broken_messages_page_is_not_xml(tmp_path: Path) -> None:
    thread = FakeThread(
        (SAMPLE_OWNER, "Marco Verdi"), (FakeMessage("Marco Verdi", at(2, 10), "pane & vino"),)
    )
    profile = sample_profile(threads=(thread,), break_messages_xml=True)
    root = write_fake_export(tmp_path / "alpha", profile)
    with pytest.raises(etree.XMLSyntaxError):
        etree.fromstring((root / "html" / "messages.htm").read_bytes())


def test_english_profile_uses_english_labels(tmp_path: Path) -> None:
    root = write_fake_export(tmp_path / "alpha", sample_profile(style="en_uk", gender_label="Male"))
    text = (root / "index.htm").read_text(encoding="utf-8")
    assert "<th>Gender</th><td>Male</td>" in text
    assert "Downloaded by" in text


def test_wall_items_nest_div_inside_p(tmp_path: Path) -> None:
    root = write_fake_export(tmp_path / "alpha", sample_profile())
    text = (root / "html" / "wall.htm").read_text(encoding="utf-8")
    assert '<p><div class="meta">' in text
