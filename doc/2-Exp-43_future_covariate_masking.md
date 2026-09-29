# 2-Exp-43: 未来日評価における共変量マスクの影響（天候先読みの除去）

作成日: 2026-09-29
土台: [2-Exp-42_unified_architecture_ladder.md](2-Exp-42_unified_architecture_ladder.md) の未来日評価
（本ブランチは `Experiments/2-Exp-42` から派生。統一モデルの実装を使うため）
関連: [2-Exp-39_future_day_empirical_vs_nn.md](2-Exp-39_future_day_empirical_vs_nn.md)、
[proposal/formulation.md](proposal/formulation.md)

## 背景

2026-09-13 に入力特徴量の実在を確認した際、未来日評価の設定に先読みが含まれていることが判明した。

未来日評価は `residual.future_mask_days: 2` で窓末尾 2 日を未来日として扱うが、
マスク対象は `future_mask_channels: [0, 1]`、すなわち**売上と欠品フラグだけ**だった。
日次共変量（割引・休日・販促・天候）は未来日の分も入力に残っていた。

このうち、休日・曜日・時刻はカレンダーから事前に確定するので問題ない。
割引・販促は「計画値として事前に分かる」という仮定を置けば許容できる。
一方、**天候は実測値であり、予測時点では分からない**。したがって未来日に対しては
オラクル情報であり、先読みにあたる。

影響範囲は、未来日を根拠にした 2 つの主張である。

| 実験 | 主張 | 先読みの有無 |
|---|---|---|
| 2-Exp-39 | 実データの未来日でも NN は経験的 ANOVA を上回る（NN の必然性） | 現行モデルが天候を先読み |
| 2-Exp-42 | 統一アーキテクチャ（Stage B）は現行モデルを未来日で上回る | 現行モデル側のみ先読み |

なお、コードを読んだ結果、2 つのモデルで未来日の扱いが異なることも判明している。

- **現行モデル**（`output_decomposition`）: エンコーダはチャネルごとのマスクで平均を取る。
  未来日でも共変量のマスクは 1 のままなので、天候が日表現に入る。
- **統一モデル**（`unified_decomposition`）: プーリングの重みがチャネル 0 のマスク 1 本で
  全特徴量に共通してかかる。未来日は全セルが除外されるため、日表現はバイアス項のみの
  定数になり、**共変量を一切使っていない**。

つまり 2-Exp-42 の未来日比較は、先読みできた現行モデルに対して、統一モデルが
何も見ずに勝っていた可能性がある。本実験でこれを数値として確定させる。

## 目的

天候（および販促）を隠した公平な条件で、次の 2 つを測り直す。

1. NN は経験的 ANOVA を未来日で上回るか（2-Exp-39 の再検証）
2. 統一モデルは現行モデルを未来日で上回るか（2-Exp-42 の再検証）

## 実験条件

2-Exp-42 の未来日設定と完全に同一で、**変えるのは `future_mask_channels` だけ**である。

- dataset: FreshRetailNet、6000 / 1500 / 1500 系列、`validation_source: train_holdout`
- residual: `series_mean`、`future_mask_days: 2`
- model: hidden 160、dims 10/10/10/8
- train: epochs 上限 120、`early_stopping_patience: 8`、lr 1e-3
- seeds: 17, 23, 31, 47, 59

実データの入力チャネルは次の 13 本である。

| ch | 内容 | 未来日に既知か |
|---|---|---|
| 0 | 売上（残差） | 未知（常にマスク） |
| 1 | 欠品フラグ | 未知（常にマスク） |
| 2 | 割引 | 計画値なら既知 |
| 3 | 休日フラグ | 既知（カレンダー） |
| 4 | 販促フラグ | 計画値なら既知 |
| 5–8 | 降水・気温・湿度・風速 | **未知（実測値）** |
| 9–12 | 時刻 sin/cos、曜日 sin/cos | 既知（カレンダー） |

| scenario | `future_mask_channels` | 意味 |
|---|---|---|
| `mask_sales_only` | `[0, 1]` | 2-Exp-42 / 2-Exp-39 の再現（対照） |
| `mask_weather` | `[0, 1, 5, 6, 7, 8]` | 天候を隠す。**本実験の主条件** |
| `mask_weather_promo` | `[0, 1, 2, 4, 5, 6, 7, 8]` | 割引・販促も隠す。計画値既知の仮定を外した下限 |

| variant | 役割 |
|---|---|
| `empirical_anova_main_effects` | 閉形式のラダー第一段（未来日の日効果は原理的に 0） |
| `output_decomp_centered` | 現行の主提案（先読みの影響を受ける側） |
| `unified_single_decoder` | 統一モデル Stage B（主提案候補） |

統一モデルの Stage A（`unified_shared_encoder`）は主提案ではないため省略する。
合計 run 数: 3 scenario × 3 variant × 5 seed = 45。

## 事前に登録する予測（自己チェック）

結果を見る前に、実装の理解から次を予測しておく。これが崩れた場合は、
結論を述べる前に理解の誤りとして報告する。

- **P1**: `empirical_anova_main_effects` は 3 条件で**完全に同一**の数値になる。
  観測済みセルの残差しか使わず、入力共変量を参照しないため。
- **P2**: `unified_single_decoder` も 3 条件で**ほぼ同一**になる。プーリングの重みが
  チャネル 0 のマスクだけであり、未来日は元から全セル除外されているため。
  AMP による数値誤差程度の差は許容する。
- **P3**: `output_decomp_centered` は天候を隠すと未来日 MAE が**悪化する**。
  その悪化幅が天候先読みの寄与そのものである。

## 判定基準

主条件は `mask_weather` とする。

| ID | 判定 | 成立条件 |
|---|---|---|
| J1 | 2-Exp-39 の再検証 | NN のいずれかが `empirical_anova` を `future_corrected_cell_mae` の seed ごとの paired 比較で 5 seed 中 4 以上上回る |
| J2 | 2-Exp-42 の再検証 | `unified_single_decoder` が `output_decomp_centered` を同じ paired 比較で 5 seed 中 4 以上上回る |
| J3 | 仮定の下限 | `mask_weather_promo` でも J1 / J2 が維持されるか |

J1 が崩れた場合、「実データの未来日で NN が必要」という主張は天候の先読みに
依存していたことになり、2-Exp-39 の記述と原稿の該当箇所を修正する。
J2 が維持されれば、統一アーキテクチャの優位は先読みなしで成立する。

## 評価指標

| 指標 | 用途 |
|---|---|
| `future_corrected_cell_mae` | 主判定 |
| `future_baseline_cell_mae` | 参照（補正なし） |
| `future_corrected_cell_bias` | 系統誤差 |
| `future_residual_hour_profile_corr` | 未来日の時間帯構造の捕捉 |
| 窓内 `corrected_cell_mae` | マスク変更が窓内に影響しないことの確認 |
| `best_epoch` / `stopped_epoch` | 収束状況（2-Exp-42 では上限到達が残課題） |

## 実行方法

smoke（ローカル CPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-43_future_covariate_masking_smoke.json
```

本番（ローカル GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-43_future_covariate_masking_freshretailnet.json
```

smoke は合成データを使う。合成データのチャネル構成は実データと異なり
（0 売上 / 1 欠品 / 2 割引 / 3 休日 / 4 天候 / 5–8 時刻・曜日 / 9 subgroup の 10 本）、
smoke の scenario では天候を ch4、割引を ch2 として読み替えている。
smoke は入出力の確認のみに使い、性能の解釈には使わない。

## 出力

```text
runs/2-Exp-43_future_covariate_masking_freshretailnet/
  mask_sales_only/seed_{17,23,31,47,59}/{3 variants}/
  mask_weather/...
  mask_weather_promo/...
  all_results.csv / aggregate.csv / summary.json
```

## smoke 確認

（実行後に追記）

## 本番結果

（実行後に追記）
