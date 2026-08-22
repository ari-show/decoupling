# 2-Exp-37: 主結果条件のハイパーパラメータ感度分析

作成日: 2026-08-22
対応ボード項目: JIMA-02 支援（主結果系列の決定と数値統一）
関連: [2-Exp-36_to_40_parallel_plan.md](2-Exp-36_to_40_parallel_plan.md)、
[2-Exp-36_latent_dimension_sensitivity.md](2-Exp-36_latent_dimension_sensitivity.md)（次元は別実験）、
[2-Exp-18_calibration_shrinkage.md](2-Exp-18_calibration_shrinkage.md)、
[2-Exp-19_bias_constrained_calibration.md](2-Exp-19_bias_constrained_calibration.md)

## 背景

JIMA の主結果候補である `output_decomp_centered` × `series_mean` residual の
学習ハイパーパラメータ（lr 1e-3、12 epoch、bias 制約 weight 0 など）は、
これまで一度も感度を確認していない初期設定のままである。

また、JIMA-02 では次の不整合が未解決である。

- Exp-32 系: baseline 0.0721 → 補正後 0.0583（calibration なし）
- Exp-23 系: baseline 0.0697 → raw 補正後 0.0501、calibration 後 0.0534

主結果をどちらの系列に置くにしても、「その数値が HP の偶然の選択に依存していないか」
「raw と calibration の寄与が分離されているか」を示せると、主結果の頑健性の主張が立つ。

本実験の目的は**最良 HP の探索ではない**。主張は逆で、
「主結果は HP の妥当な範囲の変動に対して安定である」ことを示すことにある。
したがってグリッド全探索はせず、base 設定から 1 軸ずつ動かす one-axis-at-a-time 感度に限定する。

## 目的と仮説

仮説:

```text
主結果条件の corrected MAE は、学習率・epoch 数・bias 制約 weight・
decouple weight の妥当な変動範囲に対して、中心化あり/なしの効果差
（約 0.005）より十分小さい幅でしか変動しない。
```

成立すれば「主結果は HP チューニングの産物ではない」と appendix 1 表で主張できる。
成立しない軸があれば、その軸は主結果の前提条件として本文に明記する
（隠すのではなく、感度がある軸を特定できたこと自体が成果）。

## 実験条件

### base 設定

2-Exp-32 の FreshRetailNet 設定（train/valid/test = 2000/500/500、
`output_decomp_centered`、8/8/8/6 次元、12 epoch、lr 1e-3）。
次元の感度は 2-Exp-36 が担当するため、本実験では動かさない。

### 感度軸（one-axis-at-a-time）

| scenario | 変更点 | 意図 |
|---|---|---|
| `base` | なし | 参照 |
| `lr_low` | lr 1e-3 → 5e-4 | 学習率の下方向 |
| `lr_high` | lr 1e-3 → 2e-3 | 学習率の上方向 |
| `epochs_short` | 12 → 8 epoch | 学習量の下方向 |
| `epochs_long` | 12 → 20 epoch | 学習量の上方向（過学習・selection の挙動確認） |
| `bias_w_small` | residual_bias_weight 0 → 0.01 | bias 制約の導入（2-Exp-28 で残った bias への対応候補） |
| `bias_w_large` | residual_bias_weight 0 → 0.1 | bias 制約を強めた場合の MAE への影響 |
| `decouple_off` | decouple_weight 0.01 → 0 | decouple penalty の寄与確認 |
| `with_calibration` | calibration（`validation_mae_grid`）を有効化 | raw と calibration の寄与分離（JIMA-02 対応） |

- seeds: 17, 23, 31（3 seed。方向性確認が目的のため 5 seed は使わない）
- 合計 run 数: 9 scenario × 3 seed = 27

`with_calibration` は 2-Exp-18/19 で使用した `validation_mae_grid` モード
（alpha grid 0.0〜1.2、bias_estimator median、clip 0.995）をそのまま使う。

## 評価指標

| 指標 | 見る理由 |
|---|---|
| `corrected_cell_mae` / `corrected_cell_wape` | 主性能の変動幅 |
| `high_residual_top10_corrected_mae` | 外れケース補正の変動 |
| `corrected_cell_bias` | 特に `bias_w_*` 系で MAE との trade-off を見る |
| seed 間の標準偏差 | HP 変動と seed 変動の大小比較 |
| best epoch | `epochs_*` 系で selection の挙動確認 |

## 事前に定める成功条件

1. 全 27 run が完走する。
2. 安定性の判定基準: 各 scenario の corrected MAE（3 seed 平均）と base との差が
   **±0.0025 以内**（中心化効果 0.005 の半分）なら「その軸に対して安定」とする。
3. `bias_w_*` は corrected bias の改善幅と MAE の悪化幅を併記し、
   「bias 制約は損失側でも入れられるが、主結果には含めない」判断の根拠とする。
4. `with_calibration` は raw との対比表を作り、JIMA-02 の
   「raw 提案モデルと後処理 calibration の寄与を分離」に引き渡す。

## 実行方法

smoke（ローカル CPU、入出力確認のみ）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-37_hp_sensitivity_smoke.json
```

本番（GPU、2-Exp-36 の後にキュー投入）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-37_hp_sensitivity_freshretailnet.json
```

## 出力

```text
runs/2-Exp-37_hp_sensitivity_freshretailnet/
  base/seed_17 ... base/seed_31
  lr_low/... lr_high/...
  epochs_short/... epochs_long/...
  bias_w_small/... bias_w_large/...
  decouple_off/...
  with_calibration/...
  all_results.csv    （scenario × seed × 全指標）
  aggregate.csv      （scenario ごとの mean/std）
  summary.json
```

## smoke 確認

2026-08-22 にローカル CPU で smoke（synthetic、1 epoch、seed 17、
scenario は base / lr_low / bias_w_large / with_calibration の 4 条件）を実行し、次を確認した。

- 4 scenario すべてが完走し、`all_results.csv` に 4 行が出力された。
- scenario override が実際に反映されている
  （`lr_low_seed_17_config.json` の lr が 0.0005 になっていることを確認）。
- `with_calibration` では experiments リストの置き換えが機能し、
  variant 名 `output_decomp_centered_calibrated` で calibration が実行された
  （metrics に `calibrated_calibration_alpha` などの calibration 指標が出力されることを確認）。

1 epoch の smoke のため、性能値の解釈には使わない。入出力と override 機構の確認用である。

## 本番結果

2026-08-22 にローカル GPU（RTX 5060 Ti）で全 27 run（9 scenario × 3 seed）を実行し、完走した。
baseline（`series_mean`）cell MAE は 0.072146。

### scenario 別集計（3 seed の平均 ± SD）

| scenario | corrected MAE | base との差 | 判定（±0.0025） | corrected bias | top10 MAE | best epoch |
|---|---:|---:|---|---:|---:|---:|
| `base` | 0.05881 ± 0.00120 | — | — | -0.175 ± 0.162 | 0.2528 | 12.0 |
| `lr_low` | 0.06223 ± 0.00133 | +0.00341 | **感度あり** | -0.254 | 0.2805 | 11.7 |
| `lr_high` | 0.05700 ± 0.00123 | -0.00182 | 安定 | -0.358 | 0.2490 | 11.3 |
| `epochs_short` | 0.06358 ± 0.00192 | +0.00476 | **感度あり** | -0.303 | 0.2818 | 7.7 |
| `epochs_long` | 0.05574 ± 0.00194 | -0.00307 | **感度あり（改善方向）** | -0.176 | **0.2276** | 19.7 |
| `bias_w_small` | 0.06028 ± 0.00248 | +0.00146 | 安定 | **-0.090** | 0.2471 | 11.7 |
| `bias_w_large` | 0.05713 ± 0.00077 | -0.00169 | 安定 | -0.307 | 0.2522 | 12.0 |
| `decouple_off` | 0.06231 ± 0.00513 | +0.00350 | **感度あり** | -0.125 ± 0.311 | 0.2580 | 11.3 |
| `with_calibration`（raw 表示） | 0.05881 ± 0.00120 | +0.00000 | — | -0.175 | 0.2528 | 12.0 |

`with_calibration` の raw 指標は base と完全一致する（学習は同一で calibration は後処理のため）。
calibration 後の値は `calibrated_*` カラムに出力される:

| 指標 | raw（base） | calibrated |
|---|---:|---:|
| corrected MAE | 0.05881 ± 0.00120 | **0.05813 ± 0.00016** |
| corrected WAPE | 0.9505 ± 0.0194 | 0.9395 ± 0.0027 |
| corrected bias | -0.175 ± 0.162 | -0.163 ± 0.143 |
| top10 corrected MAE | 0.2528 ± 0.0176 | 0.2458 ± 0.0172 |
| 選択された alpha | — | 1.17 ± 0.06 |

### 事前に定めた成功条件との照合

仮説「主結果は HP の妥当な変動に対して ±0.0025 以内でしか変動しない」は**不成立**。
安定だったのは lr_high / bias_w_small / bias_w_large のみで、
lr_low / epochs_short / epochs_long / decouple_off は判定幅を超えた。

### 読み取り

1. **最重要: base（12 epoch）は学習不足である。**
   `epochs_long`（20 epoch）は MAE -0.0031、top10 -0.025 の明確な改善で 3 seed 全勝。
   しかも best epoch が 19.7 と上限に張り付いており、20 epoch でも収束していない。
   lr_low の悪化・lr_high の改善もこれと整合する（学習が速いほど有利）。
   感度があること自体は仮説の否定だが、方向が「改善」なので、
   **主結果の epoch 数を増やした再学習が必要**という具体的な改善点を得た。
   JIMA-02 の主結果数値の決定は、epoch を増やした設定で行うべきである。
2. **2-Exp-36 への含意**: 2-Exp-36 の「小さい次元が良い」という結果は、
   12 epoch の学習不足と交絡している可能性が高まった（大きい次元ほど収束が遅い）。
   次元感度は epoch を増やした条件で再確認する（下記 follow-up）。
3. **decouple penalty（0.01）は維持する**: 外すと MAE が悪化し、
   seed 間 SD が最大（±0.0051）になる。安定化に寄与している。
4. **bias 制約の trade-off を損失側でも確認**: `bias_w_small`（0.01）は
   corrected bias を -0.175 → -0.090 に半減させ、MAE 悪化は +0.0015 に留まる。
   一方 `bias_w_large`（0.1）は MAE は改善するが bias が悪化（-0.307）しており、
   単調な trade-off ではない。bias 制約を本採用する場合は weight 感度の追加確認が必要。
5. **calibration の寄与分離（JIMA-02 対応）**: calibration は MAE を微改善（-0.0007）し、
   seed 間 SD を 1/7 に縮小（±0.00120 → ±0.00016）する。
   「raw モデルの改善が主で、calibration は安定化に効く」と整理できる。

### Follow-up

- `epochs_long` 方向の確認として、epoch 上限をさらに引き上げた（early stopping が
  発火するまで）主結果条件の再学習を JIMA-02 の数値決定と合わせて行う。
- 2-Exp-36 の次元グリッドを epoch 増で再実行し、「小さい次元が良い」が
  学習量の交絡でないかを確認する（2-Exp-36 doc の追記を参照）。
