from collections import Counter

import pytest

from fbgc_pipeline.anonymize.relationship import (
    RELATIONSHIPS,
    relationship_category,
    suppress_rare,
)


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Single", "single"),
        ("Impegnata/o", "in_relationship"),
        ("Impegnata", "in_relationship"),
        ("Impegnato", "in_relationship"),
        ("Impegnati dal 12 maggio 2014", "in_relationship"),
        ("Impegnata/o con Marco Verdi", "in_relationship"),
        ("Fidanzata/o ufficialmente", "engaged"),
        ("Findanzata/o ufficialmente", "engaged"),
        ("Sposata/o", "married"),
        ("Sposata/o dal 3 giugno 2012", "married"),
        ("In una relazione aperta", "other"),
        ("In una coppia di fatto", "in_relationship"),
        ("Convivente", "in_relationship"),
        ("In una relazione complicata", "other"),
        ("Vedova/o", "other"),
        ("Vedova", "other"),
        ("Vedovo", "other"),
        ("In a relationship", "in_relationship"),
        ("In an open relationship", "other"),
        ("Engaged", "engaged"),
        ("Married", "married"),
        ("It's complicated", "other"),
        ("Qualcosa di nuovo", "other"),
        (None, "unknown"),
        ("   ", "unknown"),
        ("", "unknown"),
    ],
)
def test_labels_map_to_the_vocabulary(label: str | None, expected: str) -> None:
    assert relationship_category(label) == expected


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Impegnata/o con Francesco Sposato", "in_relationship"),
        ("Impegnato con Anna Single", "in_relationship"),
        ("Sposata/o con Luca Fidanzati dal 3 giugno 2012", "married"),
        ("Fidanzata/o ufficialmente con Marta Vedovati", "engaged"),
        ("Convivente con Paolo Complicati", "in_relationship"),
        ("In a relationship with Sam Married", "in_relationship"),
        ("Engaged with Alex Widowski", "engaged"),
        ("Single con Elena", "single"),
    ],
)
def test_a_partner_name_never_changes_the_category(label: str, expected: str) -> None:
    assert relationship_category(label) == expected


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Engaged to Alex Widowski", "engaged"),
        ("Engaged to Sam Married", "engaged"),
        ("Married to Sam Single", "married"),
        ("Vedova/o di Mario Sposato", "other"),
        ("Sposata/o\nMarco Vedovati", "married"),
        ("Impegnata/o, Marco Sposato", "in_relationship"),
        ("In una relazione", "in_relationship"),
        ("In una relazione aperta", "other"),
        ("In una relazione complicata", "other"),
        ("In una relazione aperta con Mario Sposato", "other"),
        ("In una coppia di fatto con Mario Rossi", "in_relationship"),
        ("In una coppia di fatto, Mario Vedovati", "in_relationship"),
    ],
)
def test_the_leading_keyword_decides(label: str, expected: str) -> None:
    assert relationship_category(label) == expected


def test_suppress_rare_needs_a_positive_k() -> None:
    with pytest.raises(ValueError, match="k must be at least 1"):
        suppress_rare(["single"], k=0)


def test_categories_never_carry_the_label_text() -> None:
    category = relationship_category("Impegnata/o con Marco Verdi")
    assert category in RELATIONSHIPS
    assert "Marco" not in category


def test_rare_categories_become_other_and_a_small_other_joins_unknown() -> None:
    people = ["single"] * 6 + ["married"] * 2 + ["engaged"] * 5 + ["other"] + ["unknown"] * 3
    result = Counter(suppress_rare(people, k=5))
    assert result == {"single": 6, "engaged": 5, "unknown": 6}


def test_an_other_with_k_people_stays_other() -> None:
    people = ["single"] * 6 + ["married"] * 3 + ["other"] * 2
    assert Counter(suppress_rare(people, k=5)) == {"single": 6, "other": 5}


def test_suppression_keeps_the_order_of_people() -> None:
    assert suppress_rare(["single", "married", "single"], k=2) == ["single", "unknown", "single"]
