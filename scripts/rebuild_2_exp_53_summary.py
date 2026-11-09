"""Rebuild a residual-sweep summary from the per-cell summary.json files on disk.

``run_residual_sweep`` keeps every result row in memory and writes
``summary.json`` only after the last cell finishes, so an interrupted sweep
leaves no sweep-level summary even though each cell already wrote its own
``<scenario>/seed_<n>/summary.json``.

This script stitches those per-cell files back into the same structure
(``seeds`` / ``results`` / ``aggregate``) using the sweep's own ``_mean_std``,
so the rebuilt tables are identical to what an uninterrupted run would emit.

Rebuilding from disk also keeps the metric tables and the saved component
arrays consistent: both then come from the same training run of each cell.

Usage:
    uv run python scripts/rebuild_2_exp_53_summary.py \
        --run-dir runs/2-Exp-53_baseline_diagnosis_freshretailnet \
        --scenarios series_mean recent_hour_d7 recent_hour_d1 cycle7_hour \
        --seeds 17 23 31 47 59 \
        --out summary.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from decoupled_ts.experiment_logging import write_json
from decoupled_ts.residual_sweeps import _mean_std, _write_csv


def collect(run_dir: Path, scenarios: list[str], seeds: list[int],
            require_complete: bool) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    problems: list[str] = []
    for scenario in scenarios:
        for seed in seeds:
            cell = run_dir / scenario / f"seed_{seed}"
            path = cell / "summary.json"
            if not path.exists():
                problems.append(f"missing cell summary: {path}")
                continue
            payload = json.loads(path.read_text())
            results = payload["results"] if isinstance(payload, dict) else payload
            for row in results:
                # Flag cells whose saved arrays do not match the metric row,
                # which is what an interrupted overwrite leaves behind.
                variant_dir = cell / str(row["name"])
                if require_complete and not (variant_dir / "metrics.json").exists():
                    problems.append(
                        f"metric row present but arrays incomplete: {variant_dir}"
                    )
                rows.append({"scenario": scenario, "seed": seed, **row})
    return rows, problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--scenarios", nargs="+", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--out", default="summary.json",
                        help="file name written inside --run-dir")
    parser.add_argument("--write-csv", action="store_true",
                        help="also rewrite all_results.csv and aggregate.csv")
    parser.add_argument("--allow-incomplete", action="store_true",
                        help="do not fail when a cell's arrays are missing")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    rows, problems = collect(run_dir, args.scenarios, args.seeds,
                             require_complete=not args.allow_incomplete)

    expected = len(args.scenarios) * len(args.seeds)
    cells = {(r["scenario"], r["seed"]) for r in rows}
    print(f"cells found: {len(cells)} / {expected}    result rows: {len(rows)}")
    for p in problems:
        print(f"  PROBLEM  {p}")
    if problems and not args.allow_incomplete:
        raise SystemExit("refusing to write a summary with incomplete cells "
                         "(pass --allow-incomplete to override)")

    aggregate = _mean_std(rows)
    summary = {"seeds": args.seeds, "results": rows, "aggregate": aggregate}
    out_path = run_dir / args.out
    write_json(out_path, summary)
    print(f"wrote {out_path}  ({len(aggregate)} aggregate rows)")
    if args.write_csv:
        _write_csv(run_dir / "all_results.csv", rows)
        _write_csv(run_dir / "aggregate.csv", aggregate)
        print("wrote all_results.csv / aggregate.csv")


if __name__ == "__main__":
    main()
