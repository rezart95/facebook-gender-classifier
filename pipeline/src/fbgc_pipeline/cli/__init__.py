"""Command line for the pipeline (`uv run fbgc --help`). One module per command group."""

from __future__ import annotations

from fbgc_pipeline.cli.anonymization import anonymize
from fbgc_pipeline.cli.app import app
from fbgc_pipeline.cli.database import load
from fbgc_pipeline.cli.demo import fake_profiles, trace
from fbgc_pipeline.cli.extraction import extract, inventory
from fbgc_pipeline.cli.synthetic import synth_data
from fbgc_pipeline.cli.validation import calibrate_dictionary, golden

app.command()(inventory)
app.command()(extract)
app.command()(golden)
app.command("calibrate-dictionary")(calibrate_dictionary)
app.command()(anonymize)
app.command("synth-data")(synth_data)
app.command("fake-profiles")(fake_profiles)
app.command()(trace)
app.command()(load)

__all__ = ["app"]
