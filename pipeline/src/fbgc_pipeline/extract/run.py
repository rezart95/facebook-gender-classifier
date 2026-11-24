"""Run the faithful extraction over every export and write the private outputs.

Outputs are keyed by real folder codes, so they are written only to the private zone.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

import pandas as pd

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.extract.profile_extractor import ProfileResult, extract_profile
from fbgc_pipeline.locate.profile_finder import ProfileLocation, list_profiles

META_COLUMNS = [
    "wave",
    "folder_code",
    "status",
    "language",
    "gender",
    "age_at_download",
    "relationship",
]


def extract_all(
    locations: Sequence[ProfileLocation], options: FaithfulOptions, workers: int
) -> list[ProfileResult]:
    task = partial(extract_profile, options=options)
    if workers <= 1:
        return [task(location) for location in locations]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(task, locations, chunksize=4))


def results_frame(results: Sequence[ProfileResult], feature_keys: list[str]) -> pd.DataFrame:
    rows = [
        {
            "wave": r.wave,
            "folder_code": r.folder_code,
            "status": r.status,
            "language": r.language,
            "gender": r.gender,
            "age_at_download": r.age_at_download,
            "relationship": r.relationship,
            **{key: r.features.get(key, math.nan) for key in feature_keys},
        }
        for r in results
    ]
    frame = pd.DataFrame(rows, columns=[*META_COLUMNS, *feature_keys])
    return frame.astype(dict.fromkeys(["age_at_download", *feature_keys], "float64"))


def summarise_results(
    results: Sequence[ProfileResult], missing: Sequence[tuple[int, str]], options: FaithfulOptions
) -> dict[str, object]:
    """Aggregate counts only, safe to print."""
    return {
        "options": options.label,
        "profiles": len(results),
        "missing_index": len(missing),
        "by_status": dict(Counter(r.status for r in results)),
        "by_language": dict(Counter(str(r.language) for r in results)),
        "reasons": dict(Counter(r.reason.split(":")[0] for r in results if r.reason)),
    }


def run_extraction(
    raw_dir: Path, out_dir: Path, options: FaithfulOptions, workers: int
) -> dict[str, object]:
    locations, missing = list_profiles(raw_dir)
    results = extract_all(locations, options, workers)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame = results_frame(results, default_catalogue().keys(origin="2019"))
    frame.to_parquet(out_dir / f"faithful_{options.label}.parquet", index=False)
    summary = summarise_results(results, missing, options)
    statuses = [
        {"wave": r.wave, "folder_code": r.folder_code, "status": r.status, "reason": r.reason}
        for r in results
    ]
    report = json.dumps({"summary": summary, "profiles": statuses}, indent=2)
    (out_dir / f"faithful_{options.label}_report.json").write_text(
        report, encoding="utf-8", newline="\n"
    )
    return summary
