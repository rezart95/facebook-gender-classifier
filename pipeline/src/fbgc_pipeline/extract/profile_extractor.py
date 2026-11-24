"""Turn one located export into a row of faithful (2019) features."""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from typing import Literal

from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.features.faithful.assemble import faithful_features
from fbgc_pipeline.locate.profile_finder import ProfileLocation
from fbgc_pipeline.parse.export_pages import ExportPages
from fbgc_pipeline.parse.index_page import parse_index_page
from fbgc_pipeline.window.observation import is_windowed, window_bounds

Status = Literal["ok", "excluded", "failed"]


@dataclass(frozen=True)
class ProfileResult:
    wave: int
    folder_code: str
    status: Status
    language: str | None = None
    gender: str | None = None
    reason: str | None = None
    features: dict[str, float] = field(default_factory=dict)


def failure_reason(error: BaseException) -> str:
    """Exception type and innermost fbgc_pipeline frame; never the message (it can carry text)."""
    where = ""
    for frame, line in traceback.walk_tb(error.__traceback__):
        module = str(frame.f_globals.get("__name__", ""))
        if module.startswith("fbgc_pipeline"):
            where = f" at {module}:{line}"
    return f"{type(error).__name__}{where}"


def extract_profile(location: ProfileLocation, options: FaithfulOptions) -> ProfileResult:
    """Never raises: a broken export becomes a 'failed' row with the error type and place."""
    wave, code = location.wave, location.folder_code
    try:
        info = parse_index_page(location.root / "index.htm")
        if info.language == "other":
            return ProfileResult(
                wave, code, "excluded", info.language, info.gender, "unsupported UI language"
            )
        if info.downloaded_at is None and is_windowed(options.window):
            return ProfileResult(
                wave, code, "excluded", info.language, info.gender, "no download date"
            )
        bounds = window_bounds(info.downloaded_at, options.window)
        features = faithful_features(
            ExportPages.read(location.root), bounds, options.weekday_labels
        )
        return ProfileResult(wave, code, "ok", info.language, info.gender, None, features)
    except Exception as error:  # one broken export must not stop the run
        return ProfileResult(wave, code, "failed", reason=failure_reason(error))
