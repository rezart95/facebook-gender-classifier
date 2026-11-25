import pytest

from fbgc_pipeline.anonymize.pseudonyms import pid_key, pseudonymous_ids

SECRET = "a" * 32
KEYS = [pid_key(1 + index % 2, f"code-{index}") for index in range(20)]


def test_pid_key_joins_wave_and_code() -> None:
    assert pid_key(2, "ALPHA") == "2:ALPHA"


def test_ids_are_p001_to_pnnn() -> None:
    ids = pseudonymous_ids(KEYS, SECRET)
    assert sorted(ids) == [f"P{rank:03d}" for rank in range(1, 21)]


def test_ids_are_stable_and_independent_of_input_order() -> None:
    first = dict(zip(KEYS, pseudonymous_ids(KEYS, SECRET), strict=True))
    shuffled = KEYS[::-1]
    second = dict(zip(shuffled, pseudonymous_ids(shuffled, SECRET), strict=True))
    assert first == second


def test_another_secret_gives_another_assignment() -> None:
    assert pseudonymous_ids(KEYS, SECRET) != pseudonymous_ids(KEYS, "b" * 32)


def test_more_than_999_profiles_widen_the_ids() -> None:
    keys = [pid_key(1, f"code-{index}") for index in range(1000)]
    assert sorted(pseudonymous_ids(keys, SECRET))[-1] == "P1000"


def test_duplicate_keys_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        pseudonymous_ids(["1:ALPHA", "1:ALPHA"], SECRET)
