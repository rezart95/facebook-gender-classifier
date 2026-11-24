"""Helpers shared by the command modules: repo paths, the private zone and output files."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from fbgc_core.settings import PrivateZone, find_repo_root, is_inside


def repo_root() -> Path:
    return find_repo_root(Path(__file__))


def report_path(given: Path | None, default: str) -> Path:
    return given if given is not None else repo_root() / default


def write_report(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8", newline="\n")


def private_zone() -> PrivateZone:
    zone = PrivateZone.from_env()
    zone.check(repo_root())
    zone.private_dir.mkdir(parents=True, exist_ok=True)
    return zone


def ensure_outside_repo(*paths: Path) -> None:
    """Private inputs (2019 tables, Parquet keyed by folder codes) never sit inside the repo."""
    root = repo_root()
    if any(is_inside(path, root) for path in paths):
        typer.echo("refusing a private input that sits inside the repository")
        raise typer.Exit(1)
