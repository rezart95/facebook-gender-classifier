from pathlib import Path

import pytest
from typer.testing import CliRunner

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.cli import app
from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.extract.run import extract_all, results_frame
from fbgc_pipeline.locate.profile_finder import ProfileLocation
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import sample_profile
from fbgc_pipeline.validate.calibration_run import profile_counts
from fbgc_pipeline.window.observation import WindowPolicy

ENTRIES = [{"term": "NonLoSo", "phrase": "non lo so", "variant": "substring"}]


def test_two_workers_give_the_same_rows_as_one(tmp_path: Path) -> None:
    alpha = write_fake_export(tmp_path / "alpha", sample_profile())
    beta = write_fake_export(tmp_path / "beta", sample_profile(style="en_uk", gender_label="Male"))
    locations = [ProfileLocation(1, "ALPHA", alpha), ProfileLocation(2, "BETA", beta)]
    options = FaithfulOptions(WindowPolicy.ALL)
    keys = default_catalogue().keys(origin="2019")
    serial = results_frame(extract_all(locations, options, workers=1), keys)
    parallel = results_frame(extract_all(locations, options, workers=2), keys)
    assert list(parallel["status"]) == list(serial["status"]) == ["ok", "ok"]
    assert parallel.equals(serial)


def test_profile_counts_for_an_italian_export_and_one_without_messages(tmp_path: Path) -> None:
    italian = write_fake_export(tmp_path / "alpha", sample_profile())
    code, counts = profile_counts(ProfileLocation(1, "ALPHA", italian), ENTRIES, WindowPolicy.ALL)
    assert code == "ALPHA"
    assert counts is not None
    assert ("NonLoSo", "substring", "owner_personal") in counts
    silent = write_fake_export(tmp_path / "beta", sample_profile())
    (silent / "html" / "messages.htm").unlink()
    assert profile_counts(ProfileLocation(1, "BETA", silent), ENTRIES, WindowPolicy.ALL) == (
        "BETA",
        None,
    )


def test_extract_cli_output_has_no_folder_codes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = tmp_path / "raw"
    write_fake_export(raw / "wave1" / "alpha.zip", sample_profile())
    write_fake_export(raw / "wave2" / "beta", sample_profile(style="en_uk"))
    monkeypatch.setenv("FBGC_RAW_DIR", str(raw))
    monkeypatch.setenv("FBGC_PRIVATE_DIR", str(tmp_path / "private"))
    result = CliRunner().invoke(app, ["extract", "--window", "all", "--workers", "1"])
    assert result.exit_code == 0, result.output
    lowered = result.output.lower()
    assert "alpha" not in lowered
    assert "beta" not in lowered
