from __future__ import annotations

import numpy as np

from decoupled_ts.residual_experiments import cancellation_ratio


def _arrays(components: list[np.ndarray], observed: np.ndarray) -> dict[str, np.ndarray]:
    keys = ("global_component", "day_component", "hour_component", "interaction_component")
    return {"observed": observed, **dict(zip(keys, components, strict=True))}


def test_ratio_is_one_when_components_do_not_cancel() -> None:
    # all components non-negative: |sum| equals sum of |component|
    comps = [np.full((2, 3, 4), value, dtype="float32") for value in (0.1, 0.2, 0.3, 0.4)]
    out = cancellation_ratio(_arrays(comps, np.ones((2, 3, 4))))
    assert abs(out["abs_sum"] - 1.0) < 1e-6
    assert abs(out["joint"] - 1.0) < 1e-6
    assert abs(out["ratio"] - 1.0) < 1e-6


def test_ratio_grows_when_components_cancel() -> None:
    # +1 and -1 cancel: sum of |component| is 2.0 while |sum| is 0.02
    comps = [
        np.full((2, 3, 4), 1.0, dtype="float32"),
        np.full((2, 3, 4), -1.0, dtype="float32"),
        np.full((2, 3, 4), 0.01, dtype="float32"),
        np.full((2, 3, 4), 0.01, dtype="float32"),
    ]
    out = cancellation_ratio(_arrays(comps, np.ones((2, 3, 4))))
    assert abs(out["abs_sum"] - 2.02) < 1e-6
    assert abs(out["joint"] - 0.02) < 1e-6
    assert out["ratio"] > 100.0


def test_only_observed_cells_are_counted() -> None:
    observed = np.zeros((1, 2, 2))
    observed[0, 0, 0] = 1.0
    hour = np.zeros((1, 2, 2), dtype="float32")
    hour[0, 0, 0] = 0.5
    hour[0, 1, 1] = 100.0  # unobserved outlier must not move the result
    comps = [np.zeros((1, 2, 2), dtype="float32"), np.zeros((1, 2, 2), dtype="float32"), hour, np.zeros((1, 2, 2), dtype="float32")]
    out = cancellation_ratio(_arrays(comps, observed))
    assert abs(out["abs_hour_component"] - 0.5) < 1e-6
    assert abs(out["abs_sum"] - 0.5) < 1e-6
    assert abs(out["joint"] - 0.5) < 1e-6


def test_matches_the_2_exp_55_definition_on_asymmetric_input() -> None:
    rng = np.random.default_rng(0)
    comps = [rng.normal(size=(3, 4, 5)).astype("float32") for _ in range(4)]
    observed = (rng.random((3, 4, 5)) > 0.3).astype("float32")
    out = cancellation_ratio(_arrays(comps, observed))
    mask = observed.astype(bool)
    expected_abs_sum = sum(float(np.abs(c.astype(np.float64)[mask]).mean()) for c in comps)
    expected_joint = float(np.abs(sum(c.astype(np.float64) for c in comps)[mask]).mean())
    assert abs(out["abs_sum"] - expected_abs_sum) < 1e-12
    assert abs(out["joint"] - expected_joint) < 1e-12
    assert abs(out["ratio"] - expected_abs_sum / expected_joint) < 1e-12
