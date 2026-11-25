"""Anonymize on the private zone: extraction Parquet + scale file -> two anonymized Parquet files.

Both outputs stay in the private zone (FBGC_PRIVATE_DIR/anonymized). Only aggregates are
returned for printing.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.anonymize.tables import anonymize_profiles
from fbgc_pipeline.survey.scales import join_survey, load_survey_scores

ANONYMIZED_DIR = "anonymized"


def published_feature_keys() -> list[str]:
    """The 2019 feature keys, then the survey scale keys, in catalogue order."""
    catalogue = default_catalogue()
    return [*catalogue.keys(origin="2019"), *catalogue.keys(origin="survey")]


def run_anonymization(
    features_path: Path, survey_path: Path, out_dir: Path, secret: str
) -> dict[str, object]:
    profiles = pd.read_parquet(features_path)
    joined = join_survey(profiles, load_survey_scores(survey_path, default_catalogue()))
    data = anonymize_profiles(joined, published_feature_keys(), secret)
    out_dir.mkdir(parents=True, exist_ok=True)
    data.participants.to_parquet(out_dir / "participants.parquet", index=False)
    data.features_long.to_parquet(out_dir / "features_long.parquet", index=False)
    return data.summary
