"""Plot combined views of the day and interaction components for 2-Exp-47.

The two components answer different questions about the same day: the day
component is how much the whole day moves (amount), the interaction component
is how unevenly that movement is spread over the hours (shape). Combining them
is only meaningful because centering fixes which component owns which effect,
so the panels below are read together with doc/2-Exp-47_component_combination_views.md.

Inputs are the arrays written by a residual sweep with
``output.save_component_analysis_arrays`` enabled (2-Exp-44 configs). Nothing is
trained here; the figure uses one representative seed while the metrics table
covers every seed found.

Usage:
    uv run --with matplotlib python scripts/plot_2_exp_47_component_combination.py \
        --run-dir runs/2-Exp-44_component_interpretation_freshretailnet/dim10 \
        --out-dir figures/2-Exp-47
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.cluster import KMeans


REQUIRED_ARRAYS = ("day_component", "interaction_component", "observed")
EVENTS = ("holiday", "rain_top25", "promo_depth30", "activity")
EVENT_STYLE = {
    "holiday": ("holiday", "#2980b9"),
    "rain_top25": ("rain (top 25%)", "#16a085"),
    "promo_depth30": ("promo depth>0.3", "#c0392b"),
    "activity": ("activity flag", "#8e44ad"),
}
PROMO_DEPTH = 0.15
# Opening hours of the stores in this dataset; used only to orient the rank-1
# shapes consistently across series (see rank_one_factors).
DAYTIME = slice(7, 19)


def parse_seed(path: Path) -> int:
    try:
        return int(path.name.removeprefix("seed_"))
    except ValueError as exc:
        raise ValueError(f"invalid seed directory name: {path.name}") from exc


def load_arrays(variant_dir: Path) -> dict[str, Any]:
    missing = [name for name in REQUIRED_ARRAYS if not (variant_dir / f"{name}.npy").exists()]
    if not (variant_dir / "day_covariates.npy").exists():
        missing.append("day_covariates")
    if missing:
        raise FileNotFoundError(
            f"{variant_dir}: missing arrays: {', '.join(missing)}; "
            "rerun with output.save_component_analysis_arrays enabled"
        )
    arrays = {name: np.load(variant_dir / f"{name}.npy").astype(np.float64) for name in REQUIRED_ARRAYS}
    arrays["day_covariates"] = np.load(variant_dir / "day_covariates.npy").astype(np.float64)
    arrays["columns"] = list(json.loads((variant_dir / "day_covariates.json").read_text(encoding="utf-8"))["columns"])
    return arrays


def derived_fields(arrays: dict[str, Any]) -> dict[str, np.ndarray]:
    """Per (series, day) amount / shape measures and the event masks."""
    covariates, columns = arrays["day_covariates"], arrays["columns"]
    index = {name: position for position, name in enumerate(columns)}
    observed, interaction = arrays["observed"], arrays["interaction_component"]
    # `discount` is a price ratio in [0, 1] where 1.0 means no discount, so the
    # depth of the discount is its complement.
    depth = 1.0 - covariates[:, :, index["discount"]]
    rain = covariates[:, :, index["precpt"]]
    fields = {
        "day_value": arrays["day_component"][:, :, 0],
        "interaction_amplitude": np.sqrt(
            np.maximum((interaction**2 * observed).sum(axis=2) / np.clip(observed.sum(axis=2), 1.0, None), 0.0)
        ),
        "discount_depth": depth,
        "rain": rain,
        "holiday": covariates[:, :, index["holiday_flag"]] > 0.5,
        "activity": covariates[:, :, index["activity_flag"]] > 0.5,
        "promo": depth > PROMO_DEPTH,
        "promo_depth30": depth > 0.3,
        "rain_top25": rain > np.quantile(rain, 0.75),
    }
    fields["temperature"] = covariates[:, :, index["avg_temperature"]]
    return fields


def hour_profile(interaction: np.ndarray, observed: np.ndarray, day_selector: np.ndarray) -> np.ndarray:
    weights = observed * day_selector[:, :, None]
    return (interaction * weights).sum(axis=(0, 1)) / np.clip(weights.sum(axis=(0, 1)), 1.0, None)


def event_profiles(arrays: dict[str, Any], fields: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Interaction on event days minus the same profile on the remaining days."""
    interaction, observed = arrays["interaction_component"], arrays["observed"]
    profiles = {}
    for event in EVENTS:
        selected = fields[event]
        profiles[event] = hour_profile(interaction, observed, selected.astype(float)) - hour_profile(
            interaction, observed, (~selected).astype(float)
        )
    return profiles


def weekly_heatmap(arrays: dict[str, Any]) -> np.ndarray:
    """Signed interaction over (day index mod 7) x hour, not the calendar weekday."""
    interaction, observed = arrays["interaction_component"], arrays["observed"]
    series, days, hours = interaction.shape
    heatmap = np.zeros((7, hours))
    for weekday in range(7):
        selector = np.zeros(days)
        selector[np.arange(days) % 7 == weekday] = 1.0
        heatmap[weekday] = hour_profile(interaction, observed, np.broadcast_to(selector, (series, days)).astype(float))
    return heatmap


def rank_one_factors(interaction: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Leading day weights w(d) and hour shape s(h) of each series.

    ``u = w(d) * s(h)`` is unchanged when both factors flip sign, so a
    convention is needed before shapes of different series can be compared.
    Orienting by the largest absolute hour flips whenever a series' night lobe
    is marginally deeper than its daytime lobe, which splits one family into
    two mirrored halves for some seeds. Orienting by the daytime mean instead
    is stable: it puts 96-99% of series on the same side for every seed.
    """
    left, singular, right = np.linalg.svd(interaction, full_matrices=False)
    weight = left[:, :, 0] * singular[:, 0:1]
    shape = right[:, 0, :]
    daytime = shape[:, DAYTIME].mean(axis=1) if shape.shape[1] > DAYTIME.stop else shape.mean(axis=1)
    sign = np.sign(daytime)
    sign[sign == 0] = 1.0
    return weight * sign[:, None], shape * sign[:, None]


def normalize_shapes(shape: np.ndarray) -> np.ndarray:
    return shape / np.clip(np.linalg.norm(shape, axis=1, keepdims=True), 1e-9, None)


def shape_summary(normalized: np.ndarray, weight: np.ndarray) -> dict[str, float]:
    """How much the series agree on one shape, and how strongly they use it."""
    mean_shape = normalized.mean(axis=0)
    peak_hour = int(mean_shape.argmax())
    peaks = normalized.argmax(axis=1)
    return {
        "rank1_shape_peak_hour": float(peak_hour),
        "rank1_shape_frac_peak_daytime": float(((peaks >= DAYTIME.start) & (peaks < DAYTIME.stop)).mean()),
        "rank1_shape_sign_agreement_at_peak": float((normalized[:, peak_hour] > 0).mean()),
        "rank1_weight_abs_mean": float(np.abs(weight).mean()),
        "rank1_weight_abs_p90": float(np.quantile(np.abs(weight), 0.9)),
    }


def shape_clusters(normalized: np.ndarray, clusters: int, random_state: int) -> np.ndarray:
    return KMeans(n_clusters=clusters, n_init=20, random_state=random_state).fit_predict(normalized)


def safe_corr(left: np.ndarray, right: np.ndarray) -> float | None:
    left = np.asarray(left, dtype=np.float64).reshape(-1)
    right = np.asarray(right, dtype=np.float64).reshape(-1)
    if left.size < 2 or left.std() <= 1e-12 or right.std() <= 1e-12:
        return None
    return float(np.corrcoef(left, right)[0, 1])


def quadrant_shares(day_value: np.ndarray, amplitude: np.ndarray, selector: np.ndarray) -> dict[str, float]:
    """How the selected days split over the amount x shape median cross."""
    day_median, amplitude_median = np.median(day_value), np.median(amplitude)
    selected = selector.reshape(-1)
    values, amplitudes = day_value.reshape(-1)[selected], amplitude.reshape(-1)[selected]
    if values.size == 0:
        return {}
    high_day, high_amplitude = values > day_median, amplitudes > amplitude_median
    return {
        "count": float(values.size),
        "amount_up_shape_up": float((high_day & high_amplitude).mean()),
        "amount_up_shape_down": float((high_day & ~high_amplitude).mean()),
        "amount_down_shape_up": float((~high_day & high_amplitude).mean()),
        "amount_down_shape_down": float((~high_day & ~high_amplitude).mean()),
        "day_value_mean": float(values.mean()),
        "interaction_amplitude_mean": float(amplitudes.mean()),
    }


def weight_covariate_fit(weight: np.ndarray, fields: dict[str, np.ndarray]) -> dict[str, float]:
    """Regress the leading day weight on the day-level covariates, within series."""
    names = ("discount_depth", "holiday", "activity", "rain", "temperature")
    design = np.stack([np.asarray(fields[name], dtype=np.float64) for name in names], axis=2)
    design = design - design.mean(axis=1, keepdims=True)
    target = weight - weight.mean(axis=1, keepdims=True)
    matrix = np.column_stack([np.ones(design.shape[0] * design.shape[1]), design.reshape(-1, len(names))])
    beta, *_ = np.linalg.lstsq(matrix, target.reshape(-1), rcond=None)
    predicted = matrix @ beta
    flat = target.reshape(-1)
    total = float(np.sum((flat - flat.mean()) ** 2))
    metrics = {"rank1_weight_cov_r2": 1.0 - float(np.sum((flat - predicted) ** 2)) / max(total, 1e-12)}
    metrics.update({f"rank1_weight_beta_{name}": float(value) for name, value in zip(names, beta[1:])})
    return metrics


def analyze_seed(arrays: dict[str, Any], clusters: int, random_state: int) -> tuple[dict[str, float], dict[str, Any]]:
    fields = derived_fields(arrays)
    day_value, amplitude = fields["day_value"], fields["interaction_amplitude"]
    metrics: dict[str, float] = {}
    correlation = safe_corr(day_value, amplitude)
    if correlation is not None:
        metrics["corr_day_value_interaction_amplitude"] = correlation
    for name in ("discount_depth", "holiday", "activity", "rain"):
        covariate = np.asarray(fields[name], dtype=np.float64)
        for target_name, target in (("day_value", day_value), ("interaction_amplitude", amplitude)):
            correlation = safe_corr(covariate, target)
            if correlation is not None:
                metrics[f"corr_{name}_{target_name}"] = correlation
    for name, selector in (("promo", fields["promo"]), ("non_promo", ~fields["promo"]),
                           ("holiday", fields["holiday"]), ("rain_top25", fields["rain_top25"])):
        for key, value in quadrant_shares(day_value, amplitude, selector).items():
            metrics[f"quadrant_{name}_{key}"] = value

    profiles = event_profiles(arrays, fields)
    for event, profile in profiles.items():
        metrics[f"event_{event}_peak"] = float(profile.max())
        metrics[f"event_{event}_trough"] = float(profile.min())
        metrics[f"event_{event}_peak_hour"] = float(profile.argmax())
    reference = profiles["holiday"]
    for event, profile in profiles.items():
        if event == "holiday":
            continue
        correlation = safe_corr(profile, reference)
        if correlation is not None:
            metrics[f"event_{event}_corr_with_holiday"] = correlation

    weight, shape = rank_one_factors(arrays["interaction_component"])
    metrics.update(weight_covariate_fit(weight, fields))
    normalized = normalize_shapes(shape)
    metrics.update(shape_summary(normalized, weight))
    labels = order = None
    if clusters >= 2:
        labels = shape_clusters(normalized, clusters, random_state)
        order = sorted(range(clusters), key=lambda index: float(normalized[labels == index].mean(axis=0).argmax()))
        for position, cluster in enumerate(order):
            member = labels == cluster
            metrics[f"shape_group{position}_count"] = float(member.sum())
            metrics[f"shape_group{position}_peak_hour"] = float(normalized[member].mean(axis=0).argmax())
            metrics[f"shape_group{position}_mean_abs_weight"] = float(np.abs(weight[member]).mean())

    details = {
        "fields": fields,
        "profiles": profiles,
        "heatmap": weekly_heatmap(arrays),
        "normalized_shape": normalized,
        "labels": labels,
        "cluster_order": order,
        "weight": weight,
    }
    return metrics, details


def plot_panels(details: dict[str, Any], seed: int, out_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fields, profiles = details["fields"], details["profiles"]
    day_value, amplitude, promo = fields["day_value"], fields["interaction_amplitude"], fields["promo"]
    figure, axes = plt.subplots(2, 2, figsize=(11, 8))

    axis = axes[0, 0]
    axis.scatter(day_value[~promo], amplitude[~promo], s=2, alpha=0.15, color="#888888", label="non-promo")
    axis.scatter(day_value[promo], amplitude[promo], s=2, alpha=0.25, color="#c0392b",
                 label=f"promo (depth>{PROMO_DEPTH})")
    axis.axvline(np.median(day_value), color="k", lw=0.8, ls="--")
    axis.axhline(np.median(amplitude), color="k", lw=0.8, ls="--")
    axis.set_xlim(np.quantile(day_value, 0.002), np.quantile(day_value, 0.998))
    axis.set_ylim(0, np.quantile(amplitude, 0.995))
    axis.set_xlabel("day component  (amount: shift of the whole day)")
    axis.set_ylabel("interaction amplitude  (shape: how uneven the day is)")
    axis.set_title("A. amount vs shape per series-day", loc="left", fontsize=11)
    axis.legend(markerscale=4, fontsize=8, loc="upper left")

    axis = axes[0, 1]
    for event in EVENTS:
        label, color = EVENT_STYLE[event]
        axis.plot(profiles[event], label=label, color=color, lw=1.8)
    axis.axhline(0, color="k", lw=0.8)
    axis.set_xticks(range(0, 24, 3))
    axis.set_xlabel("hour")
    axis.set_ylabel("interaction, event days minus others")
    axis.set_title("B. which hours an event moves demand to", loc="left", fontsize=11)
    axis.legend(fontsize=8)

    axis = axes[1, 0]
    heatmap = details["heatmap"]
    limit = float(np.abs(heatmap).max())
    image = axis.imshow(heatmap, aspect="auto", cmap="RdBu_r", vmin=-limit, vmax=limit)
    axis.set_xticks(range(0, 24, 3))
    axis.set_yticks(range(7))
    axis.set_xlabel("hour")
    axis.set_ylabel("day index mod 7")
    axis.set_title("C. interaction over the weekly cycle", loc="left", fontsize=11)
    figure.colorbar(image, ax=axis, fraction=0.046)

    axis = axes[1, 1]
    normalized, labels, weight = details["normalized_shape"], details["labels"], details["weight"]
    hours = np.arange(normalized.shape[1])
    if labels is None:
        low, high = np.quantile(normalized, 0.1, axis=0), np.quantile(normalized, 0.9, axis=0)
        axis.fill_between(hours, low, high, color="#2980b9", alpha=0.2, label="10-90% of series")
        axis.plot(hours, normalized.mean(axis=0), lw=2, color="#2980b9", label="all series")
        strong = np.abs(weight).mean(axis=1) >= np.quantile(np.abs(weight).mean(axis=1), 0.9)
        axis.plot(hours, normalized[strong].mean(axis=0), lw=2, ls="--", color="#c0392b",
                  label=f"strongest 10% by |w| (n={int(strong.sum())})")
    else:
        for position, cluster in enumerate(details["cluster_order"]):
            member = labels == cluster
            axis.plot(
                normalized[member].mean(axis=0),
                lw=2,
                label=f"group {position} (n={int(member.sum())}, mean |w|={np.abs(weight[member]).mean():.3f})",
            )
    axis.axhline(0, color="k", lw=0.8)
    axis.set_xticks(range(0, 24, 3))
    axis.set_xlabel("hour")
    axis.set_ylabel("rank-1 shape s(h)")
    axis.set_title("D. the one shape each series redistributes along", loc="left", fontsize=11)
    axis.legend(fontsize=8)

    figure.suptitle(
        f"Combining the day and interaction components (seed {seed}, centered)",
        fontsize=12,
    )
    figure.tight_layout()
    for suffix in ("png", "pdf"):
        figure.savefig(out_dir / f"component_combination_views.{suffix}", dpi=140)
    plt.close(figure)


def numeric_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {"runs": len(rows)}
    for key in sorted({key for row in rows for key in row if key != "seed"}):
        values = [float(row[key]) for row in rows if isinstance(row.get(key), int | float)]
        if not values:
            continue
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
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="scenario directory containing seed_* directories")
    parser.add_argument("--out-dir", default="figures/2-Exp-47")
    parser.add_argument("--variant", default="output_decomp_centered")
    parser.add_argument("--representative-seed", type=int, default=17)
    parser.add_argument(
        "--shape-clusters",
        type=int,
        default=0,
        dest="clusters",
        help="split panel D into this many shape clusters; 0 (default) draws the mean shape with a 10-90%% band, "
        "which is what holds across seeds",
    )
    parser.add_argument("--random-state", type=int, default=17)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    seed_dirs = sorted(run_dir.glob("seed_*"), key=parse_seed)
    if not seed_dirs:
        raise FileNotFoundError(f"no seed_* directories found under {run_dir}")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    representative: dict[str, Any] | None = None
    for seed_dir in seed_dirs:
        seed = parse_seed(seed_dir)
        metrics, details = analyze_seed(load_arrays(seed_dir / args.variant), args.clusters, args.random_state)
        rows.append({"seed": seed, **metrics})
        if seed == args.representative_seed:
            representative = details
    if representative is None:
        available = ", ".join(str(parse_seed(path)) for path in seed_dirs)
        raise ValueError(f"representative seed {args.representative_seed} not found; available seeds: {available}")

    plot_panels(representative, args.representative_seed, out_dir)
    summary = {
        "run_dir": str(run_dir),
        "variant": args.variant,
        "representative_seed": args.representative_seed,
        "weekday": "day index mod 7, not the calendar weekday",
        "discount": "price ratio in [0, 1]; depth = 1 - ratio",
        "rows": rows,
        "aggregate": numeric_summary(rows),
    }
    (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    write_rows(out_dir / "metrics_by_seed.csv", rows)
    print(f"wrote 2-Exp-47 figure and metrics to {out_dir}")


if __name__ == "__main__":
    main()
