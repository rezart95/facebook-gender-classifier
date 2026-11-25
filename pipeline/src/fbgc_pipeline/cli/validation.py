"""Commands `fbgc golden` and `fbgc calibrate-dictionary` (local only, private inputs)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.cli.common import (
    ensure_outside_repo,
    private_zone,
    repo_root,
    report_path,
    write_report,
)
from fbgc_pipeline.features.faithful.dictionary import load_word_entries
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


def ensure_enough_profiles(count: int) -> None:
    """Refuse to overwrite the dictionary with a calibration made on too few profiles."""
    if count < MIN_PROFILES:
        typer.echo(f"only {count} profiles calibrated (need {MIN_PROFILES}); nothing written")
        raise typer.Exit(1)


def golden(
    features: Path,
    legacy_features: Path,
    legacy_info: Path,
    report: Path | None = None,
) -> None:
    """Compare faithful features with the 2019 table and write an aggregate-only report."""
    ensure_outside_repo(features, legacy_features, legacy_info)
    ours = pd.read_parquet(features)
    comparisons = compare_columns(ours, load_legacy_features(legacy_features), default_catalogue())
    agreement = gender_agreement(ours, load_legacy_gender(legacy_info))
    gaps_path = repo_root() / "docs" / "extraction-golden-gaps.md"
    gaps = gaps_path.read_text(encoding="utf-8") if gaps_path.is_file() else None
    text = render_golden_report(comparisons, features.stem, agreement, gaps)
    write_report(report_path(report, "docs/extraction-golden-report.md"), text)
    typer.echo(text.split("## Worst")[0])


def calibrate_dictionary(
    legacy_features: Path,
    window: WindowPolicy = WindowPolicy.LAST_12_MONTHS,
    workers: int = 4,
    report: Path | None = None,
) -> None:
    """Pick, per rebuilt word, the regex variant that best reproduces the 2019 counts."""
    ensure_outside_repo(legacy_features)
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
