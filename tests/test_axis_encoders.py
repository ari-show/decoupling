from __future__ import annotations

import pytest
import torch

from decoupled_ts.retail_models import DayEncoder, HourEncoder


def _grid_and_mask(days: int = 6, hours: int = 24, channels: int = 4) -> tuple[torch.Tensor, torch.Tensor]:
    torch.manual_seed(17)
    grid = torch.randn(2, days, hours, channels)
    mask = (torch.rand(2, days, hours, 1) > 0.2).float().expand_as(grid).contiguous()
    return grid, mask


@pytest.mark.parametrize("architecture", ["mlp", "mlp_wide", "gru"])
def test_axis_encoders_keep_per_step_shapes(architecture: str) -> None:
    grid, mask = _grid_and_mask()
    day = DayEncoder(grid.shape[-1], 32, 5, architecture=architecture)
    hour = HourEncoder(grid.shape[-1], 32, 5, architecture=architecture)

    assert day(grid, mask).shape == (2, grid.shape[1], 5)
    assert hour(grid, mask).shape == (2, grid.shape[2], 5)


def test_gru_day_encoder_propagates_earlier_days_while_mlp_does_not() -> None:
    grid, mask = _grid_and_mask()
    perturbed = grid.clone()
    perturbed[:, 3] = perturbed[:, 3] + 5.0

    for architecture, expect_propagation in (("gru", True), ("mlp", False), ("mlp_wide", False)):
        encoder = DayEncoder(grid.shape[-1], 32, 5, architecture=architecture).eval()
        with torch.no_grad():
            base = encoder(grid, mask)
            changed = encoder(perturbed, mask)
        same_before = torch.allclose(base[:, :3], changed[:, :3], atol=1e-6)
        same_after = torch.allclose(base[:, 4:], changed[:, 4:], atol=1e-6)
        assert same_before, architecture
        assert not torch.allclose(base[:, 3], changed[:, 3], atol=1e-6), architecture
        assert same_after is not expect_propagation, architecture


def test_mlp_wide_matches_gru_parameter_count() -> None:
    gru = DayEncoder(4, 160, 10, architecture="gru")
    wide = DayEncoder(4, 160, 10, architecture="mlp_wide")
    gru_params = sum(parameter.numel() for parameter in gru.parameters())
    wide_params = sum(parameter.numel() for parameter in wide.parameters())

    assert abs(wide_params - gru_params) / gru_params < 0.01


def test_unknown_architecture_is_rejected() -> None:
    with pytest.raises(ValueError):
        DayEncoder(4, 32, 5, architecture="lstm")
