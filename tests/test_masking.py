from __future__ import annotations

import numpy as np
import torch

from decoupled_ts.masking import hidden_cells_from_days, masking_config, sample_hidden_cells
from decoupled_ts.residual_experiments import residual_batch


def _batch(days: int = 6, hours: int = 24, channels: int = 3, batch: int = 4) -> dict[str, torch.Tensor]:
    rng = np.random.default_rng(0)
    x = torch.from_numpy(rng.random((batch, channels, days * hours)).astype("float32"))
    mask = torch.ones(batch, channels, days * hours)
    return {"x": x, "mask": mask}


def _config() -> dict[str, object]:
    return {"dataset": {"window_size": 24}, "residual": {"baseline_method": "series_mean", "target": "baseline_residual"}}


def test_random_day_masking_keeps_the_requested_number_of_days() -> None:
    hidden = sample_hidden_cells(8, 28, 24, {"keep_fraction": 0.5, "min_visible_days": 5}, torch.device("cpu"))
    visible_days = (hidden[:, :, 0] == 0).sum(dim=1)
    assert torch.equal(visible_days, torch.full((8,), 14))
    # every hour of a hidden day is hidden
    assert torch.equal(hidden.sum(dim=2) / 24.0, hidden[:, :, 0])


def test_min_visible_days_overrides_a_small_keep_fraction() -> None:
    hidden = sample_hidden_cells(3, 28, 24, {"keep_fraction": 0.01, "min_visible_days": 5}, torch.device("cpu"))
    assert torch.equal((hidden[:, :, 0] == 0).sum(dim=1), torch.full((3,), 5))


def test_tail_masking_hides_the_last_days() -> None:
    hidden = sample_hidden_cells(2, 10, 24, {"mode": "tail_days", "hidden_days": 3}, torch.device("cpu"))
    assert hidden[:, -3:, :].min() == 1.0
    assert hidden[:, :-3, :].max() == 0.0


def test_masking_config_respects_the_enabled_flag() -> None:
    assert masking_config({"masking": {"enabled": False, "keep_fraction": 0.5}}) == {}
    assert masking_config({"masking": {"enabled": True, "keep_fraction": 0.5}})["keep_fraction"] == 0.5


def test_hidden_cells_hide_the_input_but_not_the_target() -> None:
    batch, config = _batch(), _config()
    visible = np.array([0, 1, 2])
    hidden = hidden_cells_from_days(len(batch["x"]), 6, 24, visible, torch.device("cpu"))

    plain = residual_batch(batch, config)
    masked = residual_batch(batch, config, hidden_cells=hidden)

    grid = masked["x"][:, 0, :].reshape(-1, 6, 24)
    assert torch.allclose(grid[:, 3:, :], torch.zeros_like(grid[:, 3:, :]))
    assert not torch.allclose(grid[:, :3, :], torch.zeros_like(grid[:, :3, :]))
    # the reconstruction target and the observation mask are untouched
    assert torch.equal(masked["observed"], plain["observed"])
    assert torch.equal(masked["sales"], plain["sales"])
    # the baseline now uses the visible days only, so the residual changes
    assert not torch.allclose(masked["baseline"], plain["baseline"])
    assert torch.allclose(masked["baseline"][:, 0, 0], plain["sales"][:, :3, :].mean(dim=(1, 2)), atol=1e-6)


def test_tail_mask_config_and_hidden_cells_combine() -> None:
    batch = _batch(days=6)
    config = _config()
    config["residual"]["future_mask_days"] = 1
    hidden = hidden_cells_from_days(len(batch["x"]), 6, 24, np.array([0, 1, 2, 3, 4]), torch.device("cpu"))
    masked = residual_batch(batch, config, hidden_cells=hidden)
    grid = masked["x"][:, 0, :].reshape(-1, 6, 24)
    assert torch.allclose(grid[:, 5, :], torch.zeros_like(grid[:, 5, :]))
    # future_cells stays the configured tail mask, hidden_cells is reported separately
    assert masked["future_cells"][:, :-1, :].max() == 0.0
    assert masked["hidden_cells"][:, 5, :].min() == 1.0
