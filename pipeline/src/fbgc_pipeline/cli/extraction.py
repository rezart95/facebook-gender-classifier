"""Commands `fbgc inventory` and `fbgc extract` (private zone only)."""

from __future__ import annotations

import json
from dataclasses import asdict

import typer

from fbgc_pipeline.cli.common import private_zone, write_json
from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.extract.run import run_extraction
from fbgc_pipeline.features.faithful.rhythms import WeekdayLabels
from fbgc_pipeline.locate.inventory import inventory_row, summarise_inventory
from fbgc_pipeline.locate.profile_finder import list_profiles
from fbgc_pipeline.window.observation import WindowPolicy


def inventory() -> None:
    """Count exports by wave, UI language and page. Per-profile rows go to the private zone."""
    zone = private_zone()
    locations, missing = list_profiles(zone.raw_dir)
    rows = [inventory_row(location) for location in locations]
    write_json(zone.private_dir / "inventory.json", [asdict(row) for row in rows])
    typer.echo(json.dumps(summarise_inventory(rows, missing), indent=2))


def extract(
    window: WindowPolicy = WindowPolicy.LAST_12_MONTHS,
    weekday_labels: WeekdayLabels = WeekdayLabels.CORRECT,
    workers: int = 4,
) -> None:
    """Compute the faithful features of every export (Parquet + report in the private zone)."""
    zone = private_zone()
    options = FaithfulOptions(window, weekday_labels)
    summary = run_extraction(zone.raw_dir, zone.private_dir / "extract", options, workers)
    typer.echo(json.dumps(summary, indent=2))
