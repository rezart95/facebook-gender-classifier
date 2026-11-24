"""Command line for the private extraction pipeline (`uv run fbgc --help`)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import typer

from fbgc_core.catalogue import default_catalogue
from fbgc_core.settings import PrivateZone, find_repo_root
from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.extract.run import run_extraction
from fbgc_pipeline.features.faithful.dictionary import load_word_entries
from fbgc_pipeline.features.faithful.rhythms import WeekdayLabels
from fbgc_pipeline.locate.inventory import inventory_row, summarise_inventory
from fbgc_pipeline.locate.profile_finder import list_profiles
from fbgc_pipeline.validate.calibration_run import collect_word_counts
from fbgc_pipeline.validate.dictionary_calibration import (
    choose_variants,
    render_calibration_report,
    write_word_entries,
)
from fbgc_pipeline.validate.golden_compare import compare_columns, gender_agreement
from fbgc_pipeline.validate.golden_report import render_golden_report
from fbgc_pipeline.validate.legacy_table import load_legacy_features, load_legacy_gender
from fbgc_pipeline.window.observation import WindowPolicy

MIN_PROFILES = 50

app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)


@app.callback()
def main() -> None:
    """Extraction pipeline for facebook-gender-classifier. Runs only on the private zone."""


def repo_root() -> Path:
    return find_repo_root(Path(__file__))


def report_path(given: Path | None, default: str) -> Path:
    return given if given is not None else repo_root() / default


def write_report(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def private_zone() -> PrivateZone:
    zone = PrivateZone.from_env()
    zone.check(repo_root())
    zone.private_dir.mkdir(parents=True, exist_ok=True)
    return zone


def ensure_enough_profiles(count: int) -> None:
    """Refuse to overwrite the dictionary with a calibration made on too few profiles."""
    if count < MIN_PROFILES:
        typer.echo(f"only {count} profiles calibrated (need {MIN_PROFILES}); nothing written")
        raise typer.Exit(1)


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
    window: WindowPolicy = WindowPolicy.LAST_12_MONTHS,
    weekday_labels: WeekdayLabels = WeekdayLabels.CORRECT,
    workers: int = 4,
) -> None:
    """Compute the faithful features of every export (Parquet + report in the private zone)."""
    zone = private_zone()
    options = FaithfulOptions(window, weekday_labels)
    summary = run_extraction(zone.raw_dir, zone.private_dir / "extract", options, workers)
    typer.echo(json.dumps(summary, indent=2))


@app.command()
def golden(
    features: Path,
    legacy_features: Path,
    legacy_info: Path,
    report: Path | None = None,
) -> None:
    """Compare faithful features with the 2019 table and write an aggregate-only report."""
    ours = pd.read_parquet(features)
    comparisons = compare_columns(ours, load_legacy_features(legacy_features), default_catalogue())
    agreement = gender_agreement(ours, load_legacy_gender(legacy_info))
    gaps_path = repo_root() / "docs" / "extraction-golden-gaps.md"
    gaps = gaps_path.read_text(encoding="utf-8") if gaps_path.is_file() else None
    text = render_golden_report(comparisons, features.stem, agreement, gaps)
    write_report(report_path(report, "docs/extraction-golden-report.md"), text)
    typer.echo(text.split("## Worst")[0])


@app.command("calibrate-dictionary")
def calibrate_dictionary(
    legacy_features: Path,
    window: WindowPolicy = WindowPolicy.LAST_12_MONTHS,
    workers: int = 4,
    report: Path | None = None,
) -> None:
    """Pick, per rebuilt word, the regex variant that best reproduces the 2019 counts."""
    zone = private_zone()
    legacy = load_legacy_features(legacy_features)
    entries = load_word_entries()
    per_profile = collect_word_counts(zone.raw_dir, set(legacy.index), entries, window, workers)
    ensure_enough_profiles(len(per_profile))
    choices = choose_variants(per_profile, legacy, entries)
    write_word_entries(choices)
    text = render_calibration_report(choices, len(per_profile))
    write_report(report_path(report, "docs/extraction-dictionary-calibration.md"), text)
    typer.echo(f"calibrated {len(choices)} words on {len(per_profile)} profiles")
