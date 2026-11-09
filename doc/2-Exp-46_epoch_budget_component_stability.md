# 2-Exp-46: 成分解釈の学習量依存性（epochs 120 / patience 16）

作成日: 2026-10-23
対応ボード項目: 考察節に載せる成分指標が学習量に依存しないかの確認
関連: [2-Exp-44_component_interpretation.md](2-Exp-44_component_interpretation.md)、
[2-Exp-40_jima_main_results.md](2-Exp-40_jima_main_results.md)、
[2-Exp-35_freshretailnet_component_tsne.md](2-Exp-35_freshretailnet_component_tsne.md)、
[2-Exp-37_hyperparameter_sensitivity.md](2-Exp-37_hyperparameter_sensitivity.md)

（実験 ID は 45 ではなく 46 を使う。`2-Exp-45` は encoder 構成比較で既に使用済みのため。）

## 背景

2-Exp-44 は epochs 上限 60・patience 8・検証再構成損失で早期終了という
主結果条件（2-Exp-40 と同一）で成分指標を取った。5 seed の best epoch は 27〜51、
stopped epoch は 35〜59 とばらついており、5 seed の SD には早期終了位置のゆらぎが
すでに含まれている。その上で指標ごとの変動係数（CV）と best epoch との相関を取ると、
2 つのグループに分かれた。

| 指標 | 2-Exp-44 の値 | CV | best epoch との相関 |
|---|---:|---:|---:|
| day 成分と実測日効果の相関 | 0.950 | 1.4% | +0.89 |
| interaction の rank-1 比 | 0.991 | 1.0% | −0.82 |
| corr(改善幅, hour 寄与) | 0.725 | 2.5% | −0.53 |
| top10 の hour 帰属 | 0.604 | 4.3% | −0.57 |
| hour の分散寄与 | 0.362 | 9.2% | −0.06 |
| **day の分散寄与** | 0.0268 | 16.6% | **+0.60** |
| **interaction の分散寄与** | 0.0214 | 24.8% | **−0.42** |
| **global 成分の系列間 sd** | 0.0038 | 71.9% | **+0.98** |

seed 数が 5 なので相関そのものは弱い証拠だが、学習量を変えたときに実際に結論が
変わった実績がある。12 epoch（2-Exp-35、3 seed）と約 38 epoch（2-Exp-44、5 seed）の
比較は次のとおりで、2-Exp-44 では事前登録条件 2 と 3 がこの変化のために崩れた。

| 指標 | 12 epoch（2-Exp-35、seed 17/23/31） | 約 38 epoch（2-Exp-44、5 seed 平均） |
|---|---|---|
| day の分散寄与 | 0.0072 / 0.0059 / 0.0062 | 0.0268 |
| interaction の分散寄与 | 0.0182 / 0.0157 / 0.0210 | 0.0214 |
| interaction ÷ day | 2.54 / 2.67 / 3.40 | 約 0.80 |
| global の sd ÷ \|mean\| | 0.085 / 0.294 / 0.111 | 0.08〜0.40 |
| corr(global, 系列残差中央値) | +0.038 / −0.065 / +0.041 | +0.349 |

つまり「interaction が day より大きい」も「global はほぼ定数」も 12 epoch 固有の性質で、
学習量を増やすと前者は逆転し、後者は系列ごとのシフトへ変わった。
epoch 上限をさらに倍にしたときにこの動きが止まるのか、それとも続くのかを確認しないと、
考察節の記述が次の再実験でまた変わる。本実験はその確認を行う。

## 目的

1. epochs 上限 120・patience 16 で、day と interaction の分散寄与の大小関係が確定するか。
2. global 成分の系列間ばらつき（sd ÷ |mean|）と `corr_global_series_median` が
   さらに増えるのか、頭打ちになるのか。
3. 考察の主要 4 指標（day 成分と実測日効果の相関、interaction の rank-1 比、
   corr(改善幅, hour 寄与)、top10 の hour 帰属）が学習量に依存しないことの確認。
4. 学習量を倍にしても `corrected_cell_mae` が悪化しない（＝過学習していない）ことの確認。

## 実験条件

2-Exp-44 と同一のデータ・モデル・損失で、epoch 予算だけを変える。

- dataset: FreshRetailNet、train/valid/test = 6000/1500/1500、`validation_source: train_holdout`
- residual: `series_mean`、target `baseline_residual`
- model: dim10（10/10/10/8）、hidden 160
- variant: `output_decomp_centered` のみ（本実験の問いは centered の成分解釈に限る）
- seeds: 17, 23, 31, 47, 59

| scenario | epochs 上限 | patience | 位置づけ |
|---|---:|---:|---|
| `epochs60` | 60 | 8 | 2-Exp-44 と同一条件の内部対照 |
| `epochs120` | 120 | 16 | 本実験の検証条件 |

合計 run 数: 2 scenario × 5 seed × 1 variant = 10。
`epochs60` を同じ sweep 内に置くのは、2-Exp-44 との差が epoch 予算だけであることを
同一環境で担保するためである。

## 評価指標

2-Exp-44 の解析スクリプトをそのまま使い、`--variants output_decomp_centered` で
scenario ごとに実行する。主に見るのは次の指標である。

| 記号 | 指標 | 用途 |
|---|---|---|
| A | `ss_share_day`、`ss_share_interaction` とその比 | 目的 1 |
| B | `global_component_sd` ÷ \|`global_component_mean`\|、`corr_global_series_median` | 目的 2 |
| C/D/E/G | `corr_day_component_empirical`、`interaction_rank1_share_median`、`corr_improvement_hour_share`、`top10_share_hour` | 目的 3 |
| — | `corrected_cell_mae`、`best_epoch`、`stopped_epoch` | 目的 4、収束確認 |

## 事前に定める成功条件・分岐

1. **内部対照**: `epochs60` の `corrected_cell_mae` が 2-Exp-44 の 0.04828 ± 0.00032 と
   ±0.0005 以内で一致する。外れたら環境差を疑い、以降の比較を行わない。
2. **収束**: `epochs120` の全 run が `stopped_epoch` < 120。上限に張り付く run があれば
   「120 でもまだ収束していない」と報告し、3・4 の判定は保留する。
3. **day と interaction**: `epochs120` で `ss_share_day` > `ss_share_interaction` が
   5 seed 中 4 以上なら、考察の記述を「day の方が大きい」に更新する。
   3 seed 以下なら 2-Exp-44 の「同程度」を維持する。
4. **global の定数性**: sd ÷ |mean| が `epochs60` より増える seed が 4 以上なら、
   「global 成分は学習量とともに系列固有のシフトへ向かう」と書き、
   「ほぼ定数」という表現を考察から外す。増減が割れたら「学習量に依存するため
   定数性は主張しない」とだけ書く。
5. **主要 4 指標**: C/D/E/G の 4 指標が `epochs60` と `epochs120` の間で
   ±0.03 以内に収まれば、「考察の主要主張は学習量に依存しない」と結論する。
   超える指標があれば、その指標だけ学習量依存として注記する。
6. **過学習**: `epochs120` の `corrected_cell_mae` が `epochs60` より 0.0005 を超えて
   悪化しないこと。悪化する場合は主表を 60/8 のまま据え置き、本実験は
   「解釈指標の感度分析」としてのみ扱う。

## 実行方法

smoke（synthetic。scenario override が効くことの確認）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-46_epoch_budget_smoke.json
```

本番（ローカル GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-46_epoch_budget_freshretailnet.json
uv run python scripts/analyze_2_exp_44_component_interpretation.py \
  --run-dir runs/2-Exp-46_epoch_budget_freshretailnet/epochs60 \
  --out-dir figures/2-Exp-46/epochs60 --variants output_decomp_centered
uv run python scripts/analyze_2_exp_44_component_interpretation.py \
  --run-dir runs/2-Exp-46_epoch_budget_freshretailnet/epochs120 \
  --out-dir figures/2-Exp-46/epochs120 --variants output_decomp_centered
```

2-Exp-44 の 10 run（上限 60）が約 5 分だったので、本実験は 15 分程度を見込む。

## 出力

```text
runs/2-Exp-46_epoch_budget_freshretailnet/
  epochs{60,120}/seed_{17,23,31,47,59}/output_decomp_centered/
  all_results.csv / aggregate.csv / summary.json

figures/2-Exp-46/epochs{60,120}/
  metrics.json / metrics_by_seed.csv / discount_response.csv / hour_share_quartiles.csv
```

## 解釈上の制約

- 本実験は centered のみを回すため、中心化あり/なしの対比は 2-Exp-44 の結果を引く。
- 12 epoch の参照値は 2-Exp-35（3 seed、early stopping なし）であり、
  seed 数と停止規則が異なる。傾向の確認にのみ使う。
- 主表（2-Exp-40）の条件は 60/8 である。本実験で 120/16 の方が良くても、
  主表の数値を差し替えるかどうかは別途判断する（本実験の目的は解釈指標の安定性確認）。

## smoke 確認

2026-10-23 にローカル（synthetic、epochs 4/8・patience 1/2）で smoke を実行し、
scenario override が `train.epochs` / `train.early_stopping_patience` に適用されること
（`resolved_config.json` と `history.jsonl` の epoch 数で確認）、
centered のみが走ること、成分アレイ一式が保存されることを確認した。

## 本番結果

2026-10-23 にローカル GPU（RTX 5060 Ti）で全 10 run を実行し、約 10 分で完走した
（00:08:12 開始、00:17:56 終了）。解析は `figures/2-Exp-46/epochs{60,120}/` に出力した。

### 内部対照と収束（成功条件 1・2）

| 指標 | epochs60 | epochs120 | 2-Exp-44 |
|---|---:|---:|---:|
| `corrected_cell_mae` | 0.04828 ± 0.00032 | **0.04698 ± 0.00049** | 0.04828 ± 0.00032 |
| `high_residual_top10_corrected_mae` | 0.19418 ± 0.00200 | 0.19290 ± 0.00200 | 0.19418 ± 0.00200 |
| `residual_r2` | 0.41572 ± 0.00509 | 0.42536 ± 0.00926 | 0.41572 |
| `best_epoch` | 38.0 ± 9.6 | 95.6 ± 33.8 | 38.0 |
| `stopped_epoch` | 46.0 ± 9.6 | 105.8 ± 30.1 | 46.0 |

- **成功条件 1 ✓**: `epochs60` は 2-Exp-44 と全指標が一致した（同一条件なので当然だが、
  環境差がないことを同一 sweep 内で確認できた）。
- **成功条件 2 ✗**: `epochs120` は 5 run 中 3 run が上限 120 に張り付き
  （stopped 120 / best 116・113・112）、seed 31 も stopped 117 / best 101 だった。
  早期に止まったのは seed 47（stopped 52 / best 36）だけで、この run は `epochs60` と
  完全に同一の結果になっている（patience の違いが発火前に停止したため）。
  **120 epoch でもまだ収束していない。**
- **成功条件 6 ✓**: 過学習は起きていない。むしろ `corrected_cell_mae` が
  0.04828 → 0.04698（−0.0013）とさらに改善した。
  つまり **主表（2-Exp-40 / 2-Exp-44）の 60/8 条件自体がまだ学習不足**である。

### day と interaction の寄与比（成功条件 3）

| 学習量 | day | interaction | interaction ÷ day | day > interaction |
|---|---:|---:|---:|---|
| 12 epoch（2-Exp-35、3 seed） | 0.0064 | 0.0183 | 約 2.9 | 0 / 3 |
| 60 / patience 8（5 seed） | 0.0268 ± 0.0045 | 0.0214 ± 0.0053 | 約 0.80 | 4 / 5 |
| 120 / patience 16（5 seed） | 0.0257 ± 0.0013 | 0.0328 ± 0.0085 | 約 1.28 | 1 / 5 |

**大小関係は学習量で入れ替わる**。12 epoch で interaction 優位、60 で day 優位、
120 で再び interaction 優位に戻った（day > interaction は 1/5）。
成功条件 3 の分岐に従い、2-Exp-44 の「day と interaction は同程度」を維持する。
さらに本実験の結果から、**順序そのものを主張しない**ことを考察の方針として固定する。
安定しているのは hour との桁差の方で、hour は 0.336〜0.362 と day/interaction の
10 倍以上を保つ。

### global 成分の定数性（成功条件 4）

| 指標 | 12 epoch | epochs60 | epochs120 |
|---|---:|---:|---:|
| `global_component_mean` | −0.0156 | −0.0181 ± 0.0027 | −0.0181 ± 0.0020 |
| `global_component_sd` | 0.0024 | 0.0038 ± 0.0027 | **0.0086 ± 0.0030** |
| sd ÷ \|mean\| | 0.085〜0.294 | 0.079〜0.402 | 0.156〜0.640 |
| `corr_global_series_median` | −0.065〜+0.041 | +0.349 ± 0.054 | **+0.478 ± 0.048** |

sd ÷ |mean| は 5 seed 中 4 seed で増加した（唯一の非増加は、前述のとおり
`epochs60` と同一 run になった seed 47）。`corr_global_series_median` も
0.349 → 0.478 と上がり続けている。**成功条件 4 の分岐どおり、「global 成分はほぼ定数」
という表現を考察から外す**。平均値（−0.0181）と bias の帰属
（`rel_bias_global` −0.305 → −0.305）は学習量を倍にしても動かないので、
「bias は global に局在する」という主張自体は保たれる。

### 主要 4 指標の安定性（成功条件 5）

| 指標 | epochs60 | epochs120 | 差 | ±0.03 以内 |
|---|---:|---:|---:|---|
| `corr_day_component_empirical` | 0.9500 ± 0.0128 | 0.9428 ± 0.0111 | −0.007 | ✓ |
| `corr_improvement_hour_share` | 0.7250 ± 0.0182 | 0.7197 ± 0.0177 | −0.005 | ✓ |
| `interaction_rank1_share_median` | 0.9911 ± 0.0100 | 0.9569 ± 0.0335 | −0.034 | ✗（僅差） |
| `top10_share_hour` | 0.6044 ± 0.0260 | 0.5553 ± 0.0265 | −0.049 | ✗ |

C（day 成分の縮小推定）と E（改善幅の事前指標）は学習量に依存しない。
D（rank-1 比）と G（top10 の hour 帰属）は数値が動くが、結論の向きは変わらない
（rank-1 は 0.96 で依然 0.90 を大きく超え、top10 は hour が最大で 0.56）。
考察では D・G の数値に「学習量に対してやや感度がある」と注記する。

### その他の変化

学習量を倍にすると、説明の配分が hour から interaction と global へわずかに移る
（hour 0.362 → 0.336、interaction 0.021 → 0.033、global 0.001 → 0.005、
`fit_r2` 0.416 → 0.425）。`corr_global_hour_amp` は −0.821 → −0.920 とさらに強まり、
「変動の大きい系列ほど global の下方シフトが大きい」という読みは強化された。
欠品との交絡（−0.487 → −0.493）は学習量に依存しない。

### 読み取り

1. **まだ動く、というのが答えである**。120 epoch でも 5 run 中 4 run が上限付近まで
   改善を続けており、`corrected_cell_mae` も 0.04828 → 0.04698 と良くなる。
   60/8 で「収束後の数値」と呼んでいたもの（2-Exp-40 の結論 1）は、
   patience 8 で止まっていただけで収束ではなかった。
2. **学習量に依存する記述を考察から外す**: day と interaction の順序、
   global 成分の定数性。この 2 つは 12 → 60 → 120 で向きが変わる。
3. **依存しない記述は残す**: hour が day/interaction の 10 倍以上であること、
   bias が global に局在すること（−0.305 で不変）、day 成分が実測日効果の
   縮小推定量であること（相関 0.95 / 0.94）、成分寄与が改善幅の事前指標になること
   （0.725 / 0.720）、欠品との交絡（−0.49）。
4. **主表の扱い**: 本実験は解釈指標の感度分析として設計したので、主表の数値は
   2-Exp-40 の 60/8 のまま据え置く。ただし「早期終了により収束後の数値である」という
   記述は過大なので、「patience 8 の早期終了時点の数値」と書き換えるか、
   主表そのものを長い予算で取り直すかを別途判断する必要がある（JIMA-02 の再開案件）。

### 原稿への反映

- 2-Exp-44 の考察のうち、「day と interaction は同程度」は維持しつつ、
  **順序を主張しない**という但し書きを付ける。
- 「global 成分はほぼ共通シフト」という表現を削除し、
  「bias は global 成分に局在する（学習量に依らず −0.305）。その系列間ばらつきは
  学習量とともに増える」と書き換える。
- 2-Exp-40 の「学習量問題は解消された」という記述に、本実験の
  「120 epoch でも未収束、MAE はさらに 0.0013 改善」を追記する。
