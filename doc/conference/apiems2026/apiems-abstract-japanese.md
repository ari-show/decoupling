# APIEMS 2026 Abstract作成メモ（日本語）

## 目的

APIEMS 2026のAbstract-only submissionに向けて、JIMAで整理した研究内容を土台に、日本語でAbstractの材料と文章を一問一答形式で固める。

最終的には、以下の順序で英語Abstractへ変換する。

1. 研究背景・実務上の課題
2. 研究目的・問い
3. 提案手法
4. 実験設定・データ
5. 主な結果
6. 学術的・実務的意義
7. 限界・適用条件（必要な場合）

## 投稿前提

| 項目 | 現時点の情報 |
| --- | --- |
| 会議 | APIEMS 2026 |
| 投稿形式 | Abstract-only |
| Abstract言語 | 英語（まず日本語で作成） |
| フルペーパー | 今回は提出しない |
| 研究対象 | 小売需要予測、店舗・商品・日・時間帯粒度 |
| データ | FreshRetailNet、および成分回復用の合成データ |

## 既存資料から確認できる研究の骨子

## JIMA原稿から確認できた確定情報

参照ファイル：`../jima2026/paper-jima2026fall/jima2026fall.pdf`

### 原稿のタイトル

「中心化制約付き残差成分分解を用いた小売需要の時間別予測補正」

### 研究の出発点

店舗・商品ごとの時間別売上には、全期間に共通する変動、特定の日に共通する変動、特定の時間帯に共通する変動、日×時間帯の組合せに固有の変動が含まれる。従来の大域・局所表現の考え方を、日×時間帯の二軸を持つ小売需要へ拡張する。

### JIMA原稿でのモデル

基準値からの残差を、次の4成分の和として表現する。

`残差 = 全期間成分 + 日成分 + 時間帯成分 + 日×時間帯交互作用成分`

各成分の役割が重複しないよう、日成分・時間帯成分・交互作用成分に中心化制約を課す。観測残差を入力し、同一観測期間の残差を再構成する基礎検証である。

### JIMA原稿の実験結果

FreshRetailNet-50Kを用いた観測期間内の残差再構成で、MAEは次の通り。

| 手法 | MAE |
| --- | ---: |
| 基準値のみ | 0.06966 |
| 中心化なし | 0.05422 |
| 提案（中心化あり） | **0.04828** |

提案モデルは、基準値のみより約31%、中心化なしより約11% MAEが低い。JIMA原稿の限界として、観測残差を入力とした同期間の再構成に限られ、未来日の予測は今後の課題とされている。

### 研究上の問題意識

小売需要予測では、系列平均や直近の同時間帯平均などの単純な基準値が強く、売上を直接予測する複雑なモデルが基準値を安定して上回るとは限らない。一方で、基準値と実績の間の残差には、系列・日・時間帯などの構造が残る場合がある。

### 現時点の提案

売上そのものではなく、基準値からの残差を予測対象とする。残差の補正量を、以下の4つの出力成分に分解する。

- 系列成分（series / global）
- 日成分（day）
- 時間帯成分（hour）
- 日×時間帯の相互作用成分（day-hour interaction）

日成分・時間帯成分・相互作用成分に中心化（centering）制約を課し、各成分の担当範囲を固定することで、補正と解釈を両立させる。

### 現時点の主な結果候補

- 合成データでは、真の成分が存在する条件で各成分を高い相関で回復できた。
- FreshRetailNetでは、系列平均を基準値とした場合、cell MAEが0.0697から0.0501へ改善した。
- 基準値が大きく外した上位10%のケースでは、MAEが0.2923から0.1914へ改善した。
- 学習された時間帯成分と残差の時間帯プロファイルの相関は約0.99であった。
- latent表現を分割するだけでは同様の補正・解釈は得られず、出力分解と中心化の必要性が示された。
- 同時間帯直近平均のように時間帯構造をすでに吸収した基準値では、追加補正の効果は限定的であった。

※数値はAbstractに採用する前に、最終的な実験表・評価条件との整合を確認する。

## 一問一答

### Q1（未回答）

この研究を、専門外の研究者にも伝わるように一文で言うと、何を明らかにした研究ですか？

回答：

従来の、ある期間内のデータ窓を共通成分と固有成分に分けて潜在変数に落とし込む表現学習を、時間軸と日付軸へ拡張した研究である。

補足メモ：

- この表現は研究の出発点・既存手法との関係を説明するものとして採用する。
- Abstractでは、最終的な提案である「基準値からの残差を、系列・日・時間帯・日×時間帯の出力成分に分け、中心化制約で解釈可能にする」という説明へ接続する。

### Q2（未回答）

その従来の表現学習を、今回の小売需要予測に拡張しようとしたとき、どのような問題や限界がありましたか？

回答：

成分ごとの解釈性や責務の分解能を高めることに課題があった。従来は日付単位までの解像度だった表現を、時間帯成分まで含めて、より多角的に抽出できるようにすることを目指した。

### Q3（未回答）

時間帯や日付などの成分を分解して抽出できると、需要予測や実務上、何ができるようになると考えていますか？

回答：

残差から読み取れる、対象期間内全体の構造、特定の日付に起因する構造、特定の時間帯に起因する構造を切り分けて捉えられる。

### Q4（未回答）

モデルは、売上そのものを直接予測したのですか。それとも、何らかの基準値からの残差を予測したのですか？基準値を使った場合は、どのような基準値ですか？

回答：

売上そのものではなく、基準値を差し引いた残差を予測対象とした。

### Q5（未回答）

今回の実験で主に使った「基準値」は、具体的には何ですか？（例：系列全体の平均、直近同時間帯の平均など）

回答：

（要確認）会話上では「直近同時間帯平均」と回答されたが、JIMA PDFでは「対象期間における欠品セルを除いた観測売上の平均」と定義されている。

補足メモ：

- 基準値の選択自体を研究の主題とするのではなく、FreshRetailNet-50Kにおける実験条件として扱う。
- JIMA PDFに基づく場合は、期間平均を基準値とし、提案モデルのMAE 0.04828を主結果として扱う。

### Q6（未回答）

APIEMSでは、JIMA PDFと同じ実験結果（期間平均を基準値、提案MAE 0.04828）を使いますか？それとも、別実験の「直近同時間帯平均」を使いますか？

回答：

JIMA PDFと同じ実験結果を使う。すなわち、対象期間の欠品セルを除いた観測売上の平均を基準値とし、観測期間内の残差再構成を評価する。主な結果は、基準値のみ0.06966、中心化なし0.05422、提案（中心化あり）0.04828である。

### Q7（未回答）

APIEMSのAbstractでは、今回の範囲を「未来の需要予測」として強く主張しますか？それとも、JIMA原稿どおり「観測期間内の残差再構成による基礎検証」として正確に書きますか？

回答：

未来の需要予測を実現するための前段階として位置付ける。ただし、今回のAbstractではJIMA原稿どおり、観測期間内の残差再構成による基礎検証として記述する。

### Q8（未回答）

提案モデルは、売上と基準値から計算した残差以外に、どのような情報を入力として使っていますか？（例：欠品情報、曜日、休日、販促、割引率、天候など）

回答：

JIMA原稿のままとする。残差に加えて、欠品情報、曜日、休日・販促、割引率、天候などの共変量を入力に用いる。

### Q9（未回答）

APIEMSのAbstractで、研究の新規性として最も強調したいのは、次のどれですか？

1. 残差を全期間・日・時間帯・日×時間帯の4成分に分解したこと
2. 成分の役割を定める中心化制約を導入したこと
3. 4成分分解と中心化制約によってMAEを改善したこと

回答：

新規性の優先順位は、1. 残差を全期間・日・時間帯・日×時間帯の4成分に分解すること、2. 成分の役割を定める中心化制約、の順とする。MAE改善は、提案設計の有効性を示す実験結果として扱う。

### Q10（未回答）

主結果として、基準値のみMAE 0.06966、中心化なし0.05422、提案（中心化あり）0.04828、および「基準値のみより約31%、中心化なしより約11%低下」という数値をAbstractに入れてよいですか？

回答：

主結果として、基準値のみMAE 0.06966、中心化なし0.05422、提案（中心化あり）0.04828を用いる。また、提案手法は基準値のみより約31%、中心化なしより約11% MAEが低いと記述する。

### Q11（未回答）

4成分のうち、`g` に対応する成分は、Abstractでは「全期間成分」と「共通成分」のどちらの表現で統一しますか？

回答：

英語表現に合わせ、`g` に対応する成分は「global成分」と表記する。4成分は global、day、hour、day-hour interaction とする。

## 日本語Abstract初稿

小売の時間別需要には、店舗・商品ごとの基本的な需要水準に加えて、日や時間帯に応じた変動が含まれる。これらの変動を共有範囲の違いに基づいて分解できれば、将来の時間別需要予測において、基準値からの補正量を成分別に解釈できる。本研究では、基準値からの残差を、global、day、hour、day-hour interactionの4成分に分解する残差成分分解モデルを提案する。複数成分の和だけでは各成分の役割が一意に定まらないため、day、hour、interaction成分に中心化制約を導入し、成分間の冗長性を抑える。FreshRetailNet-50Kを用い、観測期間内の残差再構成によって提案手法の基礎的な有効性を検証した。基準値のみ、中心化なしの成分分解、提案手法を比較した結果、MAEはそれぞれ0.06966、0.05422、0.04828であった。提案手法は基準値のみより約31%、中心化なしより約11%低いMAEを示した。以上より、残差を共有範囲の異なる4成分に分解し、中心化制約によって各成分の役割を定めることが、時間別変動の再構成に有効であることを確認した。本研究は、共変量のみから将来の各成分を推定する時間別需要予測に向けた基礎検証として位置付けられる。

## English Abstract Draft

Hourly retail demand consists of a basic store-product demand level and variations associated with days and hours. Decomposing these variations according to their sharing ranges can provide interpretable corrections from a baseline for future hourly demand forecasting. This study proposes a residual component decomposition model that represents the residual from a baseline as four components: global, day, hour, and day-hour interaction. Because an additive decomposition alone does not uniquely determine the role of each component, we introduce centering constraints on the day, hour, and interaction components to reduce redundancy among them. Using FreshRetailNet-50K, we conduct a fundamental validation through within-period residual reconstruction. The mean absolute errors (MAEs) of the baseline-only method, the component decomposition without centering, and the proposed method are 0.06966, 0.05422, and 0.04828, respectively. The proposed method reduces MAE by approximately 31% compared with the baseline-only method and by approximately 11% compared with the decomposition without centering. These results indicate that decomposing residuals into four components with different sharing ranges, together with centering constraints that define their roles, is effective for reconstructing hourly variations. This study provides a basis for future hourly demand forecasting in which the components are estimated from covariates alone.

## 回答から作成する日本語Abstract（未完成）

### 背景・課題

（Q&Aで確定後に記入）

### 目的

（Q&Aで確定後に記入）

### 方法

（Q&Aで確定後に記入）

### 結果

（Q&Aで確定後に記入）

### 意義

（Q&Aで確定後に記入）

## 表現上の方針

- 「常に精度が向上する」とは書かず、残差構造が残る基準値で有効と表現する。
- 貢献の中心は、単純な精度改善ではなく、残差の補正と成分別解釈を同時に可能にする点とする。
- latentを分けるだけでは不十分で、出力成分の分解と中心化が重要であることを示す。
- APIEMS向けには、予測精度競争だけでなく、発注・補充などの意思決定を支援する解釈可能な診断として位置付ける。
