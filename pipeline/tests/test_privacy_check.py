import warnings

import numpy as np
import pytest

from fbgc_pipeline.synthetic.privacy_check import column_scale, distance_to_closest_record


def real_rows() -> np.ndarray:
    return np.random.default_rng(1).normal(size=(100, 6))


def test_copied_rows_fail() -> None:
    real = real_rows()
    check = distance_to_closest_record(real, real.copy())
    assert check.synthetic_p5 == 0.0
    assert not check.passed


def test_distant_rows_pass() -> None:
    real = real_rows()
    check = distance_to_closest_record(real, real + 3.0)
    assert check.synthetic_p5 > check.real_p5
    assert check.passed


def test_column_scale_handles_constant_and_empty_columns() -> None:
    real = np.array([[1.0, 5.0, np.nan], [3.0, 5.0, np.nan]])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        mean, scale = column_scale(real)
    assert mean.tolist() == [2.0, 5.0, 0.0]
    assert scale.tolist() == [1.0, 1.0, 1.0]


def test_missing_values_count_as_the_mean() -> None:
    real = np.array([[0.0, 0.0], [2.0, 2.0], [4.0, 4.0]])
    synthetic = np.array([[np.nan, 2.0]])
    check = distance_to_closest_record(real, synthetic)
    assert check.synthetic_p5 == pytest.approx(0.0)


def test_identical_real_rows_never_pass() -> None:
    real = np.zeros((10, 3))
    check = distance_to_closest_record(real, real + 5.0)
    assert check.real_p5 == 0.0
    assert not check.passed
