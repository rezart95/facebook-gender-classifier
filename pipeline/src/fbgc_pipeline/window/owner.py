"""Find the export owner's display name (kept in memory only).

myFBr took the most frequent name across one-to-one threads. Its R code
indexed thread levels with a per-message vector (a bug); counting names over
distinct one-to-one threads gives the same owner in practice.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from fbgc_pipeline.parse.records import Thread


def find_owner(threads: Sequence[Thread]) -> str | None:
    """Most frequent name across distinct one-to-one threads with messages.

    Ties go to the alphabetically first name, as R's table() sorts names.
    """
    personal = {
        thread.participants for thread in threads if not thread.is_group and thread.messages
    }
    counts = Counter(name for participants in personal for name in participants)
    if not counts:
        return None
    return max(sorted(counts), key=counts.__getitem__)
