"""「量」「形」と共変量の対応を示す 28 日分の模式図（matplotlib 版）。

Slidev の components/QuantShapeCovFigure.vue と同じ構成:
    上段: その日の共変量（休日 = 網掛け + 灰マーカー、割引の深さ = 紫の棒）
    中段: 量 = その日の日成分 a_{i,d}（橙の棒）と、実測のみの日平均（灰点）
    下段: 形 = その日の交互作用の RMS（緑の棒）と、実測のみの RMS（灰点）

使い方:
    python quant_shape_cov_figure.py                 # 模式データで描画 → quant_shape_cov.png/.svg
    python quant_shape_cov_figure.py --csv real.csv  # 実データで描画
    python quant_shape_cov_figure.py --out fig.pdf   # 出力先を指定

CSV の列（1 系列 28 日分、1 行 1 日）:
    day, holiday(0/1), discount(0〜1), amount, amount_raw, shape, shape_raw
    amount     = day_component[i, d, 0]
    amount_raw = mean_h r[i, d, h]
    shape      = sqrt(mean_h u[i, d, h]^2)
    shape_raw  = sqrt(mean_h (r[i, d, h] - mean_h r[i, d, h])^2)
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# ---- 配色（スライドと同じ） ---------------------------------------------------
C_DAY = "#eb6834"      # 日成分 = 量
C_INTER = "#008300"    # 交互作用 = 形
C_COV = "#6250d6"      # 割引の深さ
C_HOL = "#9a9a94"      # 休日マーカー
C_HOL_BG = "#f2f2ee"   # 休日の網掛け
C_RAW = "#9a9a94"      # 実測のみ（灰点）
C_AXIS = "#b8b8b2"
C_TEXT = "#52514e"

D = 28


# ---- 模式データ（Vue 版と同じ決定的な擬似乱数） ------------------------------
def _rnd(d: int, k: int) -> float:
    x = math.sin(d * 12.9898 + k * 78.233) * 43758.5453
    return x - math.floor(x) - 0.5


def synthetic() -> dict[str, np.ndarray]:
    days = np.arange(1, D + 1)
    holiday = np.array([(d % 7 == 6) or (d % 7 == 0) for d in days], dtype=float)
    disc_map = {3: 0.30, 10: 0.25, 17: 0.35, 24: 0.20, 12: 0.10, 21: 0.12}
    discount = np.array([disc_map.get(int(d), 0.0) for d in days])
    amount = np.array([0.012 + (0.045 if holiday[i] else 0) + 0.02 * discount[i] + 0.012 * _rnd(int(d), 1)
                       for i, d in enumerate(days)])
    amount_raw = np.array([amount[i] + 0.03 * _rnd(int(d), 2) for i, d in enumerate(days)])
    shape = np.array([0.015 + 0.09 * discount[i] + (0.008 if holiday[i] else 0) + 0.006 * _rnd(int(d), 3)
                      for i, d in enumerate(days)])
    shape_raw = np.array([shape[i] + 0.025 + 0.02 * _rnd(int(d), 4) for i, d in enumerate(days)])
    return dict(day=days, holiday=holiday, discount=discount,
                amount=amount, amount_raw=amount_raw, shape=shape, shape_raw=shape_raw)


def from_csv(path: Path) -> dict[str, np.ndarray]:
    import csv
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    cols = ["day", "holiday", "discount", "amount", "amount_raw", "shape", "shape_raw"]
    return {c: np.array([float(r[c]) for r in rows]) for c in cols}


# ---- 描画 ----------------------------------------------------------------------
def draw(data: dict[str, np.ndarray], out: Path, title: str | None = None, annotate: bool = True,
         caption: str | None = "模式図：1 系列の 28 日分。相関は (系列, 日) を 1 点として、同じ日の共変量と量・形を突き合わせる") -> None:
    days = data["day"]
    hol = data["holiday"] > 0.5
    bw = 0.6

    fig, axes = plt.subplots(
        3, 1, figsize=(9.0, 4.2), sharex=True,
        gridspec_kw=dict(height_ratios=[0.9, 1.4, 1.4], hspace=0.18),
    )
    ax_cov, ax_a, ax_u = axes

    # 休日の網掛け（全行）
    for ax in axes:
        for d in days[hol]:
            ax.axvspan(d - bw / 2 - 0.08, d + bw / 2 + 0.08, color=C_HOL_BG, lw=0, zorder=0)

    # 上段: 共変量
    ax_cov.bar(days[hol], 0.2, width=bw, bottom=0.75, color=C_HOL, lw=0, zorder=2)
    ax_cov.bar(days, data["discount"] * 1.6, width=bw, color=C_COV, lw=0, zorder=2)
    ax_cov.set_ylim(0, 1.0)
    ax_cov.set_yticks([0.85, 0.25])
    ax_cov.set_yticklabels(["休日", "割引の深さ"])
    ax_cov.get_yticklabels()[1].set_color(C_COV)
    ax_cov.set_title("その日の共変量", loc="left", fontsize=9, color=C_TEXT, pad=2)

    # 中段: 量
    ax_a.bar(days, data["amount"], width=bw, color=C_DAY, lw=0, zorder=2, label="提案モデルの日成分")
    ax_a.scatter(days, data["amount_raw"], s=12, color=C_RAW, zorder=3, label="実測のみ（生の残差の日平均）")
    ax_a.set_ylabel("量\nその日の日成分", color=C_DAY, fontsize=9, rotation=0, ha="right", va="center", labelpad=6)
    if annotate:
        ax_a.text(days[-1] + 0.3, ax_a.get_ylim()[1] * 0.95, "休日の日に高い → 休日×量 +",
                  ha="right", va="top", fontsize=8.5, fontweight="bold", color=C_DAY)

    # 下段: 形
    ax_u.bar(days, data["shape"], width=bw, color=C_INTER, lw=0, zorder=2, label="提案モデルの交互作用 RMS")
    ax_u.scatter(days, data["shape_raw"], s=12, color=C_RAW, zorder=3, label="実測のみ（日平均を引いた RMS）")
    ax_u.set_ylabel("形\n交互作用の RMS", color=C_INTER, fontsize=9, rotation=0, ha="right", va="center", labelpad=6)
    if annotate:
        ax_u.text(days[-1] + 0.3, ax_u.get_ylim()[1] * 0.95, "割引の日に高い → 割引×形 +",
                  ha="right", va="top", fontsize=8.5, fontweight="bold", color=C_INTER)

    # 体裁
    for ax in axes:
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(C_AXIS)
        ax.tick_params(axis="y", length=0, labelsize=8.5, colors=C_TEXT)
        ax.tick_params(axis="x", colors=C_TEXT, labelsize=8.5)
    for ax in (ax_a, ax_u):
        ax.set_yticks([])
        ax.axhline(0, color=C_AXIS, lw=0.8, zorder=1)
    ax_u.set_xticks([1, 14, 28])
    ax_u.set_xticklabels(["1日", "14日", "28日"])
    ax_u.set_xlim(0.3, D + 0.7)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=C_DAY), plt.Rectangle((0, 0), 1, 1, color=C_INTER),
        plt.Line2D([], [], marker="o", ls="", color=C_RAW, markersize=4),
    ]
    fig.legend(handles, ["量（日成分）", "形（交互作用の RMS）", "実測のみ（生の残差から直接）"],
               loc="lower center", ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, -0.02))
    if title:
        fig.suptitle(title, fontsize=10, y=0.995)
    if caption:
        fig.text(0.5, -0.07, caption, ha="center", fontsize=8, color=C_TEXT)

    fig.savefig(out, dpi=200, bbox_inches="tight")
    if out.suffix.lower() != ".svg":
        fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path, help="実データ CSV（列は冒頭の docstring 参照）")
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("quant_shape_cov.png"))
    ap.add_argument("--title", default=None)
    ap.add_argument("--font", default="Hiragino Sans", help="日本語フォント名（macOS 既定は Hiragino Sans）")
    args = ap.parse_args()

    matplotlib.rcParams["font.family"] = args.font
    matplotlib.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["svg.fonttype"] = "none"  # SVG の文字をテキストのまま残す（Keynote で編集可）

    data = from_csv(args.csv) if args.csv else synthetic()
    draw(data, args.out, args.title)
    print(f"saved: {args.out} (+ .svg)")


if __name__ == "__main__":
    main()
