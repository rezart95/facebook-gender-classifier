"""Relationship status as a controlled vocabulary. The free text is never kept.

Profile pages show labels such as "Impegnata/o con <name>" or "Sposata/o dal <date>", so the
label is mapped to a category in memory by keyword rules (Italian and English), and only the
category is written anywhere. Rare categories are then merged before publication.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from typing import Literal

Relationship = Literal["single", "in_relationship", "engaged", "married", "other", "unknown"]
RELATIONSHIPS: tuple[Relationship, ...] = (
    "single",
    "in_relationship",
    "engaged",
    "married",
    "other",
    "unknown",
)
# The keyword that starts earliest in the label decides; at the same start the longest keyword
# wins, so full phrases ("in una relazione aperta") beat their prefix ("in una relazione").
RULES: tuple[tuple[Relationship, tuple[str, ...]], ...] = (
    (
        "other",
        ("in una relazione aperta", "in una relazione complicata", "in an open relationship")
        + ("relazione aperta", "open relationship", "complicat", "vedov", "widow")
        + ("separat", "divorzi", "divorced"),
    ),
    ("married", ("sposat", "married", "unione civile", "civil union")),
    ("engaged", ("fidanzat", "findanzat", "engaged")),
    (
        "in_relationship",
        ("impegnat", "in a relationship", "in una relazione", "in una coppia di fatto")
        + ("coppia di fatto", "domestic partnership", "convivent"),
    ),
    ("single", ("single",)),
)
KEYWORDS: tuple[tuple[str, Relationship], ...] = tuple(
    (keyword, category) for category, keywords in RULES for keyword in keywords
)
# Cheap first step: drop what follows "con"/"with"/"to" (a partner's name). The earliest-keyword
# rule below is what guarantees names cannot steer the category ("di", commas, line breaks).
PARTNER_SUFFIX = re.compile(r"\s+(?:con|with|to)\b.*$", re.DOTALL)


def relationship_category(label: str | None) -> Relationship:
    """The category of a relationship label; unknown when missing, other when unrecognised.

    The leading keyword decides: names or dates after it cannot change the category.
    """
    if label is None or not label.strip():
        return "unknown"
    text = PARTNER_SUFFIX.sub("", label.lower())
    hits: list[tuple[int, int, Relationship]] = [
        (text.index(keyword), -len(keyword), category)
        for keyword, category in KEYWORDS
        if keyword in text
    ]
    return min(hits)[2] if hits else "other"


def suppress_rare(categories: Sequence[str], k: int) -> list[str]:
    """Categories with fewer than k people become 'other'; an 'other' below k joins 'unknown'."""
    if k < 1:
        raise ValueError("k must be at least 1")
    counts = Counter(categories)
    merged = [
        category if category in ("other", "unknown") or counts[category] >= k else "other"
        for category in categories
    ]
    if 0 < Counter(merged)["other"] < k:
        merged = ["unknown" if category == "other" else category for category in merged]
    return merged


RELATIONSHIP_LEVELS = 3


def generalize_relationship(category: str, level: int) -> str:
    """Level 0 keeps the category; 1 merges the partnered ones, and "other" becomes "unknown" so
    nobody is published with a status they may not have; 2 hides the relationship."""
    if level == 0:
        return category
    if level == 1:
        if category == "other":
            return "unknown"
        return category if category in ("single", "unknown") else "in_relationship"
    if level == 2:
        return "unknown"
    raise ValueError("unknown relationship level")
