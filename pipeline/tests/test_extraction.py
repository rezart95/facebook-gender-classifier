from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.cli import app
from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.extract.profile_extractor import ProfileResult, extract_profile
from fbgc_pipeline.extract.run import results_frame, run_extraction
from fbgc_pipeline.locate.profile_finder import ProfileLocation
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import sample_profile

SPANISH_INDEX = "<html><body><table><tr><th>Sexo</th><td>Mujer</td></tr></table></body></html>"


def test_extract_profile_produces_every_faithful_feature(tmp_path: Path) -> None:
    root = write_fake_export(tmp_path / "alpha", sample_profile())
    result = extract_profile(ProfileLocation(1, "ALPHA", root), FaithfulOptions())
    assert (result.status, result.language, result.gender) == ("ok", "it", "F")
    assert set(result.features) == set(default_catalogue().keys(origin="2019"))
    f = result.features
    assert (f["msg_count"], f["msg_chars_total"], f["msg_chars_mean"]) == (5, 79, 15.8)
    assert f["msg_top1_share"] == 0.6
    assert f["msg_contact_gini"] == pytest.approx(0.84)
    assert (f["msg_hour_09"], f["msg_hour_14"], f["msg_hour_23"]) == (0.4, 0.4, 0.2)
    assert (f["msg_weekday_mon"], f["msg_weekday_tue"], f["msg_weekday_sun"]) == (0.4, 0.4, 0.2)
    assert f["msg_days_active"] == 3
    assert f["dict_owner_personal_emotegood"] == 1
    assert f["dict_others_group_esclamativo"] == 2
    assert f["dict_owner_group_emotedaiii"] == 1
    assert (f["wall_links_by_owner"], f["friends_accepted"], f["events_going"]) == (1, 3, 1)


def test_other_language_exports_are_excluded(tmp_path: Path) -> None:
    root = tmp_path / "gamma"
    root.mkdir()
    (root / "index.htm").write_text(SPANISH_INDEX, encoding="utf-8")
    result = extract_profile(ProfileLocation(2, "GAMMA", root), FaithfulOptions())
    assert (result.status, result.reason) == ("excluded", "unsupported UI language")


def test_broken_export_becomes_a_failed_row(tmp_path: Path) -> None:
    root = tmp_path / "delta"
    root.mkdir()
    (root / "index.htm").write_bytes(b"")
    result = extract_profile(ProfileLocation(2, "DELTA", root), FaithfulOptions())
    assert result.status == "failed"
    assert result.reason


def test_failure_reason_has_type_and_place_but_no_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(path: Path) -> object:
        raise ValueError("secret message text")

    monkeypatch.setattr("fbgc_pipeline.extract.profile_extractor.parse_index_page", explode)
    result = extract_profile(ProfileLocation(2, "DELTA", tmp_path), FaithfulOptions())
    assert result.status == "failed"
    assert result.reason is not None
    assert result.reason.startswith("ValueError at fbgc_pipeline.extract.profile_extractor:")
    assert "secret" not in result.reason


def test_default_options_match_the_2019_data() -> None:
    assert FaithfulOptions().label == "12m_correct"


def test_run_extraction_writes_private_outputs(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    write_fake_export(raw / "wave1" / "alpha.zip", sample_profile())
    write_fake_export(raw / "wave2" / "beta", sample_profile(style="en_uk", gender_label="Male"))
    summary = run_extraction(raw, tmp_path / "out", FaithfulOptions(), workers=1)
    assert summary["by_status"] == {"ok": 2}
    frame = pd.read_parquet(tmp_path / "out" / "faithful_12m_correct.parquet")
    assert list(frame.columns[:5]) == ["wave", "folder_code", "status", "language", "gender"]
    assert frame.shape == (2, 5 + 539)
    assert (tmp_path / "out" / "faithful_12m_correct_report.json").is_file()


def test_cli_extract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = tmp_path / "raw"
    write_fake_export(raw / "wave1" / "alpha.zip", sample_profile())
    monkeypatch.setenv("FBGC_RAW_DIR", str(raw))
    monkeypatch.setenv("FBGC_PRIVATE_DIR", str(tmp_path / "private"))
    result = CliRunner().invoke(app, ["extract", "--window", "all", "--workers", "1"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "private" / "extract" / "faithful_all_correct.parquet").is_file()


def test_feature_columns_are_float64_even_when_every_value_is_whole() -> None:
    whole = [
        ProfileResult(1, "ALPHA", "ok", features={"msg_count": 5}),
        ProfileResult(2, "BETA", "ok", features={"msg_count": 7}),
    ]
    frame = results_frame(whole, ["msg_count", "msg_chars_mean"])
    assert frame["msg_count"].dtype == "float64"
    assert frame["msg_chars_mean"].dtype == "float64"
    assert results_frame([], ["msg_count"])["msg_count"].dtype == "float64"
