"""実データ（保存済み run + 前処理キャッシュ）から「量」「形」と共変量の 28 日図を描く。

    uv run python doc/conference/jima2026/presen-jima2026fall/fig/quant_shape_cov_real.py --series 17
    uv run python .../quant_shape_cov_real.py --series 17 --run runs/<run>/<scenario>/seed_17/output_decomp_centered \
        --cache data/freshretailnet/cache/eval_eval-target_d30_w24_f2_city_id_store_id-product_id_100.pt

前提: run ディレクトリの series 順と cache の series 順が一致していること（static_ids で照合する）。
    量         = day_component[i, d, 0]
    形         = sqrt(mean_h interaction_component[i, d, h]^2)
    実測のみ量 = mean_h residual[i, d, h]
    実測のみ形 = sqrt(mean_h (residual[i, d, h] - mean_h residual)^2)
    共変量     = x の日次チャネル（discount は価格比なので 割引の深さ = 1 - discount、holiday_flag）
リポジトリ直下で実行する（uv run）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quant_shape_cov_figure import draw  # noqa: E402

ROOT = Path(__file__).resolve().parents[5]  # リポジトリ直下
DEFAULT_RUN = ROOT / "runs/2-Exp-35_freshretailnet_component_tsne/series_mean_all/seed_17/output_decomp_centered"
DEFAULT_CACHE = ROOT / "data/freshretailnet/cache/eval_eval-target_d30_w24_f2_city_id_store_id-product_id_100.pt"
DAILY_COLS = ["discount", "holiday_flag", "activity_flag", "precpt", "avg_temperature", "avg_humidity", "avg_wind_level"]


def load(run: Path, cache: Path) -> dict[str, np.ndarray]:
    t = torch.load(cache, map_location="cpu", weights_only=False)
    x = t["x"].numpy()
    n, f, time = x.shape
    grid = x.reshape(n, f, time // 24, 24).transpose(0, 2, 3, 1)  # (N, D, H, F)
    day = grid[:, :, 0, :]
    sid_cache = t["static_ids"].numpy()
    sid_run = np.load(run / "static_ids.npy")
    if not np.array_equal(sid_run[:n], sid_cache):
        raise SystemExit("static_ids が一致しません。run と cache の series 順が違います")
    a = np.load(run / "day_component.npy")[:n]
    u = np.load(run / "interaction_component.npy")[:n]
    r = np.load(run / "residual.npy")[:n]
    return dict(
        depth=1.0 - day[:, :, 2 + DAILY_COLS.index("discount")],
        holiday=day[:, :, 2 + DAILY_COLS.index("holiday_flag")],
        amount=a[:, :, 0],
        shape=np.sqrt((u ** 2).mean(axis=2)),
        amount_raw=r.mean(axis=2),
        shape_raw=np.sqrt(((r - r.mean(axis=2, keepdims=True)) ** 2).mean(axis=2)),
        static_ids=sid_run[:n],
    )


def corr(p: np.ndarray, q: np.ndarray) -> float:
    return float(np.corrcoef(p.ravel(), q.ravel())[0, 1])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--series", type=int, default=17, help="描く系列の index（run 内の順）")
    ap.add_argument("--run", type=Path, default=DEFAULT_RUN)
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--font", default="Hiragino Sans")
    args = ap.parse_args()
    matplotlib.rcParams["font.family"] = args.font
    matplotlib.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["svg.fonttype"] = "none"

    d = load(args.run, args.cache)
    n = d["amount"].shape[0]
    print(f"series in cache: {n}")
    for name, cov in (("休日", d["holiday"]), ("割引の深さ", d["depth"])):
        print(f"  {name}: 量 {corr(cov, d['amount']):+.3f}  形 {corr(cov, d['shape']):+.3f}   "
              f"(実測のみ 量 {corr(cov, d['amount_raw']):+.3f}  形 {corr(cov, d['shape_raw']):+.3f})")

    i = args.series
    sid = d["static_ids"][i]
    days = np.arange(1, d["amount"].shape[1] + 1)
    data = dict(day=days, holiday=d["holiday"][i], discount=d["depth"][i],
                amount=d["amount"][i], amount_raw=d["amount_raw"][i], shape=d["shape"][i], shape_raw=d["shape_raw"][i])
    out = args.out or Path(__file__).with_name(f"quant_shape_cov_real_s{i}.png")
    cap = (f"実データ：store {sid[1]} × product {sid[6]}（評価系列 #{i}）の 28 日。"
           f"棒＝提案モデルの成分、灰点＝実測のみ。{args.run.parts[-4]} / {args.run.parts[-2]}")
    draw(data, out, caption=cap, annotate=False)
    print(f"saved: {out} (+ .svg)  static_ids={sid.tolist()}")


if __name__ == "__main__":
    main()
