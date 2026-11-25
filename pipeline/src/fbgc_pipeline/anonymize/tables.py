"""Turn extracted profiles (private, keyed by folder code) into the two anonymized tables.

- Only extracted rows with a gender label are kept.
- P-IDs come from the secret; ages become bands at the finest k-anonymous level.
- Relationship categories have rare ones merged; friend counts are rounded to the nearest 10.
- No dates are carried over at all. The scrub check runs before anything is returned.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd

from fbgc_pipeline.anonymize.age_bands import age_band
from fbgc_pipeline.anonymize.k_anonymity import K_MIN, choose_age_level, smallest_cell
from fbgc_pipeline.anonymize.pseudonyms import pid_key, pseudonymous_ids
from fbgc_pipeline.anonymize.relationship import suppress_rare
from fbgc_pipeline.anonymize.scrub import scrub_check

ROUNDED_TO_TEN = (
    "friends_accepted",
    "friends_requests_sent",
    "friends_requests_received",
    "friends_removed",
)
PARTICIPANT_COLUMNS = (
    "pid",
    "wave",
    "gender",
    "age_band",
    "relationship",
    "has_messages",
    "has_survey",
)


@dataclass(frozen=True)
class AnonymizedData:
    participants: pd.DataFrame
    features_long: pd.DataFrame
    summary: dict[str, object]


def round_to_ten(values: pd.DataFrame) -> pd.DataFrame:
    """Nearest multiple of 10, halves rounded up (125 -> 130)."""
    return cast("pd.DataFrame", np.floor(values / 10 + 0.5) * 10)


def counts(values: pd.Series) -> dict[str, int]:
    return {str(key): int(n) for key, n in values.value_counts().sort_index().items()}


def column_or(frame: pd.DataFrame, column: str, default: object) -> pd.Series:
    return frame[column] if column in frame.columns else pd.Series(default, index=frame.index)


def participant_table(usable: pd.DataFrame, pids: list[str], k: int) -> tuple[pd.DataFrame, int]:
    ages = pd.to_numeric(usable["age_at_download"], errors="coerce").tolist()
    genders = usable["gender"].astype(str).tolist()
    waves = usable["wave"].astype(int).tolist()
    level = choose_age_level(ages, genders, waves, k)
    relationships = usable["relationship"].fillna("unknown").astype(str).tolist()
    table = pd.DataFrame(
        {
            "pid": pids,
            "wave": waves,
            "gender": genders,
            "age_band": [age_band(age, level) for age in ages],
            "relationship": suppress_rare(relationships, k),
            "has_messages": (column_or(usable, "msg_count", 0.0).fillna(0) > 0).to_numpy(),
            "has_survey": column_or(usable, "has_survey", False).astype(bool).to_numpy(),
        }
    )
    return table, level


def feature_table(usable: pd.DataFrame, pids: list[str], keys: Sequence[str]) -> pd.DataFrame:
    present = [key for key in keys if key in usable.columns]
    values = usable[present].astype("float64")
    rounded = [key for key in ROUNDED_TO_TEN if key in present]
    values[rounded] = round_to_ten(values[rounded])
    values.insert(0, "pid", pids)
    long = values.melt(id_vars="pid", var_name="feature_key", value_name="value")
    long = long.dropna(subset=["value"]).sort_values(["pid", "feature_key"])
    return long.reset_index(drop=True)


def anonymize_profiles(
    profiles: pd.DataFrame, feature_keys: Sequence[str], secret: str, k: int = K_MIN
) -> AnonymizedData:
    extracted = profiles[profiles["status"] == "ok"]
    usable = extracted[extracted["gender"].notna()].reset_index(drop=True)
    keys = [pid_key(w, c) for w, c in zip(usable["wave"], usable["folder_code"], strict=True)]
    pids = pseudonymous_ids(keys, secret)
    participants, level = participant_table(usable, pids, k)
    participants = participants.sort_values("pid").reset_index(drop=True)
    features = feature_table(usable, pids, feature_keys)
    seen_codes = profiles["folder_code"].astype(str).tolist()
    scrub_check(participants, features, seen_codes, feature_keys, k)
    summary: dict[str, object] = {
        "participants": len(participants),
        "dropped_without_gender": len(extracted) - len(usable),
        "age_level": level,
        "age_bands": counts(participants["age_band"]),
        "relationship": counts(participants["relationship"]),
        "smallest_cell": smallest_cell(
            participants["age_band"].tolist(),
            participants["gender"].tolist(),
            participants["wave"].tolist(),
        ),
        "features": int(features["feature_key"].nunique()),
        "values": len(features),
    }
    return AnonymizedData(participants, features, summary)
