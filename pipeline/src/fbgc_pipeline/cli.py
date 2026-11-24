"""Command line for the private extraction pipeline (`uv run fbgc --help`)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import typer

from fbgc_core.settings import PrivateZone, find_repo_root
from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.extract.run import run_extraction
from fbgc_pipeline.features.faithful.rhythms import WeekdayLabels
from fbgc_pipeline.locate.inventory import inventory_row, summarise_inventory
from fbgc_pipeline.locate.profile_finder import list_profiles
from fbgc_pipeline.window.observation import WindowPolicy

app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)


@app.callback()
def main() -> None:
    """Extraction pipeline for facebook-gender-classifier. Runs only on the private zone."""


def private_zone() -> PrivateZone:
    zone = PrivateZone.from_env()
    zone.check(find_repo_root(Path.cwd()))
    zone.private_dir.mkdir(parents=True, exist_ok=True)
    return zone


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8", newline="\n")


@app.command()
def inventory() -> None:
    """Count exports by wave, UI language and page. Per-profile rows go to the private zone."""
    zone = private_zone()
    locations, missing = list_profiles(zone.raw_dir)
    rows = [inventory_row(location) for location in locations]
    write_json(zone.private_dir / "inventory.json", [asdict(row) for row in rows])
    typer.echo(json.dumps(summarise_inventory(rows, missing), indent=2))


@app.command()
def extract(
    window: WindowPolicy = WindowPolicy.LAST_6_MONTHS,
    weekday_labels: WeekdayLabels = WeekdayLabels.CORRECT,
    workers: int = 4,
) -> None:
    """Compute the faithful features of every export (Parquet + report in the private zone)."""
    zone = private_zone()
    options = FaithfulOptions(window, weekday_labels)
    summary = run_extraction(zone.raw_dir, zone.private_dir / "extract", options, workers)
    typer.echo(json.dumps(summary, indent=2))
