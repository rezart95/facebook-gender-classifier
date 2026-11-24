"""Survey scale scores from the 2019 scale file (private zone), joined to exports by folder code.

The file (datiScale_w1w2.Rdata) is Latin-1 encoded. Only the catalogue's survey columns are
read: the z* demographic columns never are. Codes that appear twice get averaged scores, as
in the 2019 analysis.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadr

from fbgc_core.catalogue_model import Catalogue
from fbgc_pipeline.validate.legacy_table import LEGACY_CODE_COLUMN, normalise_codes


class SurveyColumnsError(ValueError):
    """The scale file lacks columns that the catalogue expects."""


def survey_columns(catalogue: Catalogue) -> dict[str, str]:
    """2019 scale column -> catalogue key, for every survey feature."""
    return {
        spec.legacy_name: spec.key
        for spec in catalogue.features
        if spec.origin == "survey" and spec.legacy_name
    }


def read_scale_file(path: Path) -> pd.DataFrame:
    return next(iter(pyreadr.read_r(str(path), encoding="latin1").values()))


def survey_scores(frame: pd.DataFrame, catalogue: Catalogue) -> pd.DataFrame:
    """One float column per survey key, indexed by normalised folder code (duplicates averaged)."""
    columns = survey_columns(catalogue)
    missing = sorted(set(columns) - {str(column) for column in frame.columns})
    if missing:
        present = sorted(
            str(c)
            for c in frame.columns
            if str(c) != LEGACY_CODE_COLUMN and not str(c).startswith("z")
        )
        raise SurveyColumnsError(f"scale columns not found: {missing}; present: {present}")
    scores = frame[list(columns)].apply(pd.to_numeric, errors="coerce").astype("float64")
    scores = scores.rename(columns=columns)
    scores.index = pd.Index(normalise_codes(frame[LEGACY_CODE_COLUMN]), name="folder_code")
    return scores.groupby(level="folder_code", sort=True).mean()


def load_survey_scores(path: Path, catalogue: Catalogue) -> pd.DataFrame:
    return survey_scores(read_scale_file(path), catalogue)


def join_survey(profiles: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    """Profile rows plus the survey columns and `has_survey` (a left join on folder code)."""
    matched = scores.reindex(normalise_codes(profiles["folder_code"]).to_numpy())
    matched.index = profiles.index
    joined = pd.concat([profiles, matched], axis=1)
    joined["has_survey"] = matched.notna().any(axis=1)
    return joined
