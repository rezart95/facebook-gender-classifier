"""Which generalisation levels anonymize_profiles chooses, and what callers may pass in."""

import math

import pandas as pd
import pytest

from fbgc_pipeline.anonymize.tables import anonymize_profiles

SECRET = "t" * 32
KEYS = ["msg_count", "friends_accepted"]


def rows(groups: list[tuple[str, str, int]]) -> pd.DataFrame:
    """One extracted row per person; groups are (gender, relationship, how many), all aged 20."""
    people = [(gender, label) for gender, label, count in groups for _ in range(count)]
    return pd.DataFrame(
        {
            "wave": 1,
            "folder_code": [f"prof-{index:02d}" for index in range(len(people))],
            "status": "ok",
            "gender": [gender for gender, _ in people],
            "age_at_download": 20.0,
            "relationship": [label for _, label in people],
            "msg_count": 1.0,
            "friends_accepted": 120.0,
            "has_survey": True,
        }
    )


def levels(frame: pd.DataFrame) -> tuple[object, object]:
    summary = anonymize_profiles(frame, KEYS, SECRET).summary
    return summary["age_level"], summary["relationship_level"]


def test_level_zero_when_every_relationship_cell_has_five() -> None:
    assert levels(rows([("F", "single", 5), ("M", "single", 5), ("M", "married", 5)])) == (0, 0)


def test_level_one_merges_the_partnered_categories() -> None:
    frame = rows(
        [
            ("F", "single", 5),
            ("F", "married", 3),
            ("F", "engaged", 2),
            ("M", "single", 5),
            ("M", "engaged", 3),
            ("M", "married", 2),
        ]
    )
    data = anonymize_profiles(frame, KEYS, SECRET)
    assert (data.summary["age_level"], data.summary["relationship_level"]) == (0, 1)
    assert data.participants["relationship"].value_counts().to_dict() == {
        "single": 10,
        "in_relationship": 10,
    }


def test_level_two_when_even_the_merged_cell_is_thin() -> None:
    frame = rows([("F", "single", 5), ("M", "single", 3), ("M", "married", 2)])
    data = anonymize_profiles(frame, KEYS, SECRET)
    assert (data.summary["age_level"], data.summary["relationship_level"]) == (0, 2)
    assert set(data.participants["relationship"]) == {"unknown"}


def test_a_private_column_cannot_be_a_feature_key() -> None:
    with pytest.raises(ValueError, match=r"^1 feature key") as error:
        anonymize_profiles(
            rows([("F", "single", 5), ("M", "single", 5)]), ["age_at_download"], SECRET
        )
    assert "age_at_download" not in str(error.value)


def test_a_folder_code_cannot_be_a_feature_key() -> None:
    frame = rows([("F", "single", 5), ("M", "single", 5)])
    with pytest.raises(ValueError, match=r"^2 feature keys") as error:
        anonymize_profiles(frame, ["prof-00", "msg_count", "prof-01"], SECRET)
    assert "prof-" not in str(error.value)


def test_a_missing_survey_flag_means_no_survey() -> None:
    frame = rows([("F", "single", 5), ("M", "single", 5)])
    frame["has_survey"] = [True, None, math.nan, True, False] * 2
    data = anonymize_profiles(frame, KEYS, SECRET)
    assert data.participants["has_survey"].dtype == bool
    assert int(data.participants["has_survey"].sum()) == 4


def test_a_missing_message_count_column_raises() -> None:
    frame = rows([("F", "single", 5), ("M", "single", 5)]).drop(columns="msg_count")
    with pytest.raises(ValueError, match="msg_count"):
        anonymize_profiles(frame, ["friends_accepted"], SECRET)
