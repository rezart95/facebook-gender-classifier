"""Command `fbgc load`: replace the database contents with the private or the synthetic data."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.anonymize.run import ANONYMIZED_DIR
from fbgc_pipeline.cli.common import private_zone, repo_root
from fbgc_pipeline.load.database_load import is_local_database, load_database
from fbgc_pipeline.load.sources import LoadError, private_bundle, synthetic_bundle


def load(
    private: bool = typer.Option(False, "--private", help="Load the anonymized private tables."),
    synthetic: bool = typer.Option(False, "--synthetic", help="Load data/synthetic."),
    database_url: str = typer.Option(..., envvar="DATABASE_URL", help="SQLAlchemy database URL."),
    source: Path | None = typer.Option(None, "--from", help="Override the input folder."),
    traces: Path | None = typer.Option(None, help="Trace folder (default: data/demo)."),
) -> None:
    """Replace catalogue, participants, feature values and demo traces in one transaction."""
    if private == synthetic:
        typer.echo("choose exactly one of --private or --synthetic")
        raise typer.Exit(2)
    if private and not is_local_database(database_url):
        typer.echo("real (pseudonymous) data loads only into a local database before launch")
        raise typer.Exit(1)
    demo = traces if traces is not None else repo_root() / "data" / "demo"
    try:
        if private:
            folder = source if source is not None else private_zone().private_dir / ANONYMIZED_DIR
            bundle = private_bundle(folder, demo)
        else:
            folder = source if source is not None else repo_root() / "data" / "synthetic"
            bundle = synthetic_bundle(folder, demo)
        summary = load_database(database_url, bundle, default_catalogue())
    except LoadError as error:
        typer.echo(str(error))
        raise typer.Exit(1) from None
    typer.echo(json.dumps(summary, indent=2))
