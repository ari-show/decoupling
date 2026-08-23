# 2-Exp-39: 実データ未来日での経験的 ANOVA vs NN（学習量統制版）

作成日: 2026-08-22
関連: [2-Exp-30_future_day_component.md](2-Exp-30_future_day_component.md)、
[2-Exp-33_empirical_anova_baseline.md](2-Exp-33_empirical_anova_baseline.md)、
[2-Exp-38_empirical_vs_nn_epochs.md](2-Exp-38_empirical_vs_nn_epochs.md)

注: 並列計画（[2-Exp-36_to_40_parallel_plan.md](2-Exp-36_to_40_parallel_plan.md)）の
2-Exp-39（hard vs soft centering）は 40 以降へ繰り下げる。

## 背景

NN 成分モデルが経験的 ANOVA（閉形式・パラメータなし）に対して**原理的に**勝てる
唯一の土俵は、未来日の day / interaction 効果である。経験的分解は観測のない日の
day 効果を計算できず必然的に 0 になるが、NN は特徴量（曜日・販促・休日など）から
未来日の成分を構成できる。

この主張の実証状況は次のとおり。

| 比較 | 結果 | 出典 |
|---|---|---|
| 未来日 synthetic | NN 圧勝（改善率 85% vs 49%、day corr 0.983 vs 0） | 2-Exp-33 (3) |
| 未来日 FreshRetailNet | **同等**（empirical 0.0589 vs NN 0.0594、seed 13 のみ） | 2-Exp-33 (2) / 2-Exp-30 |

つまり**実データで NN の必然性を示せた比較はまだ無い**。そして 2-Exp-38 で、
窓内の「empirical 優位」が 12 epoch の学習不足による交絡だったことが確定した。
未来日 FreshRetailNet の NN 値（0.0594 / 0.0601）も同じ 12 epoch 設定であるため、
同じ交絡を抱えている疑いがある。

本実験は提案の主張の分水嶺になる。

- NN が学習量を揃えて未来日でも empirical を上回るなら、
  「実データの未来日でも NN 成分モデルが必要」という主張が初めて立つ。
- 上回らないなら、「FreshRetailNet は hour 主効果が支配的で、
  未来日でも empirical で十分（NN の必然性は特徴駆動構造がある場合に限る）」が
  学習量統制済みの結論として確定する。どちらでも論文には書ける。

## 目的と仮説

仮説:

```text
2-Exp-30/33 の未来日 FreshRetailNet 比較（NN 0.0594 vs empirical 0.0589）は
NN 側の学習不足を含む。学習量を揃える（30 epoch）と、NN の
future corrected MAE は empirical を下回る。
```

対抗仮説（こちらが成立する可能性も十分ある）:

```text
FreshRetailNet の series_mean 残差で未来日へ転移する構造は
hour 主効果と系列水準が支配的であり、これは平均の持ち越しで推定し尽くされる。
このデータでは学習量を揃えても NN は empirical を上回らない。
```

## 実験条件

2-Exp-30 の FreshRetailNet 未来日設定を sweep 化する。

- dataset: FreshRetailNet、train 2000 / eval 500 系列（Exp-30 と同一。
  `validation_source` 未指定も Exp-30 のまま維持し、再現条件を揃える）
- residual: `series_mean`、`future_mask_days: 2`（窓末尾 2 日の残差入力チャネルをゼロ化）
- seeds: 13, 17, 23, 31, 47（Exp-30 の seed 13 を含む 5 seed。
  Exp-30/33 は seed 13 の 1 本のみだったため、seed 頑健性も本実験で初めて確認する）

| scenario | epochs | NN dims |
|---|---:|---|
| `epochs12` | 12 | 8/8/8/6（Exp-30/33 の再現） |
| `epochs30` | 30 | 8/8/8/6 |
| `epochs30_dim4` | 30 | 4/4/4/4（2-Exp-36 の推奨次元） |

| variant | 内容 |
|---|---|
| `empirical_anova_main_effects` | 閉形式主効果分解（未来日 day 効果 = 0） |
| `output_decomp_centered_no_interaction` | NN（Exp-30 の未来日最良 variant） |
| `output_decomp_centered` | NN（全成分） |

合計 run 数: 3 scenario × 5 seed × 3 variant = 45。

## 評価指標

主指標は未来日セル上の指標（`future_holdout_metrics`）。

| 指標 | 見る理由 |
|---|---|
| `future_corrected_cell_mae` | 主判定。未来日での補正性能 |
| `future_baseline_cell_mae` | 参照（補正なし） |
| `future_residual_hour_profile_corr` | 未来日の hour 構造の捕捉 |
| `future_hour_component_residual_profile_corr` | hour 成分の対応 |
| 窓内 `corrected_cell_mae` | 2-Exp-38 との整合確認 |

## 事前に定める成功条件・分岐

1. **再現性**: `epochs12` の seed 13 が Exp-33 (2) の数値
   （empirical 0.0589 / NN(no int) 0.0594 / NN(全成分) 0.0601 前後）を再現する。
2. **主判定**: `epochs30`（または `epochs30_dim4`）の NN のいずれかの variant が、
   `future_corrected_cell_mae` の seed ごとの paired 比較で empirical を
   **5 seed 中 4 seed 以上**下回れば「実データ未来日でも学習量を揃えれば NN が優位」
   と結論する。
3. 下回らなければ、対抗仮説（FreshRetailNet の未来日は empirical で十分）を
   学習量統制済みの結論として採用し、NN の必然性の主張は
   「特徴駆動の day/interaction 構造がある場合（synthetic で実証）」に限定する。
4. どちらの場合も、`subsec:empirical` とラダーの記述に反映する。

## 実行方法

smoke（ローカル CPU、synthetic の future 経路確認）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-39_future_day_empirical_vs_nn_smoke.json
```

本番（ローカル GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-39_future_day_empirical_vs_nn_freshretailnet.json
```

## 出力

```text
runs/2-Exp-39_future_day_empirical_vs_nn_freshretailnet/
  epochs12/seed_{13,17,23,31,47}/{3 variants}/
  epochs30/... epochs30_dim4/...
  all_results.csv / aggregate.csv / summary.json
```

## smoke 確認

2026-08-22 にローカル CPU で smoke（synthetic、future 経路、2 scenario × 2 variant、
seed 17）を実行し、完走と `future_*` 指標の出力を確認した。

## 本番結果

2026-08-22 にローカル GPU（RTX 5060 Ti）で全 45 run を実行し、完走した。
未来日 baseline（`series_mean` の持ち越し）の future cell MAE は 0.0731。

### 未来日 corrected MAE（5 seed の平均 ± SD）

| scenario | model | future corrected MAE | 未来日改善率 | future bias | future hour corr |
|---|---|---:|---:|---:|---:|
| `epochs12` | empirical ANOVA | 0.05888 ± 0.00000 | 19.4% | **+0.0004** | **0.985** |
| `epochs12` | NN（no int） | 0.06016 ± 0.00072 | 17.7% | -0.021 | 0.954 |
| `epochs12` | NN（全成分） | 0.05990 ± 0.00151 | 18.1% | -0.024 | 0.971 |
| `epochs30` | empirical ANOVA | 0.05888 ± 0.00000 | 19.4% | **+0.0004** | **0.985** |
| `epochs30` | NN（no int） | **0.05587 ± 0.00018** | **23.6%** | -0.018 | 0.968 |
| `epochs30` | NN（全成分） | 0.05647 ± 0.00050 | 22.7% | -0.026 | 0.980 |
| `epochs30_dim4` | NN（no int） | 0.05610 ± 0.00066 | 23.2% | — | — |
| `epochs30_dim4` | NN（全成分） | 0.05677 ± 0.00105 | 22.3% | — | — |

### paired 比較（NN − empirical、future corrected MAE）

| scenario | variant | 平均差 | NN 勝敗 |
|---|---|---:|---|
| `epochs12` | no int / 全成分 | +0.00128 / +0.00103 | 0勝5敗 / 0勝5敗 |
| `epochs30` | no int / 全成分 | **-0.00300 / -0.00241** | **5勝0敗 / 5勝0敗** |
| `epochs30_dim4` | no int / 全成分 | -0.00278 / -0.00211 | **5勝0敗 / 5勝0敗** |

### 事前に定めた成功条件との照合

1. **再現性 ✓**: `epochs12` の seed 13 は Exp-30/33 の構図を再現
   （empirical 0.0589、NN 0.0591〜0.0607。「未来日は同等〜empirical 僅差優位」）。
2. **主判定 ✓**: `epochs30` の両 NN variant が 5 seed 中 5 seed で empirical を下回った
   （事前基準は 4/5 以上）。**実データ（FreshRetailNet）の未来日でも、
   学習量を揃えれば NN 成分モデルが経験的 ANOVA を明確に上回る。**
3. seed 頑健性: Exp-30/33 は seed 13 の 1 本だったが、本実験で 5 seed 化しても
   結論は変わらない（NN の SD は epochs30 no int で ±0.00018 と極めて小さい）。

### 読み取り

1. **実データでの NN の必然性を初めて実証した。** これまで NN の未来日優位は
   synthetic のみで、「FreshRetailNet では empirical で十分」が実態だった。
   学習量の交絡（2-Exp-38 と同一の原因）を除去すると、未来日改善率は
   empirical 19.4% に対し NN 23.6% となり、優位が明確になった。
2. **「hour 主効果の持ち越しで尽きる」という従来の解釈は不完全だった。**
   empirical は未来日の day 効果を原理的に持てない（= hour + 系列水準の持ち越し）。
   NN がそれを上回ったことは、FreshRetailNet の未来日残差に
   **特徴量から構成可能な day 方向の構造が実際に存在する**ことを意味する。
3. **相補性の構図は未来日でも同じ。** empirical は bias がほぼゼロ
   （+0.0004 vs NN -0.02 前後）で hour profile corr も最高（0.985）。
   平均誤差は NN、無偏性・単純さは empirical という整理が窓内・未来日で一貫した。
4. variant 間では `no_interaction` が未来日最良（0.05587）で、Exp-30 の傾向と一致。
   interaction の追加は未来日では依然有利にならない（JIMA-05 の限界記述と整合）。

### 論文への反映

- **ラダーの最終段の主張を格上げできる**: 「NN は synthetic のような特徴駆動構造が
  ある場合に必要」→「実データの未来日でも、十分に学習した NN 成分モデルは
  経験的分解を上回る（19.4% → 23.6%）。経験的分解は無 bias・閉形式という
  運用上の利点で第一選択の位置を保つ」。
- 2-Exp-33 (2) の未来日表（empirical 0.0589 vs NN 0.0594）は学習量交絡を注記し、
  本実験の 5 seed 値で更新する。
- 2-Exp-38 と合わせて、「empirical vs NN の優劣に関する既存の記述はすべて
  学習量統制版（Exp-38/39）の数値へ差し替える」ことを原稿修正の原則とする。
