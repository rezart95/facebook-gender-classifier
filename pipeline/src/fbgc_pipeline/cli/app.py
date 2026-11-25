"""The `fbgc` Typer application. Commands are registered in `fbgc_pipeline.cli`."""

from __future__ import annotations

import typer

app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)


@app.callback()
def main() -> None:
    """Pipeline for facebook-gender-classifier. Commands on real data need the private zone."""
