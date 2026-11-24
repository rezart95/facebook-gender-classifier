"""Message counts and length statistics, as myFBr's getMessages_summary computed them.

R's summary() (before R 4.0) rounded min, quartiles, median and mean to 4
significant digits and used type-7 quantiles (numpy's default).
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

import numpy as np

from fbgc_pipeline.parse.records import Message

CHAR_KEYS = (
    "msg_chars_min",
    "msg_chars_q1",
    "msg_chars_median",
    "msg_chars_mean",
    "msg_chars_q3",
    "msg_chars_max",
)


def signif(value: float, digits: int = 4) -> float:
    if value == 0 or not math.isfinite(value):
        return value
    return round(value, digits - 1 - math.floor(math.log10(abs(value))))


def r_summary(values: Sequence[float]) -> tuple[float, ...]:
    if not values:
        return (math.nan,) * 6
    array = np.asarray(values, dtype=float)
    q0, q1, q2, q3, q4 = (float(q) for q in np.quantile(array, [0, 0.25, 0.5, 0.75, 1]))
    return tuple(signif(value) for value in (q0, q1, q2, float(array.mean()), q3, q4))


def message_summary(messages: Sequence[Message]) -> dict[str, float]:
    n_messages = len(messages)
    senders = Counter(message.sender for message in messages)
    lengths = [len(message.text) for message in messages]
    ranked = [count for _, count in senders.most_common()]
    top = [ranked[i] / n_messages if i < len(ranked) else math.nan for i in range(3)]
    return {
        "msg_n_contacts": float(len(senders)),
        "msg_per_contact": n_messages / len(senders) if senders else math.nan,
        "msg_count": float(n_messages),
        "msg_chars_total": float(sum(lengths)),
        **dict(zip(CHAR_KEYS, r_summary(lengths), strict=True)),
        "msg_top1_share": top[0],
        "msg_top2_share": top[1],
        "msg_top3_share": top[2],
    }
