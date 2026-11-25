"""The extraction keeps the age at download and a relationship category, never the raw facts."""

from pathlib import Path

import pandas as pd

from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.extract.profile_extractor import extract_profile
from fbgc_pipeline.extract.run import run_extraction
from fbgc_pipeline.locate.profile_finder import ProfileLocation
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import sample_profile


def test_profile_result_has_age_and_relationship_category(tmp_path: Path) -> None:
    root = write_fake_export(tmp_path / "alpha", sample_profile())  # born 1995-03-12, single
    result = extract_profile(ProfileLocation(1, "ALPHA", root), FaithfulOptions())
    assert (result.age_at_download, result.relationship) == (20, "single")


def test_unknown_birth_date_and_missing_relationship(tmp_path: Path) -> None:
    profile = sample_profile(birthday="", relationship=None)
    root = write_fake_export(tmp_path / "alpha", profile)
    result = extract_profile(ProfileLocation(1, "ALPHA", root), FaithfulOptions())
    assert (result.age_at_download, result.relationship) == (None, "unknown")


def test_partner_names_never_reach_the_parquet(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    write_fake_export(
        raw / "wave1" / "alpha", sample_profile(relationship="Impegnata/o con Ugo Rana")
    )
    run_extraction(raw, tmp_path / "out", FaithfulOptions(), workers=1)
    frame = pd.read_parquet(tmp_path / "out" / "faithful_12m_correct.parquet")
    assert frame.loc[0, "relationship"] == "in_relationship"
    assert frame.loc[0, "age_at_download"] == 20.0
    assert frame["age_at_download"].dtype == "float64"
    assert b"Ugo" not in (tmp_path / "out" / "faithful_12m_correct.parquet").read_bytes()
