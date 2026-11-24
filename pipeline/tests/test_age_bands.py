import math
from datetime import date, datetime, timedelta, timezone

import pytest

from fbgc_pipeline.anonymize.age_bands import ALL_AGE_BANDS, age_at_download, age_band
from fbgc_pipeline.anonymize.k_anonymity import KAnonymityError, choose_age_level, smallest_cell

DOWNLOAD = datetime(2015, 11, 20, 10, 0, tzinfo=timezone(timedelta(hours=1)))


def test_age_counts_whole_years_at_the_download_date() -> None:
    assert age_at_download(date(1995, 11, 20), DOWNLOAD) == 20
    assert age_at_download(date(1995, 11, 21), DOWNLOAD) == 19
    assert age_at_download(None, DOWNLOAD) is None
    assert age_at_download(date(1995, 1, 1), None) is None


def test_ages_outside_16_to_60_are_unknown() -> None:
    assert age_at_download(date(1999, 11, 20), DOWNLOAD) == 16
    assert age_at_download(date(1999, 11, 21), DOWNLOAD) is None
    assert age_at_download(date(1955, 11, 20), DOWNLOAD) == 60
    assert age_at_download(date(1954, 11, 20), DOWNLOAD) is None


@pytest.mark.parametrize(
    ("age", "level", "band"),
    [
        (19, 0, "<20"),
        (20, 0, "20"),
        (21, 0, "21"),
        (22, 0, "22-24"),
        (24, 0, "22-24"),
        (25, 0, "25+"),
        (20, 1, "<21"),
        (21, 1, "21+"),
        (40, 2, "all"),
        (None, 0, "unknown"),
        (math.nan, 1, "unknown"),
        (None, 2, "unknown"),
    ],
)
def test_age_bands(age: float | None, level: int, band: str) -> None:
    assert age_band(age, level) == band
    assert band in ALL_AGE_BANDS


def test_smallest_cell_counts_age_gender_wave_combinations() -> None:
    assert smallest_cell(["20", "20", "21"], ["F", "F", "F"], [1, 1, 1]) == 1
    assert smallest_cell(["20", "20"], ["F", "M"], [1, 1]) == 1
    assert smallest_cell([], [], []) == 0


def test_the_finest_level_that_reaches_k_is_chosen() -> None:
    ages = [19] * 5 + [20] * 5 + [21] * 5 + [23] * 5 + [30] * 5
    assert choose_age_level(ages, ["F"] * 25, [1] * 25) == 0


def test_a_small_band_moves_to_a_coarser_level() -> None:
    ages = [19] * 5 + [20] * 3 + [21] * 5 + [22] * 2
    assert choose_age_level(ages, ["F"] * 15, [1] * 15) == 1
    assert choose_age_level([19, 20, 21, 22, 23], ["F"] * 5, [1] * 5) == 2


def test_a_small_unknown_band_fails_at_every_level() -> None:
    ages: list[float | None] = [19.0] * 10 + [None, None]
    with pytest.raises(KAnonymityError, match="at least 5 people"):
        choose_age_level(ages, ["F"] * 12, [1] * 12)


def test_cells_split_by_gender_and_wave() -> None:
    ages = [19] * 10
    genders = ["F"] * 5 + ["M"] * 5
    assert choose_age_level(ages, genders, [1] * 10) == 0
    with pytest.raises(KAnonymityError):
        choose_age_level(ages, genders, [1] * 9 + [2])


def _cohort(spec: dict[tuple[str, int], list[tuple[float | None, int]]]) -> tuple[list, list, list]:
    ages, genders, waves = [], [], []
    for (gender, wave), pairs in spec.items():
        for age, count in pairs:
            ages += [age] * count
            genders += [gender] * count
            waves += [wave] * count
    return ages, genders, waves


def test_a_realistic_skew_falls_back_to_level_1_when_the_unknown_cells_are_big_enough() -> None:
    # Shaped like the real cohort: most are 20-21, few are 22+, the small male cells are thin.
    spec: dict[tuple[str, int], list[tuple[float | None, int]]] = {
        ("F", 1): [(19, 10), (20, 40), (21, 15), (23, 8), (30, 6), (None, 9)],
        ("M", 1): [(19, 3), (20, 9), (21, 4), (23, 2), (30, 1), (None, 5)],
        ("F", 2): [(19, 12), (20, 90), (21, 30), (23, 12), (30, 6), (None, 20)],
        ("M", 2): [(19, 4), (20, 25), (21, 9), (23, 3), (30, 2), (None, 10)],
    }
    ages, genders, waves = _cohort(spec)
    assert choose_age_level(ages, genders, waves) == 1
    # Level 0 really fails here: the smallest male cell is below 5.
    level_0 = [age_band(a, 0) for a in ages]
    assert smallest_cell(level_0, genders, waves) < 5


def test_a_thin_unknown_cell_makes_every_level_fail_loudly() -> None:
    spec: dict[tuple[str, int], list[tuple[float | None, int]]] = {
        ("F", 1): [(20, 30), (None, 9)],
        ("M", 1): [(20, 20), (None, 4)],
    }
    ages, genders, waves = _cohort(spec)
    with pytest.raises(KAnonymityError, match="at least 5 people"):
        choose_age_level(ages, genders, waves)
