"""Analyze how much of a residual's axis structure is actually usable, for 2-Exp-55.

2-Exp-53 left two observations unexplained.

1. `cycle7_hour` keeps 8.83x day structure (model free, permutation p = 0.0050)
   yet its centered day component contributes exactly nothing.
2. `recent_hour_d1` keeps more hour structure than `recent_hour_d7`
   (7.65x vs 3.35x) yet improves less (+1.95% vs +7.51%).

Both ask the same question: does `diag_{axis}_relative_amplitude` measure
structure a model can *use*? This script answers it without training anything,
by fitting the best possible single-axis offset and checking whether it holds up
on cells it was not fitted on.

The residual loss is L1 (`residual_loss` in residual_experiments.py uses
`abs_loss`), so the optimal per-group offset is the **median**, not the mean. An
oracle built from means is mis-specified and can increase MAE even in sample.

For each axis the script reports four numbers:

    uncentered in-sample   the unconstrained ceiling on that axis
    uncentered held-out    the part of that ceiling that generalizes
    centered   in-sample   what the model's centered component could reach
    centered   held-out    the part of that which generalizes

Held-out splits along the *other* axis, so the fitted offset is evaluated on
cells that did not inform it: the day offset is fitted on odd hours and scored on
even hours, the hour offset is fitted on odd days and scored on even days.

It also reports the component cancellation ratio, sum of |component| over
|sum of components|, which is what separates the centered from the uncentered
parameterization.

Usage:
    uv run python scripts/analyze_2_exp_55_axis_usability.py \
        --run-dir runs/2-Exp-53_baseline_diagnosis_freshretailnet \
        --scenarios series_mean recent_hour_d1 recent_hour_d7 cycle7_hour \
        --seeds 17 23 31 47 59 \
        --out-dir figures/2-Exp-55
"""

from __future__ import annotations

import argparse
import csv
import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np

COMPONENTS = ("global", "day", "hour", "interaction")


def _median_offsets(res: np.ndarray, fit_mask: np.ndarray, axis: int) -> tuple[np.ndarray, np.ndarray]:
    """L1-optimal offset per (series, group) along `axis`, from fit cells only.

    axis=2 collapses hours, giving a per-day offset; axis=1 collapses days,
    giving a per-hour offset. Groups with no fitted cell get 0.
    """
    masked = np.where(fit_mask, res, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(masked, axis=axis)
    present = np.isfinite(med)
    return np.where(present, med, 0.0), present


def _center(offsets: np.ndarray, present: np.ndarray) -> np.ndarray:
    """Impose the model's constraint: zero mean across the axis, per series."""
    weight = present.astype(np.float64)
    mean = (offsets * weight).sum(1, keepdims=True) / np.maximum(weight.sum(1, keepdims=True), 1e-12)
    return (offsets - mean) * weight


def axis_gain(res: np.ndarray, fit_mask: np.ndarray, eval_mask: np.ndarray,
              axis_name: str, center: bool) -> float:
    """Relative MAE reduction from the best single-axis offset, scored on eval_mask."""
    collapse = 2 if axis_name == "day" else 1
    offsets, present = _median_offsets(res, fit_mask, collapse)
    if center:
        offsets = _center(offsets, present)
    if axis_name == "day":
        pred = np.broadcast_to(offsets[:, :, None], res.shape)
    else:
        pred = np.broadcast_to(offsets[:, None, :], res.shape)
    base = np.abs(res[eval_mask]).mean()
    corrected = np.abs((res - pred)[eval_mask]).mean()
    return float((base - corrected) / base) if base > 0 else float("nan")


def cancellation(cell_dir: Path, observed: np.ndarray) -> dict[str, float]:
    """sum of |component| vs |sum of components| on observed cells."""
    total = None
    abs_sum = 0.0
    per: dict[str, float] = {}
    for name in COMPONENTS:
        arr = np.load(cell_dir / f"{name}_component.npy").astype(np.float64)
        total = arr if total is None else total + arr
        per[name] = float(np.abs(arr[observed]).mean())
        abs_sum += per[name]
    joint = float(np.abs(total[observed]).mean())
    per["abs_sum"] = abs_sum
    per["joint"] = joint
    per["ratio"] = abs_sum / max(joint, 1e-12)
    return per


def analyze_cell(cell_dir: Path) -> dict[str, Any]:
    res = np.load(cell_dir / "residual.npy").astype(np.float64)
    observed = np.load(cell_dir / "observed.npy").astype(bool)
    hours = np.arange(res.shape[2])
    days = np.arange(res.shape[1])

    # day offsets are fitted on odd hours, scored on even hours
    odd_h = observed & (hours % 2 == 1)[None, None, :]
    even_h = observed & (hours % 2 == 0)[None, None, :]
    # hour offsets are fitted on odd days, scored on even days
    odd_d = observed & (days % 2 == 1)[None, :, None]
    even_d = observed & (days % 2 == 0)[None, :, None]

    out: dict[str, Any] = {"residual_abs_mean": float(np.abs(res[observed]).mean())}
    for axis, (fit, ev) in {"day": (odd_h, even_h), "hour": (odd_d, even_d)}.items():
        for center in (False, True):
            tag = "centered" if center else "uncentered"
            out[f"{axis}_{tag}_in_sample"] = axis_gain(res, observed, observed, axis, center)
            out[f"{axis}_{tag}_held_out"] = axis_gain(res, fit, ev, axis, center)
    out.update({f"cancel_{k}": v for k, v in cancellation(cell_dir, observed).items()})
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--scenarios", nargs="+", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--variants", nargs="+",
                        default=["output_decomp_centered", "output_decomp_no_center"])
    parser.add_argument("--out-dir", default="figures/2-Exp-55")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for scenario in args.scenarios:
        for variant in args.variants:
            for seed in args.seeds:
                cell = run_dir / scenario / f"seed_{seed}" / variant
                if not (cell / "residual.npy").exists():
                    print(f"  skip (no arrays): {cell}")
                    continue
                rows.append({"scenario": scenario, "variant": variant, "seed": seed,
                             **analyze_cell(cell)})

    if not rows:
        raise SystemExit("no cells analyzed")

    metric_keys = [k for k in rows[0] if k not in {"scenario", "variant", "seed"}]
    aggregate: list[dict[str, Any]] = []
    for scenario in args.scenarios:
        for variant in args.variants:
            subset = [r for r in rows if r["scenario"] == scenario and r["variant"] == variant]
            if not subset:
                continue
            entry: dict[str, Any] = {"scenario": scenario, "variant": variant, "runs": len(subset)}
            for key in metric_keys:
                vals = [r[key] for r in subset]
                mean = sum(vals) / len(vals)
                var = sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1)
                entry[f"{key}_mean"] = mean
                entry[f"{key}_std"] = var ** 0.5
            aggregate.append(entry)

    (out_dir / "metrics.json").write_text(
        json.dumps({"run_dir": str(run_dir), "rows": rows, "aggregate": aggregate},
                   indent=1, ensure_ascii=False))
    for name, data in (("axis_usability_by_seed.csv", rows), ("axis_usability.csv", aggregate)):
        fields = sorted({k for r in data for k in r})
        with (out_dir / name).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)

    # console summary, centered variant only (the one the thesis argues for)
    print(f"\n{'scenario':16s} {'axis':5s} | {'uncentered oracle':>21s} | {'centered oracle':>21s}")
    print(f"{'':16s} {'':5s} | {'in-sample':>10s} {'held-out':>10s} | {'in-sample':>10s} {'held-out':>10s}")
    for entry in aggregate:
        if entry["variant"] != "output_decomp_centered":
            continue
        for axis in ("hour", "day"):
            print(f"{entry['scenario']:16s} {axis:5s} | "
                  f"{entry[f'{axis}_uncentered_in_sample_mean']:+10.2%} "
                  f"{entry[f'{axis}_uncentered_held_out_mean']:+10.2%} | "
                  f"{entry[f'{axis}_centered_in_sample_mean']:+10.2%} "
                  f"{entry[f'{axis}_centered_held_out_mean']:+10.2%}")

    print(f"\n{'scenario':16s} {'variant':10s} {'S|c|':>8s} {'|Sc|':>8s} {'cancel':>9s}")
    for entry in aggregate:
        label = "centered" if entry["variant"].endswith("centered") else "no_center"
        print(f"{entry['scenario']:16s} {label:10s} {entry['cancel_abs_sum_mean']:8.5f} "
              f"{entry['cancel_joint_mean']:8.5f} {entry['cancel_ratio_mean']:8.1f}x")

    print(f"\nwrote 2-Exp-55 analysis to {out_dir}")


if __name__ == "__main__":
    main()
