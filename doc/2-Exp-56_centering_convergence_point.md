# 2-Exp-56: 中心化の収束点での優劣と打ち消し比の学習曲線（epochs 960 / patience 96）

作成日: 2026-11-09
対応ボード項目: JIMA-01（中心化の効果）の収束点での決着、解釈可能性の主張の裏づけ
関連: [2-Exp-54_centering_effect_long_budget.md](2-Exp-54_centering_effect_long_budget.md)、
[2-Exp-55_axis_usability_and_centering.md](2-Exp-55_axis_usability_and_centering.md)、
[2-Exp-53_baseline_diagnosis.md](2-Exp-53_baseline_diagnosis.md)、
[2-Exp-48_main_table_long_budget.md](2-Exp-48_main_table_long_budget.md)

（実験 ID は 55 まで main の索引で使用済みのため 56 を使う。）

## 背景

[2-Exp-54](2-Exp-54_centering_effect_long_budget.md) は 480 / patience 48 で
**中心化の精度優位が符号ごと反転する**ことを示した（paired +0.00159、centered 0 勝 5 敗）。
予算系列は −0.00594（60/8）→ −0.00153（240/24）→ +0.00159（480/48）である。

ただし判定には限定が付いている。**centered は 4/5 が上限 480 に到達し、
最終 50 epoch の傾きが 5 seed すべて負だった**（下降中に打ち切られた）。
一方 no_center は best が 384〜441 でその後の傾きが 4/5 で正に転じ、patience 48 が正常に発火した。
つまり no_center の 480 は収束値だが centered の 480 は収束値ではなく、
言えるのは「480 の予算では no_center のほうが速く収束する」までである。

| 2-Exp-54（480/48） | best epoch | stopped | 上限到達 | 最終 50 epoch の傾き |
|---|---|---|---|---|
| centered | 304〜480（平均 438.6） | 352〜480 | **4 / 5** | 5/5 が負 |
| no_center | 384〜441（平均 410.2） | 432〜480 | 1 / 5 | 4/5 が正 |

もう 1 つ、2-Exp-54 は打ち消し比（Σ\|成分\| ÷ \|Σ成分\|）が
**予算 8 倍（60 → 480）の範囲で centered 1.7〜1.8× とほぼ不変**であることを示した
（no_center は 5.4× → 3.7× → 3.2× と動き続ける）。
精度優位は予算で符号まで変わるのに、成分の大きさの読み取りやすさは動かない。
ただしこれは 2-Exp-54 では **run 開始後に追加した事後指標**であり、事前登録されていない。

## 目的

1. **収束点での優劣を決める。** centered が上限に当たらない予算を見つけ、
   「480 の予算では no_center が速い」を「収束点でも no_center が良い／良くない」に進める。
2. **打ち消し比を事前登録した指標として測る。** 2-Exp-55 / 2-Exp-54 はいずれも事後解析だった。
   本実験は予算 5 点目（960）を事前登録のうえで取る。
3. **打ち消し比の学習曲線を取る。** 2-Exp-53 側の仮説
   「中心化は実効的な自由度を削るので収束が遅く、同じ理由で成分が読める量になる」は、
   最終 epoch の値だけでは検証できない。epoch 方向の曲線で可否を判定する。
4. **seed 47 の収束点を検証する。** 2-Exp-54 で centered が上限に当たらず収束した唯一の seed
   （best 304 / stopped 352、`corrected_cell_mae` 0.046206）であり、それでも負けていた。
   patience 96 で best が 304 のままなら 480 の収束判定が正しかったことになる。

## 実装（本 PR に含むコード変更）

`output.cancellation_history_every` を追加した（既定 0 = 無効）。
値 N を与えると epoch 1 と N の倍数で test セットに推論を 1 回走らせ、
`cancellation_history.jsonl` に 1 行ずつ追記する。キーは
`epoch`、成分ごとの平均絶対値（`abs_global_component` / `abs_day_component` /
`abs_hour_component` / `abs_interaction_component`）、`abs_sum`（Σ\|成分\|）、
`joint`（\|Σ成分\|）、`ratio`（`abs_sum` ÷ `joint`）である。

- 定義は `scripts/analyze_2_exp_55_axis_usability.py` と同一にした
  （成分ごとに観測セルの平均絶対値を取って合算し、`joint` は成分和の平均絶対値）。
  最終 epoch の値と曲線が直接比較できる。
- アレイを毎 epoch 保存する案は採らなかった。1 snapshot が 15.4 MB（4 成分 × 3.85 MB）で、
  960 epoch を 32 刻みで 10 run 取ると 4.6 GB になる。曲線に必要なのはスカラー 3 本である。
- **RNG 状態を保存・復元している。** DataLoader の反復は `num_workers=0` でも
  グローバル RNG を 1 回消費する（`_BaseDataLoaderIter._base_seed`）ため、
  素朴に推論を挟むと以降の dropout マスクがずれて、hook なしの同一 seed run と軌跡が変わる。
  実際に smoke で epoch 2 から乖離することを確認し（train loss 差 8.6e−03）、
  hook の前後で CPU と CUDA の RNG 状態を退避・復元する形に直した。
- 単体テストを `tests/test_cancellation_ratio.py` に 4 件追加した
  （打ち消しが無いとき 1.0、打ち消すとき比が増大、観測セル限定、2-Exp-55 定義との一致）。

## 実験条件

2-Exp-54 の config から **4 点だけ**を変える。

| 項目 | 2-Exp-54 | 本実験 |
|---|---|---|
| `train.epochs` | 480 | **960** |
| `train.early_stopping_patience` | 48 | **96** |
| `output.cancellation_history_every` | なし | **32** |
| `sweep.output_dir` / `train.output_dir` | 2-Exp-54 の run 先 | 本実験の run 先 |

それ以外（dataset 6000/1500/1500、residual `series_mean`、model dim10・hidden 160、
lr 1e-3・batch 128、seeds 17/23/31/47/59、variants は
`output_decomp_no_center` と `output_decomp_centered` の 2 本）は同一である。
キー単位で差分を確認した（smoke 節）。patience は上限の 1/10 という比率を 2-Exp-46 以来維持している。

合計 run 数: 1 scenario × 5 seed × 2 variant = **10**。

## 評価指標

| 指標 | 用途 |
|---|---|
| `best_epoch` / `stopped_epoch` / 上限 960 到達数 | 目的 1。収束判定 |
| 最終 50 epoch の valid loss の傾き | 目的 1。平坦化して止まったのか下降中に切られたのかの区別 |
| `corrected_cell_mae` の paired 差・勝敗・LOO | 目的 1。向きの判定 |
| `cancellation_history.jsonl` の `ratio` | 目的 2・3。予算 5 点目と学習曲線 |
| `history.jsonl` の valid 系列 | P1 の内部対照 |
| `ss_share_*` / `interaction_rank1_share_median` / `global_component_sd` / `rel_bias_global` | 探索。予算系列の 5 点目 |

## 事前に登録する予測（自己チェック）

- **P1 内部対照**: 各 run の `history.jsonl` が 2-Exp-54 の同一 seed・同一 variant と、
  2-Exp-54 の `stopped_epoch` まで **bit 一致**する。2-Exp-54 では 2-Exp-48 に対して
  全 10 系列が bit 一致した。**これは hook が学習に影響しないことの本番規模での確認も兼ねる**
  （smoke では確認済み）。崩れたら hook の副作用または条件の取り違えとして先に報告する。
- **P2 centered の上限到達は減る**: 上限 960 到達が 0〜3 / 5 になる（480 では 4/5）。
  増える方向には出ないと予測する。
- **P3 no_center は改善しない**: すでに収束しているので、`corrected_cell_mae` は
  480 の 0.04437 から 0.0005 を超えて改善しない。best epoch も 384〜441 付近から動かない。
- **P4 向きは維持されるが差は縮む**: paired 差が 0 < Δ < +0.00159 に入る。
  centered だけが伸びるので縮むが、外挿（傾き −2.02e−06/epoch、追いつくには合計 ~1294 epoch）
  からは 960 では追いつかない。
- **P5 seed 47 の best は動かない**: 480 で唯一収束した seed なので、
  patience 96 でも best は 304 付近のままで `corrected_cell_mae` は 0.046206 付近である。
  304 より後にさらに良い点が見つかれば、patience 48 での収束判定が早すぎたことになる。
- **P6 打ち消し比は 5 点目でも不変**: centered が 1.7〜1.9× に収まる。
  no_center は 3.2× 付近かさらに下がる。
- **P7 学習曲線の形**: no_center の比は学習初期（epoch 32 以前）に最大を取り、
  その後下がって 3.2× 付近に落ち着く。centered は最初から 1.1〜1.9× に収まり大きく動かない。
  smoke（10 epoch）では no_center が 9.66×（epoch 1）→ 1.25×（epoch 4）→ 2.38×（epoch 10）、
  centered が 1.14×（epoch 1）→ 1.82×（epoch 10）だった。

### P7 の判定に分子・分母の分解を加える（run 中の精緻化。完全な事前登録ではない）

比は `abs_sum` ÷ `joint` なので、**`joint`（\|Σ成分\|）が小さい時点では比が自明に大きく出る。**
学習初期に予測がまだ小さければ、打ち消しを獲得していなくても比は上がる。
したがって P7 の判定には比の形だけでなく、**比の変化を分子と分母に分解した寄与**を使う。

区間ごとに Δlog(`ratio`) = Δlog(`abs_sum`) − Δlog(`joint`) を取り、

- 比の上昇が **`abs_sum` の増加**で説明されるなら「打ち消しを獲得した」と読める（仮説を支持）
- 比の上昇が **`joint` の縮小**で説明されるなら「予測が小さいだけ」であり支持にならない

を判定基準にする。`joint` がその時点で最終値の何倍かも併記する。

**この精緻化を書いた時点を記録しておく。** 2-Exp-53 側から本番 1 run（seed 17 の no_center）の
3 点（epoch 1 / 32 / 64 で比 4.61 → 5.16 → 6.20、`joint` 0.125 → 0.040 → 0.036）を
共有された**後**に書いたので、完全な事前登録ではない。
この 3 点では比の上昇が `joint` の縮小によるもので、smoke（epoch 1 の `joint` が最終値の
0.26 倍で比が 9.66×）とは逆の形である。つまり smoke からの外挿は効かない。
判定基準を先に固定しておくこと自体は、曲線全体を見る前なので意味がある。

## 事前に定める成功条件・分岐

1. **内部対照（P1）**: bit 一致すれば以降の判定に進む。
   崩れたら hook の副作用を疑い、原因を doc に記録してから回し直す。
2. **収束（目的 1）**: 全 10 run で `stopped_epoch` < 960 かつ
   centered の最終 50 epoch の傾きが正（＝曲がり角を過ぎた）。
   満たせば「**収束点での優劣**」として報告できる。
   上限到達が残るか傾きが負のままなら、本実験も「予算内での向き」に限定し、
   960 でも足りないことを limitation に書く。
   **`stopped_epoch` < 960 だけでは収束とは呼ばない**（2-Exp-40 で犯した誤りと同型）。
   傾きの符号を併せて見る。
3. **向き（目的 1）**: 条件 2 を満たした場合のみ収束点の判定として扱う。帯は事前に決める。

   | 帯 | paired 差 Δ | 読み方 |
   |---|---|---|
   | 逆転 | Δ ≤ 0 かつ centered 3 勝以上 | 480 の反転は予算不足の産物だった。JIMA-01 の精度の主張を復活させる |
   | 縮小 | 0 < Δ < +0.00100 | 向きは no_center 優位のまま。差は予算とともに縮む |
   | 維持 | Δ ≥ +0.00100 | 収束点でも no_center 優位。JIMA-01 の精度の主張は放棄する |

   判定は平均ではなく勝敗と t を前に出し、LOO の符号反転も併記する（2-Exp-54 と同じ方針）。
4. **seed 47（P5）**: best が 304 ± 32 の範囲なら 2-Exp-54 の収束判定は正しかったと確認できる。
   大きく後ろにずれたら、2-Exp-54 の「seed 47 は収束したうえで負けた」という記述を訂正する。
5. **打ち消し比（目的 2・P6）**: centered が 1.7〜1.9× に収まれば、
   **事前登録した条件下で**「中心化の解釈可能性への効果は予算に依存しない」と言える。
   予算系列は 60 / 120 / 240 / 480 / 960 の 5 点になる。
   崩れたら 480 までの不変は予算範囲に条件づく所見に格下げする。
6. **学習曲線（目的 3・P7）は探索**。ただし分岐だけ先に書く。
   no_center の比が初期に跳ね上がってから下がるなら
   「打ち消しは学習の初期に作られ、その後も解消されない」という形で仮説を支持する。
   最初から一定なら、収束速度と打ち消し比を同じ自由度の表れとみなす説明は否定される。
   **ただし比の動きは必ず分子・分母に分解してから読む**（P7 の節を参照）。
   `joint` の縮小で説明される上昇は支持に数えない。
   どちらでも因果は示せない（epoch 方向の相関にすぎない）ことを明記する。

   **事前登録した 2 つの形（初期に跳ね上がってから落ち着く / 最初から一定）の
   どちらにも当てはまらなかった場合の扱いも先に決めておく。**
   P7 の本文は書き換えず、「登録した形はどちらも観測されなかった」と記録したうえで、
   区間ごとの分解表（Δlog(`ratio`)、Δlog(`abs_sum`)、Δlog(`joint`)、
   成分が実際に増えたかの真偽）をそのまま出す。形に名前を付け直して
   事後の物語にしないためである。2-Exp-40 の訂正と同じ流儀で、
   登録文は残し、推論が当たらなかった旨を注記する。
   本番の途中 3 点（単調上昇）は登録した 2 つの形のどちらでもないので、
   この扱いが実際に必要になる可能性が高い。

## 実行方法

smoke（synthetic、10 epoch・patience 2、`cancellation_history_every` 2）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-56_centering_convergence_point_smoke.json
```

本番（ローカル GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-56_centering_convergence_point_freshretailnet.json
uv run --with matplotlib python scripts/analyze_2_exp_44_component_interpretation.py \
  --run-dir runs/2-Exp-56_centering_convergence_point_freshretailnet/dim10 \
  --out-dir figures/2-Exp-56 --variants output_decomp_centered output_decomp_no_center
uv run --with matplotlib python scripts/analyze_2_exp_55_axis_usability.py \
  --run-dir runs/2-Exp-56_centering_convergence_point_freshretailnet \
  --scenarios dim10 --seeds 17 23 31 47 59 \
  --variants output_decomp_centered output_decomp_no_center \
  --out-dir figures/2-Exp-56/axis_usability
```

所要見込みは 100〜120 分。2-Exp-54 の 10 run（上限 480）が 49 分で、
上限が倍かつ centered は上限近くまで走る見込みである。
hook の推論が 1 run あたり最大 30 回増えるので、その分（+5〜10 分）を見ている。

## 出力

```text
runs/2-Exp-56_centering_convergence_point_freshretailnet/
  dim10/seed_{17,23,31,47,59}/{output_decomp_no_center,output_decomp_centered}/
    history.jsonl / cancellation_history.jsonl / metrics.json / 成分アレイ
  all_results.csv / aggregate.csv / summary.json

figures/2-Exp-56/
  metrics.json / metrics_by_seed.csv / discount_response.csv / hour_share_quartiles.csv
  axis_usability/
```

## 解釈上の制約

- **上限と patience を同時に動かしている**（2-Exp-54 と同じ構図）。
  480 → 960 と 48 → 96 のどちらが効いたかは分離できない。
  分離が必要なら 960 / patience 48 を足す（+10 run）。
  予算を「上限 = patience × 10」で固定する流儀は 2-Exp-46 以来一貫しており、
  比較可能性はこの系列の内部で保たれる。
- **`stopped_epoch` < 960 は収束を意味しない。** 傾きの符号を併せて見る（成功条件 2）。
- **2 variant しかないので主表は揃わない。** `empirical_anova_main_effects` は
  学習に依らないので 0.05443 を引用できるが、calibration 行は引き継げない。
- **効果量は基準値 `series_mean`（倍率 46.33×）条件下の値である。** 2-Exp-53 の実測で、
  中心化の効果は残差に残る時間帯構造の量に対して減衰する（`recent_hour_d7` では 1 勝 4 敗）。
- **打ち消し比の曲線は test セットで測る。** 最終 epoch の値（best チェックポイントを
  読み直して計算）と曲線（その epoch の生のモデル）は測定点が違う。
  曲線の `best_epoch` 付近の値が最終値と一致するかは検算に使えるが、
  **曲線の終点を予算系列の 5 点目として読み替えてはいけない。**
  5 点目は best チェックポイントの保存アレイから計算する値である。
- **比は分母に依存する比である。** `joint`（\|Σ成分\|）が小さい時点では比が自明に大きく出るので、
  比の値だけを時系列で並べて解釈しない（P7 の節の分解を使う）。
- **曲線は因果を示さない。** 収束速度と打ち消し比が epoch 方向で連動していても、
  一方が他方を引き起こしているとは言えない。
- **「読める」と「役に立つ」は別のままである。** 打ち消し比が予算に依らないことを
  5 点目まで確認しても、読み取りやすさが下流の判断を改善することは測っていない。
  これは 2-Exp-55 と共通の残った問いである。
- `_corr` 系の指標は std ≤ 1e-8 で 0.0 を返す番兵を持つので、相関を引くときは振幅を併記する。

## smoke 確認

2026-11-09 にローカル（synthetic 128 系列 × 14 日、10 epoch・patience 2、
`cancellation_history_every` 2）で 2 variant × 1 seed = 2 run を実行し、約 9 秒で完走した。

### config の差分（機械的に確認）

2-Exp-54 の production config と平坦化して突き合わせ、`experiments` 以外の差分が
`train.epochs`（480 → 960）、`train.early_stopping_patience`（48 → 96）、
`output.cancellation_history_every`（なし → 32）、出力先 2 つの計 5 キーだけであることを確認した。
残した 2 variant の定義は 2-Exp-54 と完全一致である。

### hook が学習に影響しないこと

**初稿の hook は影響した。** `cancellation_history_every` だけを外した同一 config と
突き合わせると、epoch 1 は一致するが epoch 2 から乖離した（train loss 差 8.6e−03、
valid loss 差 2.1e−05）。原因は DataLoader の反復がグローバル RNG を 1 回消費することで、
以降の dropout マスクがずれていた。

RNG 状態の退避・復元を入れた後は、**hook あり / なしで `history.jsonl` が
2 variant とも完全一致**した。本番でも P1（2-Exp-54 との bit 一致）で再確認する。

**退避しているのは torch の CPU と CUDA の状態だけで、numpy は含めていない。**
推論経路（`predict_residuals` → DataLoader の反復 → `residual_batch` → model forward）に
グローバル numpy RNG を消費する処理が無いことを確認したためである。
リポジトリ内の numpy RNG はすべて `np.random.default_rng(seed)` で局所生成されており
（`masking.py`、`retail_data.py`、`residual_diagnostics.py`、`residual_result_analysis.py`）、
グローバル状態を触るのは学習開始前の `np.random.seed(seed)`（`train.py`）だけである。
`residual_batch` と dataset の `__getitem__`、model forward にも RNG 使用は無い。
したがって torch 側の退避で足りる。将来データ経路にグローバル numpy RNG が入った場合は
`np.random.get_state()` / `set_state()` を足す必要がある。

### 曲線が取れていること

| epoch | centered 比 | no_center 比 |
|---|---:|---:|
| 1 | 1.14× | **9.66×** |
| 2 | 1.30× | 2.64× |
| 4 | 1.68× | 1.25× |
| 6 | 1.82× | 1.37× |
| 8 | 1.80× | 1.93× |
| 10 | 1.82× | 2.38× |

synthetic・10 epoch なので値自体に意味はないが、**no_center の比が初期に大きく動き、
centered は最初から狭い範囲に収まる**という P7 の形は smoke でも見えている。
`epoch` 1 と 2 の倍数で記録されることも確認した。

## 本番結果

（実行後に追記）
