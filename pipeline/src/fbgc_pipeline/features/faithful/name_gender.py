"""Contacts' gender from first names, as TextWiller's classificaUtenti(how_class="modeFirst").

First pass: lowercase the full name, split on punctuation and spaces, look up every token,
and take the most frequent category (the first match on a tie). Second pass, only when
nothing matched: split CamelCase, drop digits, split on non-word characters.
"""

from __future__ import annotations

import csv
import math
import re
from collections import Counter
from collections.abc import Iterable
from functools import cache
from pathlib import Path

VOCABULARY_PATH = Path(__file__).with_name("data") / "textwiller_first_names.csv"
PUNCT_OR_SPACE = re.compile(r"[\s!-/:-@\[-`{-~]+")  # POSIX [[:punct:][:space:]]


@cache
def load_name_vocabulary(path: Path = VOCABULARY_PATH) -> dict[str, str]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["name"]: row["category"] for row in csv.DictReader(handle)}


def _mode_first(categories: list[str]) -> str:
    counts = Counter(categories)
    top = max(counts.values())
    winners = [category for category, count in counts.items() if count == top]
    return winners[0] if len(winners) == 1 else categories[0]


def _split_camel_case(name: str) -> str:
    return "".join(f" {char}" if char.isupper() else char for char in name)


def classify_name(full_name: str, vocabulary: dict[str, str]) -> str | None:
    name = full_name.strip()
    first = [vocabulary[t] for t in PUNCT_OR_SPACE.split(name.lower()) if t in vocabulary]
    if first:
        return _mode_first(first)
    spaced = re.sub(r"\d", "", _split_camel_case(name).lower())
    second = [vocabulary[t] for t in re.split(r"\W+", spaced) if t in vocabulary]
    return _mode_first(second) if second else None


def contact_gender_shares(senders: Iterable[str], vocabulary: dict[str, str]) -> dict[str, float]:
    categories = [classify_name(name, vocabulary) for name in sorted(set(senders))]
    male, female = categories.count("masc"), categories.count("femm")
    total = male + female
    return {
        "msg_contacts_male_share": male / total if total else math.nan,
        "msg_contacts_female_share": female / total if total else math.nan,
    }
