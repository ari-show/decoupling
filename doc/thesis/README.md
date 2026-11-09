# 修士論文 作業ドキュメント

| ファイル | 内容 |
|---|---|
| [related_work_history.md](related_work_history.md) | 従来研究の系譜（8 期の時代区分）、系譜ごとの「何を分け、どこで保証するか」、related work 章の 8 段落設計、残っている調査課題 |
| [references.md](references.md) | 参考文献 103 件の分野別リスト（層・本研究との関係・書誌確認状況つき） |
| [references.bib](references.bib) | 上記 103 件の BibTeX。キーは references.md と一致 |
| [anova_output_constraint_prior_work.md](anova_output_constraint_prior_work.md) | **本研究の方法そのものの先行例の精査**。出力成分への平均ゼロ制約は既存であることの確認、残る新規性の切り分け、本文の記述の修正案 |

## 現状

- 2026-11-09 時点で 103 件を収集。本文で必ず引く `必須` 層が 39 件あり、「最低 30 本」の要件は満たしている。
- うち 27 件は Web 検索で著者・会議・年（可能なら巻号頁）を照合済み。残り 76 件は分野の定番文献で、`references.bib` に `% TODO` を付けてある。投稿前に DOI で巻号・頁を照合する。

## 最重要: 新規性の記述を書き換える必要がある

追加調査（[anova_output_constraint_prior_work.md](anova_output_constraint_prior_work.md)）の結果、**「出力成分に平均ゼロ・主効果除去制約を入れる」という設計には先行例がある**ことが確定した。最近傍は Märtens & Yau (2020) で、VAE の decoder 出力を主効果 + 交互作用に加法分解し、各成分へ周辺効果ゼロの積分制約をペナルティとして課している。

したがって proposal の新規性 3 番はそのままでは主張できない。残る差分は「制約の仕組み」ではなく **軸の選び方（時系列の構造単位）** と **対象（強い基準値後の残差）** と **成分回復の定量評価** であり、主張の順序も 1 → 2 → 4 → 3 に変える。具体的な書き換え案は同ドキュメントにある。

## この調査で分かった、proposal に足すべき 2 点

1. **解釈可能加法モデルの「純化」系譜が最近傍である。** Hooker (2007) と Lengerich et al. (2020) は、交互作用項から主効果を抜いて一意な加法分解を回復する手続きを扱っており、本研究の centering（平均ゼロ・主効果除去）とほぼ同じ発想である。現 [../proposal/related_work_and_improvement.md](../proposal/related_work_and_improvement.md) の 5 系譜にはこの系譜が入っていないので、修論では独立した段落にする。
2. **潜在分離を主張しない選択の、理論的な裏付けが取れる。** Locatello et al. (2019) が教師なし disentanglement の非識別性を示し、Khemakhem et al. (2020) が補助変数で条件づけた prior による識別可能性を与えている。本研究が「latent の識別は保証せず、出力成分の制約で保証する」という立場を取る理由を、実験結果（2-Exp-27/28/50）だけでなく既存理論からも説明できる。

## 次の調査課題

[related_work_history.md](related_work_history.md) の第 5 節に記録してある。3 件目（ANOVA 制約を NN 出力に入れた先行例）は 2026-11-09 に調査し決着した。残るのは次の 2 件である。

1. 時間帯粒度の小売需要予測の先行研究が薄い。Boldi et al. (2019) と HNAM (2024, ただし日次) 以外の直接の比較対象が見つかっていない。
2. 欠品打ち切りと表現学習を同時に扱った研究を特定できていない。FreshRetailNet の baseline 論文 (Wang et al. 2025) の引用文献を辿るのが最短である。
