import numpy as np
import pandas as pd
import pytest

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.synthetic.copula_model import (
    fit_synthetic_model,
    nearest_correlation,
    shrink,
    spearman_to_pearson,
)
from fbgc_pipeline.synthetic.copula_sampling import sample_synthetic


def real_tables(n: int = 200) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Invented 'anonymized' data: msg_count and msg_chars_mean rise together, 20% no survey."""
    rng = np.random.default_rng(3)
    x = rng.normal(size=n)
    features = pd.DataFrame(
        {
            "msg_count": np.round(np.exp(3 + x)),
            "msg_chars_mean": 30 + 5 * x + rng.normal(size=n),
            "msg_hour_21": rng.uniform(0, 0.3, size=n),
            "gpius_total": np.where(rng.random(n) < 0.2, np.nan, rng.uniform(1, 8, size=n)),
        }
    )
    participants = pd.DataFrame(
        {
            "pid": [f"P{rank:03d}" for rank in range(1, n + 1)],
            "wave": rng.choice([1, 2], size=n),
            "gender": np.where(x + rng.normal(scale=0.5, size=n) > 0, "F", "M"),
            "age_band": rng.choice(["20", "21"], size=n),
            "relationship": "single",
        }
    )
    return participants, features


def test_spearman_to_pearson() -> None:
    rho = np.array([0.0, 0.5, 1.0, -1.0])
    assert spearman_to_pearson(rho) == pytest.approx([0.0, 0.5176, 1.0, -1.0], abs=1e-4)


def test_nearest_correlation_repairs_an_impossible_matrix() -> None:
    bad = np.array([[1.0, 0.9, 0.9], [0.9, 1.0, -0.9], [0.9, -0.9, 1.0]])
    assert np.linalg.eigvalsh(bad).min() < 0
    fixed = nearest_correlation(bad)
    assert np.linalg.eigvalsh(fixed).min() > 0
    assert np.diag(fixed) == pytest.approx([1.0, 1.0, 1.0])
    assert np.allclose(fixed, fixed.T)


def test_shrinkage_blends_toward_the_identity() -> None:
    correlation = np.array([[1.0, 0.8], [0.8, 1.0]])
    assert shrink(correlation, 0.0) == pytest.approx(correlation)
    assert shrink(correlation, 0.5) == pytest.approx(np.array([[1.0, 0.4], [0.4, 1.0]]))
    assert shrink(correlation, 1.0) == pytest.approx(np.eye(2))
    with pytest.raises(ValueError, match="between 0 and 1"):
        shrink(correlation, 1.5)


def test_fit_keeps_aggregates_only() -> None:
    participants, features = real_tables()
    model = fit_synthetic_model(participants, features, default_catalogue())
    assert model.keys == ("msg_count", "msg_chars_mean", "msg_hour_21", "gpius_total")
    assert model.quantiles.shape == (4, 101)
    assert model.quantiles[0, 0] == pytest.approx(features["msg_count"].quantile(0.01))
    assert model.quantiles[0, -1] == pytest.approx(features["msg_count"].quantile(0.99))
    assert model.missing_rates[3] == pytest.approx(features["gpius_total"].isna().mean())
    assert model.counts.tolist() == [True, False, False, False]
    assert model.blocks == ("msg", "msg", "msg", "survey")
    assert model.correlation.shape == (5, 5)
    assert model.female_share == pytest.approx((participants["gender"] == "F").mean())
    assert model.n_rows == 200


def test_sampling_is_deterministic_for_a_seed() -> None:
    model = fit_synthetic_model(*real_tables(), default_catalogue())
    first, second = sample_synthetic(model, seed=7), sample_synthetic(model, seed=7)
    pd.testing.assert_frame_equal(first[0], second[0])
    pd.testing.assert_frame_equal(first[1], second[1])
    assert not first[1].equals(sample_synthetic(model, seed=8)[1])


def test_samples_follow_the_marginals_and_the_correlation() -> None:
    participants, features = real_tables()
    people, synthetic = sample_synthetic(
        fit_synthetic_model(participants, features, default_catalogue()), 7
    )
    assert synthetic.shape == (200, 5)
    assert list(synthetic["pid"][:2]) == ["S001", "S002"]
    counts = synthetic["msg_count"]
    assert (counts == counts.round()).all()
    assert counts.min() >= features["msg_count"].quantile(0.01)
    assert counts.max() <= features["msg_count"].quantile(0.99)
    assert 0.1 < synthetic["gpius_total"].isna().mean() < 0.3
    rho = synthetic["msg_count"].corr(synthetic["msg_chars_mean"], method="spearman")
    assert rho > 0.8
    assert abs((people["gender"] == "F").mean() - (participants["gender"] == "F").mean()) < 0.1
    assert set(people["wave"]) <= {1, 2}
    assert people["has_survey"].tolist() == synthetic["gpius_total"].notna().tolist()
    assert people["has_messages"].tolist() == (synthetic["msg_count"] > 0).tolist()


def test_marginals_are_clipped_so_no_real_extreme_is_stored_or_sampled() -> None:
    participants, features = real_tables()
    features["msg_hour_21"] = np.append(np.linspace(0, 10, 199), 1000.0)
    features.loc[0, "msg_hour_21"] = -500.0
    model = fit_synthetic_model(participants, features, default_catalogue())
    stored = model.quantiles[2]
    assert features["msg_hour_21"].min() not in stored
    assert features["msg_hour_21"].max() not in stored
    for seed in range(5):
        sampled = sample_synthetic(model, seed)[1]["msg_hour_21"]
        assert sampled.max() < 1000.0
        assert sampled.min() > -500.0


def test_an_all_null_category_becomes_a_single_unknown_category() -> None:
    participants, features = real_tables()
    participants["age_band"] = None
    model = fit_synthetic_model(participants, features, default_catalogue())
    assert model.categories["age_band"] == (("unknown",), (1.0,))
    people, _ = sample_synthetic(model, 7)
    assert set(people["age_band"]) == {"unknown"}
