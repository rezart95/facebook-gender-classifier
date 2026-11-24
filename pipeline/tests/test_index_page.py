from dataclasses import fields
from datetime import date
from pathlib import Path

from fbgc_pipeline.parse.index_page import parse_index_page
from fbgc_pipeline.parse.records import ProfileInfo
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import sample_profile


def test_italian_profile_page(tmp_path: Path) -> None:
    profile = sample_profile()
    info = parse_index_page(write_fake_export(tmp_path / "alpha", profile) / "index.htm")
    assert info.language == "it"
    assert (info.gender, info.gender_raw) == ("F", "Donna")
    assert info.birth_date == date(1995, 3, 12)  # MM/DD/YYYY, as myFBr read it
    assert info.registered_at == profile.registered_at
    assert info.downloaded_at == profile.downloaded_at
    assert info.relationship == "Single"


def test_english_profile_page(tmp_path: Path) -> None:
    profile = sample_profile(style="en_us", gender_label="Male", birthday="December 3, 1994")
    info = parse_index_page(write_fake_export(tmp_path / "alpha", profile) / "index.htm")
    assert (info.language, info.gender) == ("en", "M")
    assert info.birth_date == date(1994, 12, 3)
    assert info.downloaded_at == profile.downloaded_at


def test_genere_label_and_missing_rows(tmp_path: Path) -> None:
    page = tmp_path / "index.htm"
    page.write_text(
        '<html><body><div class="contents"><table><tr><th>Genere</th><td>Uomo</td></tr>'
        "</table></div></body></html>",
        encoding="utf-8",
    )
    info = parse_index_page(page)
    assert info.gender == "M"
    assert info.downloaded_at is None
    assert info.birth_date is None


def test_profile_info_holds_no_identity_fields() -> None:
    names = {field.name for field in fields(ProfileInfo)}
    assert names == {
        "language",
        "gender",
        "gender_raw",
        "birth_date",
        "registered_at",
        "downloaded_at",
        "relationship",
    }
