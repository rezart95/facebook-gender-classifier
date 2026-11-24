"""Render the golden comparison as Markdown. Aggregates only: no participant appears."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from collections.abc import Sequence

from fbgc_pipeline.validate.golden_compare import (
    ColumnComparison,
    non_dictionary,
    overall_close_rate,
    overall_exact_rate,
)

GAPS_POINTER = "See docs/extraction-golden-gaps.md."


def _number(value: float) -> str:
    return "n/a" if math.isnan(value) else f"{value:.3g}"


def _median_correlation(items: Sequence[ColumnComparison]) -> str:
    values = [item.pearson for item in items if not math.isnan(item.pearson)]
    return _number(statistics.median(values)) if values else "n/a"


def _sort_key(item: ColumnComparison) -> float:
    return -1.0 if math.isnan(item.exact_rate) else item.exact_rate


def render_golden_report(
    comparisons: Sequence[ColumnComparison],
    options_label: str,
    gender: tuple[int, float],
    gaps_markdown: str | None = None,
) -> str:
    families: dict[str, list[ColumnComparison]] = defaultdict(list)
    for comparison in comparisons:
        families[comparison.family].append(comparison)
    rest = non_dictionary(comparisons)
    compared = max((comparison.compared for comparison in comparisons), default=0)
    lines = [
        "# Extraction golden report",
        "",
        "Faithful (2019) features recomputed in Python and compared, value by value, with the",
        "2019 feature table. Aggregates only: no participant appears in this report.",
        "",
        f"- Options: `{options_label}`",
        f"- Profiles compared: {compared}",
        f"- Overall exact-match rate (near-exact): {overall_exact_rate(comparisons):.1%}",
        f"- Overall within 0.05%: {overall_close_rate(comparisons):.1%}",
        f"- Non-dictionary exact-match rate: {overall_exact_rate(rest):.1%}",
        f"- Non-dictionary within 0.05%: {overall_close_rate(rest):.1%}",
        f"- Gender label agreement with 2019: {gender[1]:.1%} of {gender[0]} profiles",
        "",
        "## By family",
        "",
        "| Family | Columns | Exact-match rate | Within 0.05% | Median correlation |",
        "|---|---:|---:|---:|---:|",
    ]
    for family, items in families.items():
        lines.append(
            f"| {family} | {len(items)} | {overall_exact_rate(items):.1%} | "
            f"{overall_close_rate(items):.1%} | {_median_correlation(items)} |"
        )
    lines += [
        "",
        "## Worst 25 columns",
        "",
        "| Feature | 2019 column | Exact | Close | r | Max abs diff |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for item in sorted(comparisons, key=_sort_key)[:25]:
        lines.append(
            f"| `{item.key}` | `{item.legacy_name}` | {item.exact_rate:.1%} | "
            f"{item.close_rate:.1%} | {_number(item.pearson)} | {_number(item.max_abs_diff)} |"
        )
    lines += [
        "",
        "## Known gaps",
        "",
        (gaps_markdown.rstrip("\n") if gaps_markdown is not None else GAPS_POINTER),
        "",
    ]
    return "\n".join(lines)
