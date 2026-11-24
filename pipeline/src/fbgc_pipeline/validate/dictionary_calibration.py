"""Choose, for each rebuilt word, the regex variant that best reproduces the 2019 counts."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from fbgc_pipeline.features.faithful.dictionary import WORD_VARIANTS, WORDS_PATH, word_regex

CountKey = tuple[str, str, str]  # (term, variant, scope)
LEGACY_SCOPES = {
    "owner_group": "user_grp",
    "owner_personal": "user_personal",
    "others_group": "others_grp",
    "others_personal": "others_personal",
}
WORDS_HEADER = (
    "# The 79 dictionary words of the 2019 feature table. Their original regexes were never\n"
    "# published, so each `phrase` is rebuilt from the column name. `variant` (substring | word |\n"
    "# substring_ci | word_ci) is chosen by `fbgc calibrate-dictionary` against the 2019 table.\n"
)


@dataclass(frozen=True)
class WordChoice:
    term: str
    phrase: str
    variant: str
    exact_rate: float
    rates: dict[str, float]


def profile_word_counts(
    texts: Mapping[str, Sequence[str]], entries: Sequence[Mapping[str, str]]
) -> dict[CountKey, int]:
    counts: dict[CountKey, int] = {}
    for entry in entries:
        for variant in WORD_VARIANTS:
            regex = word_regex(entry["phrase"], variant)
            for scope, scope_texts in texts.items():
                counts[(entry["term"], variant, scope)] = sum(
                    len(regex.findall(t)) for t in scope_texts
                )
    return counts


def variant_rate(
    per_profile: Mapping[str, Mapping[CountKey, int]], legacy: pd.DataFrame, term: str, variant: str
) -> float:
    hits = total = 0
    for scope, legacy_scope in LEGACY_SCOPES.items():
        column = f"{legacy_scope}.{term}"
        if column not in legacy.columns:
            continue
        expected = legacy[column].astype(float).to_dict()
        for code, counts in per_profile.items():
            key = (term, variant, scope)
            if code not in expected or key not in counts or math.isnan(expected[code]):
                continue
            total += 1
            hits += int(counts[key] == expected[code])
    return hits / total if total else math.nan


def choose_variants(
    per_profile: Mapping[str, Mapping[CountKey, int]],
    legacy: pd.DataFrame,
    entries: Sequence[Mapping[str, str]],
) -> list[WordChoice]:
    choices = []
    for entry in entries:
        rates = {v: variant_rate(per_profile, legacy, entry["term"], v) for v in WORD_VARIANTS}
        scores = {v: -1.0 if math.isnan(rate) else rate for v, rate in rates.items()}
        best = max(WORD_VARIANTS, key=scores.__getitem__)
        choices.append(WordChoice(entry["term"], entry["phrase"], best, rates[best], rates))
    return choices


def write_word_entries(choices: Sequence[WordChoice], path: Path = WORDS_PATH) -> None:
    words = [{"term": c.term, "phrase": c.phrase, "variant": c.variant} for c in choices]
    body = yaml.safe_dump({"words": words}, allow_unicode=True, sort_keys=False, width=100)
    path.write_text(WORDS_HEADER + body, encoding="utf-8", newline="\n")


def render_calibration_report(choices: Sequence[WordChoice], profiles: int) -> str:
    strong = sum(1 for choice in choices if choice.exact_rate >= 0.95)
    lines = [
        "# Dictionary calibration",
        "",
        f"The rebuilt dictionary words, calibrated on {profiles} profiles. For each word the",
        "variant with the highest exact-match rate against the 2019 counts is kept.",
        "Aggregates only.",
        "",
        f"- Words at or above 95% exact matches: {strong} of {len(choices)}",
        "",
        "| Word | Phrase | Chosen | Exact | " + " | ".join(WORD_VARIANTS) + " |",
        "|---|---|---|---:|" + "---:|" * len(WORD_VARIANTS),
    ]
    for c in choices:
        rates = " | ".join(f"{c.rates.get(v, math.nan):.1%}" for v in WORD_VARIANTS)
        lines.append(f"| `{c.term}` | {c.phrase} | {c.variant} | {c.exact_rate:.1%} | {rates} |")
    return "\n".join(lines) + "\n"
