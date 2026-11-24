"""End-to-end tests of `fbgc golden` and `fbgc calibrate-dictionary` on fake R data."""

from pathlib import Path

import pandas as pd
import pyreadr
import pytest
from typer.testing import CliRunner

from fbgc_pipeline.cli import app
from fbgc_pipeline.cli.common import repo_root
from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.extract.run import run_extraction
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import sample_profile


def write_rdata(path: Path, columns: dict[str, list[object]]) -> Path:
    pyreadr.write_rdata(str(path), pd.DataFrame(columns), df_name="dati")
    return path


def test_golden_end_to_end(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    write_fake_export(raw / "wave1" / "alpha", sample_profile())
    run_extraction(raw, tmp_path / "extract", FaithfulOptions(), workers=1)
    features = tmp_path / "extract" / "faithful_12m_correct.parquet"
    legacy = write_rdata(
        tmp_path / "legacy.RData",
        {"CODICE.ZIP": ["alpha.zip"], "msg_nchar_stats.number": [5.0], "msg_n_user": [3.0]},
    )
    info = write_rdata(tmp_path / "info.RData", {"CODICE.ZIP": ["alpha"], "sesso": ["F"]})
    report = tmp_path / "golden.md"
    args = ["golden", str(features), str(legacy), str(info), "--report", str(report)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    text = report.read_text(encoding="utf-8")
    assert "Profiles compared: 1" in text
    assert "Overall exact-match rate (near-exact): 100.0%" in text
    assert "Gender label agreement with 2019: 100.0% of 1 profiles" in text
    assert "alpha" not in text.lower()
    assert "alpha" not in result.output.lower()


def test_golden_refuses_inputs_inside_the_repo(tmp_path: Path) -> None:
    inside = repo_root() / "pyproject.toml"
    args = ["golden", str(inside), str(tmp_path / "a.RData"), str(tmp_path / "b.RData")]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1
    assert "inside the repository" in result.output


def test_calibrate_dictionary_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = tmp_path / "raw"
    write_fake_export(raw / "wave1" / "alpha", sample_profile())
    legacy = write_rdata(
        tmp_path / "legacy.RData", {"CODICE.ZIP": ["alpha"], "user_personal.NonLoSo": [0.0]}
    )
    written: list[object] = []
    monkeypatch.setattr("fbgc_pipeline.cli.validation.MIN_PROFILES", 1)
    monkeypatch.setattr("fbgc_pipeline.cli.validation.write_word_entries", written.extend)
    monkeypatch.setenv("FBGC_RAW_DIR", str(raw))
    monkeypatch.setenv("FBGC_PRIVATE_DIR", str(tmp_path / "private"))
    report = tmp_path / "calibration.md"
    args = ["calibrate-dictionary", str(legacy), "--workers", "1", "--report", str(report)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "calibrated 79 words on 1 profiles" in result.output
    assert len(written) == 79
    assert "Words at or above 95% exact matches" in report.read_text(encoding="utf-8")


def test_calibrate_dictionary_refuses_inputs_inside_the_repo() -> None:
    result = CliRunner().invoke(app, ["calibrate-dictionary", str(repo_root() / "README.md")])
    assert result.exit_code == 1
    assert "inside the repository" in result.output
