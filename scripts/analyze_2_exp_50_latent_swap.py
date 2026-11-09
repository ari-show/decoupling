"""Latent swap counterfactual for 2-Exp-50.

Takes a trained checkpoint, encodes the test series, replaces one latent axis
with another series' latent, decodes again, and measures where the prediction
moved. A model that really separates the axes should move only along the axis
that was swapped.

For the centered output decomposition the day-axis answer is exact by
construction: the hour profile of the prediction is
``global + mean_d(day) + hour + mean_d(interaction)`` and the centering fixes
both day means at zero, so swapping z_day cannot move it. Without centering
those means are free, and in a latent-split model a single decoder mixes all
latents, so neither keeps the other axis still. The script measures that gap
instead of assuming it.

Usage:
    uv run python scripts/analyze_2_exp_50_latent_swap.py \
        --model centered=/path/runs/.../dim10/seed_*/output_decomp_centered \
        --model no_center=/path/runs/.../dim10/seed_*/output_decomp_no_center \
        --model latent_split=runs/.../dim10/seed_*/latent_split_four_factor \
        --out-dir figures/2-Exp-50
"""

from __future__ import annotations

import argparse
import csv
import json
from glob import glob
from pathlib import Path
from typing import Any

import numpy as np
import torch

from decoupled_ts.residual_experiments import make_residual_model, residual_batch
from decoupled_ts.retail_data import build_retail_data
from decoupled_ts.train import make_loader, resolve_device


def parse_model_arg(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"expected NAME=GLOB, got {value!r}")
    name, pattern = value.split("=", 1)
    return name, pattern


def seed_of(path: Path) -> int:
    for part in path.parts[::-1]:
        if part.startswith("seed_"):
            return int(part.removeprefix("seed_"))
    raise ValueError(f"no seed_* directory in {path}")


_BUNDLES: dict[str, Any] = {}


def cached_bundle(config: dict[str, Any]):
    """One bundle per dataset config; rebuilding it per checkpoint is the slow part."""
    key = json.dumps(config["dataset"], sort_keys=True)
    if key not in _BUNDLES:
        _BUNDLES[key] = build_retail_data(config)
    return _BUNDLES[key]


def load_checkpoint(variant_dir: Path, device: torch.device) -> tuple[torch.nn.Module, dict[str, Any], dict[str, Any]]:
    checkpoint = torch.load(variant_dir / "best.pt", map_location=device, weights_only=False)
    config, variant = checkpoint["config"], checkpoint["variant"]
    bundle = cached_bundle(config)
    model = make_residual_model(config, variant, bundle.input_dim, bundle.days, bundle.hours).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    return model, config, {"variant": variant, "bundle": bundle}


def predict(model: torch.nn.Module, encoded: dict[str, torch.Tensor]) -> torch.Tensor:
    decoded = model.decode_from_encoded(encoded)
    return decoded["residual_hat"] if isinstance(decoded, dict) else decoded


def swap_axis(model: torch.nn.Module, encoded: dict[str, torch.Tensor], axis: str) -> dict[str, torch.Tensor]:
    """Replace one latent axis with the next series' latent (a deterministic roll)."""
    key = {"day": "z_day", "hour": "z_hour"}[axis]
    swapped = dict(encoded)
    permutation = torch.roll(torch.arange(encoded[key].shape[0], device=encoded[key].device), 1)
    swapped[key] = encoded[key][permutation]
    if "z_interaction" in encoded and hasattr(model, "interaction_encoder"):
        swapped["z_interaction"] = model.interaction_encoder(swapped["z_day"], swapped["z_hour"])
    return swapped


def profiles(values: torch.Tensor, observed: torch.Tensor | None) -> tuple[np.ndarray, np.ndarray]:
    """Hour profile (mean over days) and day profile (mean over hours)."""
    if observed is None:
        hour = values.mean(dim=1)
        day = values.mean(dim=2)
    else:
        hour = (values * observed).sum(dim=1) / observed.sum(dim=1).clamp_min(1.0)
        day = (values * observed).sum(dim=2) / observed.sum(dim=2).clamp_min(1.0)
    return hour.cpu().numpy(), day.cpu().numpy()


def row_corr(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left = left - left.mean(axis=1, keepdims=True)
    right = right - right.mean(axis=1, keepdims=True)
    denominator = np.linalg.norm(left, axis=1) * np.linalg.norm(right, axis=1)
    out = np.full(len(left), np.nan)
    keep = denominator > 1e-12
    out[keep] = (left[keep] * right[keep]).sum(axis=1) / denominator[keep]
    return out


@torch.no_grad()
def swap_metrics(model: torch.nn.Module, config: dict[str, Any], bundle, device: torch.device, axis: str) -> dict[str, float]:
    loader = make_loader(bundle.test, config, shuffle=False)
    collected: dict[str, list[np.ndarray]] = {}

    def add(key: str, value: np.ndarray) -> None:
        collected.setdefault(key, []).append(np.asarray(value, dtype=np.float64))

    for batch in loader:
        batch = {key: value.to(device, non_blocking=True) for key, value in batch.items()}
        prepared = residual_batch(batch, config)
        encoded = model.encode(prepared["x"], prepared["mask"])
        base = predict(model, encoded)
        moved = predict(model, swap_axis(model, encoded, axis))
        delta = moved - base
        observed = (prepared["observed"] > 0).to(base.dtype)

        for tag, mask in (("grid", None), ("observed", observed)):
            base_hour, base_day = profiles(base, mask)
            delta_hour, delta_day = profiles(delta, mask)
            moved_hour, moved_day = profiles(moved, mask)
            add(f"{tag}_hour_shift", np.abs(delta_hour).mean(axis=1))
            add(f"{tag}_day_shift", np.abs(delta_day).mean(axis=1))
            add(f"{tag}_hour_amplitude", base_hour.std(axis=1))
            add(f"{tag}_day_amplitude", base_day.std(axis=1))
            add(f"{tag}_hour_corr", row_corr(base_hour, moved_hour))
            add(f"{tag}_day_corr", row_corr(base_day, moved_day))
        add("cell_abs_delta", (delta.abs() * observed).sum(dim=(1, 2)).cpu().numpy() / observed.sum(dim=(1, 2)).clamp_min(1.0).cpu().numpy())

    stacked = {key: np.concatenate(value) for key, value in collected.items()}
    metrics: dict[str, float] = {"n_series": float(len(stacked["cell_abs_delta"]))}
    for key, value in stacked.items():
        metrics[f"{key}_mean"] = float(np.nanmean(value))
    # the axis that was swapped should move, the other one should not
    held = "hour" if axis == "day" else "day"
    for tag in ("grid", "observed"):
        moved_amount = metrics[f"{tag}_{axis}_shift_mean"]
        held_amount = metrics[f"{tag}_{held}_shift_mean"]
        metrics[f"{tag}_leak_ratio"] = held_amount / max(moved_amount, 1e-12)
        metrics[f"{tag}_leak_vs_amplitude"] = held_amount / max(metrics[f"{tag}_{held}_amplitude_mean"], 1e-12)
    return metrics


def numeric_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key in sorted({(row["model"], row["swap_axis"]) for row in rows}):
        selected = [row for row in rows if (row["model"], row["swap_axis"]) == key]
        entry: dict[str, Any] = {"runs": len(selected)}
        for metric in sorted({name for row in selected for name in row if isinstance(row[name], int | float)}):
            values = [float(row[metric]) for row in selected]
            entry[f"{metric}_mean"] = float(np.mean(values))
            entry[f"{metric}_std"] = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        summary[f"{key[0]}|swap_{key[1]}"] = entry
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", action="append", required=True, type=parse_model_arg, help="NAME=GLOB of variant directories holding best.pt")
    parser.add_argument("--out-dir", default="figures/2-Exp-50")
    parser.add_argument("--axes", nargs="+", default=["day", "hour"])
    args = parser.parse_args()

    device = resolve_device("auto")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for name, pattern in args.model:
        directories = sorted(Path(path) for path in glob(pattern))
        if not directories:
            raise FileNotFoundError(f"{name}: no directory matched {pattern}")
        for directory in directories:
            model, config, extra = load_checkpoint(directory, device)
            for axis in args.axes:
                metrics = swap_metrics(model, config, extra["bundle"], device, axis)
                rows.append({"model": name, "seed": seed_of(directory), "swap_axis": axis, **metrics})
                print(f"{name} seed {seed_of(directory)} swap {axis}: "
                      f"grid leak ratio {metrics['grid_leak_ratio']:.2e}, "
                      f"observed leak ratio {metrics['observed_leak_ratio']:.3f}")

    summary = {
        "swap": "z_<axis> replaced by the next series' latent (deterministic roll)",
        "rows": rows,
        "aggregate": numeric_summary(rows),
    }
    (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    fieldnames = sorted({key for row in rows for key in row})
    with (out_dir / "metrics_by_seed.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote 2-Exp-50 latent swap analysis to {out_dir}")


if __name__ == "__main__":
    main()
