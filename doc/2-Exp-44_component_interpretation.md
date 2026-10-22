# 2-Exp-44: 主結果条件での成分解釈（分散寄与・bias 帰属・共変量応答）

作成日: 2026-10-22
対応ボード項目: 考察節の「4 成分に分けたことで初めて言えること」の確定
関連: [2-Exp-40_jima_main_results.md](2-Exp-40_jima_main_results.md)、
[2-Exp-35_freshretailnet_component_tsne.md](2-Exp-35_freshretailnet_component_tsne.md)、
[2-Exp-28_latent_vs_output_decomposition.md](2-Exp-28_latent_vs_output_decomposition.md)、
[2-Exp-19_bias_constrained_calibration.md](2-Exp-19_bias_constrained_calibration.md)

## 背景

2-Exp-40 で主表（`series_mean` baseline、6000/1500、early stopping、5 seed、dim10）は確定した。
一方、考察節で主張したい「成分を分けたことで初めて可能になった解釈」は、
現時点では 2-Exp-35（hour 成分の t-SNE とプロファイル相関）と
MAE ベースの component ablation しか根拠を持たない。

2-Exp-35 の保存アレイ（12 epoch、3 seed）を再解析した予備調査では、
ablation や t-SNE では見えない所見が複数見つかった。とくに次の 2 つは、
中心化された 4 成分があって初めて定義できる量である。

1. **残差分散の成分別寄与**: 中心化により 4 成分は出力グリッド上で直交するので、
   残差分散を加法的に分けられる。予備値（seed 17/23/31）は
   hour 0.40/0.25/0.34、interaction 0.018/0.016/0.021、day 0.007/0.006/0.006、global ≈ 0。
   **interaction の寄与が day の 2〜3 倍**であり、MAE ablation（2-Exp-40 dim10 5 seed で
   interaction Δ0.0021 ≈ day Δ0.0021）とも整合する。原稿の
   「実データでは interaction の寄与はほぼ 0」という記述は更新が必要である。
2. **残る bias の帰属**: day/hour/interaction は全グリッド上で平均ゼロに固定されるため、
   予測の bias は原理的に global 成分が担う。予備値では相対 bias 合計 −0.20/−0.17/−0.28 のうち
   global が −0.27/−0.21/−0.31 を占め、global 成分は系列間 sd 0.0013 でほぼ定数
   （−0.016/−0.013/−0.019）だった。`series_mean` 残差では系列水準は定義上ゼロなので、
   global 成分は「系列水準」ではなく L1 損失由来の共通中央値シフト
   （残差の平均 − 中央値ギャップ +0.042）に退化している。中心化なしでは各成分の bias が
   ±1.4 で打ち消し合い、帰属そのものが成立しない。

ただしこれらの予備値は 12 epoch の学習不足設定（2-Exp-37/38 で確認済み）に基づく。
2-Exp-40 は `output.save_latent_arrays: false`、`save_component_analysis_arrays` 未設定、
`save_checkpoints: false` であり、主結果条件の成分アレイが残っていない。
本実験は、主結果条件で成分アレイを保存し直し、考察節に載せる数値を確定させる。

## 実装（本 PR に含むコード変更）

1. `src/decoupled_ts/residual_experiments.py`
   - `save_latent_outputs` の `save_component_analysis_arrays` 経路に `sales` と `baseline` を追加した。
     bias の相対値と系列別改善幅を、データセットを再読み込みせずに解析できるようにするため。
   - `save_day_covariates` を追加した。`save_component_analysis_arrays` が真かつ
     テスト配列に `grid` がある場合、日次共変量を `day_covariates.npy`（`(N, days, C)`）と
     列名 `day_covariates.json` として保存する。列の決め方は既存の
     `residual_diagnostics._feature_indices` と同一の規約に従う（synthetic は
     discount/holiday/weather、FreshRetailNet は `dataset.daily_numeric_columns`）。
     既定は無効なので、既存実験の出力は変わらない。
2. `scripts/analyze_2_exp_44_component_interpretation.py`
   - 保存済みアレイだけを入力とし、下記 A〜H を seed × variant で計算して
     `metrics.json` / `metrics_by_seed.csv` / `discount_response.csv` /
     `hour_share_quartiles.csv` に書き出す。学習は行わない。

## 目的

主結果条件（2-Exp-40 dim10）で、次を 5 seed で確定する。

1. 残差分散の成分別寄与と交差項（A）。
2. bias の成分別帰属と global 成分の退化（B）。
3. day 成分の共変量応答が実測日効果に対して持つ縮小推定の性質（C）。
4. interaction 成分の低ランク性（D）。
5. 成分寄与プロファイルが系列別改善幅の事前指標になること（E）。
6. 成分振幅の粒度横断の連動（F）。
7. 高残差セルの原因帰属（G）。
8. hour 成分と欠品時間帯構造の交絡（H、限界として明記する）。

いずれも `output_decomp_centered` と `output_decomp_no_center` の対で取り、
「中心化がないと解釈が成立しない」ことを同じ指標の上で示す。

## 実験条件

2-Exp-40 のフルスケール設定をそのまま使い、scenario と variant を絞る。

- dataset: FreshRetailNet、train/valid/test = 6000/1500/1500、`validation_source: train_holdout`
- residual: `series_mean`、target `baseline_residual`
- model: dim10（10/10/10/8）、hidden 160
- train: epochs 上限 60、`early_stopping_patience: 8`、lr 1e-3
- seeds: 17, 23, 31, 47, 59
- variants: `output_decomp_centered`、`output_decomp_no_center`（主表の 2 行に対応）
- output: `save_latent_arrays: true`、`save_component_analysis_arrays: true`、
  `save_checkpoints: true`（成分差し替えによる反事実生成を後続実験で行えるようにする）

合計 run 数: 1 scenario × 5 seed × 2 variant = 10。

`empirical_anova_main_effects` と `output_decomp_centered_calibrated` は本実験では走らせない。
前者は 4 成分の latent を持たず、後者は raw の成分を変えないため、
主表の数値は 2-Exp-40 のものを引き続き使う。再現性の確認として
`corrected_cell_mae` が 2-Exp-40 の dim10 と一致することだけ照合する。

## 評価指標

| 記号 | 指標 | 定義 |
|---|---|---|
| A | `ss_share_{global,day,hour,interaction}` | 観測セル上の成分分散 / 残差分散 |
| A | `ss_cross_{pair}` | 成分対の交差項 / 残差分散（直交性の近似度） |
| A | `fit_r2` | 1 − SSE/SST（成分和に対する決定係数） |
| B | `rel_bias_total`、`rel_bias_{component}` | 観測セル上の bias を Σ&#124;sales&#124; で正規化した値 |
| B | `global_component_mean`、`global_component_sd` | global 成分の水準と系列間ばらつき |
| B | `corr_global_series_median`、`mean_minus_median_gap` | 中央値シフト退化の確認 |
| C | `day_cov_r2_component`、`day_cov_r2_empirical` | day 成分 / 実測日平均残差を共変量へ回帰した R² |
| C | `corr_day_component_empirical`、`sd_day_component`、`sd_day_empirical` | 対応と縮小率 |
| C | `beta_{covariate}` | 系列内中心化した共変量の回帰係数 |
| C | `discount_response.csv` | 割引ビンごとの day 成分と実測日効果 |
| D | `interaction_rank1_share_median`、`interaction_rank2_share_median` | 系列ごとの SVD エネルギー比 |
| D | `corr_interaction_hour_profile` | &#124;interaction&#124; と &#124;hour&#124; の時間帯プロファイル相関 |
| E | `corr_improvement_{component}_share` | 系列別改善幅と成分寄与の相関 |
| E | `hour_share_quartiles.csv` | hour 寄与四分位ごとの相対改善と baseline MAE |
| F | `corr_amp_hour_day`、`corr_amp_hour_interaction`、`corr_global_hour_amp` | 成分振幅の連動 |
| G | `top10_share_{component}`、`top10_baseline_mae`、`top10_corrected_mae` | 高残差セルの帰属 |
| H | `corr_hour_profile_stockout_median` | hour 成分と欠品率の時間帯プロファイル相関 |
| 検証 | `day_center_abs_mean` 等 4 指標、`component_corr_*` | 既存 `component_analysis` の制約・相関指標 |

`series_mean` 残差は観測セル平均がゼロなので、`rel_bias_total` は 4 成分の
`rel_bias_*` の和に一致する。B の帰属はこの恒等式の内訳を見ていることになる。

## 事前に定める成功条件・分岐

1. **再現性**: `output_decomp_centered` の `corrected_cell_mae` 5 seed 平均が
   2-Exp-40 dim10 の 0.04828 ± 0.00032 と ±0.0005 以内で一致する。
   外れる場合は保存フラグ以外の差分を疑い、config を再照合する。
2. **A の方向**: centered で hour 寄与が最大、かつ interaction 寄与 > day 寄与が 5 seed 中 4 以上。
   満たせば「interaction は day より大きい」と考察に書く。逆転する seed が 2 以上なら
   「interaction と day は同程度」という弱い表現に落とす。
3. **B の局在**: centered で `rel_bias_global` が `rel_bias_total` と同符号で、
   その絶対値が他 3 成分の絶対値の和を上回る seed が 5 中 4 以上。
   かつ `global_component_sd` < `|global_component_mean|` / 5。
   満たせば「残る bias は global ヘッドに局在した定数」と書き、
   対策として global ヘッドのみへの bias 制約（2-Exp-19 の一般化）を future work に挙げる。
4. **C の縮小推定**: centered で `corr_day_component_empirical` ≥ 0.80 かつ
   `day_cov_r2_component` > `day_cov_r2_empirical` が 5 seed 中 4 以上。
   no_center で `corr_day_component_empirical` < 0.3 となることも併せて示す
   （no_center は R² だけ高く出るため、R² 単独では判定しない）。
5. **D の低ランク性**: centered の `interaction_rank1_share_median` ≥ 0.90 が 5 seed すべて。
   満たせば修論の低ランク化（u = w(day feats) × shape(hour)）の根拠として引用する。
6. **E の事前指標**: centered で `corr_improvement_hour_share` ≥ 0.4 が 5 seed 中 4 以上、
   かつ hour 寄与の第 4 四分位の相対改善が第 1 四分位を上回る。
7. H は閾値を置かない。符号と大きさを限界として記述するためだけに取る。

上の 1〜6 のうち 2 つ以上が崩れた場合は、予備値が 12 epoch 固有だったと判断し、
考察節は 2-Exp-35 由来の記述を使わず、本実験で成立した項目だけに絞る。

## 実行方法

smoke（ローカル CPU、synthetic。保存経路と解析スクリプトの入出力確認）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-44_component_interpretation_smoke.json
uv run python scripts/analyze_2_exp_44_component_interpretation.py \
  --run-dir runs/2-Exp-44_component_interpretation_smoke/dim4 \
  --out-dir figures/2-Exp-44-smoke
```

本番（ローカル GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-44_component_interpretation_freshretailnet.json
uv run python scripts/analyze_2_exp_44_component_interpretation.py \
  --run-dir runs/2-Exp-44_component_interpretation_freshretailnet/dim10 \
  --out-dir figures/2-Exp-44
```

2-Exp-40 の全 40 run が RTX 5060 Ti で約 17 分（centered 1 run の学習が約 40 秒）だったので、
本実験 10 run の学習は 5 分程度、保存容量は約 0.6 GB を見込む。

## 出力

```text
runs/2-Exp-44_component_interpretation_freshretailnet/
  dim10/seed_{17,23,31,47,59}/output_decomp_{centered,no_center}/
    metrics.json
    z_{global,day,hour,interaction}.npy
    {global,day,hour,interaction}_component.npy
    residual.npy / observed.npy / sales.npy / baseline.npy / static_ids.npy
    day_covariates.npy / day_covariates.json
    best.pt
  all_results.csv / aggregate.csv / summary.json

figures/2-Exp-44/
  metrics.json / metrics_by_seed.csv / discount_response.csv / hour_share_quartiles.csv
```

## 解釈上の制約

- 保証されるのは出力 4 成分の担当範囲であり、潜在ベクトルの識別ではない。
  実データの既存 probe（2-Exp-39）は `z_hour → hour` 0.045〜0.092（24 クラス）、
  `z_day → weekday` 0.21〜0.28（7 クラス）と弱く、潜在単体の解釈は主張しない。
- 曜日は実カレンダーではなく系列内の日インデックス `mod 7`
  （`data.py: _time_features`）である。全系列が同一期間なら一貫した群だが、
  曜日ラベルの対応は未確定として扱う。
- `discount` は 0〜1 の価格比（中位数 0.976、1.0 = 割引なし、非ゼロが 99.6%）であり、
  販促日の二値指標ではない。ビンまたは連続値で扱う。
- 中心化は全グリッド上で定義され、評価は観測セル上で行うため、
  観測セルに限ると day/hour/interaction の平均は厳密にはゼロにならない
  （予備値では hour が +0.06〜+0.10。夜間の負値セルが欠品でマスクされるため）。
  A の交差項と B の各成分 bias は、このずれの大きさとしても読む。
- H のとおり hour 成分は営業時間帯・欠品の時間構造と強く対応する。
  「時間帯需要の抽出」と「検閲構造の反映」は実データでは分離できない。

## smoke 確認

2026-10-22 にローカル（synthetic、14 日 × 24 時間、test 19 系列、6 epoch、patience 1、
device=cuda）で smoke を実行し、次を確認した。

- 2 variant が完走し、`sales/baseline/residual/observed/static_ids`、4 成分、
  4 latent、`day_covariates.npy`（`(19, 14, 3)`）と
  `day_covariates.json`（`discount/holiday/weather`）、`best.pt` が保存された。
  1 variant あたり 452 KB。
- 解析スクリプトが A〜H のすべてを出力し、`metrics.json` /
  `metrics_by_seed.csv` / `discount_response.csv` / `hour_share_quartiles.csv` を書いた
  （`figures/2-Exp-44-smoke/`）。
- 恒等式と制約の確認: centered は `rel_bias_total` −0.0393 に対し
  `rel_bias_global` −0.0393、day/hour は ±0.0001、4 つの中心化違反量が 0。
  no_center は `day_center_abs_mean` 0.0395 で、bias が成分間に散った。
- 6 epoch・19 系列のため指標値そのものは評価に使わない（`fit_r2` は centered 0.041、
  no_center −0.026）。本番の 5 seed 判定とは分ける。

## 本番結果

（実行後に追記）
