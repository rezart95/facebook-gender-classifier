import math
from pathlib import Path

import pandas as pd
import pyreadr
import pytest

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.validate.golden_compare import (
    compare_columns,
    gender_agreement,
    values_close,
    values_match,
)
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


def test_values_match_is_near_exact() -> None:
    assert values_match(15.8, 15.8)
    # old intent (four significant digits) now belongs to values_close
    assert not values_match(20.0, 20.004)
    assert values_close(20.0, 20.004)
    assert not values_match(30.0, 31.0)
    assert values_match(math.nan, math.nan)
    assert not values_match(1.0, math.nan)
    assert not values_match(1999, 2000)
    assert values_match(0.25, 0.25 + 1e-13)


def test_values_close_tolerates_rounding() -> None:
    assert values_close(1999, 2000)
    assert not values_close(30.0, 31.0)
    assert values_close(math.nan, math.nan)
    assert not values_close(1.0, math.nan)


def test_compare_columns_reports_exact_rates() -> None:
    found = compare_columns(ours_frame([5, 6, 7]), legacy_frame([5, 6, 8]), default_catalogue())
    by_key = {comparison.key: comparison for comparison in found}
    assert set(by_key) == {"msg_count", "msg_chars_mean"}
    assert by_key["msg_count"].exact_rate == pytest.approx(2 / 3)
    assert by_key["msg_count"].max_abs_diff == 1
    # 20.0 vs 20.004 is close but not exact; 30.0 vs 31.0 is neither
    assert by_key["msg_chars_mean"].exact_rate == pytest.approx(1 / 3)
    assert by_key["msg_chars_mean"].close_rate == pytest.approx(2 / 3)
    assert by_key["msg_count"].close_rate == pytest.approx(2 / 3)


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


def test_gender_agreement_ignores_non_ok_rows_and_missing_genders() -> None:
    ours = ours_frame([1, 2, 3], genders=("F", "M", "F"))
    ours.loc[1, "status"] = "excluded"
    ours.loc[2, "gender"] = None
    legacy_gender = pd.Series(["F", "F", "F"], index=CODES)
    assert gender_agreement(ours, legacy_gender) == (1, 1.0)


def test_report_has_aggregates_and_no_codes() -> None:
    found = compare_columns(ours_frame([5, 6, 7]), legacy_frame([5, 6, 8]), default_catalogue())
    text = render_golden_report(found, "6m_correct", (3, 1.0))
    assert "Overall exact-match rate (near-exact): 50.0%" in text
    assert "Overall within 0.05%: 66.7%" in text
    assert "Non-dictionary exact-match rate: 50.0%" in text
    assert "Non-dictionary within 0.05%: 66.7%" in text
    assert "95%" not in text
    assert "See docs/extraction-golden-gaps.md." in text
    assert "| messages | 2 |" in text
    assert not any(code in text for code in CODES)


def test_report_includes_gaps_text_verbatim() -> None:
    found = compare_columns(ours_frame([5, 6, 7]), legacy_frame([5, 6, 8]), default_catalogue())
    gaps = "- **Window.** Hand-written gap line."
    text = render_golden_report(found, "12m_correct", (3, 1.0), gaps_markdown=gaps)
    assert gaps in text
    assert "See docs/extraction-golden-gaps.md." not in text


def test_load_legacy_features_normalises_and_drops_duplicate_codes(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {"CODICE.ZIP": ["pq-one.zip", "pq-two", "pq-two"], "msg_n_user": [1.0, 2.0, 3.0]}
    )
    path = tmp_path / "legacy.RData"
    pyreadr.write_rdata(str(path), frame, df_name="dati")
    legacy = load_legacy_features(path)
    assert list(legacy.index) == ["PQ-ONE"]
    assert legacy.loc["PQ-ONE", "msg_n_user"] == 1.0
