"""Record what each pipeline stage does to one FAKE profile, for the animated demo.

The trace holds an HTML snippet, the first parsed messages, the owner/others split, the
dictionary hits, a subset of the feature row and the anonymized row. Exports without the
fake-profile marker are refused, so a real export can never be traced by mistake.
"""

from __future__ import annotations

from pathlib import Path

from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.features.faithful.assemble import faithful_features, windowed_threads_and_owner
from fbgc_pipeline.parse.export_pages import ExportPages
from fbgc_pipeline.parse.index_page import parse_index_page
from fbgc_pipeline.synthetic.fake_export_html import FAKE_MARKER
from fbgc_pipeline.trace.stages import (
    anonymized_stage,
    dictionary_stage,
    features_stage,
    messages_stage,
    owner_stage,
    raw_html_stage,
)
from fbgc_pipeline.window.observation import window_bounds

TRACE_VERSION = 1


class NotAFakeProfileError(ValueError):
    """Traces are recorded on fake profiles only."""


def is_fake_export(root: Path) -> bool:
    index = root / "index.htm"
    return index.is_file() and FAKE_MARKER in index.read_text(encoding="utf-8", errors="replace")


def record_trace(root: Path, label: str, max_messages: int = 10) -> dict[str, object]:
    if not is_fake_export(root):
        raise NotAFakeProfileError("traces are recorded on fake profiles only")
    options = FaithfulOptions()
    info = parse_index_page(root / "index.htm")
    pages = ExportPages.read(root)
    bounds = window_bounds(info.downloaded_at, options.window)
    threads, owner = windowed_threads_and_owner(pages.threads, bounds)
    features = faithful_features(pages, bounds, options.weekday_labels)
    stages = [
        raw_html_stage(root / "html" / "messages.htm"),
        messages_stage(threads, max_messages),
        owner_stage(threads, owner),
        dictionary_stage(features),
        features_stage(features),
        anonymized_stage(info, features, label),
    ]
    return {"trace_version": TRACE_VERSION, "profile_label": label, "fake": True, "stages": stages}
