# 2-Exp-45: 日/時間帯 Encoder の GRU vs MLP 比較

作成日: 2026-10-23
対応ボード項目: 「日成分は GRU、時間帯成分は MLP」というアーキテクチャ選択の根拠づけ
関連: [2-Exp-40_jima_main_results.md](2-Exp-40_jima_main_results.md)、
[2-Exp-36_latent_dimension_sensitivity.md](2-Exp-36_latent_dimension_sensitivity.md)、
[2-Exp-37_hyperparameter_sensitivity.md](2-Exp-37_hyperparameter_sensitivity.md)

## 背景

現行モデルの Encoder は軸ごとに異なる構造を持つ。

- `DayEncoder`: 時間帯方向に集約した日ごとの観測平均・標準偏差 → `Linear(→160)+ReLU`
  → **`GRU(160)`** → `Linear(→day_dim)`。GRU は単方向なので、日 `t` の潜在は日 `≤ t` にのみ依存する。
- `HourEncoder`: 日方向に集約した時間帯ごとの観測平均・標準偏差 → `Linear(→160)+ReLU`
  → `Linear(→hour_dim)`。各時間帯は独立に符号化され、時間帯間の文脈を持たない。

この使い分けは「日成分は日の系列なので、前日までの文脈を反映できるよう GRU を使い、
時間帯成分は周期的な形なので MLP で足りる」という設計意図に基づくが、
GRU と MLP を実際に入れ替えた比較はこれまで行っていない。
主結果（2-Exp-40）は現行構成のみで取られているため、
アーキテクチャ選択が事後的な説明に見える状態にある。本実験はその空白を埋める。

比較の見通しを良くする前提として、どちらの軸でも Encoder の入力は
**軸方向の周辺統計量**（観測平均・標準偏差）である。したがって GRU と MLP の差は
次の 2 点に限られる。

1. **軸方向の文脈混合**をするか否か（GRU は混合する、MLP は各ステップ独立）。
2. **パラメータ容量**（`GRU(160,160)` は約 154k、`Linear(160,160)` 相当の MLP は約 26k）。

1 と 2 を分離しないと「GRU が良いのは再帰のためか、単にパラメータが多いためか」が決まらない。
そこで GRU と同じパラメータ数を持ち、文脈混合をしない MLP
（`Linear(160→480)+ReLU+Linear(480→160)+ReLU`、約 154k）を対照に加える。

## 実装（本 PR に含むコード変更）

1. `src/decoupled_ts/retail_models.py`
   - `axis_marginal_stats` を追加し、日軸・時間帯軸の周辺統計量の計算を 1 箇所にまとめた
     （既存の `DayEncoder` / `HourEncoder` の式と数値的に同一）。
   - `AxisEncoder` を追加した。`proj → (mixer) → head` の構造で、`architecture` が
     `mlp`（mixer なし）/ `mlp_wide`（パラメータ整合の位置ごと MLP）/ `gru`（単方向 GRU）を選ぶ。
   - `DayEncoder` / `HourEncoder` は `AxisEncoder` の薄い派生とし、既定は現行どおり
     day=`gru`、hour=`mlp`。`DayEncoder(gru)` の `state_dict` キーは従来と同一
     （`proj.0.* / rnn.* / head.*`）だが、`HourEncoder` は `net.0/net.2` から
     `proj.0/head` に変わるため、本 PR 以前に保存した checkpoint の hour encoder は
     そのままでは読めない（`runs/` は git 管理外で、再実行で復元できる範囲）。
2. `src/decoupled_ts/residual_models.py`
   - `ResidualMultiGrainAE` と `OutputDecompositionResidualModel` に
     `day_encoder` / `hour_encoder` 引数を追加した（既定は現行構成）。
3. `src/decoupled_ts/residual_experiments.py`
   - `make_residual_model` が variant の `day_encoder` / `hour_encoder`、
     なければ `model.day_encoder` / `model.hour_encoder` を読む。既定は現行構成なので
     既存 config の挙動は変わらない。
   - 各 run の結果行に `param_count` と `train_seconds` を追加した。
     アーキテクチャ比較ではコストが判断材料になるため。
4. `tests/test_axis_encoders.py`
   - 3 アーキテクチャでステップ数が保たれること、GRU 版だけが「ある日の入力変化を
     それ以降の日の潜在に伝える」こと（MLP 版は当日だけ変わる）、
     `mlp_wide` のパラメータ数が GRU と 1% 以内で一致すること、未知の名前が
     `ValueError` になることを確認する。

## 目的

主結果条件（2-Exp-40 dim10）で、次を 5 seed の対応ありの比較として確定する。

1. 日軸の GRU は、文脈混合を持たない MLP より精度が良いか（設計意図 1 の検証）。
2. 1 の差は再帰によるものか、パラメータ容量によるものか（`mlp_wide` との比較）。
3. 時間帯軸は MLP で足りるか、GRU にすると改善するか（設計意図 2 の検証）。
4. 役割を入れ替えた構成（day=MLP, hour=GRU）が現行構成に勝たないこと。
5. 以上の差とコスト（`param_count`、`train_seconds`）の釣り合い。

## 実験条件

2-Exp-40 の dim10 設定をそのまま使い、variant だけを差し替える。

- dataset: FreshRetailNet、train/valid/test = 6000/1500/1500、`validation_source: train_holdout`
- residual: `series_mean`、target `baseline_residual`
- model: dim10（global/day/hour 10、interaction 8）、hidden 160、dropout 0.1
- loss: `decouple_weight` 0.01、成分制約・bias 制約なし
- train: epochs 上限 60、`early_stopping_patience: 8`、lr 1e-3、batch 128、`reset_seed_per_variant: true`
- seeds: 17, 23, 31, 47, 59
- calibration / swap / probes: 無効（主表 raw 行と同じ条件）
- variant はすべて `output_decomposition`、`center_components: true`、`use_interaction: true`

| variant | day encoder | hour encoder | 位置づけ |
|---|---|---|---|
| `day_gru_hour_mlp` | GRU | MLP | 現行構成（提案） |
| `day_mlp_hour_mlp` | MLP | MLP | 日軸の文脈混合を外す |
| `day_mlpwide_hour_mlp` | MLP (パラメータ整合) | MLP | 日軸の容量だけ揃えた対照 |
| `day_gru_hour_gru` | GRU | GRU | 時間帯軸にも文脈混合を入れる |
| `day_gru_hour_mlpwide` | GRU | MLP (パラメータ整合) | 時間帯軸の容量だけ揃えた対照 |
| `day_mlp_hour_gru` | MLP | GRU | 役割を入れ替えた構成 |

`reset_seed_per_variant: true` により、同じ seed では全 variant が同じ初期化・同じ
データ順から始まるので、seed 単位の対応ありの差分が取れる。
合計 run 数: 1 scenario × 5 seed × 6 variant = 30。

## 評価指標

| 指標 | 定義・役割 |
|---|---|
| `corrected_cell_mae` | 主指標。`b + r_hat` の観測セル MAE |
| `corrected_cell_wape` | 同じ予測の WAPE |
| `high_residual_top10_corrected_mae` | 残差絶対値上位 10% セルの MAE |
| `residual_r2`、`residual_mae` | 残差自体の当てはまり |
| `component_ablation_without_{day,hour,interaction}_mae_delta` | 成分を落としたときの MAE 悪化幅。アーキテクチャ変更が成分の役割分担を変えるかを見る |
| `diag_day_relative_amplitude`、`diag_hour_relative_amplitude` | 成分振幅 |
| `hour_component_residual_profile_corr` | hour 成分と実測時間帯プロファイルの対応 |
| `param_count`、`train_seconds` | コスト。`train_seconds` は 1 run 目に CUDA の初期化が乗るので、比較は同一 seed 内の相対値として読む |
| `best_epoch`、`stopped_epoch` | 学習量（early stopping の発火位置） |

`residual-result-analysis` で、`day_gru_hour_mlp` を left、他 5 variant を right として
seed 単位の対応ありの差分（`left − right`）と 10,000 回の bootstrap 95% CI を取る。
負なら提案構成の方が良い。`residual_r2` は大小の向きが逆で CSV の
`left_better_runs` 列が誤読を招くため、paired 比較の指標からは外し、
`aggregate.csv` の平均値として読む。

## 事前に定める成功条件・分岐

1. **再現性**: `day_gru_hour_mlp` の `corrected_cell_mae` 5 seed 平均が
   2-Exp-40 dim10 の `output_decomp_centered`（0.04828 ± 0.00032）と ±0.0005 以内で一致する。
   外れる場合は Encoder のリファクタで数値が変わったことを疑い、先に原因を特定する。
2. **日軸の GRU（設計意図 1）**: `day_gru_hour_mlp` − `day_mlp_hour_mlp` の
   `corrected_cell_mae` 差が 5 seed すべてで負、かつ bootstrap 95% CI の上限 < 0。
   満たせば「日成分には前日までの文脈が効く」と書ける。
   CI が 0 をまたぐ場合は「日軸の GRU は MLP と同等で、選択は精度では正当化されない」と書き、
   より軽い MLP でも主結果が再現することを示す方向に記述を変える。
3. **再帰か容量か（設計意図 1 の内訳）**: 2 が成立したうえで
   `day_gru_hour_mlp` − `day_mlpwide_hour_mlp` も CI 上限 < 0 なら「再帰による文脈混合の効果」、
   CI が 0 をまたぐなら「日軸で効いているのは容量であり、再帰は必須ではない」と書く。
4. **時間帯軸の MLP（設計意図 2）**: `day_gru_hour_mlp` − `day_gru_hour_gru` の CI が 0 を含む、
   または正側（GRU が良い）でないこと。0 を含めば「周期的な形には MLP で足りる」と書ける。
   `day_gru_hour_gru` が有意に良い場合は原稿の記述を改め、hour 側も GRU に変えた構成で
   2-Exp-40 の主表を再走させる必要がある（本実験の範囲外として明記し、後続実験に回す）。
   `day_gru_hour_mlpwide` との差も同時に見て、容量による差と区別する。
5. **役割の入れ替え**: `day_mlp_hour_gru` は `day_gru_hour_mlp` に勝たない。
   勝つ場合は「軸と構造の対応づけ」自体が逆であり、設計の根拠を立て直す。
6. **コスト**: 2 と 4 の結論が「差なし」側に出た指標では、`param_count` の小さい構成を
   採用候補として併記する。

2 と 4 がどちらも「差なし」なら、原稿の記述は
「日/時間帯の構造の違いに合わせて Encoder を選んだが、精度はこの選択に鈍感である」
という形に改め、アーキテクチャ選択を主張の根拠にしない。

## 実行方法

smoke（ローカル、synthetic、6 variant × 1 seed、6 epoch。配線と出力の確認のみ）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-45_encoder_architecture_smoke.json
uv run decoupled-ts residual-result-analysis --config configs/2-Exp-45_paired_analysis_smoke.json
```

本番（ローカル GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-45_encoder_architecture_freshretailnet.json
uv run decoupled-ts residual-result-analysis --config configs/2-Exp-45_paired_analysis_freshretailnet.json
```

条件 4 の確定（epoch 上限 120、hour 側 3 variant × 5 seed = 15 run）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-45_encoder_architecture_epochs120_freshretailnet.json
uv run decoupled-ts residual-result-analysis --config configs/2-Exp-45_paired_analysis_epochs120_freshretailnet.json
```

2-Exp-40 の 40 run が RTX 5060 Ti で約 17 分だったので、本実験 30 run は 15〜20 分を見込む。
`output` は全保存フラグを false にしているので、出力は metrics と CSV のみで数 MB に収まる。

## 出力

```text
runs/2-Exp-45_encoder_architecture_freshretailnet/
  series_mean/seed_{17,23,31,47,59}/<variant>/metrics.json / history.jsonl
  all_results.csv / aggregate.csv / summary.json
runs/2-Exp-45_paired_analysis_freshretailnet/
  paired_model_delta.csv / baseline_delta.csv / summary.json

figures/2-Exp-45/
  all_results.csv / aggregate.csv / paired_model_delta.csv / baseline_delta.csv
  epochs120/all_results.csv / aggregate.csv / paired_model_delta.csv / baseline_delta.csv
```

`runs/` は git 管理外なので、判定に使う 4 つの CSV を `figures/2-Exp-45/` に複製して記録する。

## 解釈上の制約

- 比較できるのは「軸方向の周辺統計量を受けた後の処理」だけである。
  Encoder の入力そのもの（観測平均・標準偏差への集約）は全 variant で共通なので、
  「日の系列をそのまま時系列として扱う」設計（例: 日×時間帯のセル列を直接 GRU に流す）は
  本実験の比較対象ではない。それは 2-Exp-42 系の統一アーキテクチャの話になる。
- 日数は history 28 日で、GRU が利用できる文脈長はそこまでに限られる。
- `mlp_wide` はパラメータ数を GRU に合わせた対照であり、最適な MLP 構造ではない。
  「容量を揃えても再帰に届かない」ことは示せるが、
  「どんな MLP でも届かない」ことは示せない。
- 評価は残差補正後のセル MAE なので、Encoder の違いが成分の解釈可能性
  （2-Exp-35 / 2-Exp-44 系の指標）に与える影響は、成分 ablation と振幅の範囲でしか見ていない。

## smoke 確認

2026-10-23 にローカル（synthetic、128 系列、14 日 × 24 時間、hidden 40、6 epoch、
patience 1、device=cuda、1 seed）で smoke を実行し、次を確認した。

- 6 variant が完走し、`all_results.csv` に `param_count` と `train_seconds` が入った。
- `param_count` が構造どおりに動いた（hidden 40 の場合、GRU は +9,840、
  `mlp_wide` は +9,760 で、両者の差は 80）。

| variant | param_count | corrected_cell_mae | residual_r2 |
|---|---:|---:|---:|
| `day_gru_hour_mlp` | 14,259 | 1.41759 | +0.0246 |
| `day_mlp_hour_mlp` | 4,419 | 1.39910 | +0.0409 |
| `day_mlpwide_hour_mlp` | 14,179 | 1.41061 | +0.0064 |
| `day_gru_hour_gru` | 24,099 | 1.38447 | +0.0665 |
| `day_gru_hour_mlpwide` | 24,019 | 1.39453 | +0.0480 |
| `day_mlp_hour_gru` | 14,259 | 1.39906 | +0.0504 |

- `residual-result-analysis` が 5 比較 × 3 指標の `paired_model_delta.csv` と
  `baseline_delta.csv` を書いた（1 seed なので CI 幅は 0）。
- 6 epoch・128 系列・synthetic の値そのものは評価に使わない
  （`residual_r2` が 0.006〜0.067 で、まだ学習が進んでいない）。判定は本番の 5 seed で行う。
- リファクタの同値性は `tests/test_axis_encoders.py` と、
  `axis_marginal_stats` が従来の式と `allclose` であることで確認した。

## 本番結果

2026-10-23 にローカル GPU（RTX 5060 Ti）で全 30 run を実行し、約 17 分で完走した
（00:07:16 開始、00:24:25 終了。出力は 2.2 MB）。
判定に使った CSV は `figures/2-Exp-45/`（`all_results.csv`、`aggregate.csv`、
`paired_model_delta.csv`、`baseline_delta.csv`）に複製した。
以下、値は 5 seed（17, 23, 31, 47, 59）の平均 ± SD である。

### 全 variant の集計

| variant | param_count | `corrected_cell_mae` | `corrected_cell_wape` | `high_residual_top10_corrected_mae` | `residual_r2` | `train_seconds` |
|---|---:|---:|---:|---:|---:|---:|
| `day_gru_hour_mlp`（現行） | 184,362 | 0.04828 ± 0.00032 | 0.8179 ± 0.0054 | 0.19418 ± 0.00200 | 0.4157 ± 0.0051 | 32.5 ± 4.4 |
| `day_mlp_hour_mlp` | **29,802** | **0.04780 ± 0.00077** | **0.8098 ± 0.0130** | **0.19155 ± 0.00267** | **0.4300 ± 0.0107** | 31.1 ± 6.1 |
| `day_mlpwide_hour_mlp` | 184,042 | 0.04825 ± 0.00052 | 0.8175 ± 0.0088 | 0.19289 ± 0.00381 | 0.4218 ± 0.0083 | 30.9 ± 5.7 |
| `day_gru_hour_gru` | 338,922 | 0.04877 ± 0.00079 | 0.8262 ± 0.0133 | 0.19946 ± 0.00534 | 0.3873 ± 0.0218 | 34.8 ± 7.6 |
| `day_gru_hour_mlpwide` | 338,602 | 0.04934 ± 0.00090 | 0.8359 ± 0.0153 | 0.19874 ± 0.00492 | 0.3864 ± 0.0261 | 29.8 ± 4.3 |
| `day_mlp_hour_gru` | 184,362 | 0.04870 ± 0.00075 | 0.8250 ± 0.0126 | 0.19794 ± 0.00222 | 0.4014 ± 0.0082 | 32.6 ± 9.4 |

baseline（`series_mean`）は `corrected_cell_mae` 0.06966、top10 は 0.27883 で、
どの variant もそこからの改善幅（約 −0.021）に比べれば互いの差は 1 桁小さい。
`train_seconds` は 1 run 目に CUDA 初期化が乗るうえ early stopping の発火位置
（`stopped_epoch` は variant 平均 40.4〜47.4、run ごとには 30〜60）にも左右されるので、
SD の範囲で差はない。

30 run 中 3 run は上限 60 epoch に達して early stopping が発火しなかった
（`day_gru_hour_gru` seed 17 は best 58、`day_mlp_hour_gru` seed 31 は best 60、
同 seed 59 は best 57）。3 run とも hour 側が GRU の variant で、打ち切り時点でも
検証スコアが改善中だった。hour=GRU の成績は学習量不足の側に寄っている可能性があるため、
条件 4 の「時間帯軸は MLP で足りる」は、epoch 上限を伸ばした比較では弱まりうる
（§条件 4 の確定 で取り直した）。
一方、本実験の主眼である日軸の比較（条件 2・3）は全 run が上限より手前で停止しており、
この影響を受けない。

### 対応ありの比較（left = `day_gru_hour_mlp`、delta = left − right、負なら現行が良い）

| right | 指標 | delta ± SD | 95% CI | 現行が良い seed |
|---|---|---:|---|---:|
| `day_mlp_hour_mlp` | `corrected_cell_mae` | +0.00048 ± 0.00067 | [+0.00002, +0.00106] | 1/5 |
| `day_mlp_hour_mlp` | `corrected_cell_wape` | +0.00811 ± 0.01143 | [+0.00040, +0.01794] | 1/5 |
| `day_mlp_hour_mlp` | top10 MAE | +0.00263 ± 0.00372 | [−0.00025, +0.00551] | 1/5 |
| `day_mlpwide_hour_mlp` | `corrected_cell_mae` | +0.00002 ± 0.00062 | [−0.00048, +0.00044] | 2/5 |
| `day_mlpwide_hour_mlp` | top10 MAE | +0.00129 ± 0.00247 | [−0.00079, +0.00310] | 1/5 |
| `day_gru_hour_gru` | `corrected_cell_mae` | −0.00049 ± 0.00093 | [−0.00123, +0.00025] | 3/5 |
| `day_gru_hour_gru` | top10 MAE | −0.00528 ± 0.00669 | [−0.01039, −0.00017] | 3/5 |
| `day_gru_hour_mlpwide` | `corrected_cell_mae` | −0.00106 ± 0.00101 | [−0.00184, −0.00029] | 4/5 |
| `day_gru_hour_mlpwide` | top10 MAE | −0.00456 ± 0.00377 | [−0.00777, −0.00191] | 5/5 |
| `day_mlp_hour_gru` | `corrected_cell_mae` | −0.00042 ± 0.00068 | [−0.00093, +0.00013] | 4/5 |
| `day_mlp_hour_gru` | top10 MAE | −0.00376 ± 0.00170 | [−0.00476, −0.00223] | 5/5 |

### 成功条件の判定

1. **再現性（条件 1）: 成立。** `day_gru_hour_mlp` の `corrected_cell_mae` は
   0.04828 ± 0.00032 で、2-Exp-40 dim10 の `output_decomp_centered`（0.04828 ± 0.00032）と
   小数第 5 位まで一致した。top10 も 0.19418 で一致する。
   `AxisEncoder` へのリファクタは数値を変えていない。
2. **日軸の GRU（条件 2）: 不成立。方向が逆。** GRU を外した `day_mlp_hour_mlp` の方が
   平均で 0.00048 良く（相対 1.0%）、5 seed 中 4 seed で上回り、95% CI の下限も
   わずかに 0 を超えた（+0.00002）。`residual_r2` も 0.4300 対 0.4157 で MLP が良い。
   差は小さく CI の下限はほぼ 0 だが、「日軸の GRU が精度で有利」という主張はできない。
3. **再帰か容量か（条件 3）: 「どちらでもない」。** パラメータ数を GRU に揃えた
   `day_mlpwide_hour_mlp` との差は +0.00002（CI [−0.00048, +0.00044]）で完全に同等である。
   一方、最もパラメータの少ない `day_mlp_hour_mlp`（29.8k、GRU 版の 1/6）が
   両者をわずかに上回る。日軸では**再帰の有無ではなく容量の増加そのものがわずかに不利**で、
   GRU の効果は「容量を増やした分」の範囲に収まっている。
4. **時間帯軸の MLP（条件 4）: 成立。** `day_gru_hour_gru` との差は
   −0.00049（CI [−0.00123, +0.00025]）で `corrected_cell_mae` では有意でないが、
   top10 MAE は CI 上限 −0.00017 で現行が有意に良く、`residual_r2` も 0.4157 対 0.3873 で上回る。
   容量だけ揃えた `day_gru_hour_mlpwide` は `corrected_cell_mae` −0.00106
   （CI 上限 −0.00029）、top10 は 5 seed すべてで現行が良い。
   **時間帯軸は MLP で足り、文脈混合も容量追加も悪化方向である。**
   ただし hour=GRU の 3 run が epoch 上限で打ち切られているため、この判定は
   epoch 上限 120 で取り直した（§条件 4 の確定）。結論は変わらないが、
   top10 MAE の有意性は消える。
5. **役割の入れ替え（条件 5）: 成立。** `day_mlp_hour_gru` は現行に勝たない
   （`corrected_cell_mae` −0.00042、top10 は 5 seed すべて現行が良い）。
   「day に GRU、hour に MLP」という割り当ての向き自体は、逆向きより良い。
   ただし `day_mlp_hour_gru` は seed 31 と 59 が epoch 上限 60 で打ち切られており、
   この variant だけ収束させ直していない。条件 4 の取り直しでは
   `day_gru_hour_gru` の値がほぼ動かなかったので結論は変わらない見込みだが、
   条件 5 は条件 4 ほど確定していない。
6. **コスト（条件 6）: `day_mlp_hour_mlp` が採用候補。** 29,802 パラメータは現行の約 1/6 で、
   精度は同等かわずかに良い。学習時間は SD の範囲で差がない。

### 成分の役割分担

成分 ablation の悪化幅（成分を落としたときの MAE 増）は、アーキテクチャを変えても
hour が最大という構図が変わらない。

| variant | without day | without hour | without interaction |
|---|---:|---:|---:|
| `day_gru_hour_mlp` | 0.00256 ± 0.00040 | 0.01159 ± 0.00068 | 0.00207 ± 0.00028 |
| `day_mlp_hour_mlp` | 0.00324 ± 0.00065 | 0.01206 ± 0.00107 | 0.00223 ± 0.00049 |
| `day_mlpwide_hour_mlp` | 0.00290 ± 0.00030 | 0.01182 ± 0.00038 | 0.00210 ± 0.00057 |
| `day_gru_hour_gru` | 0.00248 ± 0.00069 | 0.01142 ± 0.00067 | 0.00140 ± 0.00055 |
| `day_gru_hour_mlpwide` | 0.00199 ± 0.00110 | 0.01156 ± 0.00092 | 0.00122 ± 0.00051 |
| `day_mlp_hour_gru` | 0.00301 ± 0.00079 | 0.01147 ± 0.00085 | 0.00151 ± 0.00043 |

day 成分の寄与はむしろ MLP 版（0.00324）の方が GRU 版（0.00256）より大きく、
GRU は day 成分の説明力を増やしてもいない。
`hour_component_residual_profile_corr` は全 variant 0.988〜0.997 で差がない。
`diag_day_relative_amplitude` / `diag_hour_relative_amplitude` は
全 variant で完全に同値（0.1235 / 0.5418）だった。これらは残差データ側の診断量であり、
モデル比較には使えない指標だと確認できた。

### 条件 4 の確定（epoch 上限 120）

60 epoch 版では hour=GRU の run が上限で打ち切られていたため、hour 側 3 variant
（`day_gru_hour_mlp` / `day_gru_hour_gru` / `day_gru_hour_mlpwide`）× 5 seed = 15 run を
epoch 上限 120（patience 8 は据え置き、他は同条件）で取り直した。
2026-10-23 にローカル GPU で約 8 分（03:14:26 開始、03:22:29 終了）。
**上限 120 に達した run は 0 で、全 run が early stopping で止まった**
（最長は `day_gru_hour_gru` seed 17 の best 73 / stopped 81）。

60 epoch 版で打ち切られていなかった 2 variant（`day_gru_hour_mlp`、`day_gru_hour_mlpwide`）は
per-seed の値まで完全に一致し、実行の決定性も確認できた。変わったのは
`day_gru_hour_gru` の seed 17 だけで（best 58 / stopped 60 → best 73 / stopped 81、
`corrected_cell_mae` 0.04807 → 0.04797）、5 seed 平均は 0.04877 → 0.04875 とほぼ動かない。

| variant | `corrected_cell_mae` | top10 MAE | `residual_r2` | `stopped_epoch` |
|---|---:|---:|---:|---:|
| `day_gru_hour_mlp`（現行） | 0.04828 ± 0.00032 | 0.19418 ± 0.00200 | 0.4157 ± 0.0051 | 46.0 ± 9.6 |
| `day_gru_hour_gru` | 0.04875 ± 0.00081 | 0.19883 ± 0.00565 | 0.3882 ± 0.0224 | 50.4 ± 17.7 |
| `day_gru_hour_mlpwide` | 0.04934 ± 0.00090 | 0.19874 ± 0.00492 | 0.3864 ± 0.0261 | 40.4 ± 5.8 |

| right | 指標 | delta | 95% CI | 現行が良い seed |
|---|---|---:|---|---:|
| `day_gru_hour_gru` | `corrected_cell_mae` | −0.00047 | [−0.00123, +0.00029] | 3/5 |
| `day_gru_hour_gru` | top10 MAE | −0.00465 | [−0.00976, +0.00046] | 3/5 |
| `day_gru_hour_mlpwide` | `corrected_cell_mae` | −0.00106 | [−0.00184, −0.00029] | 4/5 |
| `day_gru_hour_mlpwide` | top10 MAE | −0.00456 | [−0.00789, −0.00191] | 5/5 |

**条件 4 は成立する**（`day_gru_hour_gru` との CI が 0 を含み、GRU が良い側ではない）。
ただし 60 epoch 版からひとつ判定が変わる。top10 MAE の CI 上限が
−0.00017 から +0.00046 に動き、**「hour=GRU が有意に悪い」とは言えなくなった**。
収束させた比較での正しい読み方は「時間帯軸を GRU にしても改善しない（点推定は悪化方向、
3/5 seed で現行が良い）」であり、「GRU が有意に悪い」ではない。
`residual_r2` は 0.4157 対 0.3882 で現行が上回る。

容量だけ揃えた `day_gru_hour_mlpwide` は 60 epoch 版と同じく有意に悪い
（`corrected_cell_mae` CI 上限 −0.00029、top10 は 5 seed すべて現行が良い）。
**時間帯軸では、文脈混合は改善をもたらさず、容量追加は有意に悪化させる。**

### 結論と原稿への反映

**「日成分は日の系列なので前日までの文脈を反映できるよう GRU、時間帯成分は周期的な形なので MLP」
という説明のうち、後半（時間帯＝MLP）は支持されたが、前半（日＝GRU）は支持されない。**
日軸では GRU を外した方がわずかに良く、パラメータ数を揃えた MLP とは完全に同等である。
時間帯軸は、epoch 上限 120 まで収束させても GRU にして改善せず（点推定は悪化方向、3/5 seed）、
容量を増やすと有意に悪化する。

この結果は、本実験の評価が**窓内の再構成**である（2-Exp-40 と同じく、28 日の観測窓を
入力として同じ窓の残差を再構成する）ことで説明できる。日 `t` の day 成分は
日 `t` 自身の周辺統計量から直接同定できるので、前日までの文脈を持ち込む必要がない。
GRU の想定した利点が効くとすれば未来日の予測であり、本実験の設定ではそこを測っていない。

したがって原稿では次のように扱う。

- 窓内再構成の主結果については、「日/時間帯の構造の違いに合わせて Encoder を選んだが、
  精度はこの選択に鈍感である（日軸は GRU でも MLP でも同等、時間帯軸は GRU にしても改善しない）」
  と書き、アーキテクチャ選択を主張の根拠にしない。本実験の表をその根拠として引用する。
- 「前日までの文脈」を GRU の採用理由として書くことは、窓内再構成の範囲では撤回する。
- 主結果の再走は行わない。現行構成と `day_mlp_hour_mlp` の差は 0.0005（相対 1.0%）で、
  主表の結論（中心化あり 0.04828 対 中心化なし 0.05422）を変えないため。
  パラメータ 1/6 で同等という事実は、モデルの軽量化余地として考察に書く。

### 後続実験

未来日評価（2-Exp-39 / 2-Exp-43 の設定、未来セルをマスクして未来日の残差を予測）で
同じ 6 variant を回せば、「前日までの文脈」が効く設定があるかを直接確かめられる。
本実験の config は `experiments` の 6 行をそのまま持ち込めるので、
dataset と `future_mask_channels` の設定を 2-Exp-43 から借りるだけで組める。
