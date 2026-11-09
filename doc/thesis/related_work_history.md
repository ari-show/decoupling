# 従来研究の系譜と本研究の位置づけ（修論 related work 用）

作成日: 2026-11-09

## このドキュメントの役割

修士論文の related work 章と序論で「従来研究の幅」を確保するための地図である。

- 書誌情報そのものは [references.md](references.md) と [references.bib](references.bib) に置く。
- ここでは **どの系譜が何を分けようとしてきたか** を時代順に整理し、本研究（基準値からの残差を系列・日・時間帯・日×時間帯の出力成分に分ける）がどこに入るかを確定する。
- 既存の [../proposal/related_work_and_improvement.md](../proposal/related_work_and_improvement.md) は「5 系譜 + 6 段落」で構成を決めていた。本ドキュメントはそれを壊さず、**時代軸**と**ANOVA/加法モデルの系譜**を足して拡張したものである。

## 0. 一行での位置づけ

```text
時系列を「分ける」研究は 70 年続いているが、
分解を保証する場所は季節成分 → 状態空間 → 潜在表現 → モデル内部の trend/season
と移ってきただけで、「運用単位の出力成分として保証する」系譜はまだ薄い。
本研究はそこに、強い基準値の残差という前提つきで入る。
```

## 1. 時代別の系譜

### 第 1 期（1950s–1970s）: 系列ごとの局所モデルと季節性の分離

指数平滑（Holt, Winters）、季節調整（X-11）、ARIMA（Box & Jenkins）が確立した時期である。

- ここで既に「水準 / トレンド / 季節」という**加法的な成分分解**が実務の標準になった。
- ただし分解は系列ごとに閉じており（local model）、成分は trend/season という粗い粒度に固定されていた。
- 本研究の「基準値 $b$」は、この時代の遺産そのものである。`series_mean` や `same_hour_recent_mean` は、指数平滑・季節ナイーブの最小形と見なせる。

関連: Holt (2004/1957), Winters (1960), Shiskin et al. (1967), Box & Jenkins (1970), Cleveland et al. (1990, STL)

### 第 2 期（1960s–1990s）: 状態空間・構造時系列と分散成分

カルマンフィルタ・構造時系列（Harvey）と、実験計画・分散成分（Fisher, Scheffé, Searle et al.）が並行して成熟した。

- 構造時系列は、成分を**モデルの構造として明示**した点で本研究に近い。
- 一方 ANOVA / 分散成分の系譜は、「主効果と交互作用をどう一意に定めるか」という**識別の問題**を正面から扱った。平均ゼロ制約（sum-to-zero contrast）はここが出発点である。
- 本研究の中心仮説 $r_{idh}=g_i+a_{id}+c_{ih}+u_{idh}+\varepsilon$ は、形式上は二元配置 ANOVA（系列内の日×時間帯）であり、この系譜の直系である。

関連: Fisher (1935), Scheffé (1959), Harvey (1989), Searle et al. (1992), Gelman & Hill (2007)

### 第 3 期（1990s–2010s）: 局所パターンと、在庫・欠品下の需要推定

機械学習側では shapelet のような**局所部分列**の重要性が示され、OR / マーケティング側では**欠品による打ち切り需要**の推定が整備された。

- Shapelets 以降の系譜は「平均的な当てはまりではなく、どの局所形状が効いたか」を説明対象にした。本研究で high residual 上位を見る発想はここに接続する。
- 欠品下の需要推定（Anupindi et al., Vulcano et al.）は、観測売上が真の需要の打ち切りであることを前提にする。FreshRetailNet の stockout マスクを使う本研究は、この前提を引き継いでいる。
- 間欠需要（Croston）は、小売需要が「平均を当てる」問題ではないことの古典的根拠になる。

関連: Croston (1972), Anupindi et al. (1998), Syntetos & Boylan (2005), Vulcano et al. (2012), Ye & Keogh (2009), Grabocka et al. (2014)

### 第 4 期（2013–2020）: 深層生成モデルと disentanglement

VAE 以降、「潜在変数を意味のある因子に分ける」ことが研究テーマになった。

- 画像系の $\beta$-VAE / $\beta$-TCVAE を経て、系列では **時間不変（static/global）と時間変動（dynamic/local）** の二分が標準の切り方になった（FHVAE, DSVAE, S3VAE, C-DSVAE）。
- GP-VAE は local 潜在に時間相関の prior を入れる流れを作り、本研究の元論文（Tonekaboni et al. 2022）の GP prior に直結する。
- 同時期に Locatello et al. (2019) が「教師なしでは disentanglement は原理的に保証されない」ことを示し、Khemakhem et al. (2020) が **補助変数で条件づけた prior があれば識別可能**という条件を与えた。
- この 2 本は本研究の論理にとって決定的である。本研究は潜在の識別を主張せず、出力成分の制約に保証対象を移すが、その選択の正当化がここから取れる。

関連: Kingma & Welling (2014), Higgins et al. (2017), Chen et al. (2018), Locatello et al. (2019), Khemakhem et al. (2020), Hsu et al. (2017), Li & Mandt (2018), Zhu et al. (2020), Bai et al. (2021), Fortuin et al. (2020)

### 第 5 期（2018–2022）: 自己教師あり時系列表現と local/global の明示的分離

CPC から TS2Vec までの流れで、ラベルなし時系列から汎用表現を学ぶことが確立した。

- 粒度（timestamp / subsequence / instance）と view（時間 / 周波数、局所文脈 / 大域文脈）の設計が主要な論点になった。
- その延長として、**元論文 Tonekaboni et al. (2022)** が local 表現（GP prior つき時系列）と global 表現（系列ごと 1 本）を明示的に分け、counterfactual regularization で相互情報量を抑えた。
- 本研究の出発点はここであり、`2-Exp-26〜28` はこの設計を小売時間帯需要へ移したときに何が起きるかの検証にあたる。

関連: van den Oord et al. (2018), Franceschi et al. (2019), Tonekaboni et al. (2021, TNC), Eldele et al. (2021), Yue et al. (2022), Woo et al. (2022), Zhang et al. (2022, TF-C), Zerveas et al. (2021), Tonekaboni et al. (2022)

### 第 6 期（2021–2024）: 予測モデル内部への分解の組み込み

Transformer 系予測が、分解をアーキテクチャの中に入れた時期である。

- Autoformer の series decomposition block、FEDformer の周波数分解、N-BEATS の解釈可能基底、TimeMixer の multi-scale mixing、DLinear の trend/seasonal 線形分解。
- ここで重要なのは、**分解はもう珍しくない**が、粒度は trend / season / scale / frequency のいずれかに留まっている点である。
- 「日 × 時間帯」という**運用単位の二元配置**まで下ろした分解は、この系譜には見当たらない。これが本研究の差分の中心になる。
- また、global-local 予測の系譜（DeepAR → Deep Factors → DeepGLO → TLAE）と、Montero-Manso & Hyndman (2021) の locality/globality の理論整理は、「global 成分と系列固有成分を分ける」ことの一般的な有効性の根拠として引ける。

関連: Salinas et al. (2020), Wang et al. (2019), Sen et al. (2019), Nguyen & Quanz (2021), Oreshkin et al. (2020), Montero-Manso & Hyndman (2021), Zhou et al. (2021), Wu et al. (2021), Zhou et al. (2022), Zeng et al. (2023), Challu et al. (2023), Wang et al. (2024)

### 第 7 期（2013–2021）: 解釈可能加法モデルと「交互作用の純化」

本研究の方法論にとって、第 4〜6 期より重要な系譜である。

- GAM（Hastie & Tibshirani）→ GA²M（Lou et al. 2013）→ **functional ANOVA による純化**（Hooker 2007, Lengerich et al. 2020）→ NAM（Agarwal et al. 2021）。
- Lengerich et al. (2020) は「交互作用項に主効果が混ざっていると解釈できないので、functional ANOVA で主効果を抜き出して純化する」ことを明示的に扱っている。これは本研究の **centering（平均ゼロ・主効果除去）制約とほぼ同じ発想**である。
- したがって本研究は、「解釈可能加法モデルの純化」を**時系列の残差補正**へ持ち込んだ研究として位置づけられる。この接続は現 proposal にまだ書かれていないので、修論で足す価値が最も高い。
- Hooker (2007) は入力が従属なときの直交性（階層的直交性）を扱っており、日と時間帯が独立でない実データでの centering の正当化に使える。

関連: Hastie & Tibshirani (1986), Stone (1985), Sobol' (2001), Hooker (2007), Lou et al. (2013), Lengerich et al. (2020), Agarwal et al. (2021), Rudin (2019)

### 第 8 期（2020–2025）: 大規模小売ベンチマークと打ち切り需要データ

M5 で「階層つき小売需要の大規模比較」が標準化され、FreshRetailNet-50K で「時間帯粒度 + 欠品注釈」が公開された。

- M5 の知見（単純手法が強い、階層ごとに勝者が違う）は、本研究が「基準値を置き換えない」立場を取る根拠になる。
- FreshRetailNet-50K (2025) は、本研究の実験基盤そのものであり、欠品による構造的欠測が MAR 仮定を破ることを明示している。
- 時間帯粒度の小売需要に加法モデルを当てた先行例として Boldi et al. (2019) があり、**本研究に最も近い応用研究**の一つとして必ず引くべきである（分位点加法モデルで時間内売上を予測）。

関連: Makridakis et al. (2020, 2022a, 2022b), Fildes et al. (2022), Hyndman et al. (2011), Wickramasuriya et al. (2019), Boldi et al. (2019), Wang et al. (2025, FreshRetailNet-50K)

## 2. 系譜ごとの「何を分け、どこで保証するか」

| 系譜 | 分ける対象 | 保証の場所 | 粒度 | 本研究との差分 |
|---|---|---|---|---|
| 季節調整・指数平滑 | trend / season | 定義（決定論的） | 粗い | 本研究はこれを $b$ として温存し、残差を扱う |
| 構造時系列・状態空間 | 成分の状態 | モデル構造 | 粗い | 日×時間帯の交互作用を明示しない |
| ANOVA・分散成分 | 主効果 / 交互作用 | 制約（sum-to-zero） | 任意 | 学習モデルでなく、共変量からの予測をしない |
| disentangled 系列 VAE | static / dynamic | 潜在空間 + 正則化 | 2 分割 | 潜在の識別は保証されない（Locatello 2019） |
| 自己教師あり表現 | 文脈の粒度 | 対照損失 | 多粒度 | 因子の運用的意味は暗黙 |
| global-local 予測 | 共通 / 系列固有 | モデル分割 | 2 分割 | 日・時間帯まで割らない |
| Transformer 内分解 | trend / season / scale | アーキテクチャ | 粗い | 運用単位に対応しない |
| 加法モデルの純化 | 主効果 / 交互作用 | functional ANOVA | 特徴単位 | 時系列の残差補正には適用されていない |
| **本研究** | **系列 / 日 / 時間帯 / 日×時間帯** | **出力成分の平均ゼロ・主効果除去制約** | **運用単位** | — |

この表の最終行が、修論の貢献の主張形になる。

## 3. related work 章の段落設計（修論版・8 段落）

既存 proposal の 6 段落を、ANOVA 系譜と小売系譜を足して 8 段落に拡張する。

| # | 段落の主張 | 主な引用 |
|---|---|---|
| 1 | 時系列予測は古くから「成分に分けて読む」営みであり、trend/season の加法分解が実務の標準になった | Holt, Winters, Box & Jenkins, Cleveland (STL), Harvey, Taylor & Letham |
| 2 | 深層表現学習は、この分離を潜在空間での static/dynamic 分離として再定式化した | Kingma & Welling, Hsu, Li & Mandt, Zhu, Bai, Fortuin, Tonekaboni 2022 |
| 3 | しかし教師なしでの潜在分離は原理的に保証されず、識別には追加条件が必要である | Locatello 2019, Khemakhem 2020, Hyvärinen & Morioka 2016 |
| 4 | 自己教師あり時系列表現は下流性能では有効だが、成分の運用的意味は与えない | CPC, TNC, TS2Vec, TS-TCC, TF-C, CoST, Zerveas, PatchTST |
| 5 | 予測側では global-local 分割と内部分解が有効だが、粒度は trend/season/scale に留まる | DeepAR, Deep Factors, DeepGLO, TLAE, N-BEATS, Autoformer, FEDformer, TimeMixer, DLinear, Montero-Manso & Hyndman |
| 6 | 一方、解釈可能加法モデルの系譜は「主効果を抜いて交互作用を純化する」ことを制約として明示してきた | GAM, GA²M, Hooker 2007, Lengerich 2020, NAM, Rudin |
| 7 | 小売需要では基準値が強く、欠品による打ち切りがあり、評価は階層・外れケース依存である | M5, Fildes 2022, Croston, Anupindi, Vulcano, Boldi 2019, FreshRetailNet-50K |
| 8 | 以上より、本研究は「強い基準値後の残差」を対象に、出力補正を系列/日/時間帯/日×時間帯へ分け、平均ゼロ制約で担当範囲を固定する点で既存研究と異なる | — |

締めの英文（proposal の既存案を ANOVA 系譜ぶん拡張したもの）:

```text
Prior work has demonstrated the value of local/global separation in latent space,
contrastive time-series representations, and decomposition-based forecasting, while
the interpretable-additive-model literature has shown that interaction effects must be
purified against main effects to be readable. However, latent disentanglement is not
identifiable without additional assumptions, and existing time-series decompositions
remain at coarse levels such as trend, seasonality, or scale. In contrast, this work
targets the residual left by strong retail baselines and constrains the output correction
itself into operational components -- series, day, hour, and day-hour interaction --
with zero-mean and main-effect-removal constraints.
```

## 4. 引用の優先順位

| 層 | 本数 | 用途 |
|---|---|---|
| 必須（本文で必ず引く） | 34 | 元論文、disentanglement の識別性、global-local 予測、分解型予測、加法モデルの純化、小売・FreshRetailNet、評価指標 |
| 補強（related work と考察で引く） | 42 | 自己教師あり表現、異常検知・高残差、局所パターン、階層予測、較正 |
| 背景・歴史（序論 1 段落で束ねて引く） | 21 | 指数平滑、季節調整、ANOVA 古典、状態空間 |

合計 97 件。30 本という最低ラインには十分な余裕がある。詳細は [references.md](references.md) の「層」列を見る。

## 5. 残っている調査課題

正直に書くと、次の 3 点はまだ埋まっていない。

1. **時間帯粒度の小売需要予測の先行研究が薄い。** Boldi et al. (2019) 以外に直接の比較対象が見つかっていない。`intraday retail demand forecasting` / `hourly store sales profile` / `within-day demand profile` での追加探索が必要である。
2. **欠品打ち切りと表現学習を同時に扱った研究**を特定できていない。FreshRetailNet の baseline 論文（Wang et al. 2025）の引用文献を辿るのが最短である。
3. **二元配置 ANOVA をニューラルネットの出力制約として入れた先行例**が、Lengerich et al. (2020) 以外にあるか未確認である。もしあれば本研究の新規性の記述を弱める必要があるので、投稿前に必ず確認する。
