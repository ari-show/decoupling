# 修論用 参考文献リスト（分野別・97 件）

作成日: 2026-11-09

## 使い方

- 系譜としての読み方は [related_work_history.md](related_work_history.md) を見る。
- BibTeX は [references.bib](references.bib) にある。キーは本リストの `key` 列と一致する。
- **層**: `必須` = 本文で必ず引く / `補強` = related work・考察で引く / `背景` = 序論で束ねて引く。
- **確認**: `✓` = 2026-11-09 に Web 検索で著者・会議・年（可能なら巻号頁）まで確認済み / `△` = 定番文献だが今回は未照合。**投稿前に DOI で要確認**。
- 最低 30 本の要求に対し、`必須` だけで 34 件ある（必須 34 / 補強 42 / 背景 21）。

## A. 元論文と、潜在表現の分離（static/dynamic, local/global）

| # | key | 文献 | 層 | 本研究との関係 | 確認 |
|---|---|---|---|---|---|
| 1 | tonekaboni2022decoupling | Tonekaboni, S., Li, C.-L., Arık, S. O., Goldenberg, A., Pfister, T. "Decoupling Local and Global Representations of Time Series." AISTATS 2022, PMLR 151:8700–8714. | 必須 | 本研究の出発点。local（GP prior）/ global の分離と counterfactual 正則化 | ✓ |
| 2 | kingma2014vae | Kingma, D. P., Welling, M. "Auto-Encoding Variational Bayes." ICLR 2014. | 必須 | VAE の基礎。提案モデルの encoder/decoder の前提 | △ |
| 3 | higgins2017betavae | Higgins, I. et al. "beta-VAE: Learning Basic Visual Concepts with a Constrained Variational Framework." ICLR 2017. | 補強 | 潜在の分離を正則化強度で制御する流れ | △ |
| 4 | chen2018tcvae | Chen, R. T. Q., Li, X., Grosse, R., Duvenaud, D. "Isolating Sources of Disentanglement in Variational Autoencoders." NeurIPS 2018. | 補強 | 分離の分解（total correlation）。評価指標の議論に使える | △ |
| 5 | locatello2019challenging | Locatello, F. et al. "Challenging Common Assumptions in the Unsupervised Learning of Disentangled Representations." ICML 2019. | 必須 | 教師なし潜在分離は原理的に保証されない。本研究が保証を出力側へ移す根拠 | △ |
| 6 | khemakhem2020ivae | Khemakhem, I., Kingma, D. P., Monti, R. P., Hyvärinen, A. "Variational Autoencoders and Nonlinear ICA: A Unifying Framework." AISTATS 2020, PMLR 108:2207–2217. | 必須 | 補助変数で条件づけた prior があれば識別可能。日・時間帯を観測変数として扱う本研究の立場に接続 | ✓ |
| 7 | hyvarinen2016tcl | Hyvärinen, A., Morioka, H. "Unsupervised Feature Extraction by Time-Contrastive Learning and Nonlinear ICA." NeurIPS 2016. | 背景 | 時間構造を補助情報にした非線形 ICA の原型 | △ |
| 8 | bengio2013representation | Bengio, Y., Courville, A., Vincent, P. "Representation Learning: A Review and New Perspectives." IEEE TPAMI 35(8):1798–1828, 2013. | 背景 | 表現学習の総説。序論の導入 | △ |
| 9 | hsu2017fhvae | Hsu, W.-N., Zhang, Y., Glass, J. "Unsupervised Learning of Disentangled and Interpretable Representations from Sequential Data." NeurIPS 2017. | 補強 | FHVAE。系列の階層的な時間不変／変動分離の初期例 | △ |
| 10 | li2018dsvae | Li, Y., Mandt, S. "Disentangled Sequential Autoencoder." ICML 2018. | 補強 | DSVAE。static/dynamic 二分の標準形 | △ |
| 11 | zhu2020s3vae | Zhu, Y., Min, M. R., Kadav, A., Graf, H. P. "S3VAE: Self-Supervised Sequential VAE for Representation Disentanglement and Data Generation." CVPR 2020. | 補強 | 自己教師ありで static/dynamic を分ける | △ |
| 12 | bai2021cdsvae | Bai, J., Wang, W., Gomes, C. P. "Contrastively Disentangled Sequential Variational Autoencoder." NeurIPS 2021 (NeurIPS 34). | 補強 | 相互情報量の対照推定で分離を強める。swap 正則化との比較対象 | ✓ |
| 13 | fortuin2020gpvae | Fortuin, V., Baranchuk, D., Rätsch, G., Mandt, S. "GP-VAE: Deep Probabilistic Time Series Imputation." AISTATS 2020. | 必須 | local 潜在への GP prior。元論文の prior の直接の源流 | △ |
| 14 | chung2015vrnn | Chung, J. et al. "A Recurrent Latent Variable Model for Sequential Data." NeurIPS 2015. | 背景 | 系列潜在変数モデルの基礎 | △ |
| 15 | krishnan2017ssm | Krishnan, R. G., Shalit, U., Sontag, D. "Structured Inference Networks for Nonlinear State Space Models." AAAI 2017. | 背景 | 深層状態空間モデル。構造を入れた推論 | △ |
| 16 | rasmussen2006gp | Rasmussen, C. E., Williams, C. K. I. *Gaussian Processes for Machine Learning*. MIT Press, 2006. | 補強 | GP prior の定式化の典拠 | △ |

## B. 自己教師あり／対照学習による時系列表現

| # | key | 文献 | 層 | 本研究との関係 | 確認 |
|---|---|---|---|---|---|
| 17 | oord2018cpc | van den Oord, A., Li, Y., Vinyals, O. "Representation Learning with Contrastive Predictive Coding." arXiv:1807.03748, 2018. | 補強 | 対照学習による時系列表現の原型 | △ |
| 18 | franceschi2019unsupervised | Franceschi, J.-Y., Dieuleveut, A., Jaggi, M. "Unsupervised Scalable Representation Learning for Multivariate Time Series." NeurIPS 2019. | 補強 | triplet loss による系列表現 | △ |
| 19 | tonekaboni2021tnc | Tonekaboni, S., Eytan, D., Goldenberg, A. "Unsupervised Representation Learning for Time Series with Temporal Neighborhood Coding." ICLR 2021. | 必須 | 元論文の著者による先行研究。近傍の定義で局所表現を学ぶ | △ |
| 20 | eldele2021tstcc | Eldele, E. et al. "Time-Series Representation Learning via Temporal and Contextual Contrasting." IJCAI 2021. | 補強 | 時間／文脈の二重対照 | △ |
| 21 | yue2022ts2vec | Yue, Z. et al. "TS2Vec: Towards Universal Representation of Time Series." AAAI 2022. | 必須 | 多粒度（timestamp/instance）表現の代表。粒度設計の議論に使う | △ |
| 22 | woo2022cost | Woo, G., Liu, C., Sahoo, D., Kumar, A., Hoi, S. "CoST: Contrastive Learning of Disentangled Seasonal-Trend Representations for Time Series Forecasting." ICLR 2022. | 必須 | trend/season を**表現として**分ける。本研究の「粒度が粗い」批判の対象 | △ |
| 23 | zhang2022tfc | Zhang, X., Zhao, Z., Tsiligkaridis, T., Zitnik, M. "Self-Supervised Contrastive Pre-Training for Time Series via Time-Frequency Consistency." NeurIPS 2022. | 補強 | 時間／周波数の多 view 整合 | ✓ |
| 24 | zerveas2021tst | Zerveas, G., Jayaraman, S., Patel, D., Bhamidipaty, A., Eickhoff, C. "A Transformer-based Framework for Multivariate Time Series Representation Learning." KDD 2021. | 補強 | マスク再構成による事前学習。2-Exp-49 の日マスク学習に接続 | ✓ |
| 25 | nie2023patchtst | Nie, Y., Nguyen, N. H., Sinthong, P., Kalagnanam, J. "A Time Series is Worth 64 Words: Long-term Forecasting with Transformers." ICLR 2023. | 補強 | patch 単位の表現。窓分割の設計根拠 | △ |
| 26 | devlin2019bert | Devlin, J., Chang, M.-W., Lee, K., Toutanova, K. "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding." NAACL 2019. | 背景 | マスク予測事前学習の起点 | △ |
| 27 | he2022mae | He, K. et al. "Masked Autoencoders Are Scalable Vision Learners." CVPR 2022. | 背景 | 高いマスク率での表現学習。2-Exp-49 の keep ratio 設計の参照 | △ |
| 28 | alain2017probes | Alain, G., Bengio, Y. "Understanding Intermediate Layers Using Linear Classifier Probes." ICLR 2017 Workshop / arXiv:1610.01644. | 補強 | linear probe による表現評価。本研究の probe 実験の方法論的典拠 | △ |

## C. global-local 予測と潜在因子予測

| # | key | 文献 | 層 | 本研究との関係 | 確認 |
|---|---|---|---|---|---|
| 29 | salinas2020deepar | Salinas, D., Flunkert, V., Gasthaus, J., Januschowski, T. "DeepAR: Probabilistic Forecasting with Autoregressive Recurrent Networks." International Journal of Forecasting 36(3):1181–1191, 2020. | 必須 | 多系列を 1 モデルで学ぶ global 手法の代表 | △ |
| 30 | wang2019deepfactors | Wang, Y., Smola, A., Maddix, D. C., Gasthaus, J., Foster, D., Januschowski, T. "Deep Factors for Forecasting." ICML 2019. | 必須 | global 深層成分 + local 確率成分という明示的な分割 | ✓ |
| 31 | sen2019deepglo | Sen, R., Yu, H.-F., Dhillon, I. S. "Think Globally, Act Locally: A Deep Neural Network Approach to High-Dimensional Time Series Forecasting." NeurIPS 2019. | 必須 | global 行列分解 + local 時系列補正 | △ |
| 32 | nguyen2021tlae | Nguyen, N., Quanz, B. "Temporal Latent Auto-Encoder: A Method for Probabilistic Multivariate Time Series Forecasting." AAAI 2021, 35:9117–9125. | 補強 | 非線形因子分解を予測器と同時学習 | ✓ |
| 33 | oreshkin2020nbeats | Oreshkin, B. N., Carpov, D., Chapados, N., Bengio, Y. "N-BEATS: Neural Basis Expansion Analysis for Interpretable Time Series Forecasting." ICLR 2020. | 必須 | 解釈可能基底による trend/season 出力分解。**出力側で分解する**先行例 | △ |
| 34 | smyl2020esrnn | Smyl, S. "A Hybrid Method of Exponential Smoothing and Recurrent Neural Networks for Time Series Forecasting." International Journal of Forecasting 36(1):75–85, 2020. | 必須 | 統計的基準値 + NN 補正のハイブリッド。本研究の $b+\hat r$ の直接の先例 | △ |
| 35 | monteromanso2021locality | Montero-Manso, P., Hyndman, R. J. "Principles and Algorithms for Forecasting Groups of Time Series: Locality and Globality." International Journal of Forecasting 37(4):1632–1653, 2021. | 必須 | global/local の等価性と複雑度の理論整理。系列成分 $g_i$ の正当化 | ✓ |
| 36 | januschowski2020criteria | Januschowski, T. et al. "Criteria for Classifying Forecasting Methods." International Journal of Forecasting 36(1):167–177, 2020. | 補強 | global/local、構造的／非構造的の分類軸 | △ |
| 37 | benidis2022survey | Benidis, K. et al. "Deep Learning for Time Series Forecasting: Tutorial and Literature Survey." ACM Computing Surveys 55(6), 2022. | 背景 | 総説。序論の俯瞰 | △ |

## D. 分解型予測と季節調整（歴史軸）

| # | key | 文献 | 層 | 本研究との関係 | 確認 |
|---|---|---|---|---|---|
| 38 | holt2004forecasting | Holt, C. C. "Forecasting Seasonals and Trends by Exponentially Weighted Moving Averages." International Journal of Forecasting 20(1):5–10, 2004（原典 1957 ONR memorandum）. | 背景 | 成分分解の起点。$b$ の系譜 | △ |
| 39 | winters1960forecasting | Winters, P. R. "Forecasting Sales by Exponentially Weighted Moving Averages." Management Science 6(3):324–342, 1960. | 背景 | 季節成分つき指数平滑 | △ |
| 40 | box1970time | Box, G. E. P., Jenkins, G. M. *Time Series Analysis: Forecasting and Control*. Holden-Day, 1970. | 背景 | ARIMA。系列ごとの local モデルの標準 | △ |
| 41 | shiskin1967x11 | Shiskin, J., Young, A. H., Musgrave, J. C. "The X-11 Variant of the Census Method II Seasonal Adjustment Program." US Bureau of the Census Technical Paper No. 15, 1967. | 背景 | 季節調整の実務標準。「成分に分けて読む」制度化の例 | △ |
| 42 | cleveland1990stl | Cleveland, R. B., Cleveland, W. S., McRae, J. E., Terpenning, I. "STL: A Seasonal-Trend Decomposition Procedure Based on Loess." Journal of Official Statistics 6(1):3–73, 1990. | 必須 | 非学習の分解の代表。本研究の経験的 ANOVA baseline（2-Exp-33）の対応物 | △ |
| 43 | harvey1989structural | Harvey, A. C. *Forecasting, Structural Time Series Models and the Kalman Filter*. Cambridge University Press, 1989. | 背景 | 成分をモデル構造として明示する系譜 | △ |
| 44 | delivera2011tbats | De Livera, A. M., Hyndman, R. J., Snyder, R. D. "Forecasting Time Series with Complex Seasonal Patterns Using Exponential Smoothing." JASA 106(496):1513–1527, 2011. | 必須 | **複数季節性**（日内 × 週）の扱い。日×時間帯を分ける動機の統計側の典拠 | △ |
| 45 | taylor2018prophet | Taylor, S. J., Letham, B. "Forecasting at Scale." The American Statistician 72(1):37–45, 2018. | 補強 | 加法的な trend + seasonality + holiday 分解の実務形 | △ |
| 46 | zhou2021informer | Zhou, H. et al. "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting." AAAI 2021. | 背景 | Transformer 予測の起点 | △ |
| 47 | wu2021autoformer | Wu, H., Xu, J., Wang, J., Long, M. "Autoformer: Decomposition Transformers with Auto-Correlation for Long-Term Series Forecasting." NeurIPS 2021. | 必須 | series decomposition block。分解をアーキテクチャに入れる代表 | △ |
| 48 | zhou2022fedformer | Zhou, T. et al. "FEDformer: Frequency Enhanced Decomposed Transformer for Long-term Series Forecasting." ICML 2022. | 補強 | 周波数領域での分解 | △ |
| 49 | zeng2023dlinear | Zeng, A., Chen, M., Zhang, L., Xu, Q. "Are Transformers Effective for Time Series Forecasting?" AAAI 2023. | 必須 | 単純な trend/seasonal 線形分解が強い。本研究の「基準値は強い」立場の支持 | △ |
| 50 | challu2023nhits | Challu, C. et al. "NHITS: Neural Hierarchical Interpolation for Time Series Forecasting." AAAI 2023. | 補強 | 多重解像度の階層的分解 | △ |
| 51 | wang2024timemixer | Wang, S., Wu, H., Shi, X., Hu, T., Luo, H., Ma, L., Zhang, J. Y., Zhou, J. "TimeMixer: Decomposable Multiscale Mixing for Time Series Forecasting." ICLR 2024. | 必須 | multi-scale 分解の最新形。粒度が scale 止まりであることの例示 | ✓ |

## E. ANOVA・加法モデル・交互作用の純化（本研究の方法論の核）

| # | key | 文献 | 層 | 本研究との関係 | 確認 |
|---|---|---|---|---|---|
| 52 | fisher1935design | Fisher, R. A. *The Design of Experiments*. Oliver and Boyd, 1935. | 背景 | 主効果と交互作用という語彙の起点 | △ |
| 53 | scheffe1959anova | Scheffé, H. *The Analysis of Variance*. Wiley, 1959. | 必須 | 二元配置の side condition（平均ゼロ制約）による一意化。本研究の centering の典拠 | △ |
| 54 | searle1992variance | Searle, S. R., Casella, G., McCulloch, C. E. *Variance Components*. Wiley, 1992. | 補強 | 分散成分の推定。成分の分散寄与（2-Exp-44）の読み方 | △ |
| 55 | hastie1986gam | Hastie, T., Tibshirani, R. "Generalized Additive Models." Statistical Science 1(3):297–310, 1986. | 必須 | 加法モデルの起点 | △ |
| 56 | stone1985additive | Stone, C. J. "Additive Regression and Other Nonparametric Models." The Annals of Statistics 13(2):689–705, 1985. | 背景 | 加法構造の次元削減効果 | △ |
| 57 | sobol2001indices | Sobol', I. M. "Global Sensitivity Indices for Nonlinear Mathematical Models and their Monte Carlo Estimates." Mathematics and Computers in Simulation 55(1–3):271–280, 2001. | 補強 | 分散分解による感度指標。成分寄与率の定義に使える | △ |
| 58 | hooker2007fanova | Hooker, G. "Generalized Functional ANOVA Diagnostics for High-Dimensional Functions of Dependent Variables." Journal of Computational and Graphical Statistics 16(3):709–732, 2007. | 必須 | **入力が従属なときの階層的直交分解**。日と時間帯が独立でない実データでの centering の正当化 | ✓ |
| 59 | lou2013ga2m | Lou, Y., Caruana, R., Gehrke, J., Hooker, G. "Accurate Intelligible Models with Pairwise Interactions." KDD 2013. | 必須 | GA²M。主効果 + 対交互作用という本研究と同じ構造 | ✓ |
| 60 | lengerich2020purifying | Lengerich, B., Tan, S., Chang, C.-H., Hooker, G., Caruana, R. "Purifying Interaction Effects with the Functional ANOVA: An Efficient Algorithm for Recovering Identifiable Additive Models." AISTATS 2020, PMLR 108:2402–2412. | 必須 | **交互作用から主効果を抜いて純化する**。本研究の centering と同じ発想の最近傍文献 | ✓ |
| 61 | agarwal2021nam | Agarwal, R., Melnick, L., Frosst, N., Zhang, X., Lengerich, B., Caruana, R., Hinton, G. E. "Neural Additive Models: Interpretable Machine Learning with Neural Nets." NeurIPS 2021 (NeurIPS 34). | 必須 | NN で加法構造を保つ。本研究の 4 成分ヘッドの先例 | ✓ |
| 62 | gelman2007multilevel | Gelman, A., Hill, J. *Data Analysis Using Regression and Multilevel/Hierarchical Models*. Cambridge University Press, 2007. | 補強 | 系列固有効果を変量効果として読む見方 | △ |

## F. 解釈性一般

| # | key | 文献 | 層 | 本研究との関係 | 確認 |
|---|---|---|---|---|---|
| 63 | ribeiro2016lime | Ribeiro, M. T., Singh, S., Guestrin, C. "Why Should I Trust You?: Explaining the Predictions of Any Classifier." KDD 2016. | 補強 | 事後説明の代表。本研究の「構造で保証する」立場との対比 | △ |
| 64 | lundberg2017shap | Lundberg, S. M., Lee, S.-I. "A Unified Approach to Interpreting Model Predictions." NeurIPS 2017. | 補強 | 寄与の加法分解。成分寄与の読み方の対比対象 | △ |
| 65 | rudin2019stop | Rudin, C. "Stop Explaining Black Box Machine Learning Models for High Stakes Decisions and Use Interpretable Models Instead." Nature Machine Intelligence 1:206–215, 2019. | 必須 | 事後説明より本質的に解釈可能なモデルを使うべきという主張。本研究の設計方針の正当化 | △ |
| 66 | molnar2022iml | Molnar, C. *Interpretable Machine Learning*. 2nd ed., 2022. | 背景 | 教科書。用語の整理 | △ |

## G. 局所パターンと高残差・異常検知

| # | key | 文献 | 層 | 本研究との関係 | 確認 |
|---|---|---|---|---|---|
| 67 | ye2009shapelets | Ye, L., Keogh, E. "Time Series Shapelets: A New Primitive for Data Mining." KDD 2009. | 補強 | 局所部分列による説明の起点 | △ |
| 68 | grabocka2014learning | Grabocka, J., Schilling, N., Wistuba, M., Schmidt-Thieme, L. "Learning Time-Series Shapelets." KDD 2014. | 補強 | shapelet の学習化 | △ |
| 69 | lee2026inshape | Lee, S., Lee, S., Lee, C. "INSHAPE: Instance-Level Shapelets for Interpretable Time-Series Classification." IJCAI 2026, pp. 4456–4464. | 補強 | 系列ごとの局所説明。本研究の系列別成分の解釈と同型の問題意識 | ✓ |
| 70 | dempster2020rocket | Dempster, A., Petitjean, F., Webb, G. I. "ROCKET: Exceptionally Fast and Accurate Time Series Classification Using Random Convolutional Kernels." Data Mining and Knowledge Discovery 34:1454–1495, 2020. | 背景 | 多スケール局所特徴の有効性 | △ |
| 71 | fawaz2020inceptiontime | Ismail Fawaz, H. et al. "InceptionTime: Finding AlexNet for Time Series Classification." Data Mining and Knowledge Discovery 34:1936–1962, 2020. | 背景 | 多スケール畳み込み | △ |
| 72 | su2019omnianomaly | Su, Y. et al. "Robust Anomaly Detection for Multivariate Time Series through Stochastic Recurrent Neural Network." KDD 2019. | 補強 | 確率的再構成誤差による異常検知 | △ |
| 73 | xu2022anomalytransformer | Xu, J., Wu, H., Wang, J., Long, M. "Anomaly Transformer: Time Series Anomaly Detection with Association Discrepancy." ICLR 2022. | 補強 | 高残差ケースの検出。本研究の high residual top10 の文脈 | △ |
| 74 | tuli2022tranad | Tuli, S., Casale, G., Jennings, N. R. "TranAD: Deep Transformer Networks for Anomaly Detection in Multivariate Time Series Data." VLDB 2022 (PVLDB 15(6):1201–1214). | 補強 | 同上 | △ |
| 75 | hua2022genad | Hua, X. et al. "GenAD: General Representations of Multivariate Time Series for Anomaly Detection." arXiv:2202.04250, 2022. | 補強 | 表現学習と異常検知の接続（**arXiv のみ。査読誌版は未確認**） | ✓ |
| 76 | blazquez2021review | Blázquez-García, A., Conde, A., Mori, U., Lozano, J. A. "A Review on Outlier/Anomaly Detection in Time Series Data." ACM Computing Surveys 54(3), 2021. | 背景 | 総説。高残差の位置づけ | △ |

## H. 小売需要予測・欠品／打ち切り需要・ベンチマーク

| # | key | 文献 | 層 | 本研究との関係 | 確認 |
|---|---|---|---|---|---|
| 77 | wang2025freshretailnet | Wang, Y. et al. "FreshRetailNet-50K: A Stockout-Annotated Censored Demand Dataset for Latent Demand Recovery and Forecasting in Fresh Retail." arXiv:2505.16319, 2025. | 必須 | 本研究の実験基盤。898 店舗・18 都市・50,000 系列の時間帯別売上と欠品注釈 | ✓ |
| 78 | croston1972intermittent | Croston, J. D. "Forecasting and Stock Control for Intermittent Demands." Journal of the Operational Research Society 23(3):289–303, 1972. | 補強 | 間欠需要。小売需要が平均当てはめ問題でないことの古典 | ✓ |
| 79 | syntetos2005accuracy | Syntetos, A. A., Boylan, J. E. "The Accuracy of Intermittent Demand Estimates." International Journal of Forecasting 21(2):303–314, 2005. | 補強 | Croston 法の bias 補正。bias 評価軸の典拠 | △ |
| 80 | anupindi1998substitution | Anupindi, R., Dada, M., Gupta, S. "Estimation of Consumer Demand with Stock-Out Based Substitution: An Application to Vending Machine Products." Marketing Science 17(4):406–423, 1998. | 必須 | 欠品下では観測売上から推定した需要が bias を持つ。マスク処理の正当化 | ✓ |
| 81 | vulcano2012primarydemand | Vulcano, G., van Ryzin, G., Ratliff, R. "Estimating Primary Demand for Substitutable Products from Sales Transaction Data." Operations Research 60(2):313–334, 2012. | 必須 | 打ち切り需要の EM 推定。欠品を無視すると需要が下方 bias する | ✓ |
| 82 | boldi2019intraday | Boldi, M.-O., Chavez-Demoulin, V., Gallay, O. "Intraday Retail Sales Forecast: An Efficient Algorithm for Quantile Additive Modeling." arXiv:1912.07373, 2019. | 必須 | **時間帯粒度の小売売上に加法モデルを当てた最近傍の応用研究**。比較・差分の記述に必須 | ✓ |
| 83 | makridakis2022m5acc | Makridakis, S., Spiliotis, E., Assimakopoulos, V. "M5 Accuracy Competition: Results, Findings, and Conclusions." International Journal of Forecasting 38(4):1346–1364, 2022. | 必須 | 階層つき小売需要の大規模比較。単純手法の強さ | ✓ |
| 84 | makridakis2022m5bg | Makridakis, S., Spiliotis, E., Assimakopoulos, V. "The M5 Competition: Background, Organization, and Implementation." International Journal of Forecasting 38(4):1325–1336, 2022. | 補強 | M5 の設計。評価設計の参照 | ✓ |
| 85 | makridakis2020m4 | Makridakis, S., Spiliotis, E., Assimakopoulos, V. "The M4 Competition: 100,000 Time Series and 61 Forecasting Methods." International Journal of Forecasting 36(1):54–74, 2020. | 補強 | ハイブリッド（統計 + ML）の優位。$b+\hat r$ の正当化 | △ |
| 86 | fildes2022retail | Fildes, R., Ma, S., Kolassa, S. "Retail Forecasting: Research and Practice." International Journal of Forecasting 38(4):1283–1318, 2022. | 必須 | 小売予測の総説。基準値の強さ、粒度、運用要件 | △ |
| 87 | hyndman2011hierarchical | Hyndman, R. J., Ahmed, R. A., Athanasopoulos, G., Shang, H. L. "Optimal Combination Forecasts for Hierarchical Time Series." Computational Statistics and Data Analysis 55(9):2579–2589, 2011. | 補強 | 階層整合。系列／日／時間帯という階層の扱いの対比 | △ |
| 88 | wickramasuriya2019mint | Wickramasuriya, S. L., Athanasopoulos, G., Hyndman, R. J. "Optimal Forecast Reconciliation for Hierarchical and Grouped Time Series Through Trace Minimization." JASA 114(526):804–819, 2019. | 補強 | MinT 整合。制約つき出力という発想の近縁 | △ |

## I. 評価・統計的検証・較正

| # | key | 文献 | 層 | 本研究との関係 | 確認 |
|---|---|---|---|---|---|
| 89 | hyndman2006measures | Hyndman, R. J., Koehler, A. B. "Another Look at Measures of Forecast Accuracy." International Journal of Forecasting 22(4):679–688, 2006. | 必須 | WAPE/MAE 系指標の選択根拠 | △ |
| 90 | efron1993bootstrap | Efron, B., Tibshirani, R. J. *An Introduction to the Bootstrap*. Chapman & Hall, 1993. | 必須 | paired bootstrap（2-Exp-20）の典拠 | △ |
| 91 | demsar2006statistical | Demšar, J. "Statistical Comparisons of Classifiers over Multiple Data Sets." JMLR 7:1–30, 2006. | 補強 | 複数条件での比較手続き | △ |
| 92 | gneiting2007scoring | Gneiting, T., Raftery, A. E. "Strictly Proper Scoring Rules, Prediction, and Estimation." JASA 102(477):359–378, 2007. | 補強 | 評価指標の妥当性 | △ |
| 93 | koenker1978quantile | Koenker, R., Bassett, G. "Regression Quantiles." Econometrica 46(1):33–50, 1978. | 背景 | 分位点回帰。Boldi et al. の前提、bias/高残差の二目的評価の参照 | △ |
| 94 | guo2017calibration | Guo, C., Pleiss, G., Sun, Y., Weinberger, K. Q. "On Calibration of Modern Neural Networks." ICML 2017. | 補強 | 較正。2-Exp-18/19 の calibration と shrinkage の文脈 | △ |
| 95 | maaten2008tsne | van der Maaten, L., Hinton, G. "Visualizing Data Using t-SNE." JMLR 9:2579–2605, 2008. | 補強 | 2-Exp-35 の成分 t-SNE | △ |
| 96 | friedman2001gbm | Friedman, J. H. "Greedy Function Approximation: A Gradient Boosting Machine." The Annals of Statistics 29(5):1189–1232, 2001. | 補強 | 残差を順に当てる発想の典拠 | △ |
| 97 | he2016resnet | He, K., Zhang, X., Ren, S., Sun, J. "Deep Residual Learning for Image Recognition." CVPR 2016. | 背景 | 残差学習という語の一般的背景 | △ |

## 確認状況のまとめ

| 状態 | 件数 | 対応 |
|---|---|---|
| ✓ 書誌確認済み | 22 | そのまま引用可 |
| △ 未照合 | 75 | 定番文献。投稿前に DOI / 公式ページで巻号・頁を照合する |

未照合のものは、いずれも分野の標準文献で著者・会議・年の取り違えは起きにくいが、**巻号と頁は必ず一次情報で確認する**。特に書籍（Fisher, Scheffé, Searle, Harvey, Box & Jenkins, Rasmussen & Williams）は版によって頁が変わる。

## 本リストに意図的に入れていないもの

- LSTM / GRU / Transformer の原論文は、本研究の貢献が構造の制約側にあるため、必要になった箇所（encoder の説明）でのみ引く。
- 需要の価格弾力性・在庫最適化の文献は、本研究が発注量の意思決定を扱わないため外した。考察で運用価値を述べるときだけ Fildes et al. (2022) で代表させる。
- 因果推論（do 演算、反実仮想）の一般文献は、本研究の counterfactual が「潜在差し替え」という限定的な意味なので、誤解を避けて外した。2-Exp-50 の記述では「latent swap」と呼び、因果主張はしない。
