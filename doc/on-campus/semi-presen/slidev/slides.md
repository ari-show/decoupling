---
theme: default
title: 需要予測のための共通要因と系列固有要因の分離表現学習に関する研究
info: 修士2年 中間発表ドラフト（Slidev版・Keynote清書前提の簡易デザイン）
class: text-center
highlighter: shiki
lineNumbers: false
drawings:
  enabled: false
transition: none
mdc: true
---

# 需要予測のための<br>共通要因と系列固有要因の<br>分離表現学習に関する研究

<div class="mt-10 text-lg">

修士2年 中間発表

東京都市大学大学院 ○○研究室（要修正）

有馬 翔太

2026-XX-XX（要修正）

</div>

<!--
タイトルは4月頭の主題提出で固定。
口頭で添える一文:「主題提出時は潜在表現の分離を軸としていましたが、実験の結果、
表現を分けるだけでは補正の解釈が保証されないと分かり、分離を出力レベルまで拡張しました。
今日はその過程を報告します」— 路線変更ではなく、タイトルの問いを遂行した結果として語る。0:15
-->

---

# 背景

<div class="mt-5 text-xl">

スーパーやコンビニなどの小売現場では、<br>
店舗×商品ごとの需要を予測し、発注量の判断材料にする。

</div>

<div class="mt-5 text-center text-xl">

例：**A店×牛乳**の過去1か月間を観測し、<br>
平均売上が10本だったとする。

</div>

<div class="mt-7 grid grid-cols-2 gap-6 text-center">
<div class="p-6 border rounded bg-gray-50 dark:bg-gray-800">

**普段の売れ方**

<div class="mt-3 text-3xl">基準値 10本</div>

</div>
<div class="p-6 border rounded">

**金曜18時の売上**

<div class="mt-3 text-3xl">実績 20本</div>

</div>
</div>

<div class="mt-6 p-4 border rounded bg-yellow-50 dark:bg-yellow-900 text-center text-2xl">

基準値との差（残差） $=20-10=\mathbf{+10}$ 本

</div>

<div class="mt-5 p-4 border rounded bg-blue-50 dark:bg-blue-900 text-center text-lg">

この+10本は、普段の売れ方だけでは説明できない<br>
**基準値からの外れ方を示す情報**

</div>

<!--
小売需要予測の説明から、A店×牛乳の数値例へ直行する。
過去1か月平均10本を基準値、金曜18時の20本を実績として、
残差+10本が基準値の外れ方を示す情報だと1枚で説明する。0:35
-->

---

# 解釈

<div class="mt-3 text-center text-xl">

しかし、+10本という合計だけでは、<br>
基準値が**どの範囲で外れたか**までは分からない。

</div>

| 観測されたズレ | 担当する成分 | 捉えたい変動 |
| --- | --- | --- |
| どの日・時間帯でも +1本 | 系列 $g_i$ | A店×牛乳全体のズレ |
| ある1日（金曜日）は全時間帯で +2本 | 日 $a_{i,d}$ | その日全体のズレ |
| 毎日18時は +3本 | 時間帯 $c_{i,h}$ | 繰り返す時間帯のズレ |
| その日の18時だけ、さらに +4本 | 日×時間帯 $u_{i,d,h}$ | 特定の日×時間帯のズレ |

<div class="mt-3 p-3 border rounded bg-blue-50 dark:bg-blue-900 text-center">

金曜18時の+10本は、$1+2+3+4$ 本という<br>
**異なる範囲に現れたズレの重なり**として解釈できる

</div>

<div class="mt-3 text-sm text-gray-500 text-center">

雨・イベントはズレの**原因候補**。<br>
本研究が整理するのは原因名ではなく、ズレが現れる**単位**である。

</div>

<!--
雨・イベントのような外生要因を直接4成分の例にすると、提案の分解軸とずれるため使わない。
基準値からの+10本を、系列・日・時間帯・日×時間帯の重なりとして具体化する。
残差の解像度を上げるという抽象語ではなく、基準がどの範囲で外れたかを読む例として示す。
販促・休日・天候は入力特徴量には含むが、因果的な原因同定は本研究の主張ではない。0:40
-->

---

# 目的

<div class="mt-6 text-center text-2xl">

基準値からのズレを、<br>
**系列・日・時間帯・日×時間帯**に分けて学習する

</div>

<div class="mt-7 p-5 border rounded bg-gray-50 dark:bg-gray-800 text-center text-xl">

基準値 $b$
＋ 系列 $\hat g$
＋ 日 $\hat a$
＋ 時間帯 $\hat c$
＋ 日×時間帯 $\hat u$
＝ 最終予測 $\hat y$

</div>

<div class="mt-7 grid grid-cols-2 gap-6">
<div class="p-5 border rounded text-center">

**補正**

4成分の和で、基準値を修正する

</div>
<div class="p-5 border rounded text-center bg-blue-50 dark:bg-blue-900">

**説明**

どの単位で外れたかを数値で示す

</div>
</div>

<div class="mt-5 text-center text-lg">

目標：基準値の補正と、予測誤差の解釈を同時に行う

</div>

<!--
牛乳の例で必要性を示した後に、研究目的と提案する整理枠組みを明示する。
残差を4成分として学習し、補正と説明を同時に行うことを短くまとめる。0:35
-->

---

# 分離表現

<div class="mt-4 text-xl text-center">

需要予測モデルは、予測値が正しければ、<br>
内部で複数の変動要因が混ざっていても学習できる。

</div>

<div class="mt-6 grid grid-cols-2 gap-6">
<div class="p-5 border rounded">

**通常の予測**

<div class="mt-3 text-center text-lg">

時系列 → モデル → 予測値

</div>

- 目的は正解に近い値を出すこと
- 予測誤差だけでは、内部表現の役割は決まらない

</div>
<div class="p-5 border rounded bg-blue-50 dark:bg-blue-900">

**本研究に必要な表現**

<div class="mt-3 text-center text-lg">

時系列 → 要因別の表現 → 予測・説明

</div>

- 異なる変動を別々に持たせる
- 必要な表現を個別に利用できる

</div>
</div>

<div class="mt-5 p-3 border rounded text-center">

予測値だけでなく、変動を分けて持つ**分離表現**が必要

</div>

<!--
「他の予測手法でもよいのでは」という疑問に先回りする。
予測だけなら他のモデルでもよいが、本研究では予測補正の内訳を説明したいので、
内部表現を役割別に分ける必要があると説明する。0:35
-->

---

# VAE

<div class="mt-4 text-xl text-center">

しかし、実データには「どの変動がどの要因か」という<br>
**要因ごとの正解ラベルがない**

</div>

<div class="mt-5 p-4 border rounded bg-gray-50 dark:bg-gray-800 text-center text-lg">

時系列 $X$ → Encoder $q(z\mid X)$ → 潜在変数 $z$ → Decoder → $X$ を再構成

</div>

<div class="mt-5 grid grid-cols-3 gap-4">
<div class="p-4 border rounded">

**ラベルなしで学ぶ**

入力を再構成する過程で、<br>
観測の背後にある特徴を圧縮する

</div>
<div class="p-4 border rounded">

**構造を与える**

潜在変数ごとに異なる事前分布や<br>
時間構造を設定できる

</div>
<div class="p-4 border rounded">

**分離を促す**

正則化を加え、異なる潜在変数への<br>
情報の混入を抑えられる

</div>
</div>

<div class="mt-5 p-3 border rounded bg-blue-50 dark:bg-blue-900 text-center">

先行研究では、VAEを単なる「予測器」としてではなく、<br>
**観測から潜在要因を学び分ける枠組み**として利用する

</div>

<!--
VAEを使えば予測精度が必ず高い、という説明にはしない。
要因ラベルがない状況で、再構成・事前分布・正則化を通じて
潜在要因を役割別に学ばせられることが、分離表現研究でVAEを使う理由。0:40
-->

---

# 先行研究

<div class="grid grid-cols-2 gap-6 mt-4">
<div class="p-4 border rounded">

**Tonekaboniら（2022）[1]**

- $z_{\text{global}}$：1系列の中で<br>時間に依存しない特徴
- $z_{\text{local}}(t)$：時間とともに<br>変化する状態
- local にGP事前分布を置き、<br>反実仮想正則化で情報混入を抑える

</div>
<div class="p-4 border rounded">

**FHVAE [2] ／ DSAE [3]**

- 音声・映像を対象とするVAE
- 話者や物体などの静的な特徴と、<br>発話内容や動きなどの動的な特徴を分離
- 異なる時間尺度に対応する<br>潜在変数・事前分布を設計

</div>
</div>

<div class="mt-5 p-4 border rounded bg-blue-50 dark:bg-blue-900 text-center">

要因ラベルを直接与えなくても、<br>
**時間不変／時間変動の情報を別の潜在変数へ持たせられる**

</div>

<div class="mt-3 text-sm text-gray-500">

※ [1] の global は「系列間で共通」ではなく、「各系列の中で時間に依存しない」という意味。

</div>

<!--
VAEの役割を説明した後で、代表研究が実際に何を分けたかを示す。
Tonekaboniらのglobalを「系列間共通」と誤解させない。
FHVAEとDSAEは、静的／動的な潜在表現を分ける系譜として位置づける。0:40
-->

---

# 課題

<div class="mt-3 text-lg text-center">

潜在表現を global / local に分けても、<br>
**予測を「何が、何本分」補正したのかまでは分からない**

</div>

<div class="mt-5">

### 1. 補正量の内訳が見えない

予測が **+10本** 補正されても、global と local が<br>
それぞれ何本分を担ったのかは直接示されない

<div class="my-4 border-t"></div>

### 2. local の時間的な粒度が粗い

local は、時間とともに変わる情報をまとめた表現<br>
**日・時間帯・日×時間帯**のどこで外れたのかを区別できない

</div>

<div class="mt-5 p-3 border rounded bg-yellow-50 dark:bg-yellow-900 text-center">

global / local の2分割だけでは、<br>
現場で知りたい**「いつ、どの単位で外れたか」**に答えられない

</div>

<!--
潜在空間の内部で情報が混ざるという抽象的な説明ではなく、
予測補正の内訳が見えないことと、localの時間粒度が粗いことを具体的に示す。
次の表現スライドで、出力を4成分に分ける必要性へつなぐ。0:40
-->

---

# 表現

**入力（28日×24時間帯）**：残差履歴・欠品情報・販促／休日／天候・曜日／時刻

| 潜在変数 | Encoder が要約する範囲 | 学習させたい情報 | Decoder 出力 |
| --- | --- | --- | --- |
| $z_{\mathrm{series}}$ | 全日×全時間帯 | 系列全体に続くズレの水準・ばらつき | $\tilde g_i$ |
| $z_{\mathrm{day},d}$ | 各日の24時間＋日の並び | その日全体の変動 | $\tilde a_{i,d}$ |
| $z_{\mathrm{hour},h}$ | 各時間帯を日方向に集約 | 毎日繰り返す時間帯パターン | $\tilde c_{i,h}$ |
| $z_{\mathrm{int},d,h}$ | 日表現と時間帯表現の組 | 特定の日×時間帯にだけ残る変動 | $\tilde u_{i,d,h}$ |

<div class="mt-2 text-sm text-gray-500">

※ 実装名は $z_{\mathrm{global}}$。系列全体の補正 $g_i$ との対応を明確にするため、ここでは $z_{\mathrm{series}}$ と表記する。

</div>

<div class="mt-3 p-3 border rounded bg-yellow-50 dark:bg-yellow-900">

潜在変数に「金曜日」「雨」などの正解を直接入れるわけではない。<br>
Encoder が作る圧縮表現であり、**4成分の和が実際の残差に近づくように値と重みが学習される**。

</div>

<!--
「各潜在変数に何が入るか」への回答。
入力は全Encoderで同じだが、平均・分散を取る軸と出力形状が異なる。
z_series は全セル、z_day は時間帯方向、z_hour は日方向を要約し、
z_int は z_day と z_hour の組から作る。
実装上の z_global も「1系列の時間軸全体」を要約する。系列間で同じ値を持つ、という意味ではない。
潜在表現自体の完全な意味同定は主張せず、出力成分の担当範囲を制約する。0:40
-->

---

# 制約

```mermaid {scale: 0.72}
flowchart LR
    A["同じ入力<br>残差・欠品・外生特徴"] --> B["軸別 Encoder<br>z_series / z_day<br>z_hour / z_int"]
    B --> C["成分別 Decoder<br>g̃ / ã / c̃ / ũ"]
    C --> D["中心化<br>担当範囲を固定"]
    D --> E["成分の和<br>r̂ = ĝ+â+ĉ+û"]
    E --> F["基準値を補正<br>ŷ = b+r̂"]
```

<div class="grid grid-cols-2 gap-5 mt-2">
<div>

**学習時に与える正解**

- 各セルの残差 $r_{i,d,h}$
- 4成分それぞれの正解は与えない
- 主損失は $\hat r$ と $r$ の MAE
- 潜在間の共分散ペナルティで情報の混入を抑え、<br>Encoder と4つの Decoder を同時更新

</div>
<div>

**なぜ出力にも制約が必要か**

- 潜在表現を分けても、出力の分け方は自由
- $g$ に定数を足し、$a$ から引いても和は同じ
- 予測誤差だけでは、各成分の担当が決まらない

</div>
</div>

<div class="mt-3 p-3 border rounded bg-blue-50 dark:bg-blue-900 text-center">

軸別の集約で「何を見せるか」を分け、出力の中心化で「何を担当するか」を固定する

</div>

<!--
学習の教師信号と、学習されるパラメータを明示するページ。
4成分の真値を与える supervised decomposition ではない。
主損失は残差MAEで、潜在間の共分散ペナルティも加える。
軸別Encoderだけでは意味は保証されず、成分別Decoderと中心化制約まで含めて提案。0:40
-->

---

# 中心化

ある系列が、どの時間帯でも普段より **+2本** 売れている場合

| 予測補正の内訳 | 制約なし | 中心化あり |
|---|---:|---:|
| 時間帯成分 $\hat c_{i,h}$ | $+2,\ +2,\ \ldots,\ +2$ | $0,\ 0,\ \ldots,\ 0$ |
| 時間帯成分の平均 | $+2$ | **$0$** |
| 系列成分 $\hat g_i$ | $0$ | **$+2$** |
| 各時間帯での合計 | **$+2$** | **$+2$** |

<div class="mt-4 p-3 border rounded bg-blue-50 dark:bg-blue-900 text-center">

予測値は同じでも、中心化により<br>
**全時間帯に共通するズレは系列成分、時間帯ごとの差だけを時間帯成分**に置く

</div>

<div class="grid grid-cols-3 gap-4 mt-4 text-sm text-center">
<div>

**日成分**

全日の平均を0

</div>
<div>

**時間帯成分**

全時間帯の平均を0

</div>
<div>

**日×時間帯成分**

日方向・時間帯方向<br>それぞれの平均を0

</div>
</div>

<!--
全時間帯で共通する+2は時間帯差ではないため、時間帯成分に置かせない。
制約前後で成分の和、つまり予測補正は同じだが、中心化後は成分の担当が一意になる。
系列成分は全体水準を受け持つため中心化しない。0:45
-->



---

# 結果

同じ残差を対象に、先行研究型と提案法を比較:

| モデル | corrected MAE | top10 MAE |
| --- | ---: | ---: |
| 補正なし baseline | 0.0721 | 0.2923 |
| 潜在 global/local | 0.0614 ± 0.0030 | 0.2873 ± 0.0084 |
| 出力分解・制約なし | 0.0635 ± 0.0007 | 0.2903 ± 0.0073 |
| **出力分解 + 平均ゼロ制約** | **0.0583 ± 0.0011** | **0.2508 ± 0.0154** |

<div class="mt-4 p-4 border rounded bg-blue-50 dark:bg-blue-900 text-center">

潜在 global/local 比で、平均誤差と大外れケースの両方を改善

</div>

<div class="mt-2 text-sm text-gray-500">

FreshRetailNet-50K、5 seed。同一split・calibrationなし。詳細設定と信頼区間はAppendix。

</div>

<!--
発表の山場。データセットの仕様説明はせず、先行研究型との比較結果だけを示す。
corrected MAE は小さいほど全体の補正が良く、top10 MAE は大外れ上位10%の誤差。0:40
-->

---

# 回復

<div class="text-center text-lg">

実データでは4成分の正解が分からないため、<br>
**真の成分を埋め込んだ合成データ**で出力の意味を検証

</div>

<div class="grid grid-cols-2 gap-6 mt-4">
<div>

| 真の成分 | 推定成分との相関 |
|---|---:|
| 系列 | **0.9995** |
| 日 | **0.9979** |
| 時間帯 | **0.9991** |
| 日×時間帯 | **0.9654** |

</div>
<div class="space-y-3">

<div class="p-3 border rounded bg-blue-50 dark:bg-blue-900">

**制約あり**

系列 **0.9995** ／ 日×時間帯 **0.9654**

</div>

<div class="p-3 border rounded">

**制約なし**

系列 **−0.8976** ／ 日×時間帯 **0.0262**

</div>

<div class="text-sm text-gray-500">

平均ゼロ・主効果除去の有無を比較

</div>
</div>
</div>

<div class="mt-4 p-3 border rounded bg-blue-50 dark:bg-blue-900 text-center">

4成分を高い相関で回復し、制約を外すと成分の意味が崩れた<br>
→ **「どの単位のズレか」として読むための構造的な根拠**

</div>

<!--
説明性の根拠は、真値が既知の合成データで各出力が意図した成分を回復できること。
さらに制約なしでは予測誤差が大きく崩れなくても成分相関が崩れるため、
精度ではなく制約が成分の意味を支えていると説明する。実データで因果を保証する結果ではない。0:45
-->

---

# 結論

1. 残差を **系列・日・時間帯・日×時間帯** の出力として学習
2. 平均ゼロ・主効果除去により、各成分の担当範囲を固定
3. 実データでは、潜在分離より平均誤差と大外れケースを改善
4. 合成データでは、真の4成分を高い相関で回復

<div class="mt-6 p-4 border rounded bg-blue-50 dark:bg-blue-900 text-center">

出力を制約することで、<br>
**基準値の補正と「どの単位で外れたか」の説明を同時に行える**

</div>

<div class="mt-3 text-sm text-gray-500 text-center">

説明するのは因果的な原因ではなく、ズレが現れた単位

</div>

<!--
背景の問いに直接答える結論。実データの予測改善と、合成データの成分回復を分けて主張する。0:35
-->

---

# 展望

<div class="grid grid-cols-2 gap-6 mt-4">
<div>

**今後の検証**

1. 日×時間帯成分と<br>販促・休日・天候の対応
2. 信頼できない成分を弱める<br>状況依存の shrinkage
3. 未知系列・別期間での一般化

</div>
<div>

**発表・論文への展開**

- **JIMA**：定式化と主結果
- **APIEMS**：基準値感度と適用条件
- **修士論文**：外生要因・一般化・限界を統合

</div>
</div>

<div class="mt-6 p-4 border rounded bg-blue-50 dark:bg-blue-900 text-center">

目標：**外生要因 → ズレが現れる単位 → 運用上の打ち手**をつなぐ

</div>

<div class="mt-6 text-center text-lg">

ご清聴ありがとうございました

</div>

<!--
今後の課題とスケジュールを1枚に統合し、従来研究の説明1枚追加分を吸収する。0:40
-->

---
layout: center
class: text-center
---

# Appendix

---

# 出力制約

Decoder が出す制約前の成分を $\tilde g,\tilde a,\tilde c,\tilde u$ とする

<div class="grid grid-cols-2 gap-5 mt-3">
<div class="p-3 border rounded">

**日・時間帯成分を中心化**

$$
\hat a_{i,d}=\tilde a_{i,d}-\frac1D\sum_{d'}\tilde a_{i,d'}
$$

$$
\hat c_{i,h}=\tilde c_{i,h}-\frac1H\sum_{h'}\tilde c_{i,h'}
$$

</div>
<div class="p-3 border rounded bg-blue-50 dark:bg-blue-900">

**日×時間帯成分から主効果を除去**

$$
\begin{aligned}
\hat u_{i,d,h}
&=\tilde u_{i,d,h}
-\frac1D\sum_{d'}\tilde u_{i,d',h}
-\frac1H\sum_{h'}\tilde u_{i,d,h'}\\
&\quad+\frac1{DH}\sum_{d',h'}\tilde u_{i,d',h'}
\end{aligned}
$$

</div>
</div>

- $\sum_d\hat a=0$、$\sum_h\hat c=0$、$\sum_d\hat u=\sum_h\hat u=0$

---

# 一意性

同じ残差を表す2つの分解の差を $\Delta g,\Delta a,\Delta c,\Delta u$ とする:

$$
0=\Delta g_i+\Delta a_{i,d}+\Delta c_{i,h}+\Delta u_{i,d,h}
$$

| 平均操作 | 制約により消える成分 | 残る結論 |
| --- | --- | --- |
| 日×時間帯の全体平均 | $a,c,u$ | $\Delta g_i=0$ |
| 時間帯平均 | $c,u$ | $\Delta a_{i,d}=0$ |
| 日平均 | $a,u$ | $\Delta c_{i,h}=0$ |
| 残り | $g,a,c$ | $\Delta u_{i,d,h}=0$ |

<div class="mt-4 p-3 border rounded bg-blue-50 dark:bg-blue-900 text-center">

すべての成分差が0 → **同じ残差に対して別の分け方は存在しない**

</div>

---

# 成分回復

1500系列 × 35日 × 24時間帯、5 seed。真の成分を埋め込み、推定成分と直接比較。

| 成分 | 回復 corr |
| --- | ---: |
| series $g$ | 0.9995 |
| day $a$ | 0.9979 |
| hour $c$ | 0.9991 |
| interaction $u$ | 0.9654 |

<div class="mt-4 grid grid-cols-2 gap-4 text-center">
<div class="p-3 border rounded">

residual MAE<br>**0.0965**<br>
<span class="text-sm">noise floor ≈ 0.0957</span>

</div>
<div class="p-3 border rounded">

residual $R^2$<br>**0.9764**<br>
<span class="text-sm">残差変動の97.64%を再現</span>

</div>
</div>

---

# 時間帯成分

<img src="/figures/fig2_component_recovery.png" class="mt-4 w-full" />

- 左：真の $c_h$ と推定 $\hat c_h$。ピーク位置・谷・符号・振幅まで追従
- 右：推定時間帯成分だけを使った t-SNE。同じピーク時刻の系列がまとまる
- t-SNE は定性的な可視化であり、クラスタ間距離や向き自体には意味がない

---

# 制約効果

| | residual MAE | series corr | interaction corr |
| --- | ---: | ---: | ---: |
| **制約あり** | **0.0965** | **0.9995** | **0.9654** |
| 制約なし | 0.1069 | **-0.8976** | **0.0262** |

<div class="mt-5 p-4 border rounded bg-yellow-50 dark:bg-yellow-900 text-center">

**予測が近くても、成分の中身は崩れ得る**<br>
平均ゼロ・主効果除去は、予測精度ではなく解釈のために必要

</div>

---

# 補正器比較

| series mean 残差 | baseline | 経験的 ANOVA | NN出力分解 |
| --- | ---: | ---: | ---: |
| 平均 MAE | 0.0697 | 0.0544 | **0.0516 ± 0.0013** |
| top10 MAE | 0.2788 | **0.1793** | 0.2082 ± 0.0112 |
| 相対 bias | ≈0 | **≈0** | -0.217 ± 0.054 |

<div class="mt-4 p-4 border rounded bg-blue-50 dark:bg-blue-900">

平均誤差は系列間 pooling する NN、<br>
大外れケースと無偏性はマスク付き平均の経験的 ANOVA が優位

</div>

---

# 非定常性

**想定質疑**: 「規則性がある前提だが、非定常な需要は扱わないのか？」

- 本研究は需要の定常性を仮定していない。仮定するのは「**単純な基準値で説明できる構造が大きい**」という実務上の観察のみ
- レベルシフトやトレンドは、移動平均型の基準値（直近平均・直近7日同時間帯平均）が **追従して吸収** する
- 基準値が追従しきれない **系統的なズレ** こそが残差成分の対象:
  - 日成分 $a_{i,d}$ = 日単位の変動（特定日のイベント等）
  - 相互作用成分 $u_{i,d,h}$ = 日×時間帯の変動
- つまり非定常な変動は「扱わない」のではなく、**基準値の更新と残差成分の分担で扱う**

---

# 研究系譜

**潜在分離**

- FHVAE [2]、Disentangled Sequential Autoencoder [3]、Tonekaboni ら [1] の decoupling
- 主対象は潜在空間の static/dynamic・global/local 分離

**残差化・残差診断**

- Frisch–Waugh–Lovell、Robinson の部分線形モデル
- Breusch–Pagan、Ljung–Box、ARCH — 基準モデル後の残差構造を調べる確立した方法論

**global-local 予測・分解型予測**

- Deep Factors、DeepGLO ／ Autoformer、FEDformer
- 分解粒度は trend/season や scale であり、系列・日・時間帯・相互作用という小売運用単位ではない

---

# 参考文献

<div class="mt-4 text-[15px] leading-relaxed space-y-4">

**[1]** S. Tonekaboni, C.-L. Li, S. O. Arik, A. Goldenberg, and T. Pfister, “Decoupling Local and Global Representations of Time Series,” *Proc. 25th Int. Conf. Artificial Intelligence and Statistics (AISTATS)*, PMLR, vol. 151, pp. 8700–8714, 2022.

**[2]** W.-N. Hsu, Y. Zhang, and J. Glass, “Unsupervised Learning of Disentangled and Interpretable Representations from Sequential Data,” *Advances in Neural Information Processing Systems*, vol. 30, pp. 1878–1889, 2017.

**[3]** Y. Li and S. Mandt, “Disentangled Sequential Autoencoder,” *Proc. 35th Int. Conf. Machine Learning (ICML)*, PMLR, vol. 80, pp. 5670–5679, 2018.

**[4]** Y. Wang *et al*., “FreshRetailNet-50K: A Stockout-Annotated Censored Demand Dataset for Latent Demand Recovery and Forecasting in Fresh Retail,” *arXiv preprint arXiv:2505.16319*, 2025. doi: [10.48550/arXiv.2505.16319](https://doi.org/10.48550/arXiv.2505.16319).

</div>

---

# 合成実験

| 条件 | MAE | $R^2$ | global | day | hour | interaction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| base | 0.0965 | 0.9764 | 0.9995 | 0.9979 | 0.9991 | 0.9654 |
| low interaction | 0.0959 | 0.9765 | 0.9995 | 0.9977 | 0.9991 | 0.8211 |
| high interaction | 0.0969 | 0.9767 | 0.9994 | 0.9982 | 0.9990 | 0.9890 |
| high noise | 0.2700 | 0.8428 | 0.9990 | 0.9795 | 0.9948 | 0.8334 |
| short history | 0.0959 | 0.9764 | 0.9993 | 0.9978 | 0.9985 | 0.9547 |
| small sample | 0.1461 | 0.9446 | 0.9912 | 0.9801 | 0.9902 | 0.4252 |
| high stockout | 0.0983 | 0.9755 | 0.9992 | 0.9975 | 0.9985 | 0.9637 |
| low hour signal | 0.0951 | 0.9519 | 0.9994 | 0.9983 | 0.9895 | 0.9800 |

- 相互作用成分は系列数に敏感 → 実データでは interaction を主張しすぎない根拠

---

# 統計検証

`series_mean_all` での改善（baseline 比）:

| 指標 | 改善 | 95% CI |
| --- | --- | --- |
| raw corrected cell MAE | −0.0196 | [−0.0201, −0.0189] |
| calibrated corrected cell MAE | −0.0163 | [−0.0167, −0.0157] |
| calibrated high residual top10 MAE | −0.0874 | [−0.0905, −0.0842] |

- 5 seed で一貫 → seed 依存の偶然ではない

---

# 統制比較

| モデル | corrected MAE | WAPE | residual $R^2$ | top10 MAE |
| --- | ---: | ---: | ---: | ---: |
| latent: global/local | 0.0614 ± 0.0030 | 0.9925 | 0.0627 | 0.2873 |
| latent: global/day/hour | 0.0625 ± 0.0009 | 1.0094 | -0.0140 | 0.3005 |
| latent: + interaction | 0.0619 ± 0.0008 | 1.0001 | -0.0058 | 0.2998 |
| output: 制約なし | 0.0635 ± 0.0007 | 1.0268 | 0.0325 | 0.2903 |
| output: 制約あり・interactionなし | 0.0595 ± 0.0032 | 0.9615 | 0.2440 | **0.2500** |
| **output: 制約あり・全成分** | **0.0583 ± 0.0011** | **0.9422** | **0.2483** | 0.2508 |

- 全成分 vs interactionなしの MAE 差は -0.00119、95% CI [-0.00414, 0.00163]
- 実データで interaction を足す一貫した優位は未確認

---

# 頑健性

| 系列数 | baseline MAE | corrected MAE | top10 corrected | hour corr |
| --- | ---: | ---: | ---: | ---: |
| 2k | 0.0721 | 0.0598 | 0.2643–0.2688 | 0.943–0.983 |
| 6k | 0.0697 | 0.0510–0.0514 | 0.2126–0.2132 | 0.990–0.994 |
| 12k | 0.0694 | 0.0487–0.0494 | 0.1964–0.1994 | 0.982–0.992 |

<div class="mt-4"></div>

| 6k block | baseline MAE | corrected MAEの改善幅 | calibrated top10（bias制約） |
| --- | ---: | ---: | ---: |
| block 0 | 0.0697 | 0.0186–0.0190 | 0.1988 |
| block 1 | 0.0671 | 0.0173–0.0181 | 0.1796 |
| block 2 | 0.0693 | 0.0175–0.0179 | 0.1788 |

---

# 対数残差

| 残差スケール | モデル | corrected MAE | top10 MAE | hour corr |
| --- | --- | ---: | ---: | ---: |
| 加法 | 経験的 ANOVA | 0.0544 | **0.1793** | 1.0* |
| 加法 | NN出力分解 | **0.0516 ± 0.0013** | 0.2082 | 0.995 |
| log1p | 経験的 ANOVA | 0.0510 | **0.1804** | 1.0* |
| log1p | NN出力分解 | **0.0484 ± 0.0010** | 0.2024 | 0.995 |

- log1p で両モデルとも平均 MAE が約6%改善、優劣関係は不変
- scale dependence corr は 0.953 → 0.802：log1p で部分的に低下
- *経験的 ANOVA の hour corr = 1 は定義上のトートロジー

---

# 実験設定

- 合成データ全条件: `2-Exp-22_synthetic_difficulty_final`
- 5 seed 潜在分離 vs 出力分解: `2-Exp-32_latent_vs_output_multiseed_freshretailnet`
- bias calibration と bootstrap: `2-Exp-19` / `2-Exp-20`
- 規模・block 頑健性: `2-Exp-24` / `2-Exp-25`
- 経験的 ANOVA・additive/log 比較: `2-Exp-34_fullscale_empirical_and_log`
- hour profile / component profile 図: `2-Exp-21` / `2-Exp-29`

<div class="mt-4 text-sm text-gray-500">

MAE は観測セルのみ。欠品セルは学習・評価から除外。± は seed 間標準偏差。

</div>

---

# 方法詳細

- 平均ゼロ制約と主効果除去の数式詳細
- 損失関数の全体（再構成 + bias 制約 + 正則化）
- calibration 2方式（`mae_grid_reference` / `bias_constrained_001`）の比較表
- direct target での global/local vs 4分割の WAPE 比較（2-Exp-26）
- FreshRetailNet のデータ仕様・欠品マスクの扱い
