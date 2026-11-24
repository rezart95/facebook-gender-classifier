import math

from fbgc_pipeline.features.faithful.name_gender import (
    classify_name,
    contact_gender_shares,
    load_name_vocabulary,
)

VOCABULARY = {
    "mario": "masc",
    "andrea": "masc",
    "luca": "masc",
    "maria": "femm",
    "anna": "femm",
    "rai": "ente",
}


def test_first_pass_matches_tokens() -> None:
    assert classify_name("Mario Rossi", VOCABULARY) == "masc"


def test_most_frequent_category_wins() -> None:
    assert classify_name("Maria Anna Rossi", VOCABULARY) == "femm"


def test_tie_goes_to_the_first_match() -> None:
    assert classify_name("Andrea Maria", VOCABULARY) == "masc"
    assert classify_name("Maria Andrea", VOCABULARY) == "femm"


def test_second_pass_splits_camel_case_and_drops_digits() -> None:
    assert classify_name("MariaRossi", VOCABULARY) == "femm"
    assert classify_name("Luca92", VOCABULARY) == "masc"


def test_unknown_name() -> None:
    assert classify_name("Xyz Qwe", VOCABULARY) is None


def test_shares_use_distinct_senders_and_ignore_organisations() -> None:
    senders = ["Mario Rossi", "Mario Rossi", "Anna Neri", "Xyz", "Rai Uno"]
    assert contact_gender_shares(senders, VOCABULARY) == {
        "msg_contacts_male_share": 0.5,
        "msg_contacts_female_share": 0.5,
    }


def test_no_classified_contact_gives_nan() -> None:
    shares = contact_gender_shares(["Xyz"], VOCABULARY)
    assert all(math.isnan(value) for value in shares.values())


def test_real_vocabulary_loads() -> None:
    vocabulary = load_name_vocabulary()
    assert len(vocabulary) == 1123
    assert set(vocabulary.values()) == {"masc", "femm", "ente"}
