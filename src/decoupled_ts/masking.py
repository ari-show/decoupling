"""Day-level input masking (2-Exp-49).

Training-time masking hides the sales and stock channels of a subset of days
before the batch reaches the encoder, while the day-level covariates, the time
features and the reconstruction target stay in place. The residual baseline is
recomputed from the visible days only, so a masked batch is exactly what the
encoder would see if those days had never been recorded.

Two policies are available:

- ``random_days``: hide a random subset of days, redrawn every batch. This is
  the condition that can teach the encoder to pool across series when a single
  series carries little evidence.
- ``tail_days``: hide the last N days, matching the future-day masking already
  used by ``residual.future_mask_days``.

``loss_on`` decides what is asked of the model. ``"all"`` keeps the hidden days
in the reconstruction loss, so the model must infer them from covariates;
``"visible"`` drops them, so masking acts as input noise only.

The module also holds the held-out diagnostics that motivate the experiment.
They are reported on the test split and never affect training:

- short history: give the encoder k days and score the hour profile it produces
  against days it never saw, next to the empirical mean of the same k days and
  to that mean shrunk toward the population profile.
- transfer: rebuild a store x product series from the latents of the same
  product in *other* stores, next to the same transfer done with empirical
  profiles.
- hidden day: how much of a hidden day's level the day component recovers.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
from torch import nn


def masking_config(config: dict[str, Any]) -> dict[str, Any]:
    cfg = dict(config.get("masking", {}))
    return cfg if bool(cfg.get("enabled", False)) else {}


def sample_hidden_cells(
    batch_size: int,
    days: int,
    hours: int,
    cfg: dict[str, Any],
    device: torch.device,
    generator: torch.Generator | None = None,
) -> torch.Tensor | None:
    """Draw the per-sample hidden-cell indicator for one batch.

    Returns a ``(batch, days, hours)`` tensor with 1.0 on hidden cells, or
    ``None`` when the policy hides nothing.
    """
    mode = str(cfg.get("mode", "random_days"))
    if mode == "random_days":
        keep_fraction = float(cfg.get("keep_fraction", 0.5))
        min_visible = int(cfg.get("min_visible_days", 5))
        visible_days = int(round(keep_fraction * days))
        visible_days = max(min(days, min_visible), visible_days)
        if visible_days >= days:
            return None
        # draw on CPU so the hidden days are reproducible across devices
        scores = torch.rand(batch_size, days, generator=generator)
        hidden_index = scores.argsort(dim=1)[:, visible_days:]
        day_hidden = torch.zeros(batch_size, days)
        day_hidden.scatter_(1, hidden_index, 1.0)
        day_hidden = day_hidden.to(device)
    elif mode == "tail_days":
        hidden_days = int(cfg.get("hidden_days", 7))
        if hidden_days <= 0:
            return None
        if hidden_days >= days:
            raise ValueError(f"tail_days masking would hide every day: hidden_days={hidden_days} days={days}")
        day_hidden = torch.zeros(batch_size, days, device=device)
        day_hidden[:, -hidden_days:] = 1.0
    else:
        raise ValueError(f"unknown masking mode: {mode}")
    return day_hidden[:, :, None].expand(batch_size, days, hours).contiguous()


def hidden_cells_from_days(
    batch_size: int, days: int, hours: int, visible_days: np.ndarray, device: torch.device
) -> torch.Tensor:
    """Hidden-cell indicator that keeps exactly ``visible_days`` visible."""
    day_hidden = torch.ones(batch_size, days, device=device)
    day_hidden[:, torch.as_tensor(np.asarray(visible_days), dtype=torch.long, device=device)] = 0.0
    return day_hidden[:, :, None].expand(batch_size, days, hours).contiguous()


def _static_column(config: dict[str, Any], name: str) -> int | None:
    columns = list(config.get("dataset", {}).get("static_id_columns", []))
    return columns.index(name) if name in columns else None


def _centered_profile(values: np.ndarray) -> np.ndarray:
    return values - values.mean(axis=1, keepdims=True)


def _pooled_r2(target: np.ndarray, prediction: np.ndarray) -> float:
    reference = target.mean(axis=0, keepdims=True)
    denominator = float(((target - reference) ** 2).sum())
    if denominator <= 0.0:
        return float("nan")
    return float(1.0 - ((target - prediction) ** 2).sum() / denominator)


def _shrink_out_of_fold(estimate: np.ndarray, target: np.ndarray, folds: int = 5, seed: int = 0) -> np.ndarray:
    """Shrink each series' estimate toward the population profile.

    The shrinkage weight is fitted on the other folds, so this is the honest
    competitor for a representation that is supposed to pool across series.
    """
    rng = np.random.default_rng(seed)
    out = estimate.copy()
    splits = np.array_split(rng.permutation(len(estimate)), folds)
    for index in range(folds):
        test = splits[index]
        train = np.concatenate([splits[other] for other in range(folds) if other != index])
        population = estimate[train].mean(axis=0)
        deviation = estimate[train] - population
        numerator = float((deviation * (target[train] - population)).sum())
        denominator = float((deviation * deviation).sum())
        weight = numerator / denominator if denominator > 0 else 0.0
        out[test] = population + weight * (estimate[test] - population)
    return out


def _leave_one_out_group_mean(values: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """Mean of the other members of each row's group; NaN for singleton groups."""
    out = np.full(values.shape, np.nan, dtype=np.float64)
    flat = values.reshape(len(values), -1).astype(np.float64)
    for level in np.unique(groups):
        rows = np.where(groups == level)[0]
        if len(rows) < 2:
            continue
        total = flat[rows].sum(axis=0)
        for row in rows:
            out.reshape(len(values), -1)[row] = (total - flat[row]) / (len(rows) - 1)
    return out


@torch.no_grad()
def _forward_masked(
    model: nn.Module,
    tensors: dict[str, torch.Tensor],
    config: dict[str, Any],
    device: torch.device,
    keys: tuple[str, ...],
    visible_days: np.ndarray | None,
    batch_size: int = 256,
) -> dict[str, np.ndarray]:
    from .residual_experiments import residual_batch  # local import avoids an import cycle

    model.eval()
    collected: dict[str, list[np.ndarray]] = {key: [] for key in keys}
    total = len(tensors["x"])
    days, hours = int(tensors["days"]), int(tensors["hours"])
    for start in range(0, total, batch_size):
        chunk = {
            "x": tensors["x"][start : start + batch_size].to(device),
            "mask": tensors["mask"][start : start + batch_size].to(device),
        }
        hidden = None
        if visible_days is not None:
            hidden = hidden_cells_from_days(len(chunk["x"]), days, hours, visible_days, device)
        rb = residual_batch(chunk, config, hidden_cells=hidden)
        out = model(rb["x"], rb["mask"])
        for key in keys:
            if key in out:
                collected[key].append(out[key].detach().cpu().numpy())
            elif key in rb:
                collected[key].append(rb[key].detach().cpu().numpy())
    return {key: np.concatenate(value) for key, value in collected.items() if value}


def _gather_tensors(loader) -> dict[str, torch.Tensor]:
    parts: dict[str, list[torch.Tensor]] = {"x": [], "mask": [], "static_ids": []}
    for batch in loader:
        for key in parts:
            if key in batch:
                parts[key].append(batch[key])
    tensors = {key: torch.cat(value) for key, value in parts.items() if value}
    flat = tensors["x"].shape[-1]
    tensors["hours"] = torch.tensor(24)
    tensors["days"] = torch.tensor(flat // 24)
    return tensors


def _short_history_metrics(
    model: nn.Module,
    tensors: dict[str, torch.Tensor],
    config: dict[str, Any],
    device: torch.device,
    diag_cfg: dict[str, Any],
    sales: np.ndarray,
    observed: np.ndarray,
    train_days: np.ndarray,
    score_days: np.ndarray,
) -> dict[str, float]:
    metrics: dict[str, float] = {}
    target = _empirical_hour_profile(sales, observed, score_days)
    for k in [int(value) for value in diag_cfg.get("history_days", [3, 7, 14])]:
        if k > len(train_days):
            continue
        visible = train_days[:k]
        empirical = _empirical_hour_profile(sales, observed, visible)
        latent = _forward_masked(model, tensors, config, device, ("hour_component",), visible)["hour_component"][:, 0, :]
        latent = _centered_profile(latent.astype(np.float64))
        usable = np.isfinite(empirical).all(axis=1) & np.isfinite(target).all(axis=1)
        if usable.sum() < 10:
            continue
        shrunk = _shrink_out_of_fold(empirical[usable], target[usable])
        metrics[f"maskdiag_history{k}_series"] = float(usable.sum())
        metrics[f"maskdiag_history{k}_empirical_r2"] = _pooled_r2(target[usable], empirical[usable])
        metrics[f"maskdiag_history{k}_empirical_shrunk_r2"] = _pooled_r2(target[usable], shrunk)
        metrics[f"maskdiag_history{k}_latent_r2"] = _pooled_r2(target[usable], latent[usable])
        metrics[f"maskdiag_history{k}_latent_minus_shrunk_r2"] = (
            metrics[f"maskdiag_history{k}_latent_r2"] - metrics[f"maskdiag_history{k}_empirical_shrunk_r2"]
        )
    return metrics


def _empirical_hour_profile(sales: np.ndarray, observed: np.ndarray, days: np.ndarray) -> np.ndarray:
    counts = observed[:, days].sum(axis=1)
    totals = (sales[:, days] * observed[:, days]).sum(axis=1)
    profile = np.where(counts > 0, totals / np.maximum(counts, 1.0), np.nan)
    return _centered_profile(profile)


def _transfer_metrics(
    model: nn.Module,
    tensors: dict[str, torch.Tensor],
    config: dict[str, Any],
    device: torch.device,
    sales: np.ndarray,
    observed: np.ndarray,
    residual: np.ndarray,
    latents: dict[str, np.ndarray],
    product: np.ndarray,
) -> dict[str, float]:
    """Rebuild each series from the same product in other stores, two ways."""
    if not hasattr(model, "decode_from_encoded") or "z_global" not in latents:
        return {}
    donors = {key: _leave_one_out_group_mean(latents[key], product) for key in ("z_global", "z_day", "z_hour")}
    usable = np.isfinite(donors["z_global"].reshape(len(product), -1)[:, 0])
    if usable.sum() < 10:
        return {}
    decoded = []
    with torch.no_grad():
        for start in range(0, len(product), 256):
            stop = start + 256
            encoded = {
                "grid": torch.zeros(min(256, len(product) - start), 1, 1, 1, device=device),
                "z_global": torch.as_tensor(np.nan_to_num(donors["z_global"][start:stop]), dtype=torch.float32, device=device),
                "z_day": torch.as_tensor(np.nan_to_num(donors["z_day"][start:stop]), dtype=torch.float32, device=device),
                "z_hour": torch.as_tensor(np.nan_to_num(donors["z_hour"][start:stop]), dtype=torch.float32, device=device),
            }
            if hasattr(model, "interaction_encoder"):
                encoded["z_interaction"] = model.interaction_encoder(encoded["z_day"], encoded["z_hour"])
            decoded.append(model.decode_from_encoded(encoded)["residual_hat"].detach().cpu().numpy())
    latent_prediction = np.concatenate(decoded)

    counts = observed.astype(np.float64)
    cells = np.where(observed > 0, residual, 0.0)
    level = cells.sum(axis=(1, 2)) / np.maximum(counts.sum(axis=(1, 2)), 1.0)
    day_profile = cells.sum(axis=2) / np.maximum(counts.sum(axis=2), 1.0)
    day_profile = day_profile - day_profile.mean(axis=1, keepdims=True)
    hour_profile = cells.sum(axis=1) / np.maximum(counts.sum(axis=1), 1.0)
    hour_profile = hour_profile - hour_profile.mean(axis=1, keepdims=True)
    empirical_prediction = (
        np.nan_to_num(_leave_one_out_group_mean(level[:, None], product))[:, :, None]
        + np.nan_to_num(_leave_one_out_group_mean(day_profile, product))[:, :, None]
        + np.nan_to_num(_leave_one_out_group_mean(hour_profile, product))[:, None, :]
    )

    rows = np.where(usable)[0]
    cell_mask = observed[rows] > 0
    truth = residual[rows][cell_mask]
    per_series = {}
    for name, prediction in (("latent", latent_prediction), ("empirical", empirical_prediction)):
        per_series[name] = np.array(
            [np.mean(np.abs((residual[row] - prediction[row])[observed[row] > 0])) for row in rows]
        )
    metrics = {
        "maskdiag_transfer_series": float(len(rows)),
        "maskdiag_transfer_latent_mae": float(np.mean(np.abs(truth - latent_prediction[rows][cell_mask]))),
        "maskdiag_transfer_empirical_mae": float(np.mean(np.abs(truth - empirical_prediction[rows][cell_mask]))),
        "maskdiag_transfer_latent_r2": _pooled_r2(truth[:, None], latent_prediction[rows][cell_mask][:, None]),
        "maskdiag_transfer_win_rate": float(np.mean(per_series["latent"] < per_series["empirical"])),
    }
    metrics["maskdiag_transfer_gain_pct"] = float(
        100.0
        * (metrics["maskdiag_transfer_empirical_mae"] - metrics["maskdiag_transfer_latent_mae"])
        / max(metrics["maskdiag_transfer_empirical_mae"], 1e-12)
    )
    return metrics


def _hidden_day_metrics(
    model: nn.Module,
    tensors: dict[str, torch.Tensor],
    config: dict[str, Any],
    device: torch.device,
    sales: np.ndarray,
    observed: np.ndarray,
    residual: np.ndarray,
    visible_days: np.ndarray,
    hidden_days: np.ndarray,
) -> dict[str, float]:
    out = _forward_masked(model, tensors, config, device, ("day_component",), visible_days)
    if "day_component" not in out:
        return {}
    predicted = out["day_component"][:, :, 0].astype(np.float64)
    counts = observed.sum(axis=2)
    empirical = np.where(counts > 0, np.where(observed > 0, residual, 0.0).sum(axis=2) / np.maximum(counts, 1.0), np.nan)
    empirical = empirical - np.nanmean(empirical[:, visible_days], axis=1, keepdims=True)
    usable = np.isfinite(empirical).all(axis=1)
    if usable.sum() < 10:
        return {}
    metrics = {}
    for label, days in (("hidden", hidden_days), ("seen", visible_days)):
        target = empirical[usable][:, days].ravel()
        prediction = predicted[usable][:, days].ravel()
        metrics[f"maskdiag_{label}_day_corr"] = float(np.corrcoef(target, prediction)[0, 1])
        metrics[f"maskdiag_{label}_day_r2"] = _pooled_r2(target[:, None], prediction[:, None])
    metrics["maskdiag_hidden_day_series"] = float(usable.sum())
    return metrics


def masked_holdout_diagnostics(
    model: nn.Module,
    loader,
    config: dict[str, Any],
    device: torch.device,
    latents: dict[str, np.ndarray] | None = None,
) -> dict[str, float]:
    """Short-history, transfer and hidden-day diagnostics on the test split.

    Days are split by parity. With a 28-day window each parity class holds every
    weekday exactly twice, so the split does not confound the day of week.
    """
    diag_cfg = config.get("masking_diagnostics", {})
    if not bool(diag_cfg.get("enabled", False)):
        return {}
    from .residual_experiments import residual_batch  # local import avoids an import cycle

    tensors = _gather_tensors(loader)
    days, hours = int(tensors["days"]), int(tensors["hours"])
    train_days = np.arange(1, days, 2)
    score_days = np.arange(0, days, 2)

    with torch.no_grad():
        full = {"sales": [], "observed": [], "residual": []}
        for start in range(0, len(tensors["x"]), 256):
            chunk = {
                "x": tensors["x"][start : start + 256].to(device),
                "mask": tensors["mask"][start : start + 256].to(device),
            }
            rb = residual_batch(chunk, config)
            for key in full:
                full[key].append(rb[key].detach().cpu().numpy())
    sales = np.concatenate(full["sales"]).astype(np.float64)
    observed = np.concatenate(full["observed"]).astype(np.float64)
    residual = np.concatenate(full["residual"]).astype(np.float64)

    metrics = _short_history_metrics(
        model, tensors, config, device, diag_cfg, sales, observed, train_days, score_days
    )
    metrics.update(
        _hidden_day_metrics(model, tensors, config, device, sales, observed, residual, train_days, score_days)
    )
    product_column = _static_column(config, str(diag_cfg.get("transfer_group", "product_id")))
    if product_column is not None and latents and "static_ids" in tensors:
        product = tensors["static_ids"].numpy()[:, product_column]
        metrics.update(
            _transfer_metrics(model, tensors, config, device, sales, observed, residual, latents, product)
        )
    return metrics
