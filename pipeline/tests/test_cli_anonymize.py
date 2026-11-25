"""End to end: fake exports -> extraction -> `fbgc anonymize` with a fake scale file."""

import json
from pathlib import Path

import pandas as pd
import pyreadr
import pytest
from typer.testing import CliRunner

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.cli import app
from fbgc_pipeline.cli.common import repo_root
from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.extract.run import run_extraction
from fbgc_pipeline.survey.scales import survey_columns
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import sample_profile

SECRET = "x" * 40


def private_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Ten fake exports (five women, five men, all aged 20), extracted, plus a scale file."""
    raw = tmp_path / "raw"
    for index in range(10):
        label = "Donna" if index < 5 else "Uomo"
        write_fake_export(raw / "wave1" / f"person-{index}", sample_profile(gender_label=label))
    private = tmp_path / "private"
    run_extraction(raw, private / "extract", FaithfulOptions(), workers=1)
    scales = {legacy: [2.0, 3.0] for legacy in survey_columns(default_catalogue())}
    frame = pd.DataFrame({"CODICE.ZIP": ["person-0.zip", "person-1"], **scales})
    pyreadr.write_rdata(str(tmp_path / "scales.Rdata"), frame, df_name="dati")
    monkeypatch.setenv("FBGC_RAW_DIR", str(raw))
    monkeypatch.setenv("FBGC_PRIVATE_DIR", str(private))
    monkeypatch.setenv("FBGC_ID_SECRET", SECRET)
    return private


def test_anonymize_writes_private_tables_and_prints_aggregates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private = private_setup(tmp_path, monkeypatch)
    result = CliRunner().invoke(app, ["anonymize", "--survey", str(tmp_path / "scales.Rdata")])
    assert result.exit_code == 0, result.output
    summary = json.loads(result.output)
    assert (summary["participants"], summary["age_level"]) == (10, 0)
    assert summary["relationship_level"] == 0
    assert summary["relationship"] == {"single": 10}
    people = pd.read_parquet(private / "anonymized" / "participants.parquet")
    assert int(people["has_survey"].sum()) == 2
    values = pd.read_parquet(private / "anonymized" / "features_long.parquet")
    assert {"msg_count", "gpius_total"} <= set(values["feature_key"])
    assert "person" not in result.output.lower()
    assert SECRET not in result.output
    assert not {"pid", "folder_code"} & set(summary)


def test_anonymize_needs_the_id_secret(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    private = private_setup(tmp_path, monkeypatch)
    monkeypatch.delenv("FBGC_ID_SECRET")
    result = CliRunner().invoke(app, ["anonymize", "--survey", str(tmp_path / "scales.Rdata")])
    assert result.exit_code == 1
    assert "FBGC_ID_SECRET is not set" in result.output
    assert not (private / "anonymized").exists()


def test_anonymize_refuses_a_scale_file_inside_the_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private_setup(tmp_path, monkeypatch)
    result = CliRunner().invoke(app, ["anonymize", "--survey", str(repo_root() / "README.md")])
    assert result.exit_code == 1
    assert "inside the repository" in result.output
