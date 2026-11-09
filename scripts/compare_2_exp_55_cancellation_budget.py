"""Compare the component cancellation ratio across epoch budgets, for 2-Exp-55.

2-Exp-55 found that centering keeps the cancellation ratio
``sum|component| / |sum of components|`` near 1 while the uncentered
parameterization inflates it (up to 1477x), which is what makes centered
component magnitudes readable. That was measured at one budget (240 / 24), so it
left open whether the property survives a longer budget -- the same question
2-Exp-48 raised for the accuracy effect, which *did* turn out to be
budget-dependent.

Several earlier experiments saved component arrays at other budgets under an
otherwise identical configuration (series_mean baseline, dim10, 6000/1500
series), so the budget series can be measured without training anything.

Usage:
    uv run python scripts/compare_2_exp_55_cancellation_budget.py \
        --case 60/8:2-Exp-44:/path/to/2-Exp-44_component_interpretation_freshretailnet/dim10 \
        --case 240/24:2-Exp-48:/path/to/2-Exp-48_main_table_long_budget_freshretailnet/dim10 \
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

import numpy as np

COMPONENTS = ("global", "day", "hour", "interaction")
VARIANTS = {"output_decomp_centered": "centered", "output_decomp_no_center": "no_center"}


def cell_ratio(cell: Path) -> tuple[float, float, float]:
    observed = np.load(cell / "observed.npy").astype(bool)
    total = None
    abs_sum = 0.0
    for name in COMPONENTS:
        arr = np.load(cell / f"{name}_component.npy").astype(np.float64)
        total = arr if total is None else total + arr
        abs_sum += float(np.abs(arr[observed]).mean())
    joint = float(np.abs(total[observed]).mean())
    return abs_sum, joint, abs_sum / max(joint, 1e-12)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", required=True,
                        help="budget:source:path, e.g. 240/24:2-Exp-48:runs/.../dim10")
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--out-dir", default="figures/2-Exp-55")
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for spec in args.case:
        budget, source, path = spec.split(":", 2)
        root = Path(path)
        for variant, label in VARIANTS.items():
            for seed in args.seeds:
                cell = root / f"seed_{seed}" / variant
                if not (cell / "observed.npy").exists():
                    continue
                abs_sum, joint, ratio = cell_ratio(cell)
                rows.append({"budget": budget, "source": source, "variant": label,
                             "seed": seed, "abs_sum": abs_sum, "joint": joint,
                             "ratio": ratio})

    if not rows:
        raise SystemExit("no cells found")

    aggregate: list[dict[str, Any]] = []
    seen: list[tuple[str, str, str]] = []
    for r in rows:
        key = (r["budget"], r["source"], r["variant"])
        if key not in seen:
            seen.append(key)
    for budget, source, variant in seen:
        sub = [r for r in rows if (r["budget"], r["source"], r["variant"]) == (budget, source, variant)]
        entry: dict[str, Any] = {"budget": budget, "source": source,
                                 "variant": variant, "runs": len(sub)}
        for key in ("abs_sum", "joint", "ratio"):
            vals = [r[key] for r in sub]
            entry[f"{key}_mean"] = statistics.mean(vals)
            entry[f"{key}_std"] = statistics.stdev(vals) if len(vals) > 1 else 0.0
        aggregate.append(entry)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cancellation_budget.json").write_text(
        json.dumps({"rows": rows, "aggregate": aggregate}, indent=1, ensure_ascii=False))
    fields = sorted({k for r in aggregate for k in r})
    with (out_dir / "cancellation_budget.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(aggregate)

    print(f"{'budget':8s} {'source':9s} {'variant':10s} {'n':>2s} {'S|c|':>8s} {'|Sc|':>8s} {'cancel':>9s}")
    for e in aggregate:
        print(f"{e['budget']:8s} {e['source']:9s} {e['variant']:10s} {e['runs']:>2d} "
              f"{e['abs_sum_mean']:8.5f} {e['joint_mean']:8.5f} {e['ratio_mean']:8.1f}x")
    print(f"\nwrote cancellation budget comparison to {out_dir}")


if __name__ == "__main__":
    main()
