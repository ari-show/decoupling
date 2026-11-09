"""Analyze the cancellation ratio along the epoch axis, for 2-Exp-55.

2-Exp-55 measured ``sum|component| / |sum of components|`` at the end of
training, across budgets (60/8 ... 480/48), and found it flat at 1.7-1.8x for
the centered variant while the uncentered one moved. That left a question it
could not answer from final-epoch arrays: **when** does the uncentered
parameterization acquire its cancellation?

The hypothesis 2-Exp-55 recorded is that centering's slower convergence and its
lower cancellation ratio are the same freedom - an uncentered model can realize
a prediction as a difference of large components, so it has a wider effective
hypothesis space per unit of prediction, fits faster, and ends up with
magnitudes that say nothing. If that is right, the uncentered ratio should rise
early and stay risen. If it is flat from epoch 1, the shared-freedom reading is
not supported.

Either way this is a correlation along the epoch axis and cannot establish
cause; the doc says so.

Input is the ``cancellation_history.jsonl`` written by a run configured with
``output.cancellation_history_every``, one object per recorded epoch:

    {"epoch": n, "abs_<name>_component": ..., "abs_sum": ..., "joint": ...,
     "ratio": ...}

Usage:
    uv run python scripts/analyze_2_exp_55_cancellation_history.py \
        --run-dir <path>/2-Exp-56_centering_convergence_point_freshretailnet/dim10 \
        --seeds 17 23 31 47 59 \
        --out-dir figures/2-Exp-55
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any

COMPONENTS = ("global", "day", "hour", "interaction")
VARIANTS = {"output_decomp_centered": "centered", "output_decomp_no_center": "no_center"}


def _component_value(row: dict[str, Any], name: str) -> float | None:
    """The writer uses abs_<name>_component; accept abs_<name> as well."""
    for key in (f"abs_{name}_component", f"abs_{name}"):
        if key in row:
            return float(row[key])
    return None


def read_history(cell: Path) -> list[dict[str, Any]]:
    path = cell / "cancellation_history.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        row: dict[str, Any] = {"epoch": int(raw["epoch"]),
                               "abs_sum": float(raw["abs_sum"]),
                               "joint": float(raw["joint"]),
                               "ratio": float(raw["ratio"])}
        for name in COMPONENTS:
            value = _component_value(raw, name)
            if value is not None:
                row[f"abs_{name}"] = value
        rows.append(row)
    return sorted(rows, key=lambda r: r["epoch"])


def summarize_shape(epochs: list[int], ratios: list[float],
                    joints: list[float]) -> dict[str, Any]:
    """Describe the curve without imposing a model on it.

    The ratio has |sum of components| in its denominator, so a barely-trained
    model whose prediction is still near zero shows a large ratio for a trivial
    reason. ``joint_at_peak_over_final`` exposes that: when it is well below 1
    the peak is a small-denominator artifact, not acquired cancellation.
    """
    if not ratios:
        return {}
    peak_idx = max(range(len(ratios)), key=lambda i: ratios[i])
    first, last, peak = ratios[0], ratios[-1], ratios[peak_idx]
    span = max(ratios) - min(ratios)
    final_joint = joints[-1] if joints else float("nan")
    return {
        "joint_first_over_final": (joints[0] / final_joint) if final_joint else float("nan"),
        "joint_at_peak_over_final": (joints[peak_idx] / final_joint) if final_joint else float("nan"),
        "epoch_first": epochs[0],
        "epoch_last": epochs[-1],
        "ratio_first": first,
        "ratio_last": last,
        "ratio_peak": peak,
        "epoch_peak": epochs[peak_idx],
        "ratio_min": min(ratios),
        "ratio_span": span,
        # share of the total rise that is already present at the first record
        "front_loaded_share": (first - min(ratios)) / span if span > 0 else float("nan"),
        "rose_then_settled": bool(peak > first and peak > last),
        "monotone_rising": bool(all(b >= a - 1e-12 for a, b in zip(ratios, ratios[1:]))),
        "monotone_falling": bool(all(b <= a + 1e-12 for a, b in zip(ratios, ratios[1:]))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True,
                        help="scenario directory holding seed_* subdirectories")
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--out-dir", default="figures/2-Exp-55")
    parser.add_argument("--label", default="",
                        help="optional tag recorded in the output, e.g. 960/96")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    rows: list[dict[str, Any]] = []
    for variant, label in VARIANTS.items():
        for seed in args.seeds:
            history = read_history(run_dir / f"seed_{seed}" / variant)
            if not history:
                print(f"  no history: {run_dir / f'seed_{seed}' / variant}")
                continue
            for row in history:
                rows.append({"variant": label, "seed": seed, **row})

    if not rows:
        raise SystemExit("no cancellation_history.jsonl found")

    # aggregate across seeds at each recorded epoch
    aggregate: list[dict[str, Any]] = []
    for label in VARIANTS.values():
        sub = [r for r in rows if r["variant"] == label]
        for epoch in sorted({r["epoch"] for r in sub}):
            at = [r for r in sub if r["epoch"] == epoch]
            entry: dict[str, Any] = {"variant": label, "epoch": epoch, "runs": len(at)}
            for key in ("ratio", "abs_sum", "joint", *(f"abs_{c}" for c in COMPONENTS)):
                vals = [r[key] for r in at if key in r]
                if not vals:
                    continue
                entry[f"{key}_mean"] = statistics.mean(vals)
                entry[f"{key}_std"] = statistics.stdev(vals) if len(vals) > 1 else 0.0
            aggregate.append(entry)

    shapes: dict[str, Any] = {}
    for label in VARIANTS.values():
        curve = [e for e in aggregate if e["variant"] == label]
        shapes[label] = summarize_shape([e["epoch"] for e in curve],
                                        [e["ratio_mean"] for e in curve],
                                        [e["joint_mean"] for e in curve])

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cancellation_history.json").write_text(json.dumps(
        {"run_dir": str(run_dir), "label": args.label, "rows": rows,
         "aggregate": aggregate, "shape": shapes}, indent=1, ensure_ascii=False))
    fields = sorted({k for e in aggregate for k in e})
    with (out_dir / "cancellation_history.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(aggregate)

    for label in VARIANTS.values():
        curve = [e for e in aggregate if e["variant"] == label]
        if not curve:
            continue
        print(f"\n=== {label} ===")
        final_joint = curve[-1]["joint_mean"]
        print(f"{'epoch':>6s} {'n':>2s} {'ratio':>16s} {'S|c|':>9s} {'|Sc|':>9s} {'|Sc|/final':>10s}")
        for e in curve:
            share = e["joint_mean"] / final_joint if final_joint else float("nan")
            print(f"{e['epoch']:>6d} {e['runs']:>2d} "
                  f"{e['ratio_mean']:8.2f} ± {e['ratio_std']:5.2f} "
                  f"{e['abs_sum_mean']:9.5f} {e['joint_mean']:9.5f} {share:10.2f}")
        s = shapes[label]
        print(f"  first {s['ratio_first']:.2f} @ep{s['epoch_first']}   "
              f"peak {s['ratio_peak']:.2f} @ep{s['epoch_peak']}   "
              f"last {s['ratio_last']:.2f} @ep{s['epoch_last']}   span {s['ratio_span']:.2f}")
        print(f"  rose_then_settled={s['rose_then_settled']}  "
              f"monotone_rising={s['monotone_rising']}  "
              f"monotone_falling={s['monotone_falling']}")
        print(f"  |Sc| at peak / final = {s['joint_at_peak_over_final']:.2f}"
              f"   (well below 1 means the peak is a small-denominator artifact)")

    print(f"\nwrote cancellation history analysis to {out_dir}")


if __name__ == "__main__":
    main()
