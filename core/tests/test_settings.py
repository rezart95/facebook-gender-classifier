from pathlib import Path

import pytest

from fbgc_core.settings import PrivateZone, PrivateZoneError, find_repo_root


def make_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[tool.uv.workspace]\nmembers = []\n", encoding="utf-8")
    return root


def zone_from_env(monkeypatch: pytest.MonkeyPatch, raw: Path, private: Path) -> PrivateZone:
    monkeypatch.setenv("FBGC_RAW_DIR", str(raw))
    monkeypatch.setenv("FBGC_PRIVATE_DIR", str(private))
    return PrivateZone.from_env()


def test_find_repo_root_walks_up(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "repo")
    nested = repo / "a" / "b"
    nested.mkdir(parents=True)
    assert find_repo_root(nested) == repo.resolve()


def test_find_repo_root_fails_outside_a_workspace(tmp_path: Path) -> None:
    with pytest.raises(PrivateZoneError):
        find_repo_root(tmp_path)


def test_private_paths_outside_the_repo_pass(tmp_path: Path, monkeypatch) -> None:
    repo = make_repo(tmp_path / "repo")
    raw = tmp_path / "raw"
    raw.mkdir()
    zone_from_env(monkeypatch, raw, tmp_path / "private").check(repo)


def test_raw_dir_inside_the_repo_is_rejected(tmp_path: Path, monkeypatch) -> None:
    repo = make_repo(tmp_path / "repo")
    raw = repo / "raw"
    raw.mkdir()
    zone = zone_from_env(monkeypatch, raw, tmp_path / "private")
    with pytest.raises(PrivateZoneError, match="FBGC_RAW_DIR must be outside"):
        zone.check(repo)


def test_private_dir_inside_the_repo_is_rejected(tmp_path: Path, monkeypatch) -> None:
    repo = make_repo(tmp_path / "repo")
    raw = tmp_path / "raw"
    raw.mkdir()
    zone = zone_from_env(monkeypatch, raw, repo / "out")
    with pytest.raises(PrivateZoneError, match="FBGC_PRIVATE_DIR must be outside"):
        zone.check(repo)


def test_missing_raw_dir_is_rejected(tmp_path: Path, monkeypatch) -> None:
    repo = make_repo(tmp_path / "repo")
    zone = zone_from_env(monkeypatch, tmp_path / "nope", tmp_path / "private")
    with pytest.raises(PrivateZoneError, match="does not exist"):
        zone.check(repo)


def test_id_secret_is_required_and_long(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("FBGC_ID_SECRET", raising=False)
    zone = zone_from_env(monkeypatch, tmp_path, tmp_path / "private")
    with pytest.raises(PrivateZoneError, match="FBGC_ID_SECRET is not set"):
        zone.require_id_secret()
    monkeypatch.setenv("FBGC_ID_SECRET", "too-short")
    zone = zone_from_env(monkeypatch, tmp_path, tmp_path / "private")
    with pytest.raises(PrivateZoneError, match="at least 32 characters"):
        zone.require_id_secret()


def test_id_secret_is_returned_but_never_shown(tmp_path: Path, monkeypatch) -> None:
    secret = "s" * 40
    monkeypatch.setenv("FBGC_ID_SECRET", secret)
    zone = zone_from_env(monkeypatch, tmp_path, tmp_path / "private")
    assert zone.require_id_secret() == secret
    assert secret not in repr(zone)
    assert secret not in str(zone.model_dump())
