from pathlib import Path

import pytest

from fbgc_core.catalogue import load_catalogue
from fbgc_core.catalogue_expand import expand_family

LEGACY_COLUMNS = Path(__file__).with_name("data") / "legacy_2019_columns.txt"


SURVEY_COLUMNS = {
    *(f"F_{name}" for name in ("posi", "mood", "cognitive", "compulsive", "negative", "total")),
    *(f"E_{name}" for name in ("coping", "conformity", "enhancement", "social")),
    *(f"H_{name}" for name in ("openess", "emotional", "contious", "extraversion", "agreebleness")),
    *(
        f"I_{name}"
        for name in (
            "self_efficacy",
            "self_awareness",
            "persistence",
            "school_support",
            "family_coherence",
            "peer_support",
            "emotional_regulation",
            "empathy",
            "behavioral_self_control",
            "optimism",
            "gratitude",
            "zest",
            "belief_in_self",
            "belief_in_others",
            "emotional_competence",
            "engaged_living",
            "total",
        )
    ),
    "autostima",
    *(f"M_{name}" for name in ("pos", "neg", "cc", "nc", "csc")),
}


def test_catalogue_holds_539_faithful_and_38_survey_features() -> None:
    catalogue = load_catalogue()
    assert len(catalogue.keys(origin="2019")) == 539
    assert len(catalogue.keys(origin="survey")) == 38
    assert len(catalogue.features) == 539 + 38


def test_legacy_names_match_the_2019_table() -> None:
    expected = set(LEGACY_COLUMNS.read_text(encoding="utf-8").split())
    assert len(expected) == 529
    faithful = {s.legacy_name for s in load_catalogue().features if s.origin == "2019"}
    assert faithful - {None} == expected


def test_survey_features_keep_the_2019_scale_columns() -> None:
    survey = [spec for spec in load_catalogue().features if spec.origin == "survey"]
    assert len(SURVEY_COLUMNS) == 38
    assert {spec.legacy_name for spec in survey} == SURVEY_COLUMNS
    assert {spec.unit for spec in survey} == {"score"}
    assert all(spec.family.startswith("survey_") for spec in survey)


def test_big_five_descriptions_say_low_scores_mean_the_positive_pole() -> None:
    spec = load_catalogue().get("big5_emotional_stability")
    assert spec.legacy_name == "H_emotional"
    assert "lower scores mean more emotional stability" in spec.description_en
    assert "più bassi indicano più stabilità emotiva" in spec.description_it


def test_count_units_exclude_means_and_shares() -> None:
    catalogue = load_catalogue()
    for key in ("msg_count", "msg_chars_max", "friends_accepted", "dict_owner_group_ok"):
        assert catalogue.get(key).is_count, key
    for key in ("msg_per_contact", "msg_chars_mean", "msg_hour_09", "gpius_total"):
        assert not catalogue.get(key).is_count, key


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
