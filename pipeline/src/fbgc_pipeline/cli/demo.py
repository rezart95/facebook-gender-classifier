"""Commands on fake profiles only: `fbgc fake-profiles` (and `fbgc trace`, added later)."""

from __future__ import annotations

from pathlib import Path

import typer

from fbgc_pipeline.cli.common import repo_root
from fbgc_pipeline.synthetic.fake_profiles import FAKE_SEED, write_fake_profiles

FIXTURES_DIR = "pipeline/tests/fixtures/profiles"


def fake_profiles(n: int = 3, seed: int = FAKE_SEED, out: Path | None = None) -> None:
    """Write n fake 2015-format exports of invented people (test fixtures and demo input)."""
    target = out if out is not None else repo_root() / FIXTURES_DIR
    paths = write_fake_profiles(target, n, seed)
    typer.echo(f"wrote {len(paths)} fake profiles")
