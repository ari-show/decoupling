# 2-Exp-36: 潜在次元数の感度分析

作成日: 2026-08-22
対応ボード項目: JIMA-03（優先度 P0、期限 2026-08-31）
関連: [2-Exp-36_to_40_parallel_plan.md](2-Exp-36_to_40_parallel_plan.md)、
[proposal/research_direction_2026-08.md](proposal/research_direction_2026-08.md) 2-3節、
[proposal/risks.md](proposal/risks.md) 7節

## 背景

現在の主モデル `output_decomp_centered` の潜在次元は、実験系列によって値が揺れてきた。

| 設定 | series/day/hour | interaction | 使用実験 |
|---|---|---|---|
| 旧実験系 | 8 | 6 | 2-Exp-32/33 系 |
| 最終系 | 10 | 8 | 2-Exp-15、2-Exp-34 |
| smoke | 4 | 3 | 各 smoke config |

いずれも予備的な初期設定のままであり、次元数を振った感度比較は一度も行っていない。
`risks.md` 7節にも「潜在次元数の根拠が未検証」として残リスクに挙がっており、
発表・査読で最も突かれやすい弱点の一つである（「なぜその次元数なのか」）。

一方で、既存 config は `global_dim / day_dim / hour_dim / interaction_dim` を
パラメータ化済みであり、コード変更なしで sweep できる。JIMA 締切（08-31）前に
実施できる新規実験としては最もコストパフォーマンスが高い。

## 目的と仮説

目的は、潜在次元数に対する主結果の感度を測り、採用する次元数に根拠を与えることである。

仮説:

```text
性能（corrected MAE / WAPE）をほぼ維持できる最小の潜在次元が存在する。
すなわち、ある次元数以上では性能が飽和し、それ未満では劣化する。
```

この仮説が成立すれば、次の 2 つの主張ができる。

1. 採用する次元数は「決め打ち」ではなく、感度比較に基づく選択である。
2. 小さい次元でも性能が維持されるなら、モデルの軽量化
   （[proposal/unified_model_direction.md](proposal/unified_model_direction.md) の統一モデル方向）
   とも合流する。

仮説が成立しない場合（次元に対して性能が単調に変化し続ける、または seed 分散が
次元によって大きく暴れる場合）も、それ自体が「表現容量が結果を左右する」という
限界の記述として原稿に使える。

## 実験条件

### 次元グリッド

感度軸を 1 本にするため、比較条件では 4 成分の次元をすべて同一値にする。

| scenario | global/day/hour/interaction |
|---|---|
| `dim2` | 2 / 2 / 2 / 2 |
| `dim4` | 4 / 4 / 4 / 4 |
| `dim8` | 8 / 8 / 8 / 8 |
| `dim16` | 16 / 16 / 16 / 16 |
| `dim10_ref` | 10 / 10 / 10 / 8（現行最終系。参照条件） |

`dim10_ref` は等次元グリッドの外にあるが、「現行採用値がグリッド上のどこに
位置するか」を直接示すために入れる。10/10/10/8 の採用根拠は、この表の
dim8〜dim16 との比較として記述する。

### その他の条件

2-Exp-32 の FreshRetailNet 設定に合わせる（結果を Exp-32 系の主表と並べられるようにする）。

- dataset: FreshRetailNet-50K、train/valid/test = 2000/500/500 系列
- baseline: `series_mean`、target: `baseline_residual`
- model: `output_decomp_centered`（`center_components: true`, `use_interaction: true`）のみ
- hidden_dim: 128（固定。感度軸は潜在次元のみ）
- epochs: 12、lr: 1e-3、batch 128（Exp-32 と同一）
- seeds: 17, 23, 31, 47, 59（5 seed。JIMA 主表と同じ）
- 合計 run 数: 5 scenario × 5 seed = 25

## 評価指標

| 指標 | 見る理由 |
|---|---|
| `corrected_cell_mae` / `corrected_cell_wape` | 主性能。次元に対する飽和点を見る |
| `high_residual_top10_corrected_mae` | 外れケース補正が次元に敏感かを見る |
| `corrected_cell_bias` | 次元と系統誤差の関係 |
| seed 間の標準偏差 | 成分の安定性。小さい次元で分散が増えないか |
| パラメータ数 | 次元とモデルサイズの対応 |
| 学習時間（epoch あたり） | 計算量の目安 |

## 事前に定める成功条件

ボード（JIMA-03）の完了条件に対応して、実行前に次を固定する。

1. 全 25 run が完走し、seed 平均 ± 標準偏差を 1 表に集約できる。
2. 「性能をほぼ維持できる最小次元」の判定基準:
   dim16 の corrected MAE（5 seed 平均）を基準に、**+0.001 以内**
   （Exp-32 系の中心化あり/なしの差 -0.0052 の約 2 割）に収まる最小の次元を
   「十分な次元」とみなす。
3. `dim10_ref` が「十分な次元」の範囲に入っていれば、現行設定 10/10/10/8 を
   維持する根拠として記述する。入らなければ、採用次元の変更を検討し、
   JIMA 原稿の数値をどの設定に置くかを JIMA-02 の決定と合わせて判断する。

この基準は結果を見る前に固定したものであり、原稿にもこのまま記載する。

## 実行方法

smoke（ローカル CPU、入出力確認のみ）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-36_latent_dim_sensitivity_smoke.json
```

本番（GPU）:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-36_latent_dim_sensitivity_freshretailnet.json
```

## 出力

```text
runs/2-Exp-36_latent_dim_sensitivity_freshretailnet/
  dim2/seed_17/ ... dim2/seed_59/
  dim4/...
  dim8/...
  dim16/...
  dim10_ref/...
  all_results.csv    （scenario × seed × 全指標）
  aggregate.csv      （scenario ごとの mean/std）
  summary.json
```

集約は `all_results.csv` から scenario × seed で行い、平均 ± SD の 1 表を本ドキュメントに追記する。

## smoke 確認

2026-08-22 にローカル CPU で smoke（synthetic、1 epoch、seed 17、
scenario は dim2 / dim16 / dim10_ref の 3 条件）を実行し、次を確認した。

- 3 scenario すべてが完走し、`all_results.csv` に 3 行が出力された。
- scenario override が実際に反映されている
  （`dim16_seed_17_config.json` の model dims が 16/16/16/16、
  `dim10_ref` が 10/10/10/8 になっていることを確認）。
- `aggregate.csv` / `summary.json` が生成された。

1 epoch の smoke のため、性能値の解釈には使わない。入出力と override 機構の確認用である。

## 本番結果

2026-08-22 にローカル GPU（RTX 5060 Ti）で全 25 run（5 scenario × 5 seed）を実行し、完走した。
baseline（`series_mean`）の cell MAE は 0.072146、high residual top10 baseline MAE は 0.292300。

### scenario 別集計（5 seed の平均 ± SD）

| scenario | dims (g/d/h/u) | corrected MAE | corrected WAPE | corrected bias | top10 corrected MAE | best epoch |
|---|---|---:|---:|---:|---:|---:|
| `dim2` | 2/2/2/2 | 0.05662 ± 0.00166 | 0.9150 ± 0.0268 | -0.338 ± 0.053 | 0.2531 ± 0.0139 | 12.0 |
| `dim4` | 4/4/4/4 | **0.05619 ± 0.00077** | **0.9080 ± 0.0124** | -0.303 ± 0.100 | **0.2459 ± 0.0068** | 11.8 |
| `dim8` | 8/8/8/8 | 0.05947 ± 0.00204 | 0.9610 ± 0.0330 | -0.199 ± 0.143 | 0.2574 ± 0.0115 | 11.6 |
| `dim16` | 16/16/16/16 | 0.05927 ± 0.00186 | 0.9578 ± 0.0300 | -0.372 ± 0.163 | 0.2624 ± 0.0177 | 11.8 |
| `dim10_ref` | 10/10/10/8 | 0.06045 ± 0.00397 | 0.9769 ± 0.0642 | -0.199 ± 0.251 | 0.2533 ± 0.0137 | 11.6 |

### seed ごとの paired 比較（corrected MAE）

| 比較 | 平均差 | SD | 勝敗 |
|---|---:|---:|---|
| `dim4` − `dim16` | -0.00308 | 0.00199 | dim4 が 5勝0敗 |
| `dim4` − `dim8` | -0.00328 | 0.00238 | dim4 が 5勝0敗 |
| `dim4` − `dim10_ref` | -0.00426 | 0.00328 | dim4 が 5勝0敗 |
| `dim2` − `dim4` | +0.00043 | 0.00173 | dim2 が 2勝3敗 |

### 事前に定めた成功条件との照合

事前の判定基準は「dim16 を基準に +0.001 以内に収まる最小次元を十分とみなす」だった。
結果はこの基準の想定（次元を増やすほど良く、どこかで飽和する）と逆で、
**小さい次元の方が明確に良い**。

- `dim2` と `dim4` は dim16 より corrected MAE が良い（基準を自明に満たす）。
- `dim10_ref`（現行最終系 10/10/10/8）は dim16 比 +0.00118 で、
  事前基準 +0.001 をわずかに超え、「十分な次元」の範囲に**入らない**。
  さらに seed 間 SD が全条件中最大（±0.00397）で安定性も悪い。

### 読み取り

1. **仮説は部分的に成立**: 「性能をほぼ維持できる最小次元が存在する」どころか、
   小さい次元（4 次元）が最良だった。dim4 は corrected MAE・WAPE・top10・
   seed 間 SD（±0.00077 で最小）のすべてで最良または同率最良である。
2. **現行採用値 10/10/10/8 は支持されない**: dim4 に 5 seed すべてで負け、
   分散も最大。JIMA 主表の次元設定は 4/4/4/4 への変更を検討すべきである。
   変更する場合は JIMA-02（主結果系列の決定）と合わせて主表数値を再取得する。
3. **過剰容量は分散を増やす**: dim8 以上では MAE が悪化し seed 分散が増える。
   残差に残る構造の実効次元が小さいことを示唆し、
   [proposal/unified_model_direction.md](proposal/unified_model_direction.md) の
   軽量化・統一モデル方向（H2）とも整合する。
4. **注意（学習量の交絡）**: best epoch が全条件で上限近く（11.6〜12.0）にあり、
   12 epoch では学習が打ち切りになっている可能性がある。大きい次元ほど
   収束が遅いなら、この結果の一部は「次元が大きいほど 12 epoch では学習不足」
   と読める余地がある。2-Exp-37 の `epochs_long`（20 epoch）の結果と併せて解釈する。
5. Exp-32 系の centered 報告値 0.0583（8/8/8/6）と本実験 dim8（8/8/8/8）の 0.0595 は
   interaction 次元と乱数系列が異なるため完全一致はしない。JIMA 表に載せる際は
   どちらかの実験系列に数値を統一する（JIMA-02）。

## 30 epoch での再実行（学習量交絡の確認）

2-Exp-37 の `epochs_long` で「12 epoch は学習不足」が判明したため、
同じ次元グリッドを epochs=30 で再実行した
（config: `configs/2-Exp-36_latent_dim_sensitivity_epochs30_freshretailnet.json`、
出力: `runs/2-Exp-36_latent_dim_sensitivity_epochs30_freshretailnet/`）。

### scenario 別集計（5 seed の平均 ± SD、30 epoch）

| scenario | corrected MAE | corrected WAPE | corrected bias | top10 corrected MAE | best epoch |
|---|---:|---:|---:|---:|---:|
| `dim2` | **0.05210 ± 0.00061** | 0.8419 ± 0.0099 | -0.227 | 0.2096 | 28.4 |
| `dim4` | 0.05251 ± 0.00096 | 0.8486 ± 0.0155 | -0.257 | **0.2063** | 28.2 |
| `dim8` | 0.05426 ± 0.00296 | 0.8768 ± 0.0479 | -0.190 | 0.2090 | 27.4 |
| `dim16` | 0.05404 ± 0.00105 | 0.8733 ± 0.0169 | -0.291 | 0.2157 | 27.6 |
| `dim10_ref` | 0.05242 ± **0.00050** | 0.8471 ± 0.0081 | -0.256 | 0.2168 | 28.6 |

paired 比較（corrected MAE）: `dim4` − `dim10_ref` = +0.00009（2勝3敗）、
`dim4` − `dim16` = -0.00153（3勝2敗）、`dim2` − `dim4` = -0.00041（3勝2敗）。

### 12 epoch との比較から言えること

1. **12 epoch の結果は学習量と交絡していた。** 30 epoch では全条件が
   0.056〜0.060 → 0.052〜0.054 へ改善し、次元間の差は最大 0.002 程度に縮小した。
   特に `dim10_ref` は 12 epoch では最下位（0.06045、SD 最大）だったが、
   30 epoch では dim4 と同等（0.05242、SD は全条件中最小）まで回復した。
   「大きい次元ほど 12 epoch では学習不足」という 2-Exp-37 由来の解釈が裏づけられた。
2. **それでも小さい次元で十分である。** 30 epoch でも dim2/dim4 は dim8/dim16 より
   良いか同等で、事前基準（dim16 + 0.001 以内）を満たす最小次元は **dim2**。
   「性能をほぼ維持できる最小の潜在次元が存在する」という本実験の仮説は、
   学習量を揃えた上で成立した。
3. **次元より epoch の影響が大きい。** 次元間の差（≤0.002）より
   epoch 延長の効果（12→30 で約 -0.006）の方が 3 倍大きい。
   best epoch は 30 epoch でも 27〜29 と上限付近にあり、完全収束はしていない。
   主結果の最終数値は early stopping が発火する epoch 上限で取得する必要がある。

### JIMA 原稿への反映（12/30 epoch を併せた結論）

- 感度表は **30 epoch 版を主**、12 epoch 版を学習量交絡の注意として扱う。
- 「次元は {2,4,8,16} + 現行 10/10/10/8 の感度比較に基づく。小さい次元（2〜4）でも
  性能は維持され、現行設定は過剰容量側だが同等性能」と記述できる。
  10/10/10/8 の維持・dim4 への軽量化のどちらも根拠を持って選べる。
  軽量化の主張（unified_model_direction の H2）につなげるなら dim4 を推奨。
- **epoch 数の再設定が次元選択より先決**である。JIMA-02 の主結果数値は、
  epoch 上限を引き上げた（early stopping 前提の）再学習で確定させる。
