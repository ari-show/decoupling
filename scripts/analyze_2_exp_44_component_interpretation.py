"""Analyze output-component interpretability for 2-Exp-44.

All quantities are computed on observed cells only, from the arrays saved by a
residual sweep run with ``output.save_component_analysis_arrays`` enabled. No
model is loaded and no training happens here.

The analysis blocks follow doc/2-Exp-44_component_interpretation.md:

    A  residual variance split over the four components plus cross terms
    B  bias attribution per component and the state of the global component
    C  day component vs day-level covariates, against the empirical day effect
    D  low-rank structure of the interaction component
    E  component shares as a predictor of the per-series correction gain
    F  coupling between component amplitudes
    G  attribution on the 10% largest baseline failures
    H  hour component vs the stockout hour profile (confound, reported as is)

Usage:
    uv run python scripts/analyze_2_exp_44_component_interpretation.py \
        --run-dir runs/2-Exp-44_component_interpretation_freshretailnet/dim10 \
        --out-dir figures/2-Exp-44
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from decoupled_ts.component_analysis import (
    component_constraint_metrics,
    component_pairwise_correlations,
)


COMPONENTS = ("global", "day", "hour", "interaction")
REQUIRED_ARRAYS = (
    "global_component",
    "day_component",
    "hour_component",
    "interaction_component",
    "residual",
    "observed",
    "sales",
)
DISCOUNT_QUANTILES = (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)


def parse_seed(path: Path) -> int:
    try:
        return int(path.name.removeprefix("seed_"))
    except ValueError as exc:
        raise ValueError(f"invalid seed directory name: {path.name}") from exc


def load_arrays(variant_dir: Path) -> dict[str, Any]:
    missing = [name for name in REQUIRED_ARRAYS if not (variant_dir / f"{name}.npy").exists()]
    if missing:
        raise FileNotFoundError(
            f"{variant_dir}: missing arrays: {', '.join(missing)}; "
            "rerun with output.save_component_analysis_arrays enabled"
        )
    arrays: dict[str, Any] = {name: np.load(variant_dir / f"{name}.npy").astype(np.float64) for name in REQUIRED_ARRAYS}
    covariate_path = variant_dir / "day_covariates.npy"
    columns_path = variant_dir / "day_covariates.json"
    if covariate_path.exists() and columns_path.exists():
        arrays["day_covariates"] = np.load(covariate_path).astype(np.float64)
        arrays["day_covariate_columns"] = list(json.loads(columns_path.read_text(encoding="utf-8"))["columns"])
    return arrays


def safe_corr(left: np.ndarray, right: np.ndarray) -> float | None:
    """Pearson correlation, or None when either side is constant."""
    left = np.asarray(left, dtype=np.float64).reshape(-1)
    right = np.asarray(right, dtype=np.float64).reshape(-1)
    if left.size < 2 or left.std() <= 1e-12 or right.std() <= 1e-12:
        return None
    return float(np.corrcoef(left, right)[0, 1])


def masked_mean(values: np.ndarray, observed: np.ndarray, axis: tuple[int, ...] | int) -> np.ndarray:
    numerator = np.sum(values * observed, axis=axis)
    denominator = np.clip(np.sum(observed, axis=axis), 1.0, None)
    return numerator / denominator


def ols_r2(target: np.ndarray, design: np.ndarray) -> tuple[float, np.ndarray]:
    """R^2 and coefficients of an intercept + design least-squares fit."""
    matrix = np.column_stack([np.ones(len(design)), design])
    beta, *_ = np.linalg.lstsq(matrix, target, rcond=None)
    predicted = matrix @ beta
    total = float(np.sum((target - target.mean()) ** 2))
    return 1.0 - float(np.sum((target - predicted) ** 2)) / max(total, 1e-12), beta


def weekday_dummies(days: int) -> np.ndarray:
    """Six dummies for the day index mod 7 (not the calendar weekday)."""
    weekday = np.arange(days) % 7
    dummies = np.zeros((days, 6), dtype=np.float64)
    for level in range(6):
        dummies[weekday == level, level] = 1.0
    return dummies


def variance_split(components: dict[str, np.ndarray], residual: np.ndarray, keep: np.ndarray) -> dict[str, float]:
    """Block A: additive variance split and the cross terms it leaves over."""
    target = residual[keep]
    total = float(np.sum((target - target.mean()) ** 2))
    metrics: dict[str, float] = {}
    centered = {}
    for name, values in components.items():
        observed_values = values[keep]
        centered[name] = observed_values - observed_values.mean()
        metrics[f"ss_share_{name}"] = float(np.sum(centered[name] ** 2)) / max(total, 1e-12)
    metrics["ss_share_sum"] = float(sum(metrics[f"ss_share_{name}"] for name in components))
    names = list(components)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            metrics[f"ss_cross_{left}_{right}"] = 2.0 * float(np.sum(centered[left] * centered[right])) / max(total, 1e-12)
    predicted = sum(components.values())[keep]
    metrics["fit_r2"] = 1.0 - float(np.sum((target - predicted) ** 2)) / max(total, 1e-12)
    return metrics


def bias_attribution(
    components: dict[str, np.ndarray],
    residual: np.ndarray,
    sales: np.ndarray,
    observed: np.ndarray,
    keep: np.ndarray,
) -> dict[str, float]:
    """Block B: where the remaining prediction bias sits.

    The relative scale matches ``metrics.bias``: the signed error divided by the
    sum of absolute sales over the same cells.
    """
    denominator = max(float(np.sum(np.abs(sales[keep]))), 1e-12)
    predicted = sum(components.values())
    metrics = {"rel_bias_total": float(np.sum(predicted[keep] - residual[keep])) / denominator}
    for name, values in components.items():
        metrics[f"rel_bias_{name}"] = float(np.sum(values[keep])) / denominator
    series_global = components["global"][:, 0, 0]
    metrics["global_component_mean"] = float(series_global.mean())
    metrics["global_component_sd"] = float(series_global.std(ddof=1)) if len(series_global) > 1 else 0.0
    # series_mean residuals have mean zero per series by construction, so the
    # level role of the global component is only identifiable through the
    # mean/median gap of the residual distribution.
    series_mean = masked_mean(residual, observed, axis=(1, 2))
    series_median = np.array([np.median(residual[i][observed[i] > 0]) if (observed[i] > 0).any() else 0.0 for i in range(len(residual))])
    metrics["residual_series_mean_abs_mean"] = float(np.mean(np.abs(series_mean)))
    metrics["mean_minus_median_gap"] = float(np.mean(series_mean - series_median))
    for label, reference in (("mean", series_mean), ("median", series_median), ("gap", series_mean - series_median)):
        correlation = safe_corr(series_global, reference)
        if correlation is not None:
            metrics[f"corr_global_series_{label}"] = correlation
    return metrics


def day_covariate_response(
    day_component: np.ndarray,
    residual: np.ndarray,
    observed: np.ndarray,
    covariates: np.ndarray,
    columns: list[str],
) -> tuple[dict[str, float], np.ndarray, np.ndarray]:
    """Block C: day component and empirical day effect against covariates.

    Both targets are centered within a series, matching the centering the day
    component is trained under, and the covariates are centered the same way so
    the fit only uses within-series day-to-day movement.
    """
    series, days = day_component.shape[0], day_component.shape[1]
    estimated = day_component[:, :, 0]
    estimated = estimated - estimated.mean(axis=1, keepdims=True)
    empirical = masked_mean(residual, observed, axis=2)
    empirical = empirical - empirical.mean(axis=1, keepdims=True)
    design = np.concatenate([covariates, np.broadcast_to(weekday_dummies(days), (series, days, 6))], axis=2)
    design = design - design.mean(axis=1, keepdims=True)
    flat_design = design.reshape(-1, design.shape[2])
    r2_component, beta_component = ols_r2(estimated.reshape(-1), flat_design)
    r2_empirical, beta_empirical = ols_r2(empirical.reshape(-1), flat_design)
    metrics: dict[str, float] = {
        "day_cov_r2_component": r2_component,
        "day_cov_r2_empirical": r2_empirical,
        "sd_day_component": float(estimated.std()),
        "sd_day_empirical": float(empirical.std()),
    }
    correlation = safe_corr(estimated, empirical)
    if correlation is not None:
        metrics["corr_day_component_empirical"] = correlation
    names = [*columns, *[f"dow{level}" for level in range(6)]]
    for name, value, reference in zip(names, beta_component[1:], beta_empirical[1:]):
        metrics[f"beta_component_{name}"] = float(value)
        metrics[f"beta_empirical_{name}"] = float(reference)
    return metrics, estimated, empirical


def discount_response_rows(
    estimated: np.ndarray,
    empirical: np.ndarray,
    covariates: np.ndarray,
    columns: list[str],
    discount_column: str,
) -> list[dict[str, Any]]:
    """Per-bin response of the day component to the discount covariate.

    FreshRetailNet stores `discount` as a price ratio in [0, 1] (1.0 = no
    discount), so bins are taken on the ratio instead of a promo flag.
    """
    if discount_column not in columns:
        return []
    discount = covariates[:, :, columns.index(discount_column)]
    edges = np.unique(np.quantile(discount, DISCOUNT_QUANTILES))
    rows: list[dict[str, Any]] = []
    for index, (low, high) in enumerate(zip(edges[:-1], edges[1:])):
        last = index == len(edges) - 2
        selected = (discount >= low) & ((discount <= high) if last else (discount < high))
        if int(selected.sum()) == 0:
            continue
        rows.append(
            {
                "bin_low": float(low),
                "bin_high": float(high),
                "count": int(selected.sum()),
                "day_component_mean": float(estimated[selected].mean()),
                "empirical_day_effect_mean": float(empirical[selected].mean()),
            }
        )
    return rows


def interaction_structure(interaction: np.ndarray, hour_component: np.ndarray, observed: np.ndarray) -> dict[str, float]:
    """Block D: how close the interaction grid is to a rank-1 product."""
    singular = np.linalg.svd(interaction, compute_uv=False)
    energy = np.clip(np.sum(singular**2, axis=1), 1e-12, None)
    rank1 = (singular[:, 0] ** 2) / energy
    rank2 = np.sum(singular[:, :2] ** 2, axis=1) / energy
    metrics = {
        "interaction_rank1_share_median": float(np.median(rank1)),
        "interaction_rank1_share_mean": float(np.mean(rank1)),
        "interaction_rank2_share_median": float(np.median(rank2)),
    }
    interaction_profile = masked_mean(np.abs(interaction), observed, axis=1).mean(axis=0)
    hour_profile = np.abs(masked_mean(hour_component, observed, axis=1)).mean(axis=0)
    correlation = safe_corr(interaction_profile, hour_profile)
    if correlation is not None:
        metrics["corr_interaction_hour_profile"] = correlation
    return metrics


def series_shares(components: dict[str, np.ndarray], residual: np.ndarray, observed: np.ndarray) -> dict[str, np.ndarray]:
    """Within-series variance share of each component."""
    series_residual = masked_mean(residual, observed, axis=(1, 2))
    total = np.sum(((residual - series_residual[:, None, None]) ** 2) * observed, axis=(1, 2))
    shares = {}
    for name, values in components.items():
        series_values = masked_mean(values, observed, axis=(1, 2))
        numerator = np.sum(((values - series_values[:, None, None]) ** 2) * observed, axis=(1, 2))
        shares[name] = numerator / np.clip(total, 1e-12, None)
    return shares


def improvement_metrics(
    components: dict[str, np.ndarray],
    residual: np.ndarray,
    observed: np.ndarray,
    shares: dict[str, np.ndarray],
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """Block E: do the component shares predict where the correction helps."""
    predicted = sum(components.values())
    baseline_mae = masked_mean(np.abs(residual), observed, axis=(1, 2))
    corrected_mae = masked_mean(np.abs(residual - predicted), observed, axis=(1, 2))
    improvement = baseline_mae - corrected_mae
    relative = improvement / np.clip(baseline_mae, 1e-9, None)
    metrics: dict[str, float] = {}
    for name in components:
        for label, target in (("", improvement), ("_relative", relative)):
            correlation = safe_corr(target, shares[name])
            if correlation is not None:
                metrics[f"corr_improvement{label}_{name}_share"] = correlation
    correlation = safe_corr(improvement, baseline_mae)
    if correlation is not None:
        metrics["corr_improvement_baseline_mae"] = correlation
    rows: list[dict[str, Any]] = []
    edges = np.unique(np.quantile(shares["hour"], [0.0, 0.25, 0.5, 0.75, 1.0]))
    for index, (low, high) in enumerate(zip(edges[:-1], edges[1:])):
        last = index == len(edges) - 2
        selected = (shares["hour"] >= low) & ((shares["hour"] <= high) if last else (shares["hour"] < high))
        if int(selected.sum()) == 0:
            continue
        rows.append(
            {
                "quartile": index + 1,
                "hour_share_low": float(low),
                "hour_share_high": float(high),
                "count": int(selected.sum()),
                "baseline_mae": float(baseline_mae[selected].mean()),
                "corrected_mae": float(corrected_mae[selected].mean()),
                "relative_improvement": float(relative[selected].mean()),
            }
        )
    return metrics, rows


def amplitude_coupling(components: dict[str, np.ndarray], observed: np.ndarray) -> dict[str, float]:
    """Block F: are the component amplitudes of a series coupled."""
    day_amplitude = masked_mean(components["day"], observed, axis=2).std(axis=1)
    hour_amplitude = masked_mean(components["hour"], observed, axis=1).std(axis=1)
    interaction_amplitude = masked_mean(np.abs(components["interaction"]), observed, axis=(1, 2))
    series_global = components["global"][:, 0, 0]
    pairs = {
        "corr_amp_hour_day": (hour_amplitude, day_amplitude),
        "corr_amp_hour_interaction": (hour_amplitude, interaction_amplitude),
        "corr_amp_day_interaction": (day_amplitude, interaction_amplitude),
        "corr_global_hour_amp": (series_global, hour_amplitude),
    }
    metrics: dict[str, float] = {}
    for name, (left, right) in pairs.items():
        correlation = safe_corr(left, right)
        if correlation is not None:
            metrics[name] = correlation
    return metrics


def high_residual_attribution(
    components: dict[str, np.ndarray],
    residual: np.ndarray,
    keep: np.ndarray,
) -> dict[str, float]:
    """Block G: which component carries the correction on the worst cells."""
    threshold = float(np.quantile(np.abs(residual[keep]), 0.9))
    selected = keep & (np.abs(residual) >= threshold)
    magnitudes = {name: float(np.abs(values[selected]).mean()) for name, values in components.items()}
    total = max(sum(magnitudes.values()), 1e-12)
    metrics = {f"top10_abs_{name}": value for name, value in magnitudes.items()}
    metrics.update({f"top10_share_{name}": value / total for name, value in magnitudes.items()})
    predicted = sum(components.values())
    metrics["top10_baseline_mae"] = float(np.abs(residual[selected]).mean())
    metrics["top10_corrected_mae"] = float(np.abs(residual[selected] - predicted[selected]).mean())
    return metrics


def stockout_confound(hour_component: np.ndarray, observed: np.ndarray) -> dict[str, float]:
    """Block H: hour component against the stockout hour profile."""
    component_profile = masked_mean(hour_component, observed, axis=1)
    stockout_profile = 1.0 - observed.mean(axis=1)
    correlations = []
    for index in range(len(component_profile)):
        correlation = safe_corr(component_profile[index], stockout_profile[index])
        if correlation is not None:
            correlations.append(correlation)
    if not correlations:
        return {}
    return {
        "corr_hour_profile_stockout_median": float(np.median(correlations)),
        "corr_hour_profile_stockout_mean": float(np.mean(correlations)),
        "corr_hour_profile_stockout_series": float(len(correlations)),
    }


def analyze_variant(arrays: dict[str, Any], discount_column: str) -> tuple[dict[str, float], list[dict[str, Any]], list[dict[str, Any]]]:
    observed = arrays["observed"]
    keep = observed > 0
    residual = arrays["residual"]
    components = {name: arrays[f"{name}_component"] for name in COMPONENTS}

    metrics: dict[str, float] = {"n_series": float(len(residual)), "observed_rate": float(keep.mean())}
    metrics.update(variance_split(components, residual, keep))
    metrics.update(bias_attribution(components, residual, arrays["sales"], observed, keep))
    metrics.update(interaction_structure(components["interaction"], components["hour"], observed))
    shares = series_shares(components, residual, observed)
    for name, values in shares.items():
        metrics[f"series_share_{name}_mean"] = float(values.mean())
    improvement, quartile_rows = improvement_metrics(components, residual, observed, shares)
    metrics.update(improvement)
    metrics.update(amplitude_coupling(components, observed))
    metrics.update(high_residual_attribution(components, residual, keep))
    metrics.update(stockout_confound(components["hour"], observed))
    metrics.update(component_constraint_metrics({f"{name}_component": components[name] for name in COMPONENTS}))
    metrics.update(component_pairwise_correlations({f"{name}_component": components[name] for name in COMPONENTS}))

    discount_rows: list[dict[str, Any]] = []
    if "day_covariates" in arrays:
        covariate_metrics, estimated, empirical = day_covariate_response(
            components["day"],
            residual,
            observed,
            arrays["day_covariates"],
            arrays["day_covariate_columns"],
        )
        metrics.update(covariate_metrics)
        metrics["day_covariates_available"] = 1.0
        discount_rows = discount_response_rows(
            estimated,
            empirical,
            arrays["day_covariates"],
            arrays["day_covariate_columns"],
            discount_column,
        )
    else:
        metrics["day_covariates_available"] = 0.0
    return metrics, discount_rows, quartile_rows


def numeric_summary(rows: list[dict[str, Any]], variants: list[str]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    excluded = {"seed", "variant"}
    for variant in variants:
        selected = [row for row in rows if row["variant"] == variant]
        metrics: dict[str, Any] = {"runs": len(selected)}
        for key in sorted({key for row in selected for key in row if key not in excluded}):
            values = [float(row[key]) for row in selected if isinstance(row.get(key), int | float)]
            if not values:
                continue
            metrics[f"{key}_mean"] = float(np.mean(values))
            metrics[f"{key}_std"] = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        summary[variant] = metrics
    return summary


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="scenario directory containing seed_* directories")
    parser.add_argument("--out-dir", default="figures/2-Exp-44")
    parser.add_argument(
        "--variants",
        nargs="+",
        default=["output_decomp_no_center", "output_decomp_centered"],
    )
    parser.add_argument("--discount-column", default="discount")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    seed_dirs = sorted(run_dir.glob("seed_*"), key=parse_seed)
    if not seed_dirs:
        raise FileNotFoundError(f"no seed_* directories found under {run_dir}")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    discount_rows: list[dict[str, Any]] = []
    quartile_rows: list[dict[str, Any]] = []
    for seed_dir in seed_dirs:
        seed = parse_seed(seed_dir)
        for variant in args.variants:
            metrics, discount, quartiles = analyze_variant(load_arrays(seed_dir / variant), args.discount_column)
            rows.append({"seed": seed, "variant": variant, **metrics})
            discount_rows.extend({"seed": seed, "variant": variant, **row} for row in discount)
            quartile_rows.extend({"seed": seed, "variant": variant, **row} for row in quartiles)

    summary = {
        "run_dir": str(run_dir),
        "cells": "observed cells only (observed > 0)",
        "weekday": "day index mod 7, not the calendar weekday",
        "rows": rows,
        "aggregate": numeric_summary(rows, args.variants),
    }
    (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    write_rows(out_dir / "metrics_by_seed.csv", rows)
    write_rows(out_dir / "discount_response.csv", discount_rows)
    write_rows(out_dir / "hour_share_quartiles.csv", quartile_rows)
    print(f"wrote 2-Exp-44 analysis to {out_dir}")


if __name__ == "__main__":
    main()
