"""Turn one located export into a row of faithful (2019) features."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.features.faithful.assemble import faithful_features
from fbgc_pipeline.locate.profile_finder import ProfileLocation
from fbgc_pipeline.parse.export_pages import ExportPages
from fbgc_pipeline.parse.index_page import parse_index_page
from fbgc_pipeline.window.observation import window_bounds

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


def extract_profile(location: ProfileLocation, options: FaithfulOptions) -> ProfileResult:
    """Never raises: a broken export becomes a 'failed' row with the error type and message."""
    wave, code = location.wave, location.folder_code
    try:
        info = parse_index_page(location.root / "index.htm")
        if info.language == "other":
            return ProfileResult(
                wave, code, "excluded", info.language, info.gender, "unsupported UI language"
            )
        bounds = window_bounds(info.downloaded_at, options.window)
        features = faithful_features(
            ExportPages.read(location.root), bounds, options.weekday_labels
        )
        return ProfileResult(wave, code, "ok", info.language, info.gender, None, features)
    except Exception as error:  # one broken export must not stop the run
        return ProfileResult(wave, code, "failed", reason=f"{type(error).__name__}: {error}"[:300])
