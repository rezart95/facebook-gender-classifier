"""Turn extracted profiles (private, keyed by folder code) into the two anonymized tables.

- Only extracted rows with a gender label are kept.
- P-IDs come from the secret; ages and relationships are generalised to the finest levels at
  which every (age band, gender, wave, relationship) cell has k people.
- Rare relationship categories are merged first; friend counts are rounded to the nearest 10.
- No dates are carried over at all. The scrub check runs before anything is returned.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd

from fbgc_pipeline.anonymize.age_bands import age_band
from fbgc_pipeline.anonymize.columns import (
    PARTICIPANT_COLUMNS,
    PRIVATE_INPUT_COLUMNS,
    published_feature_keys,
)
from fbgc_pipeline.anonymize.k_anonymity import (
    K_MIN,
    choose_levels,
    require_minimum_k,
    smallest_cell,
)
from fbgc_pipeline.anonymize.pseudonyms import pid_key, pseudonymous_ids
from fbgc_pipeline.anonymize.relationship import generalize_relationship, suppress_rare
from fbgc_pipeline.anonymize.scrub import scrub_check

ROUNDED_TO_TEN = (
    "friends_accepted",
    "friends_requests_sent",
    "friends_requests_received",
    "friends_removed",
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


def survey_flags(frame: pd.DataFrame) -> np.ndarray:
    """Only an explicit True counts: a missing or NA flag fails safe to False."""
    return column_or(frame, "has_survey", False).eq(True).fillna(False).astype(bool).to_numpy()


def check_feature_keys(keys: Sequence[str]) -> None:
    """Refuse keys that are not published features. Only the count is reported, never the keys."""
    allowed = published_feature_keys() - PRIVATE_INPUT_COLUMNS
    bad = [key for key in keys if key not in allowed] + [
        key for key, n in Counter(keys).items() if n > 1 and key in allowed
    ]
    if bad:
        raise ValueError(f"{len(bad)} feature keys are not published features")


def participant_table(
    usable: pd.DataFrame, pids: list[str], k: int
) -> tuple[pd.DataFrame, int, int]:
    ages = pd.to_numeric(usable["age_at_download"], errors="coerce").tolist()
    genders = usable["gender"].astype(str).tolist()
    waves = usable["wave"].astype(int).tolist()
    if "msg_count" not in usable.columns:
        raise ValueError("the msg_count column is missing, so has_messages cannot be derived")
    relationships = suppress_rare(usable["relationship"].fillna("unknown").astype(str).tolist(), k)
    age_level, relationship_level = choose_levels(ages, genders, waves, relationships, k)
    table = pd.DataFrame(
        {
            "pid": pids,
            "wave": waves,
            "gender": genders,
            "age_band": [age_band(age, age_level) for age in ages],
            "relationship": [generalize_relationship(r, relationship_level) for r in relationships],
            "has_messages": (usable["msg_count"].fillna(0) > 0).to_numpy(),
            "has_survey": survey_flags(usable),
        }
    )
    return table[list(PARTICIPANT_COLUMNS)], age_level, relationship_level


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
    require_minimum_k(k)
    check_feature_keys(feature_keys)
    extracted = profiles[profiles["status"] == "ok"]
    usable = extracted[extracted["gender"].notna()].reset_index(drop=True)
    keys = [pid_key(w, c) for w, c in zip(usable["wave"], usable["folder_code"], strict=True)]
    pids = pseudonymous_ids(keys, secret)
    participants, age_level, relationship_level = participant_table(usable, pids, k)
    participants = participants.sort_values("pid").reset_index(drop=True)
    features = feature_table(usable, pids, feature_keys)
    seen_codes = profiles["folder_code"].astype(str).tolist()
    scrub_check(participants, features, seen_codes, k)
    summary: dict[str, object] = {
        "participants": len(participants),
        "dropped_without_gender": len(extracted) - len(usable),
        "age_level": age_level,
        "relationship_level": relationship_level,
        "age_bands": counts(participants["age_band"]),
        "relationship": counts(participants["relationship"]),
        "smallest_cell": smallest_cell(
            participants["age_band"].tolist(),
            participants["gender"].tolist(),
            participants["wave"].tolist(),
            participants["relationship"].tolist(),
        ),
        "features": int(features["feature_key"].nunique()),
        "values": len(features),
    }
    return AnonymizedData(participants, features, summary)
