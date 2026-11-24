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
# First matching rule wins; "other" goes first so "open"/"complicated" never read as a couple.
RULES: tuple[tuple[Relationship, tuple[str, ...]], ...] = (
    (
        "other",
        ("relazione aperta", "open relationship", "complicat", "vedov", "widow")
        + ("separat", "divorzi", "divorced"),
    ),
    ("married", ("sposat", "married", "unione civile", "civil union")),
    ("engaged", ("fidanzat", "findanzat", "engaged")),
    (
        "in_relationship",
        ("impegnat", "in a relationship", "coppia di fatto", "domestic partnership")
        + ("convivent",),
    ),
    ("single", ("single",)),
)
# A partner's name follows "con"/"with"; only the keyword before it counts, so a surname such as
# "Sposato" or "Vedovati" can never change the category.
PARTNER_SUFFIX = re.compile(r"\s+(?:con|with)\b.*$", re.DOTALL)


def relationship_category(label: str | None) -> Relationship:
    """The category of a relationship label; unknown when missing, other when unrecognised."""
    if label is None or not label.strip():
        return "unknown"
    text = PARTNER_SUFFIX.sub("", label.lower())
    for category, keywords in RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return "other"


def suppress_rare(categories: Sequence[str], k: int) -> list[str]:
    """Categories with fewer than k people become 'other'; an 'other' below k joins 'unknown'."""
    counts = Counter(categories)
    merged = [
        category if category in ("other", "unknown") or counts[category] >= k else "other"
        for category in categories
    ]
    if 0 < Counter(merged)["other"] < k:
        merged = ["unknown" if category == "other" else category for category in merged]
    return merged
