import numpy as np
import pandas as pd

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.synthetic.copula_model import MIN_OBSERVED, fit_synthetic_model
from fbgc_pipeline.synthetic.copula_sampling import sample_synthetic
from fbgc_pipeline.synthetic.synthetic_dataset import build_synthetic


def tables(n: int = 200) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Invented anonymized data with four dense features."""
    rng = np.random.default_rng(5)
    features = pd.DataFrame(
        {
            "msg_count": np.round(np.exp(3 + rng.normal(size=n))),
            "msg_chars_mean": rng.normal(30, 5, size=n),
            "msg_hour_21": rng.uniform(0, 0.3, size=n),
            "gpius_total": rng.uniform(1, 8, size=n),
        }
    )
    participants = pd.DataFrame(
        {
            "pid": [f"P{rank:03d}" for rank in range(1, n + 1)],
            "wave": rng.choice([1, 2], size=n),
            "gender": rng.choice(["F", "M"], size=n),
            "age_band": rng.choice(["20", "21"], size=n),
            "relationship": "single",
        }
    )
    return participants, features


def test_a_feature_with_few_values_is_left_out() -> None:
    participants, features = tables()
    features["msg_hour_22"] = np.nan
    features.loc[:4, "msg_hour_22"] = [0.1, 0.2, 0.3, 0.4, 0.5]
    model = fit_synthetic_model(participants, features, default_catalogue())
    assert "msg_hour_22" not in model.keys
    assert model.dropped_sparse == 1
    assert model.quantiles.shape == (4, 101)
    assert model.correlation.shape == (5, 5)
    assert "msg_hour_22" not in sample_synthetic(model, 1)[1].columns


def test_a_feature_at_the_minimum_is_kept() -> None:
    participants, features = tables()
    features["msg_hour_22"] = np.nan
    features.loc[: MIN_OBSERVED - 1, "msg_hour_22"] = np.linspace(0, 1, MIN_OBSERVED)
    model = fit_synthetic_model(participants, features, default_catalogue())
    assert "msg_hour_22" in model.keys
    assert model.dropped_sparse == 0


def test_tails_sit_inside_the_fifth_largest_and_smallest_values() -> None:
    participants, features = tables()
    values = np.append(np.linspace(0, 10, 24), 990.0)  # 25 values, one huge outlier
    features["msg_hour_21"] = np.nan
    features.loc[:24, "msg_hour_21"] = values
    ordered = np.sort(values)
    bound_high, bound_low = ordered[-5], ordered[4]
    model = fit_synthetic_model(participants, features, default_catalogue())
    stored = model.quantiles[model.keys.index("msg_hour_21")]
    assert stored.max() <= bound_high + 1e-9
    assert stored.min() >= bound_low - 1e-9
    for seed in range(5):
        sampled = sample_synthetic(model, seed)[1]["msg_hour_21"]
        assert sampled.max() <= bound_high + 1e-4
        assert sampled.min() >= bound_low - 1e-4


def test_a_sparse_pair_gets_no_nan_in_the_correlation() -> None:
    participants, features = tables()
    features["msg_hour_22"] = np.nan
    features["msg_hour_23"] = np.nan
    features.loc[:99, "msg_hour_22"] = np.linspace(0, 1, 100)  # 100 values
    features.loc[100:199, "msg_hour_23"] = np.linspace(0, 1, 100)  # no joint rows with the first
    model = fit_synthetic_model(participants, features, default_catalogue())
    assert not np.isnan(model.correlation).any()
    first, second = model.keys.index("msg_hour_22"), model.keys.index("msg_hour_23")
    assert abs(model.correlation[first, second]) < 1e-9


def test_build_synthetic_skips_sparse_features_in_the_distance_check() -> None:
    participants, features = tables()
    long = features.assign(pid=participants["pid"]).melt(
        id_vars="pid", var_name="feature_key", value_name="value"
    )
    extra = pd.DataFrame(
        {"pid": ["P001", "P002"], "feature_key": "msg_hour_22", "value": [0.1, 0.2]}
    )
    dataset = build_synthetic(participants, pd.concat([long, extra]), default_catalogue(), 3)
    assert "msg_hour_22" not in dataset.features.columns
