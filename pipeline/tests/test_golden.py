import math
from pathlib import Path

import pandas as pd
import pyreadr
import pytest

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.validate.golden_compare import compare_columns, gender_agreement, values_match
from fbgc_pipeline.validate.golden_report import render_golden_report
from fbgc_pipeline.validate.legacy_table import load_legacy_features

CODES = ["pq-alpha", "pq-beta", "pq-gamma"]


def ours_frame(counts: list[int], genders: tuple[str, ...] = ("F", "M", "F")) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "wave": 1,
            "folder_code": CODES,
            "status": "ok",
            "language": "it",
            "gender": list(genders),
            "msg_count": counts,
            "msg_chars_mean": [15.8, 20.0, 30.0],
        }
    )


def legacy_frame(counts: list[int]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "msg_nchar_stats.number": counts,
            "msg_nchar_stats.nchar_per_text.Mean": [15.8, 20.004, 31.0],
        },
        index=pd.Index(CODES, name="folder_code"),
    )


def test_values_match_tolerates_four_significant_digits() -> None:
    assert values_match(15.8, 15.8)
    assert values_match(20.0, 20.004)
    assert not values_match(30.0, 31.0)
    assert values_match(math.nan, math.nan)
    assert not values_match(1.0, math.nan)


def test_compare_columns_reports_exact_rates() -> None:
    found = compare_columns(ours_frame([5, 6, 7]), legacy_frame([5, 6, 8]), default_catalogue())
    by_key = {comparison.key: comparison for comparison in found}
    assert set(by_key) == {"msg_count", "msg_chars_mean"}
    assert by_key["msg_count"].exact_rate == pytest.approx(2 / 3)
    assert by_key["msg_chars_mean"].exact_rate == pytest.approx(2 / 3)
    assert by_key["msg_count"].max_abs_diff == 1


def test_only_ok_and_unique_rows_are_compared() -> None:
    ours = ours_frame([5, 6, 7])
    ours.loc[2, "status"] = "failed"
    found = compare_columns(ours, legacy_frame([5, 6, 8]), default_catalogue())
    counts = next(comparison for comparison in found if comparison.key == "msg_count")
    assert (counts.compared, counts.exact_rate) == (2, 1.0)


def test_gender_agreement() -> None:
    legacy_gender = pd.Series(["F", "F", "F"], index=CODES)
    compared, rate = gender_agreement(ours_frame([1, 2, 3]), legacy_gender)
    assert compared == 3
    assert rate == pytest.approx(2 / 3)


def test_report_has_aggregates_and_no_codes() -> None:
    found = compare_columns(ours_frame([5, 6, 7]), legacy_frame([5, 6, 8]), default_catalogue())
    text = render_golden_report(found, "6m_correct", (3, 1.0))
    assert "Overall exact-match rate: 66.7%" in text
    assert "| messages | 2 |" in text
    assert not any(code in text for code in CODES)


def test_load_legacy_features_normalises_and_drops_duplicate_codes(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {"CODICE.ZIP": ["pq-one.zip", "pq-two", "pq-two"], "msg_n_user": [1.0, 2.0, 3.0]}
    )
    path = tmp_path / "legacy.RData"
    pyreadr.write_rdata(str(path), frame, df_name="dati")
    legacy = load_legacy_features(path)
    assert list(legacy.index) == ["PQ-ONE"]
    assert legacy.loc["PQ-ONE", "msg_n_user"] == 1.0
