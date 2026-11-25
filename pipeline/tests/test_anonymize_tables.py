import math

import pandas as pd
import pytest

from fbgc_pipeline.anonymize.k_anonymity import KAnonymityError
from fbgc_pipeline.anonymize.tables import PARTICIPANT_COLUMNS, anonymize_profiles

SECRET = "t" * 32
KEYS = ["msg_count", "friends_accepted", "gpius_total"]


def profile_rows(n_female: int = 5, n_male: int = 5, n_married: int = 0) -> pd.DataFrame:
    """Extracted rows: 5 women and 5 men aged 20, one row without gender, one failed row."""
    rows: list[dict[str, object]] = []
    for index in range(n_female + n_male):
        rows.append(
            {
                "wave": 1,
                "folder_code": f"prof-{index:02d}",
                "status": "ok",
                "language": "it",
                "gender": "F" if index < n_female else "M",
                "age_at_download": 20.0,
                "relationship": "married" if index >= n_female + n_male - n_married else "single",
                "msg_count": float(index),
                "friends_accepted": 120.0 + index,
                "gpius_total": 2.5 if index % 2 else math.nan,
                "has_survey": bool(index % 2),
            }
        )
    rows.append({**rows[0], "folder_code": "prof-nogender", "gender": None})
    rows.append({"wave": 2, "folder_code": "prof-failed", "status": "failed", "gender": None})
    return pd.DataFrame(rows)


def test_participants_are_coarse_and_keyed_by_pid() -> None:
    data = anonymize_profiles(profile_rows(), KEYS, SECRET)
    people = data.participants
    assert tuple(people.columns) == PARTICIPANT_COLUMNS
    assert list(people["pid"]) == [f"P{rank:03d}" for rank in range(1, 11)]
    assert set(people["age_band"]) == {"20"}
    assert people["relationship"].value_counts().to_dict() == {"single": 10}
    assert int(people["has_messages"].sum()) == 9
    assert int(people["has_survey"].sum()) == 5
    assert data.summary["dropped_without_gender"] == 1
    assert data.summary["age_level"] == 0
    assert data.summary["relationship_level"] == 0
    assert data.summary["smallest_cell"] == 5


def test_feature_values_are_long_rounded_and_without_gaps() -> None:
    data = anonymize_profiles(profile_rows(), KEYS, SECRET)
    long = data.features_long
    assert list(long.columns) == ["pid", "feature_key", "value"]
    assert not long["value"].isna().any()
    friends = sorted(long.loc[long["feature_key"] == "friends_accepted", "value"])
    assert friends == [120.0] * 5 + [130.0] * 5  # 120..129, half rounds up
    assert (long["feature_key"] == "gpius_total").sum() == 5


def test_no_folder_code_or_date_reaches_the_output() -> None:
    data = anonymize_profiles(profile_rows(), KEYS, SECRET)
    text = data.participants.to_csv() + data.features_long.to_csv()
    assert "prof-" not in text.lower()
    assert SECRET not in text
    assert not any("date" in column or "_at" in column for column in data.participants.columns)


def test_pids_depend_on_the_secret_only_through_their_order() -> None:
    first = anonymize_profiles(profile_rows(), KEYS, SECRET).participants
    second = anonymize_profiles(profile_rows(), KEYS, "u" * 32).participants
    assert list(first["pid"]) == list(second["pid"])
    assert first.drop(columns="pid").values.tolist() != second.drop(columns="pid").values.tolist()


def test_too_few_people_in_a_cell_fails() -> None:
    with pytest.raises(KAnonymityError):
        anonymize_profiles(profile_rows(n_female=4), KEYS, SECRET)


def test_thin_relationship_cells_are_generalised_not_published() -> None:
    data = anonymize_profiles(profile_rows(n_married=2), KEYS, SECRET)
    assert data.participants["relationship"].value_counts().to_dict() == {"unknown": 10}
    assert data.summary["relationship_level"] == 2
    assert data.summary["smallest_cell"] == 5


def test_k_below_the_minimum_is_refused() -> None:
    with pytest.raises(ValueError, match="at least 5"):
        anonymize_profiles(profile_rows(), KEYS, SECRET, k=4)


def test_a_missing_survey_flag_fails_safe_to_false() -> None:
    rows = profile_rows()
    rows["has_survey"] = pd.array([True, pd.NA] * 6, dtype="boolean")
    people = anonymize_profiles(rows, KEYS, SECRET).participants
    assert people["has_survey"].dtype == bool
    assert int(people["has_survey"].sum()) == 5
