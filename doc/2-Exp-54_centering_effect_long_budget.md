# 2-Exp-54: 中心化の効果量と頭打ち位置（epochs 480 / patience 48、2 variant）

作成日: 2026-11-09
対応ボード項目: JIMA-01（中心化の効果）の効果量確定、JIMA-02（主結果系列）の学習量依存の決着
関連: [2-Exp-48_main_table_long_budget.md](2-Exp-48_main_table_long_budget.md)、
[2-Exp-46_epoch_budget_component_stability.md](2-Exp-46_epoch_budget_component_stability.md)、
[2-Exp-40_jima_main_results.md](2-Exp-40_jima_main_results.md)、
[2-Exp-44_component_interpretation.md](2-Exp-44_component_interpretation.md)

（実験 ID は 53 が基準値診断で使用済みのため 54 を使う。
作業場所は `worktrees/exp36〜53` と同じ流儀。`data/` はメイン checkout への symlink で共有し、
`runs/` は worktree 内に作る。）

## 背景

[2-Exp-48](2-Exp-48_main_table_long_budget.md) の「次に必要な実験」に対応する。

| 実験 | 予算 | centered の `corrected_cell_mae` | 上限到達 | centered − no_center |
|---|---|---:|---|---:|
| [2-Exp-40](2-Exp-40_jima_main_results.md) | 60 / patience 8 | 0.04828 ± 0.00032 | 0 / 5 | −0.00594（5 勝 0 敗） |
| [2-Exp-46](2-Exp-46_epoch_budget_component_stability.md) | 120 / patience 16 | 0.04698 ± 0.00049 | 3 / 5 | （centered のみ実施） |
| [2-Exp-48](2-Exp-48_main_table_long_budget.md) | 240 / patience 24 | 0.04679 ± 0.00055 | 4 / 5 | **−0.00153（5 勝 0 敗）** |

未決の点が 2 つある。

1. **頭打ち位置が未確定**。240 でも centered の 4/5 が上限に張り付いた（2-Exp-48 成功条件 1 ✗）。
   そのため主表は 60/8 版のまま据え置かれている。
2. **中心化の効果量が予算に依存する**。−0.00594 → −0.00153 と約 1/4 に縮んだ。
   原稿では「中心化は収束後も有利だが差は学習量を増やすと縮む。主たる価値は解釈である」と
   書く方針になっているが、その「縮む」がどこで止まるかは測っていない。

### 240 / patience 24 での停止事情は variant 間で非対称だった

本実験の設計上の論点なので、2-Exp-48 の per-seed 値を展開しておく
（`runs/2-Exp-48_main_table_long_budget_freshretailnet/all_results.csv` から集計）。

| seed | centered MAE | centered best / stopped | no_center MAE | no_center best / stopped | 差 |
|---|---:|---|---:|---|---:|
| 17 | 0.04693 | 237 / **240（上限）** | 0.04740 | 143 / 167 | −0.00047 |
| 23 | 0.04667 | 228 / **240（上限）** | 0.04699 | 239 / **240（上限）** | −0.00033 |
| 31 | 0.04752 | 237 / **240（上限）** | 0.04935 | 74 / 98 | −0.00183 |
| 47 | 0.04598 | 232 / **240（上限）** | 0.04863 | 147 / 171 | −0.00265 |
| 59 | 0.04684 | 138 / 162 | 0.04922 | 106 / 130 | −0.00238 |

paired 差は平均 **−0.001531**、seed 間 SD **0.001076**、SEM **0.000481** である。

- centered は **4/5 が上限 240 で打ち切られた**。伸ばす余地が残っている。
- no_center は **4/5 が patience 24 で停止した**（98〜171）。上限には当たっていない。

つまり 240/24 の比較は、「上限で切られた centered」と「patience で止まった no_center」を
並べたものである。予算を 480 / patience 48 に倒すと、**centered には上限の緩和が効き、
no_center には patience の緩和が効く**。両方が同時に動くため効果量がどちらに振れるかは
事前には決まらない。これは本実験の弱点ではなく、測る理由である（制約節も参照）。

## 目的

1. 480 / patience 48 で centered と no_center が上限到達を脱するか、
   つまり **early stopping が効く位置がこの予算の内側に入るか**を確認する。
2. その予算での効果量 centered − no_center を測り、60/8 → 240/24 → 480/48 の系列にする。
3. 原稿の書き方を決める。さらに縮むなら「主たる価値は解釈」の裏づけになり、
   止まるなら効果量の下限として書ける。どちらでも原稿は書ける。
4. （探索）成分指標の 480 点を取り、2-Exp-48 で単調と分かった傾向
   （`ss_share_interaction` の増加、`interaction_rank1_share` の低下、global の系列間ばらつきの増加）
   が続くかを見る。

## 実験条件

2-Exp-48 の config から **4 点だけ**を変える。

| 項目 | 2-Exp-48 | 本実験 |
|---|---|---|
| `train.epochs` | 240 | **480** |
| `train.early_stopping_patience` | 24 | **48** |
| `experiments` | 4 variant | **2 variant**（`output_decomp_no_center` / `output_decomp_centered`） |
| `sweep.output_dir` / `train.output_dir` | 2-Exp-48 の run 先 | 本実験の run 先 |

それ以外（dataset 6000/1500/1500・`validation_source: train_holdout`、residual `series_mean`、
model dim10（10/10/10/8）・hidden 160、lr 1e-3・batch 128、seeds 17/23/31/47/59、
`selection_metric: valid_loss_residual_reconstruction`、`amp`、`reset_seed_per_variant`、
`save_latent_arrays` / `save_component_analysis_arrays` / `save_checkpoints` / `save_hour_heatmap`）は
2-Exp-48 と同一である。config は 2-Exp-48 の JSON から生成し、差分が上表の 4 点だけであることを
機械的に確認した（smoke 節に記録）。

patience は 2-Exp-46 の 16、2-Exp-48 の 24 と同じ比率（上限の 1/10）を保った。

合計 run 数: 1 scenario × 5 seed × 2 variant = **10**。

### 外した 2 variant の扱い

- `empirical_anova_main_effects`: 学習を行わないため epoch 予算の影響を受けない。
  2-Exp-48 では 5 seed すべてが 0.05443 で完全一致した（確認済み）。
  本実験では回さず、**外部定数 0.05443 として引用する**。
- `output_decomp_centered_calibrated`: calibration は 60/8（2-Exp-40 読み取り 4）と
  240/24（2-Exp-48 成功条件 4、+0.0004 で悪化）の両方で効かないことが確定しており、
  本実験の問い（効果量と頭打ち位置）と独立である。

この 2 本を外した代償として、**本実験単独では主表の 4 行を揃えられない**。
主表の差し替え判断は成功条件 5 に書く。

## 評価指標

| 指標 | 用途 |
|---|---|
| `stopped_epoch` / `best_epoch` | 目的 1。上限 480 到達の有無が主判定 |
| `corrected_cell_mae` | 目的 2 の主指標。paired 差をこれで取る |
| `corrected_cell_wape` / `high_residual_top10_corrected_mae` / `corrected_cell_bias` | 主表の他行と同じ指標。予算を跨いだ傾向の確認 |
| `history.jsonl` の `valid_loss_residual_reconstruction` | P1 の内部対照。2-Exp-48 の同一 run と軌跡を突き合わせる |
| `ss_share_{day,hour,interaction}` / `global_component_sd` / `interaction_rank1_share_median` / `rel_bias_global` | 目的 4。2-Exp-44 の解析スクリプトで取得 |

## 事前に登録する予測（自己チェック）

- **P1 内部対照（軌跡の重なり）**: 各 run の `history.jsonl` の `valid_loss_residual_reconstruction` が、
  2-Exp-48 の同一 seed・同一 variant の系列と、2-Exp-48 の `stopped_epoch` までほぼ一致する。
  予算以外を変えていないので、学習軌跡は途中まで同一になるはずである。

  同一条件の再現性については根拠が 2 つある。1 つは 2-Exp-46 の `epochs60` が 2-Exp-44 と
  全指標一致したこと。もう 1 つは 2-Exp-53（基準値診断。別ブランチで進行中、doc は未マージ）の
  `series_mean` scenario を 2-Exp-48 の `dim10` scenario と突き合わせた結果である。

  | variant | 2-Exp-53 | 2-Exp-48 | 差 |
  |---|---:|---:|---:|
  | `empirical_anova_main_effects` | 0.05443 ± 0.00000 | 0.05443 ± 0.00000 | +0.00000 |
  | `output_decomp_no_center` | 0.04832 ± 0.00107 | 0.04832 ± 0.00107 | +0.00000 |
  | `output_decomp_centered` | 0.04679 ± 0.00055 | 0.04679 ± 0.00055 | +0.00000 |

  `corrected_cell_mae` の mean と std が両方一致しているので、平均が偶然合ったのではなく
  seed ごとに再現している。`baseline_cell_mae` 0.06966、`diag_hour_relative_amplitude` 0.54176、
  `diag_day_relative_amplitude` 0.12352 も一致した。2-Exp-48 は競合なしの別時刻に回した実験なので、
  同一機・同一 seed なら集約指標が再現することの直接の証拠になる。

  **ただしこれは集約指標レベルでの一致であり、bit 一致の確認ではない。**
  `corrected_cell_mae` は観測セル平均なので、kernel 選択の揺れがあっても丸めで消え得る。
  `cudnn.benchmark = True` と AMP を使う以上、epoch 単位の loss では一致幅が緩くなる可能性がある。
  P1 の判定は集約指標ではなく `history.jsonl` を直接突き合わせて行い、
  採用した許容幅（および一致が崩れた epoch 位置）を結果節に明示する。
- **P2 centered は上限を脱する**: 上限 480 到達が 0〜2 / 5 に減る。
  240 では 4/5、120 では 3/5 だったので、増える方向には出ないと予測する。
- **P3 no_center は patience の緩和で改善する**: 2-Exp-48 で patience 24 停止だった
  seed 17 / 31 / 47 / 59 の `corrected_cell_mae` が改善する（0.04740 / 0.04935 / 0.04863 / 0.04922 より小さくなる）。
  seed 23 は上限到達だったので上限の緩和で改善する。
- **P4 効果量はさらに縮む**: paired 差が −0.00153 より 0 側に寄る。
  根拠は P3 で、no_center 側に伸びる余地が centered より多く残っていることである。
  ただし centered も上限で切られていたので、確信度は P2・P3 より低い。
- **P5 向きは不変**: 5 seed 中 4 以上で centered < no_center。
- **P6 成分指標の単調傾向が続く**: `ss_share_interaction` が 0.0427 より増え、
  `interaction_rank1_share_median` が 0.850 より下がり、
  `global_component_sd` ÷ |mean| の範囲が 0.563〜0.787 より上に出る。
  `corr_improvement_hour_share`（0.72〜0.75）と `rel_bias_global`（−0.27〜−0.31）は動かない。

P1 が崩れた場合は条件の取り違えとして**他の判定を止めて先に報告する**。

## 事前に定める成功条件・分岐

1. **内部対照（P1）**: 一致すれば以降の判定に進む。
   一致しなければ config の取り違えか環境差として扱い、原因を doc に記録してから回し直す。
2. **頭打ち位置（目的 1）**: 全 10 run で `stopped_epoch` < 480 かつ `best_epoch` < `stopped_epoch`。
   満たせば「この予算の内側で early stopping が効いた」と書ける。
   上限到達が残るなら 480 でも打ち切りが続くと報告し、主表は 60/8 版のまま据え置いて
   「予算を 480 まで倒しても改善が続く」を limitation に追加する。
   **注**: `stopped_epoch` < 480 は収束の十分条件ではない。2-Exp-40 で訂正したのと同じ誤りを
   繰り返さないため、本実験でも数値は「`patience 48` の早期終了時点」と書き、
   判定には上限到達の有無だけを使う。
3. **効果量（目的 2・3）**。判定の帯を事前に決める。
   240/24 の paired 差 −0.001531、seed 間 SD 0.001076、SEM 0.000481 を基準にする。

   | 帯 | paired 差 Δ | 読み方 |
   |---|---|---|
   | 縮小 | Δ ≥ −0.00077（240 の半分以下） | 「中心化の主たる価値は解釈」を本線にする。性能差は予算とともに消える方向と書く |
   | 据え置き | Δ ≤ −0.00120 | 効果量の下限として 0.0012 を書く。「予算を倍にしても縮まなかった」 |
   | 判定不能 | −0.00120 < Δ < −0.00077 | 240/24 との差は seed ゆらぎに埋もれる。区間 −0.0015〜−0.0008 として報告する |

   seed 5 本・paired SD 0.00108 では 0.0005 程度の差は検出できない。帯はこの限界の上に置いている。
4. **向き（P5）**: 4 勝以上なら JIMA-01 の向きは、**基準値 `series_mean` の条件下で**
   予算に依らないと確定する（基準値を跨いだ主張にはしない。制約節を参照）。
   3 勝以下なら中心化の性能上の優位は学習量依存だったことになり、
   JIMA-01 は解釈（成分の担当範囲の固定）の主張に限定する。
5. **主表の差し替え**: 2 と 4 が成立した場合に限り、centered / no_center の 2 行について
   480/48 版の採用を提案する。ただし **empirical 行と calibration 行は 480/48 で取っていない**ため、
   行間で予算が揃わない表は作らない。差し替えるなら 4 variant すべてを 480/48 で取り直す
   追加実験（20 run）が必要であることを doc に明記する。
   `empirical_anova_main_effects` は学習に依らないので 0.05443 をそのまま使えるが、
   calibration 行は学習に依るので引き継げない。
6. **成分指標（目的 4・P6）は探索**。閾値を置かず、12 / 60 / 120 / 240 / 480 の系列として報告する。

## 実行方法

smoke（synthetic、10 epoch・patience 2。2 variant と保存経路の確認）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-54_centering_effect_long_budget_smoke.json
```

本番（ローカル GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-54_centering_effect_long_budget_freshretailnet.json
uv run --with matplotlib python scripts/analyze_2_exp_44_component_interpretation.py \
  --run-dir runs/2-Exp-54_centering_effect_long_budget_freshretailnet/dim10 \
  --out-dir figures/2-Exp-54 --variants output_decomp_centered output_decomp_no_center
```

所要見込みは 60〜90 分。2-Exp-48 の 20 run（上限 240、centered 4 run が上限まで）が約 34 分だった。
本実験は run 数が半分で上限が倍、かつ centered 5 run は上限近くまで走る見込みである。

**本番は 2-Exp-53（基準値診断、60 run・240 epoch）の完走後に回す。**
同一 GPU（RTX 5060 Ti）を使うため、重ねると両方の所要時間が伸びる。

`run_residual_sweep` は全 cell のループを抜けた後に `all_results.csv` → `aggregate.csv` →
`summary.json` の順で書くので、`all_results.csv` があれば全 cell 完走と読める。
逆に途中で落ちるとこの 3 つは残らず、cell 別の `summary.json` だけが残る。
その場合は cell 別から縫い直せる（2-Exp-53 ブランチの
`scripts/rebuild_2_exp_53_summary.py`。名前は 53 専用だが中身は汎用で、
sweep 本体の `_mean_std` を import しているので集計は一致する）。

## 出力

```text
runs/2-Exp-54_centering_effect_long_budget_freshretailnet/
  dim10/seed_{17,23,31,47,59}/{output_decomp_no_center,output_decomp_centered}/
  all_results.csv / aggregate.csv / summary.json

figures/2-Exp-54/
  metrics.json / metrics_by_seed.csv / discount_response.csv / hour_share_quartiles.csv
```

## 解釈上の制約

- **上限と patience の 2 つのレバーを同時に動かしている。**
  しかも効くレバーが variant で違う（centered は上限 240 → 480、no_center は patience 24 → 48）。
  したがって効果量が動いた場合、その原因を上限と patience に分離できない。
  分離が必要なら 480 / patience 24 の scenario を足す（+10 run）。
  本実験では分離せず、**その予算での効果量の値**だけを報告する。
  予算を「上限 = patience × 10」で固定して系列を作るのは 2-Exp-46 / 2-Exp-48 と同じ流儀であり、
  比較可能性はこの系列の内部で保たれる。
- **`stopped_epoch` < 480 は収束を意味しない。** 2-Exp-40 で「early stopping したので収束」と
  書いたのが誤りだったのと同型である。本実験の数値も「`patience 48` の早期終了時点」である。
- **2 variant しかないので主表全体の差し替えはできない**（成功条件 5）。
- **絶対値の比較は予算を揃えた行の間でのみ行う。** 480/48 の centered を 240/24 の
  calibration 行や 60/8 の empirical 行と同じ表に並べない。
- **seed は 5 本のみ。** paired SD 0.00108 なので、効果量の 0.0005 程度の差は検出できない。
- **test 集合は全予算で同一**なので、予算を跨ぐ比較は探索的であり、多重比較の補正を入れていない。
- 成分指標は `output_decomp_centered` と `output_decomp_no_center` の 2 本でのみ取る。
  2-Exp-44 / 2-Exp-46 / 2-Exp-48 の系列と同じ指標なので、点を足す形で読める。
- **本実験が測る効果量は基準値 `series_mean` の条件下の値である。**
  2-Exp-53（基準値診断。別ブランチで進行中）が 240 / patience 24 で測った実測値。

  | scenario | baseline | centered | no_center | paired 差 | centered 勝敗 |
  |---|---:|---:|---:|---:|---|
  | `series_mean` | 0.06966 | 0.04679 ± 0.00055 | 0.04832 ± 0.00107 | **−0.00153 ± 0.00108** | **5 勝 0 敗** |
  | `recent_hour_d7` | 0.05796 | 0.05361 ± 0.00036 | 0.05351 ± 0.00067 | **+0.00010 ± 0.00075** | **1 勝 4 敗** |

  いずれも 5 seed を揃えた paired。`series_mean` の paired 差と SD は 2-Exp-48 と一致する。
  `recent_hour_d7`（`same_hour_recent_mean`、`recent_days` 7）では**中心化の優位が消える**。
  **判定に使うのは勝敗 1 勝 4 敗のほうである。** paired 差の平均 +0.00010 は SD 0.00075 の
  1/7 でゼロと区別できず、しかも符号は seed 59 単独（−0.00115）に依存する。
  他の 4 seed はすべて no_center 側（+0.00007〜+0.00071）であり、
  seed 17 を除いた 4 seed で取ると平均は −0.00003 に反転するが勝敗は 1 勝 3 敗のままである。
  平均の符号は seed 集合で動くが、勝敗は動かない。
  したがって「中心化は d7 では効かない」が妥当な読みで、「悪化する」と言うには足りない。
  したがって本実験の結論は「基準値 `series_mean`、予算 480 / patience 48」の
  2 条件を明示して書く。中心化の価値を基準値に依らない主張として書かない。
  基準値を跨いだ効果量の整理は 2-Exp-53 の担当である。
  なおこの反転は 240 / patience 24 での観測であり、480 / patience 48 で保たれるかは未知である。
  2-Exp-48 で効果量が学習量依存だった（−0.00594 → −0.00153）ことを踏まえると、
  「中心化の効果量は予算と基準値の両方に依存し、予算方向では縮小、基準値方向では消失する」
  という整理になる見込みである。

## smoke 確認

2026-11-09 にローカル（synthetic 128 系列 × 14 日、10 epoch・patience 2）で
2 variant × 1 seed = 2 run を実行し、**約 12 秒で完走**した。

### config の差分（機械的に確認）

2-Exp-48 の config と JSON を平坦化して突き合わせた結果、`experiments` 以外の差分は 4 点だけだった。

| 本番 config のキー | 2-Exp-48 | 2-Exp-54 |
|---|---|---|
| `train.epochs` | 240 | 480 |
| `train.early_stopping_patience` | 24 | 48 |
| `sweep.output_dir` | `runs/2-Exp-48_main_table_long_budget_freshretailnet` | `runs/2-Exp-54_centering_effect_long_budget_freshretailnet` |
| `train.output_dir` | 同上 `/base` | 同上 `/base` |

`experiments` は 4 本から 2 本に絞ったが、**残した 2 本の定義は 2-Exp-48 と完全一致**である
（`type` / `center_components` / `use_interaction` をキーごとに比較）。
run 数は 5 seed × 2 variant = 10。smoke config も同じく variant と出力先だけが 2-Exp-48 smoke と違う。

### 確認できたこと

- **2 variant が完走し、保存出力が揃う。** 各 run に `{global,day,hour,interaction}_component.npy`、
  `z_*.npy`、`best.pt`、`history.jsonl`、`metrics.json` が出た。
- **中心化が効いている。** `component_{day,hour,interaction_day,interaction_hour}_mean_abs` は
  centered で 2.4e-11〜1.4e-8、no_center で 0.131〜0.274。
- **残差側の経路は variant に依存しない。** `baseline_cell_mae` が 2 variant で完全一致
  （1.4467525482177734）。本番でも検算として使える。
- **予算が config から効いている。** `stopped_epoch` が 2 run とも 10（= 上限）で、
  patience 2 に当たる前に上限で打ち切られた。
- **成分解析コマンドが 2 variant 構成で通る。**
  `analyze_2_exp_44_component_interpretation.py` に `--variants output_decomp_centered
  output_decomp_no_center` を渡すと `aggregate` に両 variant が出て、
  目的 4 で使う `ss_share_*` / `interaction_rank1_share_median` / `global_component_sd` /
  `rel_bias_*` / `fit_r2` が揃った（smoke の出力はリポジトリに入れていない）。
- **P1 の突き合わせが可能である。** 2-Exp-48 の run に `history.jsonl` が残っており、
  epoch ごとの `valid_loss_residual_reconstruction` を持つ。

smoke の centered − no_center は −0.03184 だったが、synthetic・10 epoch の値であり
本番の効果量とは無関係である（経路確認のみ）。

## 本番結果

（実行後に追記）
