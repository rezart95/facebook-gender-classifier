"""Command `fbgc anonymize` (private zone only)."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from fbgc_core.settings import PrivateZoneError
from fbgc_pipeline.anonymize.run import ANONYMIZED_DIR, run_anonymization
from fbgc_pipeline.cli.common import ensure_outside_repo, private_zone
from fbgc_pipeline.extract.options import FaithfulOptions


def anonymize(
    survey: Path = typer.Option(..., help="The 2019 scale file (datiScale_w1w2.Rdata)."),
    features: Path | None = typer.Option(None, help="Extraction Parquet (default: the latest)."),
) -> None:
    """Write pseudonymous participants and feature values to the private zone; print aggregates."""
    zone = private_zone()
    try:
        secret = zone.require_id_secret()
    except PrivateZoneError as error:
        typer.echo(str(error))
        raise typer.Exit(1) from None
    default = zone.private_dir / "extract" / f"faithful_{FaithfulOptions().label}.parquet"
    source = features if features is not None else default
    ensure_outside_repo(source, survey)
    summary = run_anonymization(source, survey, zone.private_dir / ANONYMIZED_DIR, secret)
    typer.echo(json.dumps(summary, indent=2))
