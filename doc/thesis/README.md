# 修士論文 作業ドキュメント

| ファイル | 内容 |
|---|---|
| [related_work_history.md](related_work_history.md) | 従来研究の系譜（8 期の時代区分）、系譜ごとの「何を分け、どこで保証するか」、related work 章の 8 段落設計、残っている調査課題 |
| [references.md](references.md) | 参考文献 97 件の分野別リスト（層・本研究との関係・書誌確認状況つき） |
| [references.bib](references.bib) | 上記 97 件の BibTeX。キーは references.md と一致 |

## 現状

- 2026-11-09 時点で 97 件を収集。本文で必ず引く `必須` 層が 34 件あり、「最低 30 本」の要件は満たしている。
- うち 22 件は Web 検索で著者・会議・年（可能なら巻号頁）を照合済み。残り 75 件は分野の定番文献で、`references.bib` に `% TODO` を付けてある。投稿前に DOI で巻号・頁を照合する。

## この調査で分かった、proposal に足すべき 2 点

1. **解釈可能加法モデルの「純化」系譜が最近傍である。** Hooker (2007) と Lengerich et al. (2020) は、交互作用項から主効果を抜いて一意な加法分解を回復する手続きを扱っており、本研究の centering（平均ゼロ・主効果除去）とほぼ同じ発想である。現 [../proposal/related_work_and_improvement.md](../proposal/related_work_and_improvement.md) の 5 系譜にはこの系譜が入っていないので、修論では独立した段落にする。
2. **潜在分離を主張しない選択の、理論的な裏付けが取れる。** Locatello et al. (2019) が教師なし disentanglement の非識別性を示し、Khemakhem et al. (2020) が補助変数で条件づけた prior による識別可能性を与えている。本研究が「latent の識別は保証せず、出力成分の制約で保証する」という立場を取る理由を、実験結果（2-Exp-27/28/50）だけでなく既存理論からも説明できる。

## 次の調査課題

[related_work_history.md](related_work_history.md) の第 5 節に 3 件（時間帯粒度の小売需要予測、欠品打ち切り × 表現学習、ANOVA 制約を NN 出力に入れた先行例）を記録してある。3 件目は新規性の記述に直接関わるため、投稿前に必ず確認する。
