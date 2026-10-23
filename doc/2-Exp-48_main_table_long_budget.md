# 2-Exp-48: 主表 4 variant の長い epoch 予算での取り直し（epochs 240 / patience 24）

作成日: 2026-10-23
対応ボード項目: JIMA-02（主結果系列の決定と数値統一）の再開
関連: [2-Exp-46_epoch_budget_component_stability.md](2-Exp-46_epoch_budget_component_stability.md)、
[2-Exp-40_jima_main_results.md](2-Exp-40_jima_main_results.md)、
[2-Exp-44_component_interpretation.md](2-Exp-44_component_interpretation.md)、
[2-Exp-37_hyperparameter_sensitivity.md](2-Exp-37_hyperparameter_sensitivity.md)

（実験 ID は 45〜47 が使用済みのため 48 を使う。45 は encoder 構成比較、
46 は成分解釈の学習量依存性、47 は成分組み合わせの可視化。
作業場所は `worktrees/exp36〜43` と同じ流儀で `/home/shota/worktrees/exp48`。
`data/` はメイン checkout への symlink で共有し、`runs/` は worktree 内に作る。）

## 背景

2-Exp-40 は「epochs 上限 60・patience 8 で全 NN run が上限手前で停止したので、
学習量問題は解消され、主結果は収束後の数値である」と結論した。
2-Exp-46 はこれを否定した。

| 学習量 | `corrected_cell_mae`（centered、5 seed） | 停止状況 |
|---|---:|---|
| 12 epoch（2-Exp-35、3 seed） | — | 上限固定、early stopping なし |
| 60 / patience 8 | 0.04828 ± 0.00032 | best 27〜51、stopped 35〜59 |
| 120 / patience 24 相当（2-Exp-46） | **0.04698 ± 0.00049** | 5 run 中 3 run が上限 120 に張り付き（best 112〜116） |

120 epoch でも大半の run が上限まで改善を続け、MAE はさらに 0.0013 良くなった。
つまり 60/8 は「収束」ではなく「patience 8 で止まった点」である。
主表の 5 行はすべてこの条件で取られているため、行間の比較（centered 対 no_center、
centered 対 empirical、raw 対 calibration）が学習量の違いに汚染されている可能性がある。

本実験は、主表の 4 variant を同一条件で、収束するまで十分長い予算で取り直す。

## 目的

1. epochs 240 / patience 24 で、NN 3 variant が上限手前で停止するか（＝収束するか）を確認する。
2. 収束後の主表数値を取得し、2-Exp-40 の 60/8 版と比較する。
3. 主表の 3 つの主張が収束後も成立するかを確認する。
   - centered > no_center（JIMA-01）
   - centered > empirical ANOVA
   - calibration は収束後には効かない（2-Exp-40 の読み取り 4）
4. 成分アレイも保存し、2-Exp-46 で学習量依存と分かった指標
   （day と interaction の寄与比、global の系列間ばらつき）が 240 epoch でどうなるかを見る。

## 実験条件

2-Exp-40 のフルスケール設定から、epoch 予算と出力保存だけを変える。

- dataset: FreshRetailNet、train/valid/test = 6000/1500/1500、`validation_source: train_holdout`
- residual: `series_mean`、target `baseline_residual`
- model: dim10（10/10/10/8）、hidden 160
- train: epochs 上限 **240**、`early_stopping_patience` **24**、lr 1e-3
- seeds: 17, 23, 31, 47, 59
- variants: `empirical_anova_main_effects`、`output_decomp_no_center`、
  `output_decomp_centered`、`output_decomp_centered_calibrated`
- output: `save_latent_arrays` / `save_component_analysis_arrays` / `save_checkpoints` を有効化

合計 run 数: 1 scenario × 5 seed × 4 variant = 20。
patience は 2-Exp-46 の 16 からさらに広げた。120/16 で 3 run が上限に達したため、
同じ比率（上限の 1/10）を保ったまま上限を倍にする。

## 評価指標

| 指標 | 用途 |
|---|---|
| `best_epoch` / `stopped_epoch` | 目的 1。収束判定 |
| `corrected_cell_mae` / `corrected_cell_wape` | 主表の主指標 |
| `high_residual_top10_corrected_mae` | 外れケース行 |
| `corrected_cell_bias` | 系統誤差行 |
| `calibrated_corrected_cell_*` | calibration 行（raw と分離） |
| `ss_share_day` / `ss_share_interaction` / `global_component_sd` | 目的 4（2-Exp-44 の解析スクリプトで取得） |

## 事前に定める成功条件・分岐

1. **収束（目的 1）**: NN 3 variant のすべての run で `stopped_epoch` < 240 かつ
   `best_epoch` < `stopped_epoch`。満たせば「収束後の主表」と呼べる。
   上限に張り付く run があれば、本実験も「未収束」と報告し、
   主表は 60/8 のまま据え置いたうえで「学習量を増やすと改善が続く」ことを
   limitation に書く。
2. **JIMA-01（centered 対 no_center）**: paired 比較で centered が 5 seed 中 4 以上勝つ。
   勝てば中心化の主張は収束後も成立。負けるなら中心化の効果は学習量依存だったことになり、
   主表の構成を見直す。
3. **centered 対 empirical**: 同じく 5 seed 中 4 以上。
4. **calibration**: `calibrated_corrected_cell_mae` が raw を上回らない
   （＝ 2-Exp-40 の「収束後は較正の余地がない」が維持される）。
   逆転するなら calibration 行の記述を書き換える。
5. **主表の差し替え判断**: 1 を満たし、かつ 2・3 が成立した場合に限り、
   本実験の数値を JIMA 主表に採用する。1 を満たさない場合は採用しない。
6. **目的 4 は探索**: day と interaction の寄与比、global の sd は閾値を置かず、
   2-Exp-46 の 12 → 60 → 120 の系列に 240 の点を足して傾向だけ報告する。

## 実行方法

smoke（synthetic、10 epoch・patience 2。4 variant と保存経路の確認）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-48_main_table_long_budget_smoke.json
```

本番（ローカル GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-48_main_table_long_budget_freshretailnet.json
uv run python scripts/analyze_2_exp_44_component_interpretation.py \
  --run-dir runs/2-Exp-48_main_table_long_budget_freshretailnet/dim10 \
  --out-dir figures/2-Exp-48 --variants output_decomp_centered output_decomp_no_center
```

2-Exp-46 の 10 run（上限 60 と 120）が約 10 分だったので、
上限 240 の 20 run は 40〜70 分を見込む。

## 出力

```text
runs/2-Exp-48_main_table_long_budget_freshretailnet/
  dim10/seed_{17,23,31,47,59}/{4 variants}/
  all_results.csv / aggregate.csv / summary.json

figures/2-Exp-48/
  metrics.json / metrics_by_seed.csv / discount_response.csv / hour_share_quartiles.csv
```

## 解釈上の制約

- 本実験は学習量だけを変えた取り直しであり、モデル・データ・損失は 2-Exp-40 と同一である。
  差が出た場合、その原因は学習量に限定できる。
- `empirical_anova_main_effects` は学習を行わないため、epoch 予算の影響を受けない。
  2-Exp-40 と同じ値になるはずで、これが内部対照になる。
- 2-Exp-46 と同様、早期終了の停止位置は seed ごとに異なる。
  5 seed の SD にはそのゆらぎが含まれる。

## smoke 確認

2026-10-23 にローカル（synthetic、10 epoch・patience 2）で smoke を実行し、
4 variant が完走すること、`save_component_analysis_arrays` と `save_checkpoints` を
有効にした出力一式が保存されることを確認した。

## 本番結果

2026-10-23 にローカル GPU（RTX 5060 Ti）で全 20 run を実行し、約 34 分で完走した
（00:27:01 開始、01:01:17 終了）。成分解析は `figures/2-Exp-48/` に出力した。

### 収束（成功条件 1）

| variant | best epoch | stopped epoch | 上限 240 到達 |
|---|---|---|---|
| `empirical_anova_main_effects` | 1（学習なし） | 25 | — |
| `output_decomp_no_center` | 74〜239 | 98〜240 | 1 / 5 |
| `output_decomp_centered` | 138〜237 | 162〜240 | **4 / 5** |

**成功条件 1 ✗。240 epoch でも収束していない。**
centered は 5 run 中 4 run が上限 240 に張り付き（best 228〜237）、
早期に止まったのは seed 59（best 138 / stopped 162）だけだった。
2-Exp-46（120 で 3/5 張り付き）から状況は改善していない。
したがって成功条件 5 により、**本実験の数値は JIMA 主表に採用しない**。

### 主表の数値（5 seed 平均 ± SD）

| 行 | corrected MAE | corrected WAPE | top10 MAE | bias | 60/8 版（2-Exp-40） |
|---|---:|---:|---:|---:|---:|
| baseline のみ | 0.06966 | — | 0.27883 | ~0 | 同左 |
| empirical ANOVA | 0.05443 ± 0.00000 | 0.9221 | **0.17929** | **0.0000** | 0.05443 / 0.17935 |
| no_center | 0.04832 ± 0.00107 | 0.8186 | 0.19240 | −0.211 | 0.05422 / 0.23057 |
| **centered（raw）** | **0.04679 ± 0.00055** | **0.7927** | 0.18918 | −0.237 | 0.04828 / 0.19418 |
| centered + calibration | 0.04722 ± 0.00040 | — | — | — | 0.04878 |

学習なしの empirical は 2-Exp-40 と一致し（0.05443、top10 は 0.17929 対 0.17935 で
小数第 4 位まで一致）、内部対照として機能した。

### paired 比較（corrected MAE、5 seed）

| 比較 | 240 / patience 24 | 60 / patience 8（2-Exp-40） |
|---|---:|---:|
| centered − no_center | **−0.00153（5 勝 0 敗）** | −0.00594（5 勝 0 敗） |
| centered − empirical | **−0.00764（5 勝 0 敗）** | −0.00615（5 勝 0 敗） |

- **成功条件 2 ✓**: centered は no_center に 5 seed 全勝。中心化の主張は維持される。
  ただし **差は −0.0059 から −0.0015 へ約 1/4 に縮んだ**。
  no_center 自体が 0.05422 → 0.04832 と大きく改善しており、
  60/8 で見えていた中心化の優位の大部分は **no_center 側の学習不足**だった。
- **成功条件 3 ✓**: empirical には 5 seed 全勝で、差は −0.0062 から −0.0076 へ広がった。
  ただし top10（0.1793 対 0.1892）と無 bias（0.0000 対 −0.237）は依然 empirical が良い。
  相補性の構図は変わらない。
- **成功条件 4 ✓**: calibration は raw を上回らない（0.04722 対 0.04679、+0.0004）。
  「収束後は較正の余地がない」という 2-Exp-40 の読み取りは、
  さらに長い予算でも維持された。

### 成分指標の学習量依存（目的 4）

2-Exp-35 / 2-Exp-44 / 2-Exp-46 に本実験の点を足した系列。

| 指標 | 12 | 60 / 8 | 120 / 16 | 240 / 24 |
|---|---:|---:|---:|---:|
| `ss_share_hour` | 0.330 | 0.362 | 0.336 | 0.349 |
| `ss_share_day` | 0.0064 | 0.0268 | 0.0257 | 0.0296 |
| `ss_share_interaction` | 0.0183 | 0.0214 | 0.0328 | **0.0427** |
| interaction ÷ day | 2.9 | 0.80 | 1.28 | **1.44** |
| `fit_r2` | 0.380 | 0.416 | 0.425 | **0.441** |
| `global_component_sd` | 0.0024 | 0.0038 | 0.0086 | **0.0104** |
| sd ÷ \|mean\| | 0.085〜0.294 | 0.079〜0.402 | 0.156〜0.640 | **0.563〜0.787** |
| `corr_global_series_median` | ≈0 | 0.349 | 0.478 | **0.504** |
| `corr_day_component_empirical` | — | 0.950 | 0.943 | 0.912 |
| `interaction_rank1_share_median` | — | 0.991 | 0.957 | **0.850** |
| `corr_improvement_hour_share` | — | 0.725 | 0.720 | 0.748 |
| `top10_share_hour` | — | 0.604 | 0.555 | 0.540 |
| `rel_bias_global` | — | −0.305 | −0.305 | −0.270 |

読み取り。

1. **day と interaction**: 240 では interaction > day が 5 seed 全部で成立し、
   比は 1.44 まで開いた。60/8 だけが day 優位で、12・120・240 は interaction 優位である。
   学習量を増やすほど interaction の寄与が単調に増える（0.021 → 0.033 → 0.043）ことは
   一貫しているので、考察では「順序は学習量に依存する」とした 2-Exp-46 の方針を維持しつつ、
   「十分長い予算では interaction の寄与が day を上回り、増え続ける」と書ける。
2. **global 成分**: sd ÷ |mean| が 0.56〜0.79 まで上がり、
   `corr_global_series_median` も 0.504 に達した。
   「ほぼ定数」は完全に否定され、**系列ごとの中央値シフト**という性格が確定した。
   一方 `rel_bias_global` は −0.27〜−0.31 で安定しており、bias の局在は学習量に依らない。
3. **rank-1 性は弱まる**: 0.991 → 0.957 → 0.850。学習量が増えると interaction は
   単純な「日の重み × 時間帯形状」では表せない構造を持ち始める。
   2-Exp-46 で「向きは変わらない（0.90 超）」と書いたが、240 では 0.85 まで落ちた。
   **低ランク化（u = w(day) × s(h)）を修論の拡張として正当化する根拠は弱い**ので、
   考察では「短い予算では rank-1 に近い」と条件付きで書く。
4. **学習量に依らない指標**: `corr_improvement_hour_share`（0.72〜0.75）、
   `rel_bias_global`、hour が分散寄与と top10 帰属の両方で最大であること。
   考察の中核はこの 3 つに置くのが安全である。
5. no_center の `corr_day_component_empirical` は 240 でも −0.857〜+0.219 と不安定で、
   day 成分が実測日効果に対応しないという 2-Exp-44 の対比は維持された。

### 事前に定めた成功条件との照合

| # | 条件 | 判定 |
|---|---|---|
| 1 | 全 NN run が `stopped_epoch` < 240 | **✗** centered 4/5 が上限到達 |
| 2 | centered > no_center が 4 seed 以上 | ✓ 5/5（ただし差は 1/4 に縮小） |
| 3 | centered > empirical が 4 seed 以上 | ✓ 5/5（差は拡大） |
| 4 | calibration が raw を上回らない | ✓ +0.0004 で悪化 |
| 5 | 1 と 2・3 がそろえば主表を差し替える | **✗** 1 が崩れたため差し替えない |
| 6 | 成分指標は探索 | 上表のとおり報告 |

### 原稿への反映

- **主表は 2-Exp-40 の 60/8 版のまま据え置く**（成功条件 5）。
  ただし「early stopping により学習量問題は解消された／収束後の数値である」という
  2-Exp-40 の記述は誤りなので、「patience 8 による早期終了時点の数値」に改め、
  「予算を 240 まで伸ばすと centered は 0.04679、no_center は 0.04832 まで改善し、
  上限到達が続く」ことを limitation に明記する。
- **JIMA-01（中心化の効果）は効果量を学習量と一緒に書く**。
  60/8 で −0.0059、240/24 で −0.0015、いずれも 5 seed 全勝。
  「中心化は収束後も予測性能で有利だが、その差は学習量を増やすと縮む。
  中心化の主たる価値は解釈（成分の担当範囲の固定）である」という形にする。
  60/8 の −0.0059 だけを示して「中心化は性能でも大きく有利」と書くのは過大である。
- empirical との相補性（top10 と無 bias は empirical が優位）は両予算で不変なので、
  現在の記述のまま使える。
- 考察の成分解釈は、学習量に依らない 3 点（改善幅の事前指標、bias の global 局在、
  hour の支配）を中心に据え、rank-1 性と day/interaction の順序は条件付きで書く。

### 次に必要な実験

240 でも上限到達が続くため、どこで頭打ちになるかは未確定である。
予算を 480 / patience 48 まで倒して centered と no_center の 2 variant だけ回せば
（10 run、約 70 分）、主表を収束条件で確定できる見込みである。
その時点で centering の効果量が −0.0015 からさらに縮むかどうかも確認したい。
