"""Q&A figure: what the whole-period component $g_i$ can and cannot tell you.

Three panels:
  (a) distribution of the learned $g_i$ against the per-series L1-optimal value
  (b) $g_i$ against the series level $b_i$ (the baseline itself)
  (c) the mean-to-typical gap by series-level quintile, absolute and relative

The learned component is pooled over the 5 seeds of the 2-Exp-44 run; the
per-series optimal value is the median of the residual left after the day /
hour / interaction components, which is what $g_i$ would be if it minimised
MAE series by series.

Usage (from the repository root):
    uv run --with matplotlib python scripts/plot_global_component_vs_series_level.py \
        --run-dir runs/2-Exp-44_component_interpretation_freshretailnet/dim10 \
        --out figures/qa_global_component/global_component_vs_series_level.pdf --png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def iqr(values: np.ndarray) -> float:
    lo, hi = np.nanpercentile(values, [25, 75])
    return float(hi - lo)

SEEDS = (17, 23, 31, 47, 59)
VARIANT = "output_decomp_centered"
LEARNED = "#1f4e79"
IDEAL = "#c0504d"


def load_seed(seed_dir: Path) -> dict[str, np.ndarray]:
    load = lambda name: np.load(seed_dir / f"{name}.npy")  # noqa: E731
    residual = load("residual")
    observed = load("observed") > 0
    rest = load("day_component") + load("hour_component") + load("interaction_component")
    left = residual - rest
    ideal = np.array([np.median(left[i][observed[i]]) if observed[i].any() else np.nan for i in range(len(left))])
    sales = load("sales")
    return {
        "learned": load("global_component")[:, 0, 0],
        "ideal": ideal,
        "level": load("baseline")[:, 0, 0],
        "zero_rate": np.array([(sales[i][observed[i]] == 0).mean() if observed[i].any() else np.nan for i in range(len(sales))]),
    }


def quintile_medians(level: np.ndarray, values: np.ndarray, n_bins: int = 5) -> tuple[np.ndarray, np.ndarray]:
    """Median of ``values`` per level quintile.

    The median rather than the mean, because the learned component reacts only
    for the two or three busiest series in the panel and their values would
    otherwise carry the top quintile on their own.
    """
    order = np.argsort(np.argsort(level)) / len(level)
    centers, summary = [], []
    for i in range(n_bins):
        sel = (order >= i / n_bins) & (order < (i + 1) / n_bins)
        centers.append(float(np.nanmedian(level[sel])))
        summary.append(float(np.nanmedian(values[sel])))
    return np.array(centers), np.array(summary)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default="runs/2-Exp-44_component_interpretation_freshretailnet/dim10")
    parser.add_argument("--out", default="figures/qa_global_component/global_component_vs_series_level.pdf")
    parser.add_argument("--png", action="store_true", help="also write a .png next to the pdf")
    args = parser.parse_args()

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    import matplotlib.patheffects as pe

    plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.7, "pdf.fonttype": 42, "ps.fonttype": 42})
    global OUTLINE
    OUTLINE = [pe.Stroke(linewidth=3.4, foreground="white"), pe.Normal()]

    run_dir = Path(args.run_dir)
    per_seed = [load_seed(run_dir / f"seed_{seed}" / VARIANT) for seed in SEEDS]
    learned = np.concatenate([s["learned"] for s in per_seed])
    level_all = np.concatenate([s["level"] for s in per_seed])
    ideal = per_seed[0]["ideal"]
    level = per_seed[0]["level"]
    zero_rate = per_seed[0]["zero_rate"]

    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.5))

    ax = axes[0]
    bins = np.linspace(-0.09, 0.01, 70)
    ax.hist(ideal, bins=bins, color=IDEAL, alpha=0.55, label="per-series optimum")
    ax.hist(learned, bins=bins, color=LEARNED, alpha=0.75, label="learned $g_i$")
    ax.axvline(0.0, color="0.75", linewidth=0.6, zorder=0)
    ax.set_xlabel("$g_i$  (units / hour)")
    ax.set_ylabel("series count")
    ax.set_title("(a) The learned component collapses", fontsize=8.5)
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    below = int((learned < bins[0]).sum())
    ax.text(
        0.97, 0.62,
        f"IQR  learned {iqr(learned):.4f}\nIQR  optimum {iqr(ideal):.4f}\n{below} learned values off-scale",
        transform=ax.transAxes, ha="right", va="top", fontsize=7,
    )

    ax = axes[1]
    ax.axhline(0.0, color="0.75", linewidth=0.6, zorder=0)
    ax.scatter(level_all, learned, s=3, color=LEARNED, alpha=0.20, linewidths=0, label="learned $g_i$")
    ax.scatter(level, ideal, s=3, color=IDEAL, alpha=0.30, linewidths=0, label="per-series optimum")
    for values, lvl, color in ((learned, level_all, LEARNED), (ideal, level, IDEAL)):
        cx, cy = quintile_medians(lvl, values)
        ax.plot(cx, cy, color=color, linewidth=2.2, marker="o", markersize=4, path_effects=OUTLINE)
    ax.set_xscale("log")
    ax.set_xlabel("series level $b_i$  (units / hour, log)")
    ax.set_ylabel("$g_i$")
    ax.set_ylim(-0.09, 0.01)
    ax.set_title("(b) Busyness is in $b_i$, not in $g_i$", fontsize=8.5)
    ax.legend(frameon=False, fontsize=7, loc="lower left", bbox_to_anchor=(-0.02, -0.02))
    clipped = int((ideal < -0.09).sum()) + int((learned < -0.09).sum())
    ax.text(0.97, 0.97, f"{clipped} points\nbelow axis", transform=ax.transAxes, ha="right", va="top", fontsize=6.5, color="0.4")

    ax = axes[2]
    cx, abs_ideal = quintile_medians(level, ideal)
    _, abs_learned = quintile_medians(level_all, learned)
    _, rel_ideal = quintile_medians(level, ideal / np.clip(level, 1e-6, None))
    x = np.arange(len(cx))
    ax.bar(x - 0.2, -abs_ideal, width=0.4, color=IDEAL, label="optimum")
    ax.bar(x + 0.2, -abs_learned, width=0.4, color=LEARNED, label="learned")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{v:.3f}" for v in cx], fontsize=7)
    ax.set_xlabel("series-level quintile (median $b_i$)")
    ax.set_ylabel("mean-to-typical gap  $-g_i$")
    ax.set_title("(c) Absolute gap grows, relative gap shrinks", fontsize=8.5)
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    twin = ax.twinx()
    twin.plot(x, -100.0 * rel_ideal, color="0.25", linewidth=1.2, linestyle="--", marker="s", markersize=3)
    twin.set_ylabel("optimum gap as % of $b_i$", fontsize=7.5)
    twin.set_ylim(0, 70)
    twin.tick_params(labelsize=7)

    fig.tight_layout()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    if args.png:
        fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    print(f"wrote {out}")
    print(f"learned g: median {np.median(learned):+.5f} IQR {iqr(learned):.5f} range [{learned.min():.4f}, {learned.max():.4f}]")
    print(f"optimum g: median {np.nanmedian(ideal):+.5f} IQR {iqr(ideal):.5f}")
    print(f"learned below -0.05: {int((learned < -0.05).sum())} of {learned.size}")
    print(f"series level b: range [{level.min():.4f}, {level.max():.4f}]")
    print(f"zero rate: mean {np.nanmean(zero_rate):.3f}")


if __name__ == "__main__":
    main()
