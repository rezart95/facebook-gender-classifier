"""The scrub check: anonymized tables hold only P-IDs, known category codes and numbers.

Error messages name the table and column, never the offending value.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from fbgc_pipeline.anonymize.age_bands import ALL_AGE_BANDS
from fbgc_pipeline.anonymize.k_anonymity import smallest_cell
from fbgc_pipeline.anonymize.relationship import RELATIONSHIPS

PID_REGEX = r"P\d{3,}"
PARTICIPANT_TEXT = frozenset({"pid", "gender", "age_band", "relationship"})
FEATURE_TEXT = frozenset({"pid", "feature_key"})
VOCABULARIES: dict[str, frozenset[str]] = {
    "gender": frozenset({"M", "F"}),
    "age_band": ALL_AGE_BANDS,
    "relationship": frozenset(RELATIONSHIPS),
}


class AnonymizationError(ValueError):
    """An anonymized table failed the scrub check."""


def text_columns(frame: pd.DataFrame) -> set[str]:
    return {
        str(column)
        for column in frame.columns
        if not (is_numeric_dtype(frame[column]) or is_bool_dtype(frame[column]))
    }


def scrub_check(
    participants: pd.DataFrame,
    features_long: pd.DataFrame,
    folder_codes: Iterable[str],
    feature_keys: Iterable[str],
    k: int,
) -> None:
    tables = {
        "participants": (participants, PARTICIPANT_TEXT),
        "features": (features_long, FEATURE_TEXT),
    }
    for name, (frame, allowed) in tables.items():
        extra = text_columns(frame) - allowed
        if extra:
            raise AnonymizationError(f"{name} has unexpected text columns: {sorted(extra)}")
        if not frame["pid"].astype(str).str.fullmatch(PID_REGEX).all():
            raise AnonymizationError(f"{name}.pid holds a value that is not a P-ID")
    for column, vocabulary in VOCABULARIES.items():
        if not participants[column].isin(vocabulary).all():
            raise AnonymizationError(f"participants.{column} holds a value outside its codes")
    if not features_long["feature_key"].isin(set(feature_keys)).all():
        raise AnonymizationError("features.feature_key holds an unknown feature key")
    codes = {code.upper() for code in folder_codes}
    for name, (frame, allowed) in tables.items():
        for column in sorted(allowed):
            if frame[column].astype(str).str.upper().isin(codes).any():
                raise AnonymizationError(f"{name}.{column} holds a folder code")
    cell = smallest_cell(
        participants["age_band"].tolist(),
        participants["gender"].tolist(),
        participants["wave"].tolist(),
    )
    if cell < k:
        raise AnonymizationError(f"an (age band, gender, wave) cell has fewer than {k} people")
