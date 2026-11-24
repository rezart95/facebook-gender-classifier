"""Command line for the pipeline (`uv run fbgc --help`). One module per command group."""

from __future__ import annotations

from fbgc_pipeline.cli.app import app
from fbgc_pipeline.cli.extraction import extract, inventory
from fbgc_pipeline.cli.validation import calibrate_dictionary, golden

app.command()(inventory)
app.command()(extract)
app.command()(golden)
app.command("calibrate-dictionary")(calibrate_dictionary)

__all__ = ["app"]
