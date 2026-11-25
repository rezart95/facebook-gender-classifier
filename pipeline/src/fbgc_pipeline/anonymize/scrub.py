"""The scrub check: anonymized tables hold only P-IDs, known category codes and numbers.

It is independent of the code that builds the tables and fails closed: the columns, dtypes and
vocabularies are fixed here. Error messages name the table and column, never the offending value.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_float_dtype, is_integer_dtype, is_string_dtype

from fbgc_pipeline.anonymize.age_bands import ALL_AGE_BANDS
from fbgc_pipeline.anonymize.columns import (
    FEATURE_COLUMNS,
    PARTICIPANT_COLUMNS,
    published_feature_keys,
)
from fbgc_pipeline.anonymize.k_anonymity import smallest_cell
from fbgc_pipeline.anonymize.relationship import RELATIONSHIPS

PID_REGEX = r"P\d{3,}"
PARTICIPANT_TEXT = ("pid", "gender", "age_band", "relationship")
FEATURE_TEXT = ("pid", "feature_key")
WAVES = frozenset({1, 2})
VOCABULARIES: dict[str, frozenset[object]] = {
    "gender": frozenset({"M", "F"}),
    "age_band": ALL_AGE_BANDS,
    "relationship": frozenset(RELATIONSHIPS),
}


class AnonymizationError(ValueError):
    """An anonymized table failed the scrub check."""


def text_columns(frame: pd.DataFrame) -> set[str]:
    return {str(column) for column in frame.columns if is_string_dtype(frame[column])}


def check_columns(name: str, frame: pd.DataFrame, expected: tuple[str, ...]) -> None:
    columns = [str(column) for column in frame.columns]
    extra = sorted(set(columns) - set(expected))
    if extra:
        raise AnonymizationError(f"{name} has unexpected columns: {extra}")
    missing = sorted(set(expected) - set(columns))
    if missing:
        raise AnonymizationError(f"{name} is missing columns: {missing}")
    if columns != list(expected):
        raise AnonymizationError(f"{name} columns are out of order")


def check_dtypes(participants: pd.DataFrame, features_long: pd.DataFrame) -> None:
    for name, frame, text in (
        ("participants", participants, PARTICIPANT_TEXT),
        ("features", features_long, FEATURE_TEXT),
    ):
        for column in text:
            if not is_string_dtype(frame[column]):
                raise AnonymizationError(f"{name}.{column} is not text")
    wave = participants["wave"]
    if is_bool_dtype(wave) or not is_integer_dtype(wave):
        raise AnonymizationError("participants.wave is not an integer")
    for column in ("has_messages", "has_survey"):
        if not is_bool_dtype(participants[column]):
            raise AnonymizationError(f"participants.{column} is not boolean")
    value = features_long["value"]
    if not is_float_dtype(value) or not np.isfinite(value.to_numpy(dtype="float64")).all():
        raise AnonymizationError("features.value is not a number without gaps")


def check_codes(participants: pd.DataFrame, features_long: pd.DataFrame) -> None:
    for name, frame in (("participants", participants), ("features", features_long)):
        if not frame["pid"].str.fullmatch(PID_REGEX).all():
            raise AnonymizationError(f"{name}.pid holds a value that is not a P-ID")
    if not participants["wave"].isin(WAVES).all():
        raise AnonymizationError("participants.wave holds a value outside its codes")
    for column, vocabulary in VOCABULARIES.items():
        if not participants[column].isin(vocabulary).all():
            raise AnonymizationError(f"participants.{column} holds a value outside its codes")
    if not features_long["feature_key"].isin(published_feature_keys()).all():
        raise AnonymizationError("features.feature_key holds an unknown feature key")


def scrub_check(
    participants: pd.DataFrame, features_long: pd.DataFrame, folder_codes: Iterable[str], k: int
) -> None:
    check_columns("participants", participants, PARTICIPANT_COLUMNS)
    check_columns("features", features_long, FEATURE_COLUMNS)
    check_dtypes(participants, features_long)
    check_codes(participants, features_long)
    codes = {code.upper() for code in folder_codes}
    for name, frame, text in (
        ("participants", participants, PARTICIPANT_TEXT),
        ("features", features_long, FEATURE_TEXT),
    ):
        for column in text:
            if frame[column].str.upper().isin(codes).any():
                raise AnonymizationError(f"{name}.{column} holds a folder code")
    cell = smallest_cell(
        participants["age_band"].tolist(),
        participants["gender"].tolist(),
        participants["wave"].tolist(),
        participants["relationship"].tolist(),
    )
    if cell < k:
        raise AnonymizationError(
            f"an (age band, gender, wave, relationship) cell has fewer than {k} people"
        )
