from pathlib import Path

import pytest
from typer.testing import CliRunner

from fbgc_pipeline.anonymize.relationship import RELATIONSHIPS
from fbgc_pipeline.cli import app
from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.extract.profile_extractor import extract_profile
from fbgc_pipeline.locate.profile_finder import ProfileLocation
from fbgc_pipeline.synthetic.fake_profiles import generate_fake_profile, write_fake_profiles

FIXTURES = Path(__file__).with_name("fixtures") / "profiles"
FIXTURE_NAMES = ["fake-01", "fake-02", "fake-03"]


def test_profiles_are_deterministic() -> None:
    assert generate_fake_profile(1) == generate_fake_profile(1)
    assert generate_fake_profile(1) != generate_fake_profile(2)
    assert generate_fake_profile(1, seed=1) != generate_fake_profile(1)


def test_odd_profiles_are_women_and_even_profiles_men() -> None:
    assert generate_fake_profile(1).gender_label == "Donna"
    assert generate_fake_profile(2).gender_label == "Uomo"


def test_chats_contain_emoji_and_emoticons() -> None:
    texts = [m.text for t in generate_fake_profile(1).threads for m in t.messages]
    assert any(ord(char) > 0x2600 for text in texts for char in text)
    assert any(":)" in text or "<3" in text or ";)" in text for text in texts)


def test_a_generated_profile_extracts_with_dictionary_hits(tmp_path: Path) -> None:
    root = write_fake_profiles(tmp_path, 1)[0]
    result = extract_profile(ProfileLocation(1, "FAKE-01", root), FaithfulOptions())
    assert (result.status, result.gender) == ("ok", "F")
    assert result.features["msg_count"] > 0
    hits = sum(value for key, value in result.features.items() if key.startswith("dict_owner_"))
    assert hits > 0
    assert result.relationship in RELATIONSHIPS
    assert result.age_at_download is not None and 17 <= result.age_at_download <= 26


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_committed_fixtures_extract_cleanly(name: str) -> None:
    result = extract_profile(ProfileLocation(1, name.upper(), FIXTURES / name), FaithfulOptions())
    assert result.status == "ok"
    assert result.features["msg_count"] > 0


def test_committed_fixtures_match_the_generator(tmp_path: Path) -> None:
    """If this fails after a Faker upgrade, regenerate: uv run fbgc fake-profiles --n 3."""
    write_fake_profiles(tmp_path, 3)
    for name in FIXTURE_NAMES:
        for page in ("index.htm", "html/messages.htm", "html/wall.htm"):
            fresh = (tmp_path / name / page).read_bytes()
            assert fresh == (FIXTURES / name / page).read_bytes(), f"{name}/{page}"


def test_cli_fake_profiles(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["fake-profiles", "--n", "2", "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert sorted(path.name for path in tmp_path.iterdir()) == ["fake-01", "fake-02"]
