from pathlib import Path

import pandas as pd
import pytest
import typer

from fbgc_pipeline.cli import MIN_PROFILES, ensure_enough_profiles
from fbgc_pipeline.features.faithful.dictionary import WORD_VARIANTS, load_word_entries
from fbgc_pipeline.validate.dictionary_calibration import (
    WordChoice,
    choose_variants,
    profile_word_counts,
    render_calibration_report,
    write_word_entries,
)

ENTRIES = [{"term": "NonLoSo", "phrase": "non lo so", "variant": "substring"}]


def test_profile_word_counts_cover_every_variant_and_scope() -> None:
    counts = profile_word_counts(
        {"owner_personal": ["Non lo so, non lo so"], "others_group": []}, ENTRIES
    )
    assert len(counts) == 4 * 2
    assert counts[("NonLoSo", "substring", "owner_personal")] == 1
    assert counts[("NonLoSo", "substring_ci", "owner_personal")] == 2
    assert counts[("NonLoSo", "word", "others_group")] == 0


def test_choose_variants_picks_the_best_match() -> None:
    per_profile = {
        "pq-alpha": profile_word_counts({"owner_personal": ["Non lo so, non lo so"]}, ENTRIES),
        "pq-beta": profile_word_counts({"owner_personal": ["NON LO SO"]}, ENTRIES),
    }
    legacy = pd.DataFrame({"user_personal.NonLoSo": [2.0, 1.0]}, index=["pq-alpha", "pq-beta"])
    choice = choose_variants(per_profile, legacy, ENTRIES)[0]
    assert (choice.variant, choice.exact_rate) == ("substring_ci", 1.0)
    assert choice.rates["substring"] == 0.0


def test_write_word_entries_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "words.yaml"
    write_word_entries([WordChoice("no", "no", "word", 0.9, {})], path)
    assert load_word_entries(path) == [{"term": "no", "phrase": "no", "variant": "word"}]
    assert path.read_text(encoding="utf-8").startswith("# The 79 dictionary words")


def test_calibration_report_says_the_rates_are_in_sample() -> None:
    text = render_calibration_report([], 300)
    sentence = "Calibrated in-sample on the same profiles the golden report compares, "
    assert sentence + "so these rates are optimistic." in text


def test_too_few_calibrated_profiles_refuse_to_write() -> None:
    with pytest.raises(typer.Exit) as stop:
        ensure_enough_profiles(MIN_PROFILES - 1)
    assert stop.value.exit_code == 1
    ensure_enough_profiles(MIN_PROFILES)


def test_calibration_report_lists_every_word() -> None:
    choice = WordChoice("bello", "bello", "word", 0.97, dict.fromkeys(WORD_VARIANTS, 0.97))
    text = render_calibration_report([choice], 300)
    assert "| `bello` | bello | word | 97.0% |" in text
    assert "1 of 1" in text
