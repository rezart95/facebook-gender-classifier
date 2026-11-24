from pathlib import Path

from fbgc_pipeline.locate.language import detect_language
from fbgc_pipeline.locate.profile_finder import list_profiles
from fbgc_pipeline.parse.html_loading import load_tree
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import sample_profile


def test_lists_profiles_from_both_waves(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    write_fake_export(raw / "wave1" / "alpha.zip", sample_profile())
    nested = raw / "wave2" / "beta"
    write_fake_export(nested / "beta", sample_profile())
    (nested / "__MACOSX" / "junk").mkdir(parents=True)
    (raw / "wave2" / "gamma").mkdir()
    (raw / "wave2" / ".directory").write_text("x", encoding="utf-8")
    found, missing = list_profiles(raw)
    assert [(location.wave, location.folder_code) for location in found] == [
        (1, "ALPHA"),
        (2, "BETA"),
    ]
    assert found[1].root == nested / "beta"
    assert missing == [(2, "GAMMA")]


def test_detects_italian_english_and_other(tmp_path: Path) -> None:
    italian = write_fake_export(tmp_path / "it", sample_profile()) / "index.htm"
    english = write_fake_export(tmp_path / "en", sample_profile(style="en_uk")) / "index.htm"
    spanish = tmp_path / "index.htm"
    spanish.write_text(
        "<html><body><table><tr><th>Sexo</th><td>Mujer</td></tr></table></body></html>",
        encoding="utf-8",
    )
    assert detect_language(load_tree(italian, keep_nesting=False)) == "it"
    assert detect_language(load_tree(english, keep_nesting=False)) == "en"
    assert detect_language(load_tree(spanish, keep_nesting=False)) == "other"
