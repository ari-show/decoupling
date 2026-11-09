"""Prospective screening check for 2-Exp-51.

Asks whether the structure a series shows in an earlier window predicts how
much the correction helps in a later window. The screening numbers use only the
observed residual - no model output - so they can be computed before deciding
whether to apply the method.

For each series the residual variance of the screening window is split the way
a two-way ANOVA would:

    SS_total = SS_hour (hour marginal) + SS_day (day marginal) + SS_rest

``SS_rest`` is what neither margin explains: the true day-hour interaction plus
noise. Counts per hour and per day weight the marginals, so stockout cells drop
out instead of biasing the split.

The evaluation window then gets the relative improvement of the correction,
``(baseline MAE - corrected MAE) / baseline MAE``, and the script reports how
well the three shares predict it.

Usage:
    uv run python scripts/analyze_2_exp_51_prospective_screening.py \
        --run-dir 'runs/.../dim10/seed_*/output_decomp_centered' \
        --share-days 21 --label future_masked --out-dir figures/2-Exp-51
"""

from __future__ import annotations

import argparse
import csv
import json
from glob import glob
from pathlib import Path
from typing import Any

import numpy as np

COMPONENTS = ("global", "day", "hour", "interaction")


def seed_of(path: Path) -> int:
    for part in path.parts[::-1]:
        if part.startswith("seed_"):
            return int(part.removeprefix("seed_"))
    raise ValueError(f"no seed_* directory in {path}")


def load_arrays(variant_dir: Path) -> dict[str, np.ndarray]:
    names = ["residual", "observed", *[f"{name}_component" for name in COMPONENTS]]
    missing = [name for name in names if not (variant_dir / f"{name}.npy").exists()]
    if missing:
        raise FileNotFoundError(f"{variant_dir}: missing {', '.join(missing)}")
    return {name: np.load(variant_dir / f"{name}.npy").astype(np.float64) for name in names}


def structure_shares(residual: np.ndarray, observed: np.ndarray) -> dict[str, np.ndarray]:
    """Two-way ANOVA style split of the residual variance, per series."""
    count = np.clip(observed.sum(axis=(1, 2)), 1.0, None)
    mean = (residual * observed).sum(axis=(1, 2)) / count
    total = (((residual - mean[:, None, None]) ** 2) * observed).sum(axis=(1, 2))

    hour_count = observed.sum(axis=1)
    hour_mean = (residual * observed).sum(axis=1) / np.clip(hour_count, 1.0, None)
    hour_ss = (hour_count * (hour_mean - mean[:, None]) ** 2).sum(axis=1)

    day_count = observed.sum(axis=2)
    day_mean = (residual * observed).sum(axis=2) / np.clip(day_count, 1.0, None)
    day_ss = (day_count * (day_mean - mean[:, None]) ** 2).sum(axis=1)

    rest_ss = np.clip(total - hour_ss - day_ss, 0.0, None)
    denominator = np.clip(total, 1e-12, None)
    return {
        "hour_share": hour_ss / denominator,
        "day_share": day_ss / denominator,
        "rest_share": rest_ss / denominator,
        "total_ss": total,
    }


def improvement(arrays: dict[str, np.ndarray], day_slice: slice) -> dict[str, np.ndarray]:
    residual = arrays["residual"][:, day_slice]
    observed = arrays["observed"][:, day_slice]
    predicted = sum(arrays[f"{name}_component"][:, day_slice] for name in COMPONENTS)
    count = np.clip(observed.sum(axis=(1, 2)), 1.0, None)
    baseline_mae = (np.abs(residual) * observed).sum(axis=(1, 2)) / count
    corrected_mae = (np.abs(residual - predicted) * observed).sum(axis=(1, 2)) / count
    absolute = baseline_mae - corrected_mae
    return {
        "baseline_mae": baseline_mae,
        "corrected_mae": corrected_mae,
        "absolute_improvement": absolute,
        "relative_improvement": absolute / np.clip(baseline_mae, 1e-9, None),
        "observed_cells": observed.sum(axis=(1, 2)),
    }


def safe_corr(left: np.ndarray, right: np.ndarray) -> float | None:
    if left.size < 2 or left.std() <= 1e-12 or right.std() <= 1e-12:
        return None
    return float(np.corrcoef(left, right)[0, 1])


def regression_r2(target: np.ndarray, design: np.ndarray) -> tuple[float, np.ndarray]:
    matrix = np.column_stack([np.ones(len(design)), design])
    beta, *_ = np.linalg.lstsq(matrix, target, rcond=None)
    predicted = matrix @ beta
    total = float(np.sum((target - target.mean()) ** 2))
    return 1.0 - float(np.sum((target - predicted) ** 2)) / max(total, 1e-12), beta


def quartile_rows(shares: np.ndarray, relative: np.ndarray, baseline: np.ndarray, name: str) -> list[dict[str, Any]]:
    edges = np.unique(np.quantile(shares, [0.0, 0.25, 0.5, 0.75, 1.0]))
    rows = []
    for index, (low, high) in enumerate(zip(edges[:-1], edges[1:])):
        last = index == len(edges) - 2
        selected = (shares >= low) & ((shares <= high) if last else (shares < high))
        if not selected.any():
            continue
        rows.append(
            {
                "share_name": name,
                "quartile": index + 1,
                "share_low": float(low),
                "share_high": float(high),
                "count": int(selected.sum()),
                "baseline_mae": float(baseline[selected].mean()),
                "relative_improvement": float(relative[selected].mean()),
            }
        )
    return rows


def analyze(variant_dir: Path, share_days: int, min_cells: int, screen_on: str = "past") -> tuple[dict[str, float], list[dict[str, Any]]]:
    arrays = load_arrays(variant_dir)
    days = arrays["residual"].shape[1]
    if not 0 < share_days < days:
        raise ValueError(f"share-days must be inside (0, {days}), got {share_days}")
    screen = slice(0, share_days)
    evaluate = slice(share_days, days)
    # "eval" screens on the window it predicts: an oracle bound, not a usable rule
    screen_slice = screen if screen_on == "past" else evaluate

    shares = structure_shares(arrays["residual"][:, screen_slice], arrays["observed"][:, screen_slice])
    gains = improvement(arrays, evaluate)
    # a series needs enough observed cells on both sides for the split to mean anything
    keep = (arrays["observed"][:, screen_slice].sum(axis=(1, 2)) >= min_cells) & (gains["observed_cells"] >= min_cells)

    metrics: dict[str, float] = {
        "n_series": float(len(keep)),
        "n_series_kept": float(keep.sum()),
        "share_days": float(share_days),
        "eval_days": float(days - share_days),
    }
    for name in ("hour_share", "day_share", "rest_share"):
        metrics[f"screen_{name}_mean"] = float(shares[name][keep].mean())
    relative = gains["relative_improvement"][keep]
    metrics["relative_improvement_mean"] = float(relative.mean())
    metrics["worse_series_fraction"] = float((relative < 0).mean())

    for name in ("hour_share", "day_share", "rest_share"):
        value = safe_corr(relative, shares[name][keep])
        if value is not None:
            metrics[f"corr_relative_{name}"] = value
    for label, series in (("baseline_mae", gains["baseline_mae"][keep]), ("absolute_improvement", gains["absolute_improvement"][keep])):
        value = safe_corr(relative, series)
        if value is not None:
            metrics[f"corr_relative_{label}"] = value

    design = np.column_stack([shares[name][keep] for name in ("hour_share", "day_share", "rest_share")])
    r2, beta = regression_r2(relative, design)
    metrics["regression_r2"] = r2
    for name, value in zip(("hour_share", "day_share", "rest_share"), beta[1:]):
        metrics[f"beta_{name}"] = float(value)

    rows: list[dict[str, Any]] = []
    for name in ("hour_share", "rest_share"):
        rows.extend(quartile_rows(shares[name][keep], relative, gains["baseline_mae"][keep], name))
    return metrics, rows


def numeric_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {"runs": len(rows)}
    for key in sorted({name for row in rows for name in row if isinstance(row[name], int | float) and name != "seed"}):
        values = [float(row[key]) for row in rows if key in row]
        summary[f"{key}_mean"] = float(np.mean(values))
        summary[f"{key}_std"] = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    return summary


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="glob of variant directories holding the saved arrays")
    parser.add_argument("--share-days", type=int, required=True, help="days used for the screening window")
    parser.add_argument("--label", default="run")
    parser.add_argument("--out-dir", default="figures/2-Exp-51")
    parser.add_argument("--min-cells", type=int, default=24, help="minimum observed cells per window")
    parser.add_argument("--screen-on", choices=["past", "eval"], default="past",
                        help="'past' is the usable rule; 'eval' screens on the evaluation window itself as an oracle bound")
    args = parser.parse_args()

    directories = sorted(Path(path) for path in glob(args.run_dir))
    if not directories:
        raise FileNotFoundError(f"no directory matched {args.run_dir}")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    quartiles: list[dict[str, Any]] = []
    for directory in directories:
        metrics, quartile = analyze(directory, args.share_days, args.min_cells, args.screen_on)
        seed = seed_of(directory)
        rows.append({"label": args.label, "seed": seed, **metrics})
        quartiles.extend({"label": args.label, "seed": seed, **row} for row in quartile)
        print(f"{args.label} seed {seed}: corr(rel, hour) {metrics.get('corr_relative_hour_share', float('nan')):+.3f}, "
              f"corr(rel, rest) {metrics.get('corr_relative_rest_share', float('nan')):+.3f}, R2 {metrics['regression_r2']:.3f}")

    summary = {
        "label": args.label,
        "screening": f"empirical residual variance split, window={args.screen_on}, share_days={args.share_days}, no model output",
        "evaluation": "relative improvement on the remaining days",
        "rows": rows,
        "aggregate": numeric_summary(rows),
    }
    (out_dir / f"{args.label}_metrics.json").write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    write_rows(out_dir / f"{args.label}_metrics_by_seed.csv", rows)
    write_rows(out_dir / f"{args.label}_quartiles.csv", quartiles)
    print(f"wrote {args.label} screening analysis to {out_dir}")


if __name__ == "__main__":
    main()
