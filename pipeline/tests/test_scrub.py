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


def check(participants: pd.DataFrame, features: pd.DataFrame, codes: set[str]) -> None:
    scrub_check(participants, features, codes, k=5)


def test_clean_tables_pass() -> None:
    check(*tables(), {"ALPHA"})


def test_an_unexpected_text_column_fails() -> None:
    participants, features = tables()
    with pytest.raises(
        AnonymizationError, match=r"participants has unexpected columns: \['note'\]"
    ):
        check(participants.assign(note="hello"), features, set())


def test_a_date_column_fails() -> None:
    participants, features = tables()
    dated = participants.assign(registered=pd.Timestamp("2010-01-01"))
    with pytest.raises(AnonymizationError, match="registered"):
        check(dated, features, set())


def test_a_value_outside_the_codes_fails() -> None:
    participants, features = tables()
    participants.loc[0, "relationship"] = "Impegnata/o con Ugo"
    with pytest.raises(AnonymizationError, match="relationship holds a value outside") as error:
        check(participants, features, set())
    assert "Ugo" not in str(error.value)


def test_a_folder_code_anywhere_fails_without_being_printed() -> None:
    participants, features = tables()
    with pytest.raises(AnonymizationError, match="holds a folder code") as error:
        check(participants, features, {"p003"})
    assert "P003" not in str(error.value)


def test_a_folder_code_in_a_feature_key_fails_without_being_printed() -> None:
    participants, features = tables()
    with pytest.raises(AnonymizationError, match="features.feature_key holds a folder code") as e:
        check(participants, features, {"MSG_COUNT"})
    assert "msg_count" not in str(e.value).lower()


def test_a_non_pid_fails() -> None:
    participants, features = tables()
    participants.loc[0, "pid"] = "ALPHA"
    with pytest.raises(AnonymizationError, match="not a P-ID"):
        check(participants, features, set())


def test_a_non_pid_in_the_features_table_fails() -> None:
    participants, features = tables()
    features.loc[0, "pid"] = "alpha"
    with pytest.raises(AnonymizationError, match="features.pid holds a value that is not a P-ID"):
        check(participants, features, set())


def test_an_unknown_feature_key_fails() -> None:
    participants, features = tables()
    features.loc[0, "feature_key"] = "free_text"
    with pytest.raises(AnonymizationError, match="unknown feature key") as error:
        check(participants, features, set())
    assert "free_text" not in str(error.value)


def test_a_private_column_name_is_not_a_known_feature_key() -> None:
    participants, features = tables()
    features.loc[0, "feature_key"] = "age_at_download"
    with pytest.raises(AnonymizationError, match="unknown feature key"):
        check(participants, features, set())


def test_survey_feature_keys_are_known() -> None:
    participants, features = tables()
    features.loc[0, "feature_key"] = "gpius_total"
    check(participants, features, set())


def test_a_small_cell_fails() -> None:
    participants, features = tables()
    participants.loc[0, "gender"] = "M"
    with pytest.raises(AnonymizationError, match="fewer than 5 people"):
        check(participants, features, set())


def test_a_thin_relationship_cell_fails() -> None:
    participants, features = tables()
    participants.loc[0, "relationship"] = "married"
    with pytest.raises(AnonymizationError, match="fewer than 5 people"):
        check(participants, features, set())
