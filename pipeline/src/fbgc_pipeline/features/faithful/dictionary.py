"""Dictionary counts with stringr::str_count semantics (non-overlapping matches).

Four scopes: messages the owner wrote or others wrote, in group or one-to-one chats.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import yaml

from fbgc_pipeline.features.faithful.dictionary_patterns import MYFBR_PATTERNS
from fbgc_pipeline.parse.records import Thread

SCOPES = ("owner_group", "owner_personal", "others_group", "others_personal")
WORD_VARIANTS = ("substring", "word", "substring_ci", "word_ci")
WORDS_PATH = Path(__file__).with_name("data") / "dictionary_words.yaml"


@dataclass(frozen=True)
class DictionaryPattern:
    term: str
    regex: re.Pattern[str]


def word_regex(phrase: str, variant: str) -> re.Pattern[str]:
    if variant not in WORD_VARIANTS:
        raise ValueError(f"unknown word variant: {variant!r}")
    body = re.escape(phrase)
    if variant.startswith("word"):
        body = rf"\b{body}\b"
    return re.compile(body, re.IGNORECASE if variant.endswith("_ci") else 0)


def load_word_entries(path: Path = WORDS_PATH) -> list[dict[str, str]]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["words"]


@cache
def load_dictionary(path: Path = WORDS_PATH) -> tuple[DictionaryPattern, ...]:
    fixed = [DictionaryPattern(term, re.compile(pattern)) for term, pattern in MYFBR_PATTERNS]
    words = [
        DictionaryPattern(entry["term"], word_regex(entry["phrase"], entry["variant"]))
        for entry in load_word_entries(path)
    ]
    return tuple(fixed + words)


def scoped_texts(threads: Sequence[Thread], owner: str | None) -> dict[str, list[str]]:
    texts: dict[str, list[str]] = {scope: [] for scope in SCOPES}
    for thread in threads:
        kind = "group" if thread.is_group else "personal"
        for message in thread.messages:
            author = "owner" if owner is not None and message.sender == owner else "others"
            texts[f"{author}_{kind}"].append(message.text)
    return texts


def dictionary_counts(
    threads: Sequence[Thread], owner: str | None, patterns: Sequence[DictionaryPattern]
) -> dict[str, float]:
    pairs = [(scope, pattern) for scope in SCOPES for pattern in patterns]
    if owner is None:
        return {f"dict_{scope}_{pattern.term.lower()}": math.nan for scope, pattern in pairs}
    texts = scoped_texts(threads, owner)
    return {
        f"dict_{scope}_{pattern.term.lower()}": float(
            sum(len(pattern.regex.findall(text)) for text in texts[scope])
        )
        for scope, pattern in pairs
    }
