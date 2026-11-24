"""Collect per-profile word counts for calibration (private zone, optionally in parallel)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

from fbgc_pipeline.features.faithful.assemble import windowed_threads_and_owner
from fbgc_pipeline.features.faithful.dictionary import scoped_texts
from fbgc_pipeline.locate.profile_finder import ProfileLocation, list_profiles
from fbgc_pipeline.parse.index_page import parse_index_page
from fbgc_pipeline.parse.messages_page import parse_messages_page
from fbgc_pipeline.validate.dictionary_calibration import CountKey, profile_word_counts
from fbgc_pipeline.window.observation import WindowPolicy, is_windowed, window_bounds


def collect_word_counts(
    raw_dir: Path,
    codes: set[str],
    entries: Sequence[Mapping[str, str]],
    window: WindowPolicy,
    workers: int,
) -> dict[str, dict[CountKey, int]]:
    locations, _ = list_profiles(raw_dir)
    occurrences = Counter(location.folder_code for location in locations)
    chosen = [
        location
        for location in locations
        if location.folder_code in codes and occurrences[location.folder_code] == 1
    ]
    task = partial(profile_counts, entries=[dict(entry) for entry in entries], window=window)
    if workers <= 1:
        results = [task(location) for location in chosen]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(task, chosen, chunksize=2))
    return {code: counts for code, counts in results if counts is not None}


def profile_counts(
    location: ProfileLocation, entries: list[dict[str, str]], window: WindowPolicy
) -> tuple[str, dict[CountKey, int] | None]:
    """Counts for one export, or None when it cannot be calibrated."""
    try:
        info = parse_index_page(location.root / "index.htm")
        messages = location.root / "html" / "messages.htm"
        if info.language == "other" or not messages.is_file():
            return location.folder_code, None
        if info.downloaded_at is None and is_windowed(window):
            return location.folder_code, None
        bounds = window_bounds(info.downloaded_at, window)
        threads, owner = windowed_threads_and_owner(parse_messages_page(messages), bounds)
        if owner is None:
            return location.folder_code, None
        return location.folder_code, profile_word_counts(scoped_texts(threads, owner), entries)
    except Exception:  # a broken export is skipped; the extraction report already lists it
        return location.folder_code, None
