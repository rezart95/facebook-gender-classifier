"""The scrub check demands the exact published columns, dtypes and codes."""

import pandas as pd
import pytest

from fbgc_pipeline.anonymize.scrub import AnonymizationError, scrub_check


def tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    participants = pd.DataFrame(
        {
            "pid": [f"P{rank:03d}" for rank in range(1, 6)],
            "wave": [1] * 5,
            "gender": ["F"] * 5,
            "age_band": ["20"] * 5,
            "relationship": ["single"] * 5,
            "has_messages": [True] * 5,
            "has_survey": [False] * 5,
        }
    )
    features = pd.DataFrame({"pid": ["P001", "P002"], "feature_key": ["msg_count"] * 2})
    return participants, features.assign(value=[1.0, 2.0])


def check(participants: pd.DataFrame, features: pd.DataFrame) -> None:
    scrub_check(participants, features, set(), k=5)


def test_an_extra_numeric_column_in_participants_fails() -> None:
    participants, features = tables()
    with pytest.raises(AnonymizationError, match=r"participants has unexpected columns: \['age'\]"):
        check(participants.assign(age=21), features)


def test_an_extra_column_in_features_fails() -> None:
    participants, features = tables()
    with pytest.raises(AnonymizationError, match=r"features has unexpected columns: \['extra'\]"):
        check(participants, features.assign(extra=1.0))


def test_a_missing_column_fails() -> None:
    participants, features = tables()
    with pytest.raises(AnonymizationError, match="participants is missing columns"):
        check(participants.drop(columns="has_survey"), features)


def test_reordered_columns_fail() -> None:
    participants, features = tables()
    with pytest.raises(AnonymizationError, match="features columns are out of order"):
        check(participants, features[["feature_key", "pid", "value"]])


@pytest.mark.parametrize(
    ("column", "bad"),
    [("gender", "X"), ("age_band", "21-23"), ("wave", 3), ("relationship", "complicated")],
)
def test_a_category_outside_its_codes_fails(column: str, bad: object) -> None:
    participants, features = tables()
    participants.loc[0, column] = bad
    with pytest.raises(AnonymizationError, match=f"participants.{column} holds a value outside"):
        check(participants, features)


@pytest.mark.parametrize("band", ["unknown", "all", "<20", "25+"])
def test_every_age_band_label_is_a_known_code(band: str) -> None:
    participants, features = tables()
    check(participants.assign(age_band=band), features)


@pytest.mark.parametrize("column", ["has_messages", "has_survey"])
def test_a_flag_that_is_not_boolean_fails(column: str) -> None:
    participants, features = tables()
    with pytest.raises(AnonymizationError, match=f"participants.{column} is not boolean"):
        check(participants.assign(**{column: [1] * 5}), features)


def test_a_non_numeric_or_missing_value_fails() -> None:
    participants, features = tables()
    with pytest.raises(AnonymizationError, match="features.value is not a number"):
        check(participants, features.assign(value=["a", "b"]))
    with pytest.raises(AnonymizationError, match="features.value is not a number"):
        check(participants, features.assign(value=[1.0, float("nan")]))


def test_a_non_integer_wave_fails() -> None:
    participants, features = tables()
    with pytest.raises(AnonymizationError, match="participants.wave is not an integer"):
        check(participants.assign(wave=[1.0] * 5), features)
