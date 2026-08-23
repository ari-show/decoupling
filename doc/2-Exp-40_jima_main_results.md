# 2-Exp-40: JIMA 主結果の確定（epoch 延長 + early stopping、フルスケール）

作成日: 2026-08-22
対応ボード項目: JIMA-01（中心化あり/なしの主表統合）、JIMA-02（主結果系列の決定と数値統一、P0）
関連: [2-Exp-36_latent_dimension_sensitivity.md](2-Exp-36_latent_dimension_sensitivity.md)、
[2-Exp-37_hyperparameter_sensitivity.md](2-Exp-37_hyperparameter_sensitivity.md)、
[2-Exp-38_empirical_vs_nn_epochs.md](2-Exp-38_empirical_vs_nn_epochs.md)、
[2-Exp-39_future_day_empirical_vs_nn.md](2-Exp-39_future_day_empirical_vs_nn.md)、
[2-Exp-34_fullscale_empirical_and_log.md](2-Exp-34_fullscale_empirical_and_log.md)

## 背景

2026-08-22 の一連の実験（2-Exp-36〜39）は、いずれも同じ結論を指した。

| 実験 | 発見 |
|---|---|
| 2-Exp-37 | 現行 12 epoch は学習不足。20 epoch でも未収束 |
| 2-Exp-36 | 30 epoch でも best epoch が上限付近。次元差（≤0.002）より epoch 効果（-0.006）が大きい |
| 2-Exp-38 | 「窓内で empirical ANOVA 優位」は学習不足の交絡。30 epoch で NN が 5 seed 全勝 |
| 2-Exp-39 | 実データ未来日でも同様。学習量を揃えれば NN が 5 seed 全勝 |

一方、JIMA 原稿の主結果数値は未確定のままである（JIMA-02）。

- Exp-32 系（2000/500、12 epoch）: baseline 0.0721 → 0.0583
- Exp-23 系（6000/1500、test=valid、calibration あり）: 0.0697 → 0.0501
- Exp-34 系（6000/1500、train_holdout、12 epoch）: 0.0697 → 0.0516

これらはすべて 12 epoch の学習不足を抱えており、そのまま主表に使えない。
本実験は、学習量問題を early stopping で解消した上で、
主表（JIMA-01/02）に載せる数値をフルスケール設定で一括取得する。

## 実装（本 PR に含むコード変更）

residual パイプライン（`src/decoupled_ts/residual_experiments.py`）に
patience 型 early stopping を追加した（retail 側 `retail_experiments.py` と同じ仕様）。

- `train.early_stopping_patience`: selection metric が改善しない epoch がこの回数
  続いたら学習を打ち切る。0（既定）で無効 = 既存挙動と完全互換。
- `train.early_stopping_min_delta`: 改善とみなす最小差分。
- 結果に `stopped_epoch` を追加し、打ち切り位置を記録する。

これにより「best epoch が epoch 上限に張り付く」問題を、上限を大きく取った上で
patience により自動停止する形で解消する。

## 目的

1. JIMA-02: 主結果系列を「6000/1500・train_holdout・early stopping」で確定し、
   本文・表・概要の数値を統一する基礎数値を取得する。
2. JIMA-01: 中心化あり/なしの比較を同条件・5 seed で取得する。
3. raw と calibration の寄与を同一 run 内で分離する（JIMA-02 の要件）。
4. ladder の empirical 行を同条件で取得する（Exp-38/39 の学習量統制の結論と整合）。
5. 採用次元（JIMA-03 の残論点）をフルスケールで確定する。

## 実験条件

Exp-34 のフルスケール設定を基礎とする。

- dataset: FreshRetailNet、train/valid/test = 6000/1500/1500、`validation_source: train_holdout`
  （モデル選択と最終評価の分離。Exp-23 系の test=valid 問題を回避）
- residual: `series_mean`、target `baseline_residual`
- train: epochs 上限 60、`early_stopping_patience: 8`、lr 1e-3、hidden 160
- seeds: 17, 23, 31, 47, 59（5 seed。JIMA 主表要件）

| scenario | NN dims (g/d/h/u) | 位置づけ |
|---|---|---|
| `dim10` | 10/10/10/8 | 現行最終系（Exp-34 と同一） |
| `dim4` | 4/4/4/4 | 2-Exp-36 の推奨次元 |

| variant | 主表での行 |
|---|---|
| `empirical_anova_main_effects` | ladder の第一選択行（決定論的・無 bias） |
| `output_decomp_no_center` | 中心化 ablation（JIMA-01） |
| `output_decomp_centered` | **主提案（raw）** |
| `output_decomp_centered_calibrated` | 主提案 + validation MAE-grid calibration |

合計 run 数: 2 scenario × 5 seed × 4 variant = 40。

## 評価指標

| 指標 | 用途 |
|---|---|
| `corrected_cell_mae` / `corrected_cell_wape` | 主表の主指標 |
| `high_residual_top10_corrected_mae` | 外れケース行 |
| `corrected_cell_bias` | 系統誤差行 |
| `calibrated_corrected_cell_*` | calibration 行（raw と分離） |
| `best_epoch` / `stopped_epoch` | early stopping の発火確認（学習不足解消の証拠） |
| 中心化違反系（`component_*_mean_abs`） | centered / no_center の対比 |

## 事前に定める成功条件・分岐

1. **学習量問題の解消**: すべての NN run で `stopped_epoch < 60`（patience により
   自動停止）かつ `best_epoch < stopped_epoch`。これが満たされれば
   「主結果は収束後の数値」と主張できる。満たされない run があれば epoch 上限を
   引き上げて再実行する。
2. **JIMA-01**: `output_decomp_centered` が `output_decomp_no_center` を
   corrected MAE の paired 比較で 5 seed 中 4 以上上回る（Exp-32 系の再確認）。
3. **採用次元の確定**: dim4 と dim10 の corrected MAE 差が 0.001 以内なら
   軽量な dim4 を主表に採用する。0.001 を超えて dim10 が良ければ dim10 を採用し、
   Exp-36 の結論に「フルスケールでは大きめの次元が有利」と追記する。
4. **主表の構成**: 採用 scenario の 5 seed 平均 ± SD を、
   baseline / empirical / no_center / centered(raw) / centered+calibration の
   5 行で構成する。これを JIMA-02 の「統一数値」とする。

## 実行方法

smoke（ローカル CPU。early stopping の発火経路を patience=1 で確認）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-40_jima_main_results_smoke.json
```

本番（ローカル GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-40_jima_main_results_freshretailnet.json
```

## 出力

```text
runs/2-Exp-40_jima_main_results_freshretailnet/
  dim10/seed_{17,23,31,47,59}/{4 variants}/
  dim4/...
  all_results.csv / aggregate.csv / summary.json
```

## smoke 確認

2026-08-22 にローカル CPU で smoke（synthetic、epochs 6・patience 1、4 variant）を実行し、
完走と early stopping の発火経路（patience による break、`stopped_epoch` の記録）を確認した。

## 本番結果

2026-08-22 にローカル GPU（RTX 5060 Ti）で全 40 run を実行し、完走した。
baseline（`series_mean`）cell MAE は 0.06966、top10 baseline MAE は 0.27883。

### early stopping の発火状況（成功条件 1）

- **dim10: 全 NN run が上限 60 の手前で patience により停止**（stopped 23〜59、
  best epoch 15〜51）。学習量問題は解消された。
- dim4: centered の seed 23/59 が上限 60 に到達（best epoch 58 / 53）、
  no_center の seed 17 は best epoch 60 で改善が続いたまま上限到達。
  dim4 は収束の確認が 5 seed 中 2〜3 seed で不完全である。

### 主表（scenario 別、5 seed の平均 ± SD）

**dim10（10/10/10/8）**:

| 行 | corrected MAE | corrected WAPE | top10 MAE | bias |
|---|---:|---:|---:|---:|
| baseline のみ | 0.06966 | — | 0.27883 | ~0 |
| empirical ANOVA（主効果） | 0.05443 ± 0.00000 | 0.9221 | **0.17935** | **+0.0000** |
| no_center | 0.05422 ± 0.00214 | 0.9187 | 0.23057 | -0.308 |
| **centered（raw、主提案）** | **0.04828 ± 0.00032** | **0.8179** | 0.19418 | -0.263 |
| centered + calibration | 0.04878 ± 0.00031 | 0.8179 | 0.19891 | -0.266 |

**dim4（4/4/4/4）**: centered 0.04873 ± 0.00068（dim10 との差 +0.00045、dim4 1勝4敗）、
no_center 0.05866 ± 0.00614（不安定）。

### paired 比較（corrected MAE、5 seed）

| 比較 | dim10 | dim4 |
|---|---:|---:|
| centered − no_center | **-0.00594（5勝0敗）** | -0.00993（5勝0敗） |
| centered − empirical | **-0.00615（5勝0敗）** | -0.00570（5勝0敗） |

### 事前に定めた成功条件との照合

1. **学習量の解消**: dim10 は全 run で満たした。dim4 は 2〜3 run で上限到達し不完全。
2. **JIMA-01 ✓**: centered が no_center を両 scenario で 5 seed 全勝
   （dim10 で -0.00594）。中心化の効果は収束後もむしろ大きくなった。
3. **採用次元**: 事前規則 3（差 0.001 以内なら dim4）だけを見れば dim4 だが、
   規則 1（全 run の収束確認）を dim4 は満たさない。規則 1 を優先し、
   **主表は dim10（10/10/10/8）を採用**する。dim4 は「差 +0.00045 で同等」という
   頑健性確認として報告する（2-Exp-36 の「小次元で十分」はフルスケールでも
   性能面では成立するが、収束の確実性で dim10 に利がある）。
4. **主表の確定 ✓**: 上の dim10 表を JIMA-02 の統一数値とする。

### 読み取り

1. **主結果の確定値**: `series_mean` baseline 0.06966 → centered raw **0.04828 ± 0.00032**
   （改善率 **30.7%**）。従来候補（Exp-32 系 0.0583、Exp-34 系 0.0516）より明確に良く、
   seed 間 SD も ±0.0003 と小さい。12 epoch の学習不足がすべての旧数値を
   劣化させていたことが確定した。
2. **中心化あり/なし（JIMA-01）**: 収束後の no_center は 0.05422 で empirical と同水準まで
   しか到達せず、centered は -0.0059 の明確な差をつけた。「中心化は解釈のためだけでなく、
   収束後の予測性能でも有利」という強い形で主表に書ける。
3. **empirical との関係（ladder）**: centered は empirical を 5 seed 全勝（-0.0062）。
   Exp-38/39 のフルスケール版として整合。top10 は依然 empirical が最良（0.1794 vs 0.1942）で、
   無偏性も empirical のみが持つ。相補性の構図は主表にそのまま現れている。
4. **calibration は収束後には不要**: MAE-grid calibration は 10 run 中 9 run で
   α = 1.0（恒等）を選択し、MAE をわずかに悪化させた（+0.0005）。
   Exp-37（12 epoch）で見えた calibration の効果は学習不足の補償だったと解釈できる。
   主表の主数値は raw とし、calibration 行は「収束後は較正の余地がない」ことの
   証拠として載せる。
5. **残る課題は bias**: centered の bias -0.263 は収束後も残る。無 bias が必要な
   運用では、Exp-19 の bias 制約付き calibration または Exp-37 で確認した
   損失側 bias 制約（weight 0.01 で bias 半減、MAE +0.0015）を併用する。
   この trade-off は limitation として本文に明記する。

### JIMA 原稿への反映

- **主表**: 上記 dim10 表（5 行構成）を本文 Table に採用。数値の出典はすべて本実験
  （6000/1500・train_holdout・early stopping・5 seed）に統一する（JIMA-02 完了条件）。
- 中心化あり/なし比較（JIMA-01）は同表内で完結。合成データの成分相関
  （2-Exp-32/35 系の既存値）を対にして「予測性能と成分回復を別の主張として記述」する。
- 旧数値（0.0583 / 0.0516 / 0.0501）を引く既存記述はすべて本表へ差し替え、
  Exp-33/34 の empirical 比較の記述は Exp-38/39 の学習量統制版と併せて更新する。
- 次元は「10/10/10/8（感度分析 2-Exp-36 と本実験 dim4 対照により裏づけ）」と記述する。
