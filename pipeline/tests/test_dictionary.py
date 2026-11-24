import math
import re

import pytest

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.features.faithful.dictionary import (
    dictionary_counts,
    load_dictionary,
    word_regex,
)
from fbgc_pipeline.features.faithful.dictionary_patterns import MYFBR_PATTERNS
from fbgc_pipeline.parse.records import Message, Thread


def count(term: str, text: str) -> int:
    pattern = next(pattern for pattern in load_dictionary() if pattern.term == term)
    return len(pattern.regex.findall(text))


def test_terms_follow_the_2019_column_order() -> None:
    expected = [
        spec.legacy_name.split(".", 1)[1]
        for spec in default_catalogue().features
        if spec.family == "dictionary"
        and spec.legacy_name
        and spec.legacy_name.startswith("user_grp.")
    ]
    assert len(expected) == 110
    assert [pattern.term for pattern in load_dictionary()] == expected


def test_myfbr_quirks_are_kept() -> None:
    patterns = dict(MYFBR_PATTERNS)
    assert patterns["EMOTEUHUH"] == patterns["EMOTEIHIH"]
    assert re.compile(patterns["EMOTELOVE"]).findall("<3 \u2764") == ["<3"]


def test_emoticons_punctuation_and_interjections() -> None:
    assert count("EMOTEGOOD", "ciao :))) e :-)") == 2
    assert count("domanda", "come? davvero??") == 3
    assert count("EMOTEDAIII", "dai forzaaa") == 1
    assert count("EMOTEAHAH", "ahahah") == 1


def test_word_variants() -> None:
    assert len(word_regex("non lo so", "substring").findall("Non lo so, non lo so")) == 1
    assert len(word_regex("non lo so", "substring_ci").findall("Non lo so, non lo so")) == 2
    assert len(word_regex("io", "substring").findall("io e il mio cane")) == 2
    assert len(word_regex("io", "word").findall("io e il mio cane")) == 1
    with pytest.raises(ValueError):
        word_regex("x", "fuzzy")


def test_counts_split_by_author_and_chat_kind() -> None:
    personal = Thread(
        ("Owner", "Ann"), (Message("Owner", None, "ok? ok?"), Message("Ann", None, "ok"))
    )
    group = Thread(("Owner", "Ann", "Bob"), (Message("Bob", None, "ok!"),))
    counts = dictionary_counts([personal, group], "Owner", load_dictionary())
    assert len(counts) == 440
    assert counts["dict_owner_personal_domanda"] == 2
    assert counts["dict_owner_personal_ok"] == 2
    assert counts["dict_others_personal_ok"] == 1
    assert counts["dict_others_group_esclamativo"] == 1
    assert counts["dict_owner_group_ok"] == 0


def test_unknown_owner_gives_nan() -> None:
    assert all(
        math.isnan(value) for value in dictionary_counts([], None, load_dictionary()).values()
    )
