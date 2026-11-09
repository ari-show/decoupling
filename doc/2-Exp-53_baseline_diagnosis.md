# 2-Exp-53: 基準値診断 — どの基準値の後にどの構造が残るか

作成日: 2026-11-09
対応ボード項目: APIEMS C3（Diagnosis: 基準値選択そのものを診断対象にする）
関連: [2-Exp-16_residual_target_sensitivity.md](2-Exp-16_residual_target_sensitivity.md)、
[2-Exp-21_visualization.md](2-Exp-21_visualization.md)、
[2-Exp-48_main_table_long_budget.md](2-Exp-48_main_table_long_budget.md)、
[2-Exp-44_component_interpretation.md](2-Exp-44_component_interpretation.md)、
[conference/jima2026/qa_global_component.md](conference/jima2026/qa_global_component.md)、
[conference/apiems2026/paper-story.md](conference/apiems2026/paper-story.md)

## 背景

JIMA 2026 秋季大会（2026-10-25）の質疑で答えきれなかった論点が 1 つある。

> 従来研究の global/local 成分から、提案の全期間成分への意味接続が分からない。
> **平均による残差獲得は意味をなさないのでは？**

この問いは本研究の前提そのものを突いている。`r = y − b` と置いた瞬間、残差に何が残るかは
基準値 `b` が何を吸収したかで決まる。基準値が時間帯構造まで吸収していれば、
残差に時間帯成分は残らず、4 成分に分ける意味も薄れる。

答えの方向は [paper-story.md](conference/apiems2026/paper-story.md) の L7 と C3 に既に書いてある。

> L7: 実データでの効果は基準値に依存する。これは弱点ではなく「基準値診断」という機能である。
> C3: どの基準値の後にどの残差構造が残るかを測る評価プロトコルを提示し、
> 基準値選択そのものを診断対象にした。

ところが**この主張を主結果条件で測った実験が無い**。根拠は 2-Exp-16 / 2-Exp-21 の旧条件
（3 seed・12 epoch・early stopping なし）だけである。

| 基準値（2-Exp-16 / 21、3 seed・旧条件） | baseline → corrected | `hour_component_residual_profile_corr` |
|---|---|---:|
| `series_mean` | 0.0697 → 0.0524 | **+0.9912** |
| `same_hour_recent_mean` d7 | 0.0580 → 0.0564 | **−0.8840** |
| `weekday_same_hour_mean` | 0.0420 → **0.0427（悪化）** | ほぼ 0 |

向きは出ているが、seed 数・学習量・系列数がすべて主結果条件と違う。
APIEMS Abstract はこの旧条件を根拠に

> 同時間帯直近平均のように時間帯構造をすでに吸収した基準値では、追加補正の効果は限定的であった。

と limitation に書いている。

本実験はこれを主結果条件で測り直す。あわせて、**判定をモデルに依存しない形に作り替える**。
上表の `hour_component_residual_profile_corr` は学習済みモデルの出力を使うので、
「モデルが当てられなかった」のか「残差に構造が無かった」のかを分離できない
（2-Exp-51 で指摘した循環と同型の問題）。本実験では残差自身の軸構造に対する
**permutation 検定**を主判定に置く。

## 目的

1. 基準値を 4 種に振り、**モデル非依存の残差診断**（残差自身の軸振幅と permutation 検定）と
   **モデル依存の補正効果**を、2-Exp-48 と同一条件で同時に取得する。
2. モデル非依存の判定が補正効果の順序を予測できるかを確認する。
   できれば「**学習前に基準値を診断できる**」= C3 の deliverable になる。
3. 中心化の効果（centered − no_center）が基準値に依存するかを測る。
   2-Exp-48 で効果量が学習量に依存すると分かったので、基準値依存も押さえておく。
4. **global 成分の役割が基準値で変わるかを確認する。**
   `series_mean` では残差の系列平均が定義上ゼロ（2-Exp-44 で実測 2.4e-9）なので
   global は水準を担えない。他の基準値ではこの恒等式が成立しないため、
   global に水準が入り込む余地が生まれる。これが質疑の論点への直接の答えになる。

## 実験条件

2-Exp-48 の設定から、**`residual.baseline_method` / `residual.recent_days` と
`diagnostics.n_permutations` だけを変える。**

- dataset: FreshRetailNet、train/valid/test = 6000/1500/1500、`validation_source: train_holdout`
- model: dim10（10/10/10/8）、hidden 160
- train: epochs 上限 240、`early_stopping_patience` 24、lr 1e-3
- seeds: 17, 23, 31, 47, 59
- diagnostics: `n_permutations` 200、`permutation_chunk` 16
- output: `save_component_analysis_arrays` / `save_checkpoints` を有効化

### scenario（基準値の 4 種）

| scenario | `baseline_method` | 基準値が吸収する構造 | 位置づけ |
|---|---|---|---|
| `series_mean` | `series_mean` | 系列水準のみ | **内部対照**（2-Exp-48 を再現すべき） |
| `recent_hour_d7` | `same_hour_recent_mean`（`recent_days` 7） | 系列水準 + 時間帯（直近 7 日） | 主条件 |
| `recent_hour_d1` | `same_hour_recent_mean`（`recent_days` 1） | 系列水準 + 時間帯（直近 1 日） | 不安定な基準値の対照 |
| `cycle7_hour` | `weekday_same_hour_mean` | 系列水準 + 時間帯 + 7 日周期 | 時間帯プロファイルを厳密に消す |

並べる軸は「基準値の精度」ではなく「**基準値が吸収した構造**」である。
`d1` と `d7` は吸収する構造が同じで推定の安定性だけが違い、
smoke では `d1` のほうが基準値として**弱い**（MAE が `series_mean` より大きい）ことを確認した。
したがって「強い基準値ほど補正余地が小さい」ではなく
「**吸収された構造は取り戻せない**」が検証すべき命題になる。

### variant（3 本）

`empirical_anova_main_effects`、`output_decomp_no_center`、`output_decomp_centered`。

`output_decomp_centered_calibrated` は入れない。calibration は 60/8 でも 240/24 でも
効かないことが確定しており（2-Exp-40 読み取り 4、2-Exp-48 成功条件 4）、
本実験の問いと独立である。

合計 run 数: 4 scenario × 5 seed × 3 variant = **60**。
2-Exp-48 の 20 run が約 34 分だったので、同じ予算で 100 分前後を見込む。

## 評価指標

### モデル非依存（残差そのものの性質。学習を一切使わない）

| 指標 | 用途 |
|---|---|
| `diag_hour_relative_amplitude` / `diag_day_relative_amplitude` | 残差の軸プロファイル振幅 ÷ 平均絶対残差 |
| `diag_hour_permutation_pvalue` / `diag_day_permutation_pvalue` | **主判定。**軸方向を shuffle した帰無分布に対する p 値 |
| `diag_hour_null_relative_amplitude_p95` / `diag_day_*` | 帰無分布の 95% 点。振幅の有意水準の目安 |
| `diag_hour_profile_std` / `diag_day_profile_std` | 振幅そのもの（スケールつき） |
| `diag_residual_abs_mean` | 残差の大きさ |
| `baseline_cell_mae` / `baseline_cell_wape` / `baseline_cell_bias` | 基準値の精度 |

p 値は `(超過数 + 1) / (n + 1)` なので `n_permutations` 200 では下限 0.00498。
`p = 0.005` は「200 回の shuffle で 1 度も超えられなかった」を意味する。

> **本番結果による注記（2026-11-09 追記）**: この「主判定」の置き方は誤りだった。
> 実データ 6000 系列では帰無分布が締まるため、hour の p 値は 4 scenario のうち 3 つで
> 下限に張り付き判別力が無い。実際に判別したのは **帰無分布 95% 点に対する倍率**である。
> 主判定は `diag_*_permutation_pvalue` ではなく
> `diag_*_relative_amplitude` ÷ `diag_*_null_relative_amplitude_p95` に読み替える。
> 詳細は本番結果の「モデル非依存の診断」と成功条件 2 の判定を参照。

これらは variant に依存しないので、同一 scenario の 3 variant で同一値になる。
**一致しない場合は集計経路の誤りを示すので、検算として使う**（smoke で確認済み）。

### モデル依存（補正の効き方）

| 指標 | 用途 |
|---|---|
| `corrected_cell_mae` | 補正後の精度 |
| **相対改善率** = (`baseline_cell_mae` − `corrected_cell_mae`) / `baseline_cell_mae` | **scenario 間の横並びはこれで行う**（絶対差は基準値のスケールが違うため不可） |
| `hour_component_residual_profile_corr` | hour 成分が残差の時間帯プロファイルを捉えているか |
| `residual_hour_profile_corr` / `residual_hour_profile_mae` | **予測**残差プロファイルと実測の一致度（モデル依存。下記注意） |
| `component_ablation_without_{global,day,hour,interaction}_mae_delta` | どの成分が効いているか。目的 4 は global の delta |
| `corrected_cell_bias` | 系統誤差 |
| `high_residual_top10_{baseline,corrected}_mae` | 外れケースでの効き |
| `component_{day,hour,interaction_day,interaction_hour}_mean_abs` | 中心化違反（centered は ~0 のはず） |
| `best_epoch` / `stopped_epoch` | 基準値ごとに収束位置が違う可能性 |

> **注意**: `residual_hour_profile_corr` は名前に反して**モデル依存**である。
> 実装は `corr(実測残差の時間帯プロファイル, 予測残差の時間帯プロファイル)` であり、
> 残差自身の性質ではない。設計初稿ではこれをモデル非依存指標として扱っていたが、
> smoke で variant 間の値が割れたため誤りと判明し、分類を修正した（smoke 節に記録）。

### オフライン解析（成分アレイから）

2-Exp-44 の解析スクリプトを scenario ごとに流し、`ss_share_{global,day,hour,interaction}` と
`rel_bias_{total,global}` を取る。目的 4 の判定にはこの `rel_bias_global` を使う。

## 事前に登録する予測（自己チェック）

- **P1 内部対照**: `series_mean` × `output_decomp_centered` が 2-Exp-48 と小数第 5 位まで一致する
  （`corrected_cell_mae` 0.04679 ± 0.00055）。`empirical_anova_main_effects` は 0.05443 で完全一致する。
- **P2 吸収された構造は取り戻せない**: `diag_hour_permutation_pvalue` が
  `series_mean` で有意（≤ 0.01）、`recent_hour_d7` / `recent_hour_d1` / `cycle7_hour` で非有意。
  これが成立すれば「平均による残差獲得が意味をなすか」をモデルなしで判定できる。
- **P3 `cycle7_hour` の時間帯プロファイルは厳密ゼロ**: `weekday_same_hour_mean` は
  (7 日周期 × 時間帯) の平均を引くため、残差を全日で平均した時間帯プロファイルは
  恒等的にゼロになる。`diag_hour_relative_amplitude` が 0.000、
  `hour_component_residual_profile_corr` も 0 になる（smoke で 0.0000 を確認済み）。
- **P4 日軸は残る**: `diag_day_permutation_pvalue` は `series_mean` /
  `recent_hour_d7` / `recent_hour_d1` で有意、`cycle7_hour` でのみ非有意。
  時間帯を吸収する基準値は日効果を消さない。
- **P5 相対改善率が P2 の順序と一致する**: `series_mean` が最大で、
  hour が非有意な 3 scenario では大きく落ちる。
- **P6 hour ablation の減衰**: `component_ablation_without_hour_mae_delta` が
  `series_mean` の +0.0116 を最大として、他 scenario で縮む。
- **P7 過剰な基準値では補正が害になる**: `cycle7_hour` で相対改善率が負
  （`corrected_cell_mae` > `baseline_cell_mae`）。smoke では centered で −0.0031 だった。
- **P8 経験的 ANOVA も同じ向き**: 3 variant すべてで P5 の順序が保たれる。
  基準値が吸収した構造は、NN でも経験推定でも取り戻せない。
- **P9 global の役割の変化**: `series_mean` 以外の scenario で
  `component_ablation_without_global_mae_delta` と `|rel_bias_global|` が増える。

P1 が崩れた場合は条件の取り違えとして**他の判定を止めて先に報告する**。

## 事前に定める成功条件・分岐

1. **内部対照（P1）**: 一致すれば以降の判定に進む。
   一致しなければ scenario override が `residual` に届いていない等の実装問題として扱い、
   原因を doc に記録してから回し直す。
2. **モデル非依存の診断（P2・P4・P5）**: permutation 検定の有意・非有意が
   相対改善率の大小と対応すれば、**「学習前に基準値を診断できる」を C3 の deliverable として主張する**。
   対応しない場合は「診断には学習後の `hour_component_residual_profile_corr` が必要」に改め、
   C3 の記述を事後指標に限定する。
3. **適用条件への反転（P7）**: 成立すれば、limitation ではなく**適用条件**として書く。
   「基準値が日周期 × 時間帯の平均まで吸収している場合、残差成分分解は適用しない」という
   明示的な除外条件になる。成立しなければ「改善幅が小さくなるだけ」と弱める。
4. **中心化の基準値依存（目的 3）**: 閾値を置かず探索。
   centered − no_center の paired 差を scenario ごとに報告し、
   2-Exp-48 の学習量依存（−0.00594 → −0.00153）と並べる。
   有意な差が残るのが `series_mean` だけなら、中心化の主張の適用範囲も基準値に条件づく。
5. **global の役割（目的 4・P9）**: 閾値を置かず探索。
   成立すれば「`series_mean` を使う限り global は水準を担えない」という
   qa_global_component.md の論法が**基準値に依存する条件つきの主張**であることを明記する。
6. **P3 は構造的予測**: 崩れたら実装理解の誤りなので、他の判定より先に報告する。

## 実行方法

smoke（synthetic、10 epoch・patience 2。4 scenario × 3 variant の経路確認）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-53_baseline_diagnosis_smoke.json
```

本番（ローカル GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-53_baseline_diagnosis_freshretailnet.json
```

成分アレイの解析は scenario ごとに流す:

```bash
for s in series_mean recent_hour_d7 recent_hour_d1 cycle7_hour; do
  uv run --with matplotlib python scripts/analyze_2_exp_44_component_interpretation.py \
    --run-dir runs/2-Exp-53_baseline_diagnosis_freshretailnet/$s \
    --out-dir figures/2-Exp-53/$s \
    --variants output_decomp_centered output_decomp_no_center
done
```

## 出力

```text
runs/2-Exp-53_baseline_diagnosis_freshretailnet/
  {series_mean,recent_hour_d7,recent_hour_d1,cycle7_hour}/seed_{17,23,31,47,59}/{3 variants}/
  all_results.csv / aggregate.csv / summary.json

figures/2-Exp-53/
  {series_mean,recent_hour_d7,recent_hour_d1,cycle7_hour}/
    metrics.json / metrics_by_seed.csv / discount_response.csv / hour_share_quartiles.csv
```

## 解釈上の制約

- **`weekday_same_hour_mean` の「曜日」は実カレンダーの曜日ではない。**
  実装（`_weekday_same_hour_mean_torch`）は窓内の日インデックスを `% 7` した値を使う。
  2-Exp-47 で mod 7 の行 3・4 が休日フラグ比率 1.000 と分かっているので位相は窓内で一貫するが、
  曜日名は特定できない。本 doc では `cycle7_hour`（7 日周期 × 時間帯平均）と呼ぶ。
- **`same_hour_recent_mean` は窓の初日に窓全体の時間帯平均を使う。**
  実装は `start == day` のとき `hour_mean`（窓全体の平均）で埋めるため、
  初日の基準値には後続日の情報が入る。窓内評価では既存実験と同じ扱いだが、
  未来日評価に持ち込む場合は別途切り分けが必要である。
- **絶対 MAE は scenario 間で横並びできない。** 基準値ごとに残差のスケールが違う。
  横並びは相対改善率で行い、絶対値は scenario 内の variant 比較にのみ使う。
- **`cycle7_hour` は day 成分と交互作用成分の担当も構造的に削る。**
  7 日周期 × 時間帯の平均を引いた後の残差には、周期的な日効果が残らない。
  この scenario で寄与が落ちるのは提案の不利ではなく定義上の帰結である。
- **permutation 検定は「軸方向に構造があるか」しか言わない。**
  非有意は「その軸の主効果が平均操作で消えた」ことを示すだけで、
  交互作用が残っているかは別に見る必要がある（`diag_*` に交互作用の検定は無い）。
- **p 値の下限は 0.00498**（`n_permutations` 200）。より細かい水準が必要なら n を上げる。
- **log1p 系の基準値は除外した。** `log1p_series_mean` / `log1p_same_hour_recent_mean` は
  対数スケールで残差を作るため MAE の単位が他 scenario と異なり、相対改善率でも横並びできない。
- **240 epoch でも未収束である**（2-Exp-48 成功条件 1 ✗）。本実験の数値も
  「`patience 24` による早期終了時点」であり、収束後の値ではない。
  scenario 間で `stopped_epoch` が揃わない可能性があるため、必ず併記する。

## smoke 確認

2026-11-09 にローカル（synthetic 128 系列 × 14 日、10 epoch・patience 2、`n_permutations` 200）で
本番と同じ config 構成の 4 scenario × 3 variant × 1 seed = 12 run を実行し、
**約 6 秒で完走**した。permutation 検定を全 run で有効にしてもコストは無視できる。

### 確認できたこと

- **scenario override が `residual` に届いている。** `baseline_cell_mae` が
  scenario ごとに異なる（1.44675 / 1.38259 / 1.68154 / 0.80430）。
- **`cycle7_hour` の時間帯プロファイルは厳密ゼロ（P3 の構造的予測）。**
  `diag_hour_relative_amplitude` と `hour_component_residual_profile_corr` が
  3 variant すべてで 0.0000 になった。
- **permutation 検定が狙いどおり効く。** synthetic での値（3 variant で完全一致）:

  | scenario | `diag_hour_relative_amplitude` | hour p 値 | `diag_day_relative_amplitude` | day p 値 |
  |---|---:|---:|---:|---:|
  | `series_mean` | 0.3726 | **0.0050** | 0.2189 | **0.0050** |
  | `recent_hour_d7` | 0.0325 | 1.0000 | 0.2271 | **0.0050** |
  | `recent_hour_d1` | 0.0268 | 1.0000 | 0.1823 | **0.0050** |
  | `cycle7_hour` | 0.0000 | 1.0000 | 0.0811 | 0.1443 |

  P2・P4 の形（hour は series_mean でのみ有意、day は cycle7_hour でのみ非有意）が
  synthetic で既に出ている。本番で再現するかが判定になる。
- **P7（過剰な基準値では補正が害になる）も synthetic で出ている。**
  `cycle7_hour` の centered 相対改善率が −0.0031。
- **`d1` は基準値として弱い。** `baseline_cell_mae` 1.68154 が `series_mean` 1.44675 より大きい。
  scenario の並びを「基準値の精度」ではなく「吸収した構造」に置く設計判断の裏づけになった。

### 設計の修正（smoke で見つけた誤り）

初稿は `residual_hour_profile_corr` / `residual_hour_profile_mae` を
モデル非依存指標に分類していたが、**同一 scenario の 3 variant で値が割れた**
（`series_mean` で 0.9547 / 0.9639 / 0.9999）。
実装を確認すると `corr(実測残差の時間帯プロファイル, **予測**残差の時間帯プロファイル)` であり、
モデル依存だった。モデル非依存の判定は `diag_*` 系に限定し、主判定を permutation 検定へ移した。

`baseline_cell_mae` / `diag_hour_relative_amplitude` / `diag_residual_abs_mean` は
3 variant で完全一致することを確認しており、検算として使える。

## 本番結果

2026-11-09 にローカル GPU（RTX 5060 Ti）で 4 scenario × 5 seed × 3 variant = 60 run を実行し、
**全 run 完走**した（18:10:44 開始、19:36:01 終了、約 85 分）。欠損 cell は無い。

### 実行記録（事故と復旧）

本番 sweep は**二重に起動された**。18:10:44 に起動した本番 sweep が走っている状態で、
それに気づかず 18:16:02 に 2 本目を起動し、ユーザーの判断で 18:48 に後発が停止された。
2 プロセスは同一の `output_dir` に書いていたが、**同一 cell を同時刻に書いた瞬間は無い**
（後発が常に 1 cell 分遅れており、cell ごとの開始・終了時刻に重なりが無いことを確認した）。
したがって各 cell の指標は、それぞれ自分の完結した学習から算出されている。

停止の副作用で `recent_hour_d7/seed_17/output_decomp_centered` のディスク成果物
（`metrics.json`・成分アレイ・`best.pt`）が欠損した。指標行自体は seed 階層の
`summary.json` に残っていたため主表には影響しないが、成分解析が 4 seed に落ちるため
sweep 完走後に当該 cell のみ再実行した（19:36:04〜19:43:11）。

**再実行は正典の値を小数第 6 位まで完全に再現した。**

| variant | 正典（sweep 出力） | 再実行 | 差 |
|---|---:|---:|---:|
| `empirical_anova_main_effects` | 0.059885 | 0.059885 | +0.000000 |
| `output_decomp_no_center` | 0.052628 | 0.052628 | +0.000000 |
| `output_decomp_centered` | 0.053247 | 0.053247 | +0.000000 |

`hour_component_residual_profile_corr`（+0.9999 / −0.7602 / −0.8092）と
`stopped_epoch`（25 / 240 / 240）も一致した。約 1.5 時間後・GPU コンテキストを変えた
独立再実行での一致なので、**同一 seed・同一 config の決定論性は集約指標レベルで確認できた**
（bit 一致の確認ではない。`cudnn.benchmark = True` と AMP の留保は残る）。

本 doc の表は**すべて sweep 自身が出力した `summary.json`（60 run）を正典とする**。
再実行は成分アレイの復元が目的であり、値が一致したため成分解析と主表の整合も保たれている。

### 内部対照（成功条件 1、P1）

`series_mean` scenario が 2-Exp-48 の `dim10` scenario を**完全に再現した**。

| variant | 2-Exp-53 | 2-Exp-48 | 差 |
|---|---:|---:|---:|
| `empirical_anova_main_effects` | 0.05443 ± 0.00000 | 0.05443 ± 0.00000 | +0.00000 |
| `output_decomp_no_center` | 0.04832 ± 0.00107 | 0.04832 ± 0.00107 | +0.00000 |
| `output_decomp_centered` | 0.04679 ± 0.00055 | 0.04679 ± 0.00055 | +0.00000 |

`baseline_cell_mae` 0.06966、`diag_hour_relative_amplitude` 0.54176、
`diag_day_relative_amplitude` 0.12352 も一致。標準偏差まで一致しているので
平均が偶然合ったのではなく seed ごとに一致している。**成功条件 1 を満たすので以降の判定に進む。**

モデル非依存指標が同一 scenario の 3 variant で完全一致することも確認した（検算、不一致ゼロ）。

### モデル非依存の診断（主判定）

| scenario | `baseline_cell_mae` | hour 振幅 | 帰無 p95 | **倍率** | hour p | day 振幅 | 帰無 p95 | **倍率** | day p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `series_mean` | 0.06966 | 0.54176 | 0.01170 | **46.32×** | 0.0050 | 0.12352 | 0.01098 | 11.25× | 0.0050 |
| `recent_hour_d1` | 0.06651 | 0.10393 | 0.01359 | **7.65×** | 0.0050 | 0.13530 | 0.01479 | 9.15× | 0.0050 |
| `recent_hour_d7` | 0.05796 | 0.04147 | 0.01238 | **3.35×** | 0.0050 | 0.13663 | 0.01384 | 9.87× | 0.0050 |
| `cycle7_hour` | 0.04200 | **5.379e-09** | 0.01326 | **0.00×** | **1.0000** | 0.12745 | 0.01441 | 8.83× | 0.0050 |

**p 値は判別しなかった。** hour の permutation p 値は `series_mean` / `recent_hour_d1` /
`recent_hour_d7` の 3 条件すべてで下限 0.00498（201 回の shuffle で 1 度も超えられず）であり、
事前登録 P2 の「`series_mean` でのみ有意」は成立しない。6000 系列では帰無分布が締まって
相対振幅の 95% 点が 0.0117〜0.0136 しかないため、振幅 0.0415 でも 3.35 倍あり有意になる。
smoke（128 系列・合成）で p = 1.0000 と綺麗に分かれたのは帰無分布が緩かったためで、
実データには外挿できなかった。

**判別したのは効果量（帰無分布 95% 点に対する倍率）である。** 46.32× → 7.65× → 3.35× → 0.00×
と 1 桁以上動く。以降の判定はこの倍率で行う。

`cycle7_hour` の hour 振幅は **5 seed すべてで同一の 5.379e-09**（他 scenario の約 1/10⁸）で、
hour p = 1.0000。`weekday_same_hour_mean` が mod 7 × 時間帯の平均を引くため残差の
時間帯プロファイルが恒等的に消える、という P3 の構造的予測が実データで確認された。
浮動小数の丸め残差なので「厳密に 0」ではなく 5.4e-09 と記録する。

**日軸は 4 scenario すべてで有意（p = 0.0050）で、倍率も 8.83〜11.25× とほぼ不変である。**
`cycle7_hour` でも 8.83× 残る。事前登録 P4 は「`cycle7_hour` でのみ非有意」と予測していたが
成立しない。`weekday_same_hour_mean` は (mod 7 クラス, 時間帯) ごとの平均をゼロにするだけで、
個々の日の平均をゼロにはしないため、日ごとの偏差は残る。smoke では day p = 0.1443 で
非有意だったので、**これも合成データから外挿できなかった項目である**。

### 補正効果

絶対 MAE は scenario 間で横並びできない（基準値ごとに残差のスケールが違う）。
横並びは相対改善率 = (`baseline_cell_mae` − `corrected_cell_mae`) / `baseline_cell_mae` で行う。

| scenario | variant | `corrected_cell_mae` | 相対改善率 | `stopped_epoch` |
|---|---|---:|---:|---:|
| `series_mean` | anova | 0.05443 ± 0.00000 | +21.87% | 25.0 |
| | no_center | 0.04832 ± 0.00107 | +30.64% | 161.2 |
| | **centered** | **0.04679 ± 0.00055** | **+32.84%** | 224.4 |
| `recent_hour_d7` | anova | 0.05988 ± 0.00000 | **−3.31%** | 25.0 |
| | no_center | 0.05351 ± 0.00067 | +7.69% | 240.0 |
| | centered | 0.05361 ± 0.00036 | +7.51% | 220.2 |
| `recent_hour_d1` | anova | 0.07078 ± 0.00000 | **−6.42%** | 25.0 |
| | no_center | 0.06634 ± 0.00007 | +0.26% | 101.6 |
| | centered | 0.06522 ± 0.00142 | +1.95% | 131.6 |
| `cycle7_hour` | anova | 0.04497 ± 0.00000 | **−7.08%** | 25.0 |
| | no_center | 0.04203 ± 0.00002 | **−0.07%** | 97.8 |
| | centered | 0.04230 ± 0.00061 | **−0.73%** | 76.4 |

**相対改善率は倍率の順序と一致しない。** 倍率は `recent_hour_d1`（7.65×）が
`recent_hour_d7`（3.35×）より大きいのに、改善率は d1（+1.95%）が d7（+7.51%）を下回る。
事前登録 P5 は「`series_mean` が最大で、hour が非有意な 3 scenario では大きく落ちる」としており、
最大が `series_mean` である点は成立するが、残り 3 条件の順序は予測できていない。

d1 は直近 1 日だけで基準値を作るため推定が不安定で、残差に残る時間帯構造の多くがノイズ由来と
考えられる。**構造として検出されても精度には変換できない。**
`no_center` の改善率が +0.26% しかなく、d1 の小さな改善のほとんどが中心化由来であることも
この読みと整合する。

**P7（過剰な基準値では補正が害になる）は成立した。** `cycle7_hour` の相対改善率は
centered −0.73%、no_center −0.07% でいずれも負。経験的 ANOVA はさらに強く、
`recent_hour_d7` −3.31%、`recent_hour_d1` −6.42%、`cycle7_hour` −7.08% と
**時間帯を吸収する基準値すべてで基準値より悪化する**。

**P8 は成立した。** 3 variant すべてで改善率の順序が
`series_mean` > `recent_hour_d7` > `recent_hour_d1` > `cycle7_hour` に揃う。
基準値が吸収した構造は、NN でも経験推定でも取り戻せない。

**学習量について。** `recent_hour_d7` の `no_center` は 5 seed すべてが上限 240 epoch に到達した。
2-Exp-48 の「240 epoch でも未収束」は基準値を変えても続いており、本実験の数値も収束値ではない。
`stopped_epoch` は scenario で大きく違う（`cycle7_hour` centered 76.4 〜 `recent_hour_d7` no_center 240.0）
ので、scenario 間の比較には停止位置の差が混入している。

### 中心化の基準値依存（成功条件 4）

同一 seed の paired 差（centered − no_center、負なら中心化が有利）。

| scenario | hour 倍率 | paired 差 | sd | t | centered 勝敗 | LOO 符号反転 |
|---|---:|---:|---:|---:|---|---|
| `series_mean` | 46.32× | **−0.00153** | 0.00108 | **−3.18** | **5 勝 0 敗** | **0/5** |
| `recent_hour_d1` | 7.65× | −0.00112 | 0.00146 | −1.72 | 3 勝 2 敗 | 0/5 |
| `recent_hour_d7` | 3.35× | +0.00010 | 0.00074 | +0.30 | 1 勝 4 敗 | **2/5** |
| `cycle7_hour` | 0.00× | +0.00028 | 0.00060 | +1.03 | 2 勝 3 敗 | 0/5 |

**中心化の効き方は hour 倍率に対して単調に減衰する。ただし倍率が正の 3 点に限る。**
倍率 46.32× → 7.65× → 3.35× に対し、t が −3.18 → −1.72 → +0.30、
勝敗が 5 勝 0 敗 → 3 勝 2 敗 → 1 勝 4 敗 と揃う。
中心化は `series_mean` 固有の現象ではなく、**残差に残る時間帯構造の量に比例して効く**。

**`cycle7_hour`（0.00×）はこの系列に並べない。** 構造が無ければ中心化が働く対象も無いので、
ここでの paired 差は雑音である。5 seed のうち 4 つが ±2.5e-5 に収まり
（+2.4e-05 / −1.5e-05 / −1e-06 / +2.5e-05）、seed 47 のみ +0.00135 で平均と t を動かしている。
t = +1.03・2 勝 3 敗を減衰の 4 点目として読むと、勝敗が 1 勝 4 敗から 2 勝 3 敗に戻るため
系列が破れる。**構造がゼロの条件では centered と no_center の比較自体が定義されない**ものとして
別枠に置く。

確立しているのは `series_mean` だけである。符号反転 0/5・全部分集合で 4 勝 0 敗・
LOO 平均 −0.00125〜−0.00183 で、平均値で記述できるのはこの条件に限る。
`recent_hour_d1` は t = −1.72・3 勝 2 敗で**弱く centered 側に傾くが確立していない**。
`recent_hour_d7` は **LOO で 2/5 反転する**（seed 17 を落とすと −0.000030、seed 31 を落とすと
−0.000051）ので、平均の符号自体が n=5 では定まらない。正確には
**「`recent_hour_d7` では中心化の効果はゼロと区別できず、平均の符号も定まらない。勝敗 1 勝 4 敗は安定」**。
`cycle7_hour` は 4 seed が ±2.5e-5 に収まり、seed 47 のみ +0.00135 で平均が動く。

### 成分解析（成功条件 5、目的 4、P9）

残差分散のうち各成分が説明する割合（`ss_share_*`）と global の相対バイアス。

**`output_decomp_centered`**

| scenario | global | day | hour | interaction | **合計** | `rel_bias_global` |
|---|---:|---:|---:|---:|---:|---:|
| `series_mean` | 0.00681 | 0.02958 | **0.34853** | 0.04273 | **0.42765** | −0.26949 |
| `recent_hour_d7` | 0.00118 | 0.03906 | 0.00761 | **0.06651** | 0.11436 | −0.12273 |
| `recent_hour_d1` | 0.00072 | 0.01564 | 0.00644 | 0.01964 | 0.04245 | −0.03531 |
| `cycle7_hour` | 0.00006 | 0.00000 | 0.00000 | 0.00000 | **0.00006** | +0.00843 |

**`output_decomp_no_center`**

| scenario | global | day | hour | interaction | 合計 | `rel_bias_global` |
|---|---:|---:|---:|---:|---:|---:|
| `series_mean` | 0.00002 | 0.00024 | 0.06487 | 0.18931 | 0.25444 | +0.22420 |
| `recent_hour_d7` | 0.00000 | 0.00003 | 0.00052 | 0.17522 | 0.17576 | +0.31364 |
| `recent_hour_d1` | 0.00000 | 0.00015 | 0.01261 | 0.00049 | 0.01325 | +0.31464 |
| `cycle7_hour` | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | +0.31404 |

**基準値が時間帯を吸収すると、中心化された分解の重心が hour から interaction と day に移る。**
`series_mean` では hour が 0.34853 で支配的だが、`recent_hour_d7` では hour が 0.00761 に落ち、
interaction が 0.06651、day が 0.03906 で上回る。

**`cycle7_hour` では分解全体が崩壊する。** centered の `ss_share` 合計が 0.00006 で、
4 成分で残差分散をほとんど説明していない。`component_ablation_without_*_mae_delta` も
day −0.00000 / hour +0.00000 / interaction +0.00000 と全成分がゼロで、モデルは
実質 global のみに縮退している。日軸には 8.83× の構造が残っているのに使われていない。

一方 `no_center` は同条件で成分が生きている（ablation global +0.01713 / day +0.02200 /
hour +0.01284 / interaction +0.01877）。**にもかかわらず最終 MAE はほぼ同一**
（0.04203 対 0.04230、paired +0.00028）。

これは ablation 指標の意味を限定する。**`component_ablation_without_X_mae_delta` が大きいことは
「成分 X が精度に貢献している」ではなく「モデルの出力が X に依存している」しか意味しない。**
成分を持たない centered と、大きな成分を持ちそれに強く依存する no_center が同じ精度に
着地している。同じ論点は `recent_hour_d7` の経験的 ANOVA にも現れており、
`hour_component_residual_profile_corr` が +0.9999（時間帯プロファイルを完全に捉えている）
なのに `component_ablation_without_hour_mae_delta` は +0.00007 で、
**構造を捉えていることと精度が上がることが分離している**。

**P9 は variant 依存で、予測は `no_center` でのみ成立した。**
`|rel_bias_global|` は no_center では `series_mean` の +0.22420 から他 3 scenario で
+0.31364〜+0.31464 に増え、ほぼ飽和する。`series_mean` では残差の系列平均が定義上ゼロで
global が水準を担えないが、他の基準値ではこの恒等式が崩れて global に水準が入り込む、
という [qa_global_component.md](conference/jima2026/qa_global_component.md) の論法どおりである。
しかし centered では逆に −0.26949 → −0.12273 → −0.03531 → +0.00843 と縮む。
中心化が分解全体をゼロ方向へ縮めるため、global も一緒に縮む。
**global の役割についての主張は、基準値だけでなく中心化の有無にも条件づく。**

### hour 成分の振幅と相関（指標の読み方）

`hour_component_residual_profile_corr` は**振幅と併記しないと読めない**。

| scenario | variant | 相関 | hour 成分プロファイル振幅 |
|---|---|---:|---:|
| `series_mean` | centered | +0.9895 ± 0.0106 | 0.0029〜0.0046 |
| `recent_hour_d7` | centered | **−0.8334 ± 0.0450** | 0.0029〜0.0046 |
| `recent_hour_d7` | no_center | −0.0229 ± **0.5613** | 0.0020〜0.0445 |
| `recent_hour_d1` | centered | +0.6432（番兵 1 件含む） | **0.000000**〜0.0045 |
| `cycle7_hour` | centered | 0.0000（番兵） | 0.000000 |

**旧条件の所見が主結果条件で再現した。** `recent_hour_d7` × centered の相関は
**−0.8334 ± 0.0450**（5 seed すべて −0.777〜−0.895）。旧条件（3 seed・12 epoch・early stopping なし）
の −0.8840 が、5 seed・240 epoch・patience 24 でも符号・大きさともに再現している。
**これが本実験の最大の収穫で、C3 と L7 の根拠を旧条件から主結果条件に差し替えられる。**

**相関 0.0000 は測定値ではなく番兵値である。** `_corr`（`residual_experiments.py:698`）は
いずれかのベクトルの標準偏差が 1e-8 以下のとき 0.0 を返す。
`recent_hour_d1`/seed_17 の centered では hour 成分が完全に消滅しており
（プロファイル振幅 0.000000、`hour_component_cell_abs_mean` 0.000000、ablation +0.000000）、
相関 +0.0000 は「無相関」ではなく「分散が無く計算できない」の意味である。
番兵を除くと `recent_hour_d1` centered は +0.8040 ± 0.2305（n=4）。
`cycle7_hour` の 0.0000 も同じ番兵で、「基準値が時間帯を完全に吸収した」を意味する。

**基準値が時間帯を吸収していると、中心化は hour 成分をゼロに向けて縮める。**
`recent_hour_d1` では潰れきって 1 seed で消滅する。
`recent_hour_d1` で相関の分散が大きい（±0.4182、番兵込み）のは再現性が低いからではなく、
**振幅がゼロ近傍で相関が ill-conditioned になるから**である。
`recent_hour_d1`/seed_47 の centered では `component_ablation_without_hour_mae_delta` が
**−0.000054** で負、つまり hour 成分を抜くと MAE がわずかに改善する。

### 事前登録の予測の判定

| | 予測 | 判定 | 根拠 |
|---|---|---|---|
| P1 | 内部対照が 2-Exp-48 と一致 | **成立** | 3 variant すべて差 +0.00000、std も一致 |
| P2 | hour が `series_mean` でのみ有意 | **不成立** | p は 3 条件で下限 0.00498。`cycle7_hour` のみ 1.0000 |
| P3 | `cycle7_hour` の hour プロファイルは厳密ゼロ | **成立** | 5 seed すべて 5.379e-09、hour p = 1.0000 |
| P4 | 日軸は `cycle7_hour` でのみ非有意 | **不成立** | 4 scenario すべて day p = 0.0050、倍率 8.83〜11.25× |
| P5 | 相対改善率が P2 の順序と一致 | **部分的** | 最大が `series_mean` は成立。d1 < d7 で順序が崩れる |
| P6 | hour ablation の減衰 | **成立** | +0.01332 → +0.00094 / +0.00047 / +0.00000 |
| P7 | 過剰な基準値では補正が害になる | **成立** | `cycle7_hour` centered −0.73%、anova は 3 条件すべて負 |
| P8 | 経験的 ANOVA も同じ向き | **成立** | 3 variant すべてで同順序 |
| P9 | `series_mean` 以外で global の役割が増す | **variant 依存** | no_center で成立（+0.224 → +0.314）、centered で逆 |

### 成功条件の判定

1. **内部対照** ✓ 一致したので以降の判定に進んだ。
2. **モデル非依存の診断** → **中間着地。** permutation の二値判定は実データで判別力が無く
   （4 条件のうち `cycle7_hour` のみ分離）、判別するのは効果量（帰無分布比）だった。
   その倍率は**中心化の効き方は単調に予測する**が、**補正全体の改善量は予測しない**
   （`recent_hour_d1` が反例）。したがって C3 の deliverable は
   「学習前に基準値を診断できる」ではなく、**「残存構造の量は学習前に測れる。それは中心化の
   効き方を予測し、補正全体については実現可能な改善量の上限を与える」**に限定する。
   記述は「有意か」ではなく「帰無分布の何倍か」で行う。
3. **適用条件への反転** ✓ 成立。`cycle7_hour` で相対改善率が負（centered −0.73%、no_center −0.07%、
   anova −7.08%）。limitation ではなく**適用条件**として
   「基準値が日周期 × 時間帯の平均まで吸収している場合、残差成分分解は適用しない」と書ける。
   経験的 ANOVA については `recent_hour_d7` / `recent_hour_d1` でも既に負なので、
   除外条件はより広い（時間帯を吸収する基準値すべて）。
4. **中心化の基準値依存** → 倍率が正の 3 点で単調減衰。`series_mean` 条件固有ではない。
   確立しているのは `series_mean`（t = −3.18、5 勝 0 敗、LOO 反転 0/5）のみで、
   `recent_hour_d1` は未確立、`recent_hour_d7` はゼロと区別できない。
   `cycle7_hour` は構造がゼロで比較が定義されないため系列に含めない。
   2-Exp-48 の学習量依存（−0.00594 → −0.00153）と並べると、
   **中心化の効果量は予算方向では縮小し、基準値方向では残存構造の量に比例して減衰する。**
5. **global の役割** → P9 は `no_center` でのみ成立。
   qa_global_component.md の論法は**基準値と中心化の有無の両方に条件づく**。
6. **P3 は構造的予測** ✓ 成立（5.379e-09、全 seed 同一値）。

### 解釈上の制約（追加分）

設計時の制約節に加えて、本番結果から以下を追加する。

- **`hour_component_residual_profile_corr` の 0.0000 は番兵値で、未定義を含む。**
  `_corr` は標準偏差 1e-8 以下で 0.0 を返す。相関を引用するときは必ず
  `hour_component_profile_mean_abs` を併記し、消滅した成分と無相関の成分を区別する。
  設計初稿で `residual_hour_profile_corr` をモデル非依存と誤分類したのに続き、
  **指標の性質を読み違えた 2 件目**である。
- **`component_ablation_without_X_mae_delta` は X の精度貢献を測らない。**
  モデル出力の X への依存度を測る。`cycle7_hour` で、全成分がゼロの centered と
  大きな ablation を持つ no_center が同じ精度に着地したことが反例になる。
- **permutation の p 値は系列数に依存する。** 6000 系列では帰無分布が締まり、
  相対振幅 0.04 でも有意になる。p 値を scenario 間の比較に使ってはならない。
  比較は帰無分布 95% 点に対する倍率で行う。
- **smoke からの外挿が効かなかった項目が 2 件ある**（P2 の hour 非有意、P4 の day 非有意）。
  合成データは帰無分布が緩いため、permutation 検定の有意・非有意は実データで作り直す必要がある。
- **`stopped_epoch` が scenario 間で揃っていない**（76.4〜240.0）。
  `recent_hour_d7` の no_center は 5 seed すべて上限到達。scenario 間の比較には
  停止位置の差が混入している。

### この実験が答えた質疑

> 従来研究の global/local 成分から、提案の全期間成分への意味接続が分からない。
> **平均による残差獲得は意味をなさないのでは？**

答えは「**基準値が何を吸収したかで決まり、その量は学習前に測れる**」である。

残差に残る時間帯構造の量は、帰無分布に対する倍率として学習を使わずに測れる
（46.32× / 7.65× / 3.35× / 0.00×）。それがゼロなら 4 成分に分ける意味は無く、
実際 `cycle7_hour` では分解が崩壊し補正は害になる（−0.73%）。
その意味で**「平均による残差獲得が意味をなすか」は測定可能な問いであり、答えは基準値に依存する**。

ただし倍率が正でも改善が出るとは限らない（`recent_hour_d1`、7.65× で +1.95%）。
倍率は上限であって実現値ではない。

### 残った問い

> **2026-11-09 追記**: 下の 2 件は [2-Exp-55_axis_usability_and_centering.md](2-Exp-55_axis_usability_and_centering.md)
>（事後解析）で解決した。どちらも原因は同じで、**`diag_{axis}_relative_amplitude` は
> モデルが使える構造の量を測っていない**ことだった。他方の軸で分割した oracle を当てると、
> `series_mean` 以外では日軸・時間帯軸のどちらも held-out で負になる
> （`cycle7_hour` の日軸は in-sample +1.75% に対し held-out −4.70%）。
> `cycle7_hour` の day 成分がゼロなのは表現可能性でも最適化でもなく、使える構造が無いためである。
> `recent_hour_d1` の 7.65× も雑音を数え上げたもので、held-out では d7 のほうが使える構造が多い。

- **`cycle7_hour` の日軸。** 8.83× の構造が残っているのに centered の day 成分は寄与ゼロである。
  中心化の制約が (mod 7 クラス内偏差) を表現できないのか、最適化が到達していないのかを切り分ける。
- **`recent_hour_d1` の非単調性。** 倍率 7.65× に対し改善率 +1.95% は `recent_hour_d7`（3.35× で +7.51%）
  を下回る。残差の時間帯構造のうちノイズ由来の割合を直接測る指標が必要。
- **未来日評価。** 本実験は観測期間内の残差再構成であり、`same_hour_recent_mean` は窓の初日に
  窓全体の平均を使う（窓内 transductive）。未来日に持ち込む場合は切り分けが必要。
