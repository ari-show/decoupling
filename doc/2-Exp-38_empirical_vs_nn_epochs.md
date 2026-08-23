# 2-Exp-38: 経験的 ANOVA vs NN の窓内比較の再検証（学習量交絡の確認）

作成日: 2026-08-22
関連: [2-Exp-33_empirical_anova_baseline.md](2-Exp-33_empirical_anova_baseline.md)、
[2-Exp-34_fullscale_empirical_and_log.md](2-Exp-34_fullscale_empirical_and_log.md)、
[2-Exp-36_latent_dimension_sensitivity.md](2-Exp-36_latent_dimension_sensitivity.md)、
[2-Exp-37_hyperparameter_sensitivity.md](2-Exp-37_hyperparameter_sensitivity.md)

注: 並列計画（[2-Exp-36_to_40_parallel_plan.md](2-Exp-36_to_40_parallel_plan.md)）では
2-Exp-38 を共有 backbone（H-EXT-05）に割り当てていたが、2-Exp-36/37 の結果を受けた
本追試を優先して 38 とする。共有 backbone は 39 以降へ繰り下げる。

## 背景

2-Exp-33 は、外部レビュー「NN の必然性は閉形式の素朴 ANOVA 分解に勝ることで
初めて正当化される」に応え、2000/500 系列の窓内比較で次を得た。

| model | corrected MAE | top10 MAE | bias |
|---|---:|---:|---:|
| empirical ANOVA（主効果） | **0.0555** | **0.1817** | ~0 |
| NN（中心化・全成分、12 epoch） | 0.0583 ± 0.0011 | 0.2508 | -0.19 |

この「窓内・小規模スケールでは empirical が NN に勝つ」という結論は、
論文の `subsec:empirical`（ラダーの第一選択として経験的補正を置く根拠）に使われている。
2-Exp-34 では 6000/1500 系列で平均 MAE が逆転（NN 0.0516 vs empirical 0.0544）し、
「スケール依存の相補性」として整理された。

しかし 2-Exp-37 で「12 epoch は学習不足」（20 epoch で -0.0031、なお未収束）が判明し、
2-Exp-36 の 30 epoch 再実行では同じ 2000/500 設定で NN が 0.0521〜0.0525 まで下がった。
これは Exp-33 の empirical 0.0555 を下回る値であり、
**「窓内・小規模で empirical 優位」という結論自体が学習不足と交絡していた疑い**がある。

## 目的と仮説

目的は、Exp-33 の窓内比較を学習量を揃えて再実行し、
`subsec:empirical` の記述をどう修正すべきかを確定することである。

仮説:

```text
Exp-33 の「窓内で empirical > NN（平均 MAE）」は 12 epoch の学習不足による。
30 epoch では同一設定・同一 seed で NN が empirical を平均 MAE で上回る。
一方、top10 と無偏性（bias ~0）は 30 epoch でも empirical が優位のまま残る。
```

後半も重要である。平均 MAE が逆転しても top10 / bias の empirical 優位が残るなら、
「相補性」と「ラダー」の物語は維持され、修正は「小規模スケールでの平均 MAE の
優劣」の部分に限定される。

## 実験条件

2-Exp-33 の FreshRetailNet config（= Exp-32 と同一の 2000/500/500、
`series_mean`、train_holdout、5 seed）を基に、scenario で epoch と次元を振る。

| scenario | epochs | NN dims (g/d/h/u) | 位置づけ |
|---|---:|---|---|
| `epochs12` | 12 | 8/8/8/6 | Exp-33 の再現（同一条件の対照） |
| `epochs30` | 30 | 8/8/8/6 | 学習量のみを変えた主比較 |
| `epochs30_dim4` | 30 | 4/4/4/4 | 2-Exp-36 の推奨次元との組み合わせ |

variant は Exp-33 と同じ 2 つ:

- `empirical_anova_main_effects`（`type: empirical_anova`、閉形式・決定論的・パラメータなし）
- `output_decomp_centered`（NN、中心化・全成分）

合計 run 数: 3 scenario × 5 seed × 2 variant = 30
（empirical は決定論的なので scenario/seed 間で同一値になる想定。パイプライン整合のため sweep のまま流す）。

## 経験的 ANOVA モデルとは何か（参照用の要約）

`EmpiricalAnovaResidualModel` は学習パラメータを持たない。窓内の観測残差
$r_{i,d,h}$ からマスク付き平均で次を計算し、$\hat r = \hat g + \hat a + \hat c$ を出力する。

```text
g_i     = 窓内の全観測セルの残差平均                     （系列成分）
a_{i,d} = 日 d の残差平均 − g_i                          （日成分）
c_{i,h} = 時間帯 h の残差平均 − g_i                      （時間帯成分）
u       = 0（interaction は使わない。完全観測窓では
          u まで含めると r̂ = r の恒等写像に退化するため）
```

これは formulation.md 13 節の「行平均・列平均・全体平均」による分解を
観測データに直接適用したものであり、T-EXT-02（Appendix B）の言葉では
ANOVA 射影 $P_g, P_a, P_c$ を残差の経験平均に適用した閉形式の推定器、
すなわち**提案枠組みの退化ケース**である。NN との違いは分解の形ではなく
「成分を平均で推定するか、特徴量から NN で推定するか」だけである。

## 評価指標

| 指標 | 見る理由 |
|---|---|
| `corrected_cell_mae` | 主比較。epoch を揃えた優劣 |
| `high_residual_top10_corrected_mae` | empirical 優位が残るか（相補性の確認） |
| `corrected_cell_bias` | empirical の無偏性 vs NN の系統偏り |
| `corrected_cell_wape` | 補助 |
| best epoch | NN の収束状況 |

## 事前に定める成功条件・分岐

1. `epochs12` で Exp-33 の数値（empirical 0.0555 / NN 0.0583 前後）が再現される。
2. 主判定: `epochs30` の NN が empirical を corrected MAE で **5 seed 中 4 seed 以上**
   上回れば、「窓内・小規模で empirical 優位」は学習不足の交絡と結論し、
   論文の `subsec:empirical` を修正する。
3. top10 / bias で empirical 優位が残るかを併記する。残る場合、相補性の主張は
   「平均 MAE はスケールによらず十分学習した NN が優位。外れケースと無偏性は
   empirical が優位」へ更新する。残らない場合はラダーの第一選択の位置づけ自体を再検討する。

## 実行方法

smoke（ローカル CPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-38_empirical_vs_nn_epochs_smoke.json
```

本番（ローカル GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-38_empirical_vs_nn_epochs_freshretailnet.json
```

## 出力

```text
runs/2-Exp-38_empirical_vs_nn_epochs_freshretailnet/
  epochs12/seed_{17,23,31,47,59}/{empirical_anova_main_effects,output_decomp_centered}/
  epochs30/...
  epochs30_dim4/...
  all_results.csv / aggregate.csv / summary.json
```

## smoke 確認

2026-08-22 にローカル CPU で smoke（synthetic、1 epoch、seed 17、2 scenario × 2 variant）を
実行し、両 variant の完走と `all_results.csv` の出力を確認した。

## 本番結果

2026-08-22 にローカル GPU（RTX 5060 Ti）で全 30 run を実行し、完走した。
empirical は想定どおり決定論的で、全 scenario・全 seed で同一値。

### scenario × variant 集計（5 seed の平均 ± SD）

| scenario | model | corrected MAE | top10 MAE | corrected bias |
|---|---|---:|---:|---:|
| `epochs12` | empirical ANOVA | 0.05555 ± 0.00000 | **0.18174** | **-0.0000** |
| `epochs12` | NN（8/8/8/6） | 0.05831 ± 0.00111 | 0.25085 | -0.187 |
| `epochs30` | empirical ANOVA | 0.05555 ± 0.00000 | **0.18174** | **-0.0000** |
| `epochs30` | NN（8/8/8/6） | 0.05278 ± 0.00146 | 0.21094 | -0.218 |
| `epochs30_dim4` | empirical ANOVA | 0.05555 ± 0.00000 | **0.18174** | **-0.0000** |
| `epochs30_dim4` | NN（4/4/4/4） | **0.05251 ± 0.00096** | 0.20629 | -0.257 |

### paired 比較（NN − empirical、corrected MAE）

| scenario | 平均差 | NN 勝敗 |
|---|---:|---|
| `epochs12` | +0.00276 | 0勝5敗 |
| `epochs30` | **-0.00277** | **5勝0敗** |
| `epochs30_dim4` | **-0.00304** | **5勝0敗** |

### 事前に定めた成功条件との照合

1. **再現性 ✓**: `epochs12` は Exp-33 の数値を正確に再現した
   （empirical 0.05555 = Exp-33 の 0.0555、NN 0.05831 ≈ 0.0583）。
2. **主判定 ✓**: `epochs30` で NN が 5 seed 中 5 seed で empirical を上回った
   （事前基準は 4/5 以上）。したがって
   **「窓内・小規模（2000/500）で empirical 優位」という Exp-33 の結論は、
   12 epoch の学習不足による交絡だった**と結論する。
3. **相補性は維持 ✓**: top10 は empirical が依然大差で優位（0.182 vs 0.206〜0.211）、
   bias も empirical は構成上ゼロ、NN は -0.22〜-0.26 の系統的過小補正が残る
   （むしろ 30 epoch でわずかに悪化）。

### 読み取り

1. **Exp-33/34 の「スケール依存の逆転」という整理は不正確だった。**
   Exp-34 の 6000/1500 での NN 逆転は「データが増えたから」ではなく、
   同一 epoch 数でもデータが 3 倍あれば実効的な学習量（更新回数）が 3 倍になる
   ことの効果と分離できていなかった。学習量を揃えれば **2000/500 でも NN が
   平均 MAE で優位**であり、スケールは逆転の本質ではない。
2. **相補性の主張は次の形に更新する**:
   「平均 MAE は（十分に学習した）NN が優位。外れケース（top10）と無偏性は
   empirical が優位」。スケール条件は削除する。
3. **ラダーの物語への影響**: 経験的補正を第一選択とする根拠は
   「窓内で NN より正確だから」ではなく、
   「パラメータなし・無 bias・外れケースに強い・実装が自明」という
   運用上の性質に置き直す。NN の必然性の主張（未来日の day/interaction、
   synthetic での成分回復）は影響を受けない。
4. **NN の bias（-0.22〜-0.26）は学習を延ばしても解消しない**。
   bias の解消には 2-Exp-18/19 の calibration または 2-Exp-37 で確認した
   損失側 bias 制約（weight 0.01 で bias 半減）が引き続き必要である。

### 論文への反映（`subsec:empirical` の修正点）

- 「窓内では empirical が NN を上回る（2000/500）」の記述を削除し、
  「学習量を揃えると平均 MAE は NN が優位（2000/500 と 6000/1500 の両方）。
  top10 と無偏性は empirical が優位」へ差し替える。
- Exp-33 の表を引く箇所には、12 epoch の値であることと本実験による更新を注記する。
- 2-Exp-34 の「スケールで構図が変わった」という段落は「学習量を揃えた再検証
  （2-Exp-38）により、逆転の要因はスケールではなく学習量と判明」へ更新する。
