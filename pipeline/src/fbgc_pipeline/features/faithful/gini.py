"""myFBr's normalised Gini heterogeneity of messages across people."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence


def gini_heterogeneity(labels: Sequence[str]) -> float:
    """1 - sum(p^2), divided by its maximum (k-1)/k; 0 when undefined, as in R."""
    counts = Counter(labels)
    total, k = len(labels), len(counts)
    if total == 0 or k <= 1:
        return 0.0
    gini = 1 - sum((count / total) ** 2 for count in counts.values())
    return gini / ((k - 1) / k)
