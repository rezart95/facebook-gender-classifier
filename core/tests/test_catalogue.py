from pathlib import Path

import pytest

from fbgc_core.catalogue import load_catalogue
from fbgc_core.catalogue_expand import expand_family

LEGACY_COLUMNS = Path(__file__).with_name("data") / "legacy_2019_columns.txt"


def test_catalogue_holds_the_539_faithful_features() -> None:
    catalogue = load_catalogue()
    assert len(catalogue.features) == 539
    assert catalogue.keys(origin="2019") == catalogue.keys()


def test_legacy_names_match_the_2019_table() -> None:
    expected = set(LEGACY_COLUMNS.read_text(encoding="utf-8").split())
    assert len(expected) == 529
    assert set(load_catalogue().legacy_to_key()) == expected


def test_the_2am_hour_has_no_legacy_column() -> None:
    assert load_catalogue().get("msg_hour_02").legacy_name is None
    assert load_catalogue().get("msg_hour_03").legacy_name == "msg_freq_ore.03"


def test_dictionary_keys_are_lowercase_and_keep_the_legacy_case() -> None:
    spec = load_catalogue().get("dict_owner_group_nonloso")
    assert spec.legacy_name == "user_grp.NonLoSo"
    assert spec.family == "dictionary"


def test_weekday_template_uses_mapping_values() -> None:
    spec = load_catalogue().get("msg_weekday_sun")
    assert spec.legacy_name == "msg_freq_giorni.domenic"
    assert "Sunday" in spec.description_en


def test_template_expansion() -> None:
    family = {
        "name": "f",
        "origin": "new",
        "template": {
            "key": "x_{d[key]}_{n}",
            "legacy": "L.{n}",
            "unit": "u",
            "en": "E {d[en]}",
            "it": "I {d[it]}",
        },
        "expand": {"d": [{"key": "a", "en": "A", "it": "AA"}], "n": ["1", "2"]},
        "legacy_missing": ["L.2"],
    }
    entries = expand_family(family)
    assert [entry["key"] for entry in entries] == ["x_a_1", "x_a_2"]
    assert [entry["legacy_name"] for entry in entries] == ["L.1", None]
    assert entries[0]["description_en"] == "E A"


def test_duplicate_keys_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "catalogue.yaml"
    path.write_text(
        "version: 1\nfamilies:\n  - name: f\n    origin: new\n    features:\n"
        "      - {key: a, unit: u, en: e, it: i}\n      - {key: a, unit: u, en: e, it: i}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_catalogue(path)
