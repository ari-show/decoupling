# スライドの根拠と数値の対応

2026-10-23のストーリー改訂時に整理。主発表は23枚、付録は7枚。

## 主張の範囲

主評価は観測残差を入力した同じ期間の再構成。出力の共有範囲を中心化で定義し、合成データでの成分回復と実データでの成分診断を示す。将来予測、経営指標の改善、潜在次元の意味、販促の因果効果は主評価の達成事項に含めない。

## 数値・図の出典

| 使用箇所 | 根拠 | 扱い |
| --- | --- | --- |
| 実データ主表、まとめ | `configs/2-Exp-40_jima_main_results_freshretailnet.json`、`doc/2-Exp-40_jima_main_results.md` | 最大60 epoch／patience 8、5 seed。日GRU・時間帯MLP。0.04828を全MLPの数値として説明しない |
| 合成成分回復 | 元スライドの2-Exp-29とProcrustes再解析、`configs/2-Exp-29_synthetic_component_recovery_figure.json` | 12 epoch、1 seed。今回、モデル実験と回転解析は再実行していない。回転後相関を相関上限とは呼ばない |
| 考察1の分散比・相対bias | [PR #50](https://github.com/ari-show/decoupling/pull/50)、[`figures/2-Exp-44/metrics.json`](https://github.com/ari-show/decoupling/blob/Experiments/2-Exp-44/figures/2-Exp-44/metrics.json) | 取得した全データを `2-Exp-44_metrics.json` に保存。`rows` のcentered 5 seedを算術平均 |
| 考察2の全期間成分図 | [PR #58](https://github.com/ari-show/decoupling/pull/58)、[固定コミットの図](https://github.com/ari-show/decoupling/blob/916bf6423fc746881af88d9fe0b5a8a9f65606b3/figures/qa_global_component/global_component_vs_series_level.png) | `public/figures/global_component_vs_series_level.png` に原図を保存。学習gは5 seedプール、比較する最適定数はseed17。ヒストグラムは件数で母数が異なる。原解析は再実行していない |
| 考察3の共変量相関 | [PR #52](https://github.com/ari-show/decoupling/pull/52)、2-Exp-47 | 5 seed平均。観察的な関連であり因果効果とはしない |
| 学習予算の付録 | [PR #55](https://github.com/ari-show/decoupling/pull/55)、2-Exp-48 | 240 epochでも未収束。中心化の差が縮むことを示し、収束後の優劣は確定しない |
| Encoder比較の付録 | [PR #51](https://github.com/ari-show/decoupling/pull/51)、2-Exp-45 | 日MLPの0.04780と主表の日GRUの0.04828を区別。MLPのseed間SDが小さいとはしない |
| 差し替え・マスクの付録 | [PR #56](https://github.com/ari-show/decoupling/pull/56)、[PR #57](https://github.com/ari-show/decoupling/pull/57) | 主表とは別の追加検証。構造上の漏れ抑制と未知日への一般化を区別 |
| 潜在情報・移植の探索付録 | 元スライドのstage1〜8、stage15〜19、fig3再解析 | 既存数値を保存して付録化。この編集では原stageコード・全出力との再照合は未実施。原因を中心化や非線形性に断定しない |

## 分散の式の修正

`ss_share_k = Var(c_k)/Var(r)`。成分分散比の和に符号付き交差項の和を足すと、`Var(r_hat)/Var(r)`になる。予測R²と同じ量ではない。

取得した2-Exp-44の5 seed平均は次の通り。

| 量 | 中心化あり | 中心化なし |
| --- | ---: | ---: |
| 成分分散比の和 | 0.411802 | 0.126547 |
| 交差項の符号付き合計 | 0.003539 | 0.085999 |
| 推定残差の分散比 | 0.415341 | 0.212546 |
| 予測R² | 0.415719 | 0.279431 |

観測マスク下では個々の交差項はゼロではない。符号付き合計が小さいことを厳密な直交性と同一視しない。主発表ではR²の内訳という表現を削除し、分散比と平均誤差への寄与を別の診断として示す。

## 全期間成分の解釈

他成分固定時の最適定数は、観測セル上の `median(r-a-t-u)`。系列の売上中央値と平均の差そのものとは一般に異なる。中央値基準に変えてもgがゼロになる保証はなく、再学習で検証する。事後の成分除去と、成分を持たないモデルの再学習も等価とは扱わない。

## 2026-10-24：付録の記号・モデル構造の照合

- `data.py: frame_to_examples`：入力13チャネル。入力マスクは残差チャネルだけが観測マスク、残りは1。
- `data.py: _time_features`：日番号mod 7による周期位置。実日付の曜日とは区別。
- `retail_models.py: GlobalEncoder / DayEncoder / HourEncoder`：チャネル別の平均・SD、分母max(count,1)、平方根内epsilon=1e-6。日GRUは28日分の集約特徴を読む。
- `residual_models.py: OutputDecompositionResidualModel`：生出力tildeと中心化後hatを区別。中心化はマスクなしの全格子で行う。
- `retail_models.py: covariance_penalty`：g,a,tの系列要約に対するバッチ内交差共分散。分母max(B-1,1)、二乗要素平均を3対分足す。
- `residual_experiments.py: residual_loss`：主設定は観測セルMAE+0.01×共分散罰則。他の罰則重みは0。
- Procrustes再解析の列標準化の有無は引き続き未照合。列中心化の場合の定義として式と注記を掲載し、数値の再計算はしていない。
