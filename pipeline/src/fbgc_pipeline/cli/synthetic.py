"""Command `fbgc synth-data`: private anonymized tables in, public synthetic dataset out."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.anonymize.run import ANONYMIZED_DIR
from fbgc_pipeline.cli.common import ensure_outside_repo, private_zone, repo_root
from fbgc_pipeline.synthetic.privacy_check import SyntheticPrivacyError
from fbgc_pipeline.synthetic.synthetic_dataset import (
    DEFAULT_SEED,
    build_synthetic,
    read_anonymized,
    write_synthetic,
)


def synth_data(
    source: Path | None = typer.Option(None, "--from", help="Anonymized tables folder."),
    out: Path | None = typer.Option(None, help="Output folder (default: data/synthetic)."),
    seed: int = DEFAULT_SEED,
    shrinkage: float = typer.Option(0.0, help="Blend correlations toward 0 (0 to 1)."),
) -> None:
    """Fit a synthetic dataset on aggregates of the anonymized data; write it if it passes."""
    zone = private_zone()
    folder = source if source is not None else zone.private_dir / ANONYMIZED_DIR
    ensure_outside_repo(folder)
    participants, long = read_anonymized(folder)
    try:
        dataset = build_synthetic(participants, long, default_catalogue(), seed, shrinkage)
    except SyntheticPrivacyError as error:
        typer.echo(str(error))
        raise typer.Exit(1) from None
    sizes = write_synthetic(dataset, out if out is not None else repo_root() / "data" / "synthetic")
    summary = {
        "rows": len(dataset.participants),
        "features": dataset.features.shape[1] - 1,
        "shrinkage": shrinkage,
        "distance_p5_synthetic_to_real": round(dataset.check.synthetic_p5, 4),
        "distance_p5_real_to_real": round(dataset.check.real_p5, 4),
        "bytes": sizes,
    }
    typer.echo(json.dumps(summary, indent=2))
