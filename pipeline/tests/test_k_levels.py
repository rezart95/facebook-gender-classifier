"""Relationship generalisation hierarchy and the joint (age, relationship) level choice."""

import pytest

from fbgc_pipeline.anonymize.k_anonymity import KAnonymityError, choose_levels, smallest_cell
from fbgc_pipeline.anonymize.relationship import RELATIONSHIPS, generalize_relationship


def test_level_zero_keeps_every_category() -> None:
    assert [generalize_relationship(label, 0) for label in RELATIONSHIPS] == list(RELATIONSHIPS)


def test_level_one_merges_the_partnered_categories() -> None:
    merged = {label: generalize_relationship(label, 1) for label in RELATIONSHIPS}
    assert merged == {
        "single": "single",
        "in_relationship": "in_relationship",
        "engaged": "in_relationship",
        "married": "in_relationship",
        "other": "in_relationship",
        "unknown": "unknown",
    }


def test_level_two_hides_the_relationship() -> None:
    assert {generalize_relationship(label, 2) for label in RELATIONSHIPS} == {"unknown"}


def test_an_unknown_level_is_rejected() -> None:
    with pytest.raises(ValueError, match="relationship level"):
        generalize_relationship("single", 3)


def test_smallest_cell_counts_any_number_of_columns() -> None:
    assert smallest_cell(["a", "a", "b"], ["F", "F", "F"], [1, 1, 1], ["x", "y", "x"]) == 1


def test_age_detail_is_preferred_over_relationship_detail() -> None:
    ages = [20.0] * 5 + [25.0] * 5
    relationships = ["single"] * 8 + ["married"] * 2
    assert choose_levels(ages, ["F"] * 10, [1] * 10, relationships) == (0, 2)


def test_relationship_stays_fine_when_only_the_age_is_thin() -> None:
    ages = [20.0] * 3 + [22.0] * 7
    assert choose_levels(ages, ["F"] * 10, [1] * 10, ["single"] * 10) == (2, 0)


def test_failure_without_any_combination_names_no_row() -> None:
    with pytest.raises(KAnonymityError, match="no combination") as error:
        choose_levels([20.0] * 4, ["F"] * 4, [1] * 4, ["single"] * 4)
    assert "20" not in str(error.value)
