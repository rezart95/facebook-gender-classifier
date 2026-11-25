"""Builders for the stages of a demo trace. Each returns a JSON-ready dict (no NaN)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from fbgc_pipeline.anonymize.age_bands import age_at_download
from fbgc_pipeline.anonymize.pseudonyms import pid_key, pseudonymous_ids
from fbgc_pipeline.anonymize.relationship import relationship_category
from fbgc_pipeline.anonymize.tables import check_feature_keys, feature_table, participant_table
from fbgc_pipeline.parse.records import ProfileInfo, Thread

SNIPPET_CHARS = 1200
THREAD_START = '<div class="thread">'
TRACE_FEATURES = (
    "msg_count",
    "msg_n_contacts",
    "msg_chars_mean",
    "msg_contacts_female_share",
    "msg_top1_share",
    "msg_days_active",
    "msg_hour_21",
    "dict_owner_personal_emotegood",
    "dict_owner_personal_emotelove",
    "dict_others_personal_domanda",
    "wall_items_total",
    "friends_accepted",
)
# Fake profiles only. A single anonymized row always gets P001, whatever the secret.
DEMO_SECRET = "fake-profiles-only-demo-secret-0000"
# One fake profile can never form a k >= 5 cell; real tables go through anonymize_profiles.
DEMO_K = 1


def number(value: float) -> float | None:
    return None if math.isnan(value) else value


def raw_html_stage(page: Path) -> dict[str, object]:
    text = page.read_text(encoding="utf-8")
    start = max(text.find(THREAD_START), 0)
    snippet = text[start : start + SNIPPET_CHARS]
    snippet = snippet[: snippet.rfind(">") + 1]  # end on a whole tag
    return {"stage": "raw_html", "page": "html/messages.htm", "snippet": snippet}


def messages_stage(threads: Sequence[Thread], limit: int) -> dict[str, object]:
    flat = [(i, thread, message) for i, thread in enumerate(threads) for message in thread.messages]
    shown = [
        {
            "thread": i,
            "group": thread.is_group,
            "sender": message.sender,
            "sent_at": message.sent_at.isoformat() if message.sent_at else None,
            "text": message.text,
        }
        for i, thread, message in flat[:limit]
    ]
    return {"stage": "parsed_messages", "total": len(flat), "messages": shown}


def owner_stage(threads: Sequence[Thread], owner: str | None) -> dict[str, object]:
    messages = [message for thread in threads for message in thread.messages]
    owned = sum(1 for message in messages if message.sender == owner)
    return {
        "stage": "owner_split",
        "owner": owner,
        "owner_messages": owned,
        "others_messages": len(messages) - owned,
        "group_threads": sum(1 for t in threads if t.is_group and t.messages),
        "personal_threads": sum(1 for t in threads if not t.is_group and t.messages),
    }


def dictionary_stage(features: dict[str, float]) -> dict[str, object]:
    hits = [
        {"feature": key, "count": value}
        for key, value in sorted(features.items())
        if key.startswith("dict_") and not math.isnan(value) and value > 0
    ]
    return {"stage": "dictionary_hits", "hits": hits}


def features_stage(features: dict[str, float]) -> dict[str, object]:
    return {"stage": "features", "values": {key: number(features[key]) for key in TRACE_FEATURES}}


def anonymized_stage(
    info: ProfileInfo, features: dict[str, float], label: str
) -> dict[str, object]:
    """The anonymization steps on one fake row. `anonymize_profiles` itself refuses k < 5."""
    if not info.gender:
        raise ValueError("the fake profile has no gender label")
    row = {
        "wave": 1,
        "folder_code": label,
        "status": "ok",
        "gender": info.gender,
        "age_at_download": age_at_download(info.birth_date, info.downloaded_at),
        "relationship": relationship_category(info.relationship),
        "has_survey": False,
        **features,
    }
    frame = pd.DataFrame([row])
    check_feature_keys(list(features))
    pids = pseudonymous_ids([pid_key(1, label)], DEMO_SECRET)
    participants, _, _ = participant_table(frame, pids, DEMO_K)
    features_long = feature_table(frame, pids, list(features))
    person = {
        str(key): value.item() if hasattr(value, "item") else value
        for key, value in participants.iloc[0].items()
    }
    shown = features_long[features_long["feature_key"].isin(TRACE_FEATURES)]
    values = dict(zip(shown["feature_key"].tolist(), shown["value"].tolist(), strict=True))
    return {"stage": "anonymized", "k": DEMO_K, "participant": person, "features": values}
