"""Analyze the day-masking sweep of 2-Exp-49.

Reads the sweep's ``all_results.csv`` and reports the three held-out
diagnostics per variant, the paired per-seed differences against the
no-masking control, and the pre-registered success conditions.

The empirical and shrunk-empirical columns do not depend on the trained
model, so they must be identical across variants of the same sweep; the
script checks that and fails loudly if they are not.

Usage:
    uv run --with matplotlib python scripts/analyze_2_exp_49_masked_training.py \
        --run-dir runs/2-Exp-49_masked_day_training_freshretailnet \
        --out-dir figures/2-Exp-49
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

CONTROL = "M0_no_masking"
HISTORY_DAYS = (2, 3, 5, 7, 10, 14)
# pre-registered in doc/2-Exp-49_masked_day_training.md
SUCCESS = {
    "history_k": 7,
    "min_seeds_latent_beats_shrunk": 3,
    "transfer_gain_vs_control_pct": 5.0,
    "transfer_min_win_rate": 0.97,
    "hidden_day_min_corr": 0.30,
    "max_corrected_mae_regression_pct": 3.0,
}


def load_results(run_dir: Path) -> pd.DataFrame:
    path = run_dir / "all_results.csv"
    if not path.exists():
        raise SystemExit(f"missing {path}; run the sweep first")
    return pd.read_csv(path)


def available_history_days(df: pd.DataFrame) -> list[int]:
    return [k for k in HISTORY_DAYS if f"maskdiag_history{k}_latent_r2" in df.columns]


def check_model_free_columns(df: pd.DataFrame) -> list[str]:
    """Empirical baselines must not vary across variants within a seed."""
    problems = []
    for k in available_history_days(df):
        for column in (f"maskdiag_history{k}_empirical_r2", f"maskdiag_history{k}_empirical_shrunk_r2"):
            spread = df.groupby("seed")[column].nunique()
            if (spread > 1).any():
                problems.append(column)
    return problems


def summary_table(df: pd.DataFrame) -> pd.DataFrame:
    columns = [c for c in df.columns if c.startswith("maskdiag_") and not c.endswith("_series")]
    grouped = df.groupby("name")[columns]
    mean, std = grouped.mean(), grouped.std()
    table = pd.DataFrame(index=mean.index)
    for column in columns:
        table[column] = [f"{mean[column][name]:.4f} ± {std[column][name]:.4f}" for name in mean.index]
    return table


def paired_against_control(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    control = df[df.name == CONTROL].set_index("seed")
    if control.empty:
        return pd.DataFrame()
    for name, group in df.groupby("name"):
        if name == CONTROL:
            continue
        group = group.set_index("seed")
        shared = control.index.intersection(group.index)
        row: dict[str, object] = {"variant": name, "seeds": len(shared)}
        for k in available_history_days(df):
            column = f"maskdiag_history{k}_latent_r2"
            delta = group.loc[shared, column] - control.loc[shared, column]
            row[f"d_history{k}_r2"] = round(float(delta.mean()), 4)
            row[f"wins_history{k}"] = int((delta > 0).sum())
        if "maskdiag_transfer_latent_mae" in df.columns:
            delta = group.loc[shared, "maskdiag_transfer_latent_mae"] - control.loc[shared, "maskdiag_transfer_latent_mae"]
            row["d_transfer_mae"] = round(float(delta.mean()), 5)
            row["transfer_gain_vs_control_pct"] = round(
                float(-100.0 * delta.mean() / control.loc[shared, "maskdiag_transfer_latent_mae"].mean()), 2
            )
        if "maskdiag_hidden_day_corr" in df.columns:
            row["d_hidden_day_corr"] = round(
                float((group.loc[shared, "maskdiag_hidden_day_corr"] - control.loc[shared, "maskdiag_hidden_day_corr"]).mean()), 4
            )
        if "corrected_cell_mae" in df.columns:
            base = control.loc[shared, "corrected_cell_mae"].mean()
            row["corrected_mae_regression_pct"] = round(
                float(100.0 * (group.loc[shared, "corrected_cell_mae"].mean() - base) / base), 2
            )
        rows.append(row)
    return pd.DataFrame(rows)


def success_report(df: pd.DataFrame) -> dict[str, object]:
    k = SUCCESS["history_k"]
    report: dict[str, object] = {"criteria": SUCCESS, "variants": {}}
    control = df[df.name == CONTROL].set_index("seed")
    latent = f"maskdiag_history{k}_latent_r2"
    shrunk = f"maskdiag_history{k}_empirical_shrunk_r2"
    for name, group in df.groupby("name"):
        group = group.set_index("seed")
        entry: dict[str, object] = {}
        if latent in group and shrunk in group:
            beats = int((group[latent] > group[shrunk]).sum())
            entry["seeds_latent_beats_shrunk"] = beats
            entry["criterion_1_short_history"] = bool(beats >= SUCCESS["min_seeds_latent_beats_shrunk"])
        if "maskdiag_transfer_latent_mae" in group and not control.empty:
            shared = control.index.intersection(group.index)
            gain = float(
                100.0
                * (control.loc[shared, "maskdiag_transfer_latent_mae"].mean() - group.loc[shared, "maskdiag_transfer_latent_mae"].mean())
                / control.loc[shared, "maskdiag_transfer_latent_mae"].mean()
            )
            win = float(group["maskdiag_transfer_win_rate"].mean())
            entry["transfer_gain_vs_control_pct"] = round(gain, 2)
            entry["transfer_win_rate"] = round(win, 4)
            entry["criterion_2_transfer"] = bool(
                gain >= SUCCESS["transfer_gain_vs_control_pct"] and win >= SUCCESS["transfer_min_win_rate"]
            )
        if "maskdiag_hidden_day_corr" in group:
            corr = float(group["maskdiag_hidden_day_corr"].mean())
            entry["hidden_day_corr"] = round(corr, 4)
            entry["criterion_3_hidden_day"] = bool(corr >= SUCCESS["hidden_day_min_corr"])
        if "corrected_cell_mae" in group and not control.empty:
            shared = control.index.intersection(group.index)
            base = control.loc[shared, "corrected_cell_mae"].mean()
            regression = float(100.0 * (group.loc[shared, "corrected_cell_mae"].mean() - base) / base)
            entry["corrected_mae_regression_pct"] = round(regression, 2)
            entry["criterion_4_no_regression"] = bool(regression <= SUCCESS["max_corrected_mae_regression_pct"])
        report["variants"][name] = entry
    return report


def make_figure(df: pd.DataFrame, out_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    days = available_history_days(df)
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))

    ax = axes[0]
    control = df[df.name == CONTROL]
    if not control.empty and days:
        ax.plot(days, [control[f"maskdiag_history{k}_empirical_r2"].mean() for k in days], "o--",
                color="#777", label="empirical mean of the k days")
        ax.plot(days, [control[f"maskdiag_history{k}_empirical_shrunk_r2"].mean() for k in days], "s--",
                color="#2ca02c", label="empirical + optimal shrinkage")
    for name, group in df.groupby("name"):
        if days:
            ax.plot(days, [group[f"maskdiag_history{k}_latent_r2"].mean() for k in days], "^-", label=name)
    ax.set_xlabel("days of history given to the encoder")
    ax.set_ylabel("held-out-day profile $R^2$")
    ax.axhline(0.0, color="k", lw=0.6)
    ax.legend(fontsize=7)
    ax.set_title("short history")

    ax = axes[1]
    if "maskdiag_transfer_latent_mae" in df.columns:
        names = list(df.name.unique())
        means = [df[df.name == name]["maskdiag_transfer_latent_mae"].mean() for name in names]
        errors = [df[df.name == name]["maskdiag_transfer_latent_mae"].std() for name in names]
        ax.bar(range(len(names)), means, yerr=errors, color="#d62728", width=0.6)
        empirical = df["maskdiag_transfer_empirical_mae"].mean()
        ax.axhline(empirical, color="k", ls="--", lw=1)
        ax.text(0.02, empirical, "empirical transfer", fontsize=7, va="bottom")
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=20, ha="right", fontsize=7)
        ax.set_ylabel("residual cell MAE")
    ax.set_title("transfer: same product, other stores")

    ax = axes[2]
    if "maskdiag_hidden_day_corr" in df.columns:
        names = list(df.name.unique())
        hidden = [df[df.name == name]["maskdiag_hidden_day_corr"].mean() for name in names]
        seen = [df[df.name == name]["maskdiag_seen_day_corr"].mean() for name in names]
        index = np.arange(len(names))
        ax.bar(index - 0.2, seen, 0.38, color="#1f77b4", label="days the encoder saw")
        ax.bar(index + 0.2, hidden, 0.38, color="#d62728", label="days hidden from it")
        ax.axhline(0.0, color="k", lw=0.8)
        ax.set_xticks(index)
        ax.set_xticklabels(names, rotation=20, ha="right", fontsize=7)
        ax.set_ylabel("corr(day component, empirical day level)")
        ax.legend(fontsize=7)
    ax.set_title("hidden-day structure")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    fig.savefig(out_path.with_suffix(".pdf"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--skip-figure", action="store_true")
    args = parser.parse_args()

    run_dir, out_dir = Path(args.run_dir), Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = load_results(run_dir)

    inconsistent = check_model_free_columns(df)
    if inconsistent:
        raise SystemExit(f"model-free baselines differ across variants: {inconsistent}")

    table = summary_table(df)
    table.to_csv(out_dir / "diagnostics_by_variant.csv")
    paired = paired_against_control(df)
    paired.to_csv(out_dir / "paired_vs_control.csv", index=False)
    report = success_report(df)
    (out_dir / "success_report.json").write_text(json.dumps(report, indent=2))
    df.to_csv(out_dir / "all_results.csv", index=False)

    pd.set_option("display.width", 250)
    print("== held-out diagnostics by variant (mean ± sd over seeds) ==")
    print(table.to_string())
    print("\n== paired difference against", CONTROL, "==")
    print(paired.to_string(index=False) if not paired.empty else "(no control variant in this sweep)")
    print("\n== pre-registered success conditions ==")
    print(json.dumps(report["variants"], indent=2))

    if not args.skip_figure:
        make_figure(df, out_dir / "masked_training_diagnostics.png")
    print(f"\nwrote {out_dir}")


if __name__ == "__main__":
    main()
