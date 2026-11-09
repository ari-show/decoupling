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

（実行後に追記）
