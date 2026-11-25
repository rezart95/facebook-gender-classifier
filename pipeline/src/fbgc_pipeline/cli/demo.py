"""Commands on fake profiles only: `fbgc fake-profiles` and `fbgc trace`."""

from __future__ import annotations

from pathlib import Path

import typer

from fbgc_pipeline.cli.common import repo_root, write_json
from fbgc_pipeline.synthetic.fake_profiles import FAKE_SEED, write_fake_profiles
from fbgc_pipeline.trace.recorder import NotAFakeProfileError, record_trace

FIXTURES_DIR = "pipeline/tests/fixtures/profiles"


def fake_profiles(n: int = 3, seed: int = FAKE_SEED, out: Path | None = None) -> None:
    """Write n fake 2015-format exports of invented people (test fixtures and demo input)."""
    target = out if out is not None else repo_root() / FIXTURES_DIR
    paths = write_fake_profiles(target, n, seed)
    typer.echo(f"wrote {len(paths)} fake profiles")


def trace(
    profile: Path = typer.Option(..., help="A fake profile folder (with index.htm)."),
    out: Path = typer.Option(..., help="Where to write the JSON trace."),
    messages: int = 10,
) -> None:
    """Record each pipeline stage on a FAKE profile as JSON, for the animated demo."""
    try:
        payload = record_trace(profile, profile.name, messages)
    except NotAFakeProfileError as error:
        typer.echo(str(error))
        raise typer.Exit(1) from None
    write_json(out, payload)
    typer.echo(f"wrote the trace of {profile.name}")
