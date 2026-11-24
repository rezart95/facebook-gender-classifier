from pathlib import Path

import pytest
from typer.testing import CliRunner

from fbgc_pipeline.cli import app, repo_root, report_path
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import sample_profile


def test_repo_root_comes_from_the_package_location() -> None:
    assert (repo_root() / "pyproject.toml").is_file()
    assert (repo_root() / "pipeline" / "src" / "fbgc_pipeline").is_dir()


def test_default_report_paths_resolve_against_the_repo_root() -> None:
    assert report_path(None, "docs/x.md") == repo_root() / "docs" / "x.md"
    assert report_path(Path("custom.md"), "docs/x.md") == Path("custom.md")


def test_commands_work_from_any_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = tmp_path / "raw"
    write_fake_export(raw / "wave1" / "alpha.zip", sample_profile())
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("FBGC_RAW_DIR", str(raw))
    monkeypatch.setenv("FBGC_PRIVATE_DIR", str(tmp_path / "private"))
    result = CliRunner().invoke(app, ["inventory"])
    assert result.exit_code == 0, result.output


def test_private_dir_inside_the_repo_is_refused_from_any_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FBGC_RAW_DIR", str(tmp_path))
    monkeypatch.setenv("FBGC_PRIVATE_DIR", str(repo_root() / "private-must-not-exist"))
    result = CliRunner().invoke(app, ["inventory"])
    assert result.exit_code != 0
    assert not (repo_root() / "private-must-not-exist").exists()
