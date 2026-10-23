# 2-Exp-49: 日のランダムマスク学習が短履歴推定と移植性に与える効果

## 背景

2-Exp-44 の学習済みモデル（dim10 / 60 epoch / 5 seed、FreshRetailNet eval 1500 系列）の
保存済み潜在と出力成分を再解析したところ、本モデルの潜在表現について次の3点が分かった。

1. **hour 成分は系列の経験プロファイルをなぞるだけで、系列間のプーリングをしていない。**
   `AxisEncoder` は hour 軸の周辺統計量（各時刻の平均・分散）を入力とする設計なので、
   構造上「その系列の経験推定の変換」以上にはなれない。実測でも、履歴 k 日だけを
   可視にして残りの日のプロファイルを予測させると、経験平均とほぼ同じ値になり、
   経験平均を母集団平均へ最適に縮小した推定には全域で負ける。

   | 履歴 | 経験平均 | 経験＋最適縮小 | 潜在 hour 成分 |
   |---:|---:|---:|---:|
   | 3日 | 0.129 | **0.379** | 0.104 |
   | 7日 | 0.497 | **0.548** | 0.502 |
   | 14日 | 0.694 | **0.711** | 0.684 |

2. **一方で、潜在は「移植」では経験分解に明確に勝つ。** 同一商品・他店舗の潜在平均を
   decode して対象系列を復元すると、同じ情報源から作った経験的プロファイル加算より
   残差セル MAE が良い（5 seed 平均、中心化あり）。

   | 作り方 | 残差セル MAE | 系列ごとの勝率 |
   |---|---:|---:|
   | 経験的: 商品の level+day+hour プロファイルを足す | 0.0628 | — |
   | 潜在: 商品の `z_global, z_day, z_hour` を decode | **0.0566 ± 0.0004** | **0.972 ± 0.003** |

   中心化なしでは 0.0582 ± 0.0012 / 勝率 0.746 ± 0.075 に落ちる。中心化制約は
   成分の担当範囲を固定するだけでなく、潜在の移植性そのものを支えている。

3. **day 成分は隠した日に一般化しない。** 偶数日の売上をエンコーダから隠すと、
   day 成分と実測日水準の相関は見た日 0.939 に対し隠した日 −0.014 になる。
   本モデルはマスクなしで学習しているため、day encoder はその日の売上を読んでおり、
   共変量から日効果を構成する経路を持っていない。

1 と 3 はどちらも「学習時に欠測を経験していない」ことで説明できる。本実験は、
訓練時に日をランダムに隠すだけで 1 と 3 が改善するか、そして 2 がさらに伸びるかを
検証する。

## 目的と仮説

- **H1（縮小の獲得）**: 訓練時に日を隠すと、エンコーダは可視日が少ないときに母集団
  プロファイルへ寄せる挙動を学習し、短履歴の held-out R² が経験＋最適縮小に追いつく。
- **H2（移植性の強化）**: 可視日が減る状況で学習した潜在は系列固有ノイズへの過適合が
  減り、商品潜在の店舗間移植 MAE がマスクなしより下がる。
- **H3（day 成分の一般化）**: 隠した日も再構成対象に含めると、day encoder は売上では
  なく共変量（曜日・値引き・天候）経由で日効果を作らざるを得ず、隠した日との相関が
  正になる。

## マスクの定義

マスクは **sales (ch0) と stock (ch1) のみ**を隠し、日次共変量と時刻特徴は残す
（既存の `residual.future_mask_channels=[0,1]` と同じ規約）。隠した日は baseline
（`series_mean`）の計算からも除外するので、マスク後のバッチは「その日が記録されて
いなかった場合にエンコーダが見るもの」と厳密に一致する。マスクは訓練時のみ適用し、
validation と test は常に全窓を見る（選択指標の比較可能性を保つため）。

`loss_on` がモデルへの要求を決める。

- `all`: 隠した日も再構成損失に残す（= masked autoencoding）。H3 が成立しうる条件。
- `visible`: 隠した日を損失から落とす（= 入力ノイズのみ）。H3 の寄与を切り分ける対照。

## 実験条件

本番設定は `configs/2-Exp-49_masked_day_training_freshretailnet.json`。
データ・モデル・学習設定は 2-Exp-44 と同一（6000/1500/1500 系列、
`hidden 160 / global 10 / day 10 / hour 10 / interaction 8`、60 epoch、
early stopping patience 8、lr 1e-3、batch 128、`series_mean` 残差、
seeds 17 / 23 / 31 / 47 / 59）。

| variant | 入力マスク | 損失対象 | 中心化 | 役割 |
|---|---|---|---|---|
| `M0_no_masking` | なし | 全観測セル | あり | 対照（2-Exp-44 の再現） |
| `M1_random50_loss_all` | ランダム日・可視50% | 全観測セル | あり | 本命 |
| `M2_random50_loss_visible` | ランダム日・可視50% | 可視セルのみ | あり | H3 の寄与の切り分け |
| `M3_tail7_loss_all` | 末尾連続7日 | 全観測セル | あり | 2-Exp-39/43 の future masking との接続 |
| `M1_random50_loss_all_no_center` | ランダム日・可視50% | 全観測セル | **なし** | マスク学習が中心化の代替にならないことの確認 |

可視日率のスイープは `configs/2-Exp-49_masked_keep_ratio_freshretailnet.json`
（可視 25% / 75%、seeds 17 / 23 / 31）。可視日数の下限は 5 日に固定する
（可視日が少なすぎると `series_mean` baseline 自体が不安定になり、
マスクの効果と baseline のノイズが交絡するため）。

smoke 設定は `configs/2-Exp-49_masked_day_training_smoke.json`（300/300/100 系列、
2 epoch、1 seed）。入出力の確認専用であり、性能の判定には使わない。

## 評価指標

評価は test split（eval 1500 系列）で行い、日を偶奇で分割する。28 日窓では
奇数日・偶数日がそれぞれ各曜日をちょうど2回ずつ含むため、この分割は曜日と交絡しない。
指標は学習には一切影響せず、`metrics.json` に `maskdiag_*` として出力される。

### A. 短履歴リズム推定

奇数日のうち先頭 k 日（k ∈ {2,3,5,7,10,14}）だけを可視にしてエンコードし、
hour 成分の24次元プロファイルを偶数日の実測プロファイルに対して採点する。

| 指標 | 内容 |
|---|---|
| `maskdiag_history{k}_empirical_r2` | 可視 k 日の経験平均プロファイル |
| `maskdiag_history{k}_empirical_shrunk_r2` | 同じ経験平均を母集団へ out-of-fold で最適縮小したもの |
| `maskdiag_history{k}_latent_r2` | モデルの hour 成分 |
| `maskdiag_history{k}_latent_minus_shrunk_r2` | 上2つの差。H1 の主指標 |

経験系の2指標はモデルに依存しないので、同一 seed では全 variant で一致しなければ
ならない。解析スクリプトはこれを検査し、一致しない場合は失敗する。

### B. 移植

同一商品・他店舗の潜在平均（leave-one-series-out）を decode し、対象系列の残差
グリッドをその系列自身の履歴を使わずに復元する。比較対象は同じ情報源から作った
経験的プロファイル加算。

| 指標 | 内容 |
|---|---|
| `maskdiag_transfer_latent_mae` | 潜在経由の残差セル MAE |
| `maskdiag_transfer_empirical_mae` | 経験的加算の残差セル MAE（モデル非依存） |
| `maskdiag_transfer_gain_pct` | 経験に対する改善率 |
| `maskdiag_transfer_win_rate` | 潜在が勝った系列の割合 |

### C. 隠した日の day 成分

偶数日の売上を隠してエンコードし、day 成分と実測日水準の相関を、隠した日と
見た日の両方で測る（`maskdiag_hidden_day_corr` / `maskdiag_seen_day_corr`）。

### D. 退行チェック

既存指標（`corrected_cell_mae` / `corrected_cell_wape` / `residual_r2` /
`hour_component_residual_profile_corr` / 中心化違反量4種）で退行がないことを見る。

## 事前に定める成功条件

1. **主**: A の k=7 で `M1_random50_loss_all` の潜在が経験＋最適縮小を
   5 seed 中 3 seed 以上で上回る（現状の差 −0.047 を正へ反転）。
2. **主**: B で `M1_random50_loss_all` の移植 MAE が `M0_no_masking` 比 5% 以上改善し、
   勝率 0.97 以上を維持する。
3. **副**: C で隠した日の相関が 0.30 以上（現状 −0.014）。`M1` と `M2` の差が
   この効果が `loss_on=all` から来ていることを示す。
4. **退行禁止**: D の `corrected_cell_mae` の悪化が `M0` 比 +3% 以内、
   中心化ありの variant で中心化違反量が `< 1e-6` を維持。

条件1は「上回る」を基準にするが、追いつく（差が ±0.01 以内）場合も
「マスク学習で縮小を獲得した」と記述できる水準として併記する。

### 分岐

- 1 を満たさず 2 のみ満たす → 「マスク学習は移植性を強化するが縮小は学習しない」と
  限定して記述する。主張は移植性に寄せる。
- 1 も 2 も満たさない → ボトルネックは学習目標ではなくエンコーダ構造（hour 軸の
  周辺統計量変換器であること）だと結論し、論点を 2-Exp-45 の encoder 比較の延長へ移す。
- 3 のみ満たす → 未来日予測（2-Exp-39）側の主張の補強材料として扱い、
  表現の性質の主張には使わない。

## 実行方法

smoke 学習:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-49_masked_day_training_smoke.json
```

smoke 解析:

```bash
uv run --with matplotlib python scripts/analyze_2_exp_49_masked_training.py \
  --run-dir runs/2-Exp-49_masked_day_training_smoke \
  --out-dir figures/2-Exp-49-smoke
```

本番学習:

```bash
uv run decoupled-ts residual-sweep --config configs/2-Exp-49_masked_day_training_freshretailnet.json
uv run decoupled-ts residual-sweep --config configs/2-Exp-49_masked_keep_ratio_freshretailnet.json
```

本番解析:

```bash
uv run --with matplotlib python scripts/analyze_2_exp_49_masked_training.py \
  --run-dir runs/2-Exp-49_masked_day_training_freshretailnet \
  --out-dir figures/2-Exp-49
```

## 出力

```text
figures/2-Exp-49/
  diagnostics_by_variant.csv    variant ごとの3指標（seed 平均 ± SD）
  paired_vs_control.csv         M0 との seed 対応差
  success_report.json           事前条件との照合
  all_results.csv               sweep の全 run
  masked_training_diagnostics.png / .pdf
```

## コスト

2-Exp-44 は 5 seed × 2 variant が実測約5分だった。本実験は 5 seed × 5 variant と
3 seed × 2 variant なので、合計 20〜30 分程度を見込む。

## smoke 確認

2026-10-23 にローカルで smoke を実行し、次を確認した。

- 5 variant すべてが 2 epoch を完走した。
- `maskdiag_history{3,7,14}_*`、`maskdiag_transfer_*`、`maskdiag_hidden_day_*` が
  `metrics.json` と `all_results.csv` に出力された。
- 経験系の指標が全 variant で一致した（`empirical_r2 = -0.664`、
  `empirical_shrunk_r2 = 0.179`）。解析スクリプトの一致検査も通過した。
- 解析スクリプトが表・CSV・`success_report.json`・図を生成した。

smoke の潜在側の値（`history14_latent_r2 = -0.88` など）は 2 epoch・300 系列の
学習不足によるもので、判定には使わない。

診断コード自体は、2-Exp-44 seed 17（centered）の学習済み checkpoint に対して
実行し、本実験とは独立に書いた解析（scratchpad）と一致することを確認した。

| 指標 | 独立解析 | 本実装 |
|---|---:|---:|
| `history3_latent_r2` | 0.104 | 0.1038 |
| `history7_latent_r2` | 0.502 | 0.5013 |
| `history14_latent_r2` | 0.684 | 0.6836 |
| `history7_empirical_shrunk_r2` | 0.548 | 0.5485 |
| `transfer_latent_mae` | 0.05705 | 0.0571 |
| `transfer_empirical_mae` | 0.06278 | 0.0628 |
| `transfer_win_rate` | 0.975 | 0.975 |
| `seen_day_corr` | 0.939 | 0.9372 |

`hidden_day_corr` は独立解析 −0.014、本実装 −0.009 で符号と大きさは一致する
（使用系列の条件が独立解析は「偶数日に7時間以上観測」741 系列、本実装は
「全日が有限」1053 系列と異なるため）。

## 本番結果

（本番実行後に記入）

## 解釈上の制約

- A の潜在側は、マスクなしで学習したモデルにとっては分布外入力である。`M0` の
  A の値はそのハンデを含むため、`M0` と `M1` の差は「マスク学習の効果」と
  「分布外ハンデの解消」の和であり、前者だけを取り出したものではない。
- 経験＋最適縮小は縮小係数を同じ test split 上で out-of-fold に推定するため、
  実運用で得られる値よりやや楽観的である。H1 の判定は保守側に倒している。
- B の移植は商品が2店舗以上に存在する系列に限られる（eval 1500 系列中 1402 系列）。
- 隠した日の day 成分（C）は、日次共変量が与えられていることを前提とする。
  共変量のない設定には一般化しない。
