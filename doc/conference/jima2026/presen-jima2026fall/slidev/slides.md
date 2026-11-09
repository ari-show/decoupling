---
theme: default
title: 中心化制約付き残差成分分解を用いた小売需要の時間別予測補正
info: JIMA 2026 秋季大会 発表スライド（Slidev）
class: text-center
highlighter: shiki
lineNumbers: false
drawings:
  enabled: false
transition: none
mdc: true
colorSchema: light
aspectRatio: 16/9
canvasWidth: 980
fonts:
  sans: Noto Sans JP
  weights: 400,700
---

# 中心化制約付き残差成分分解を用いた<br>小売需要の時間別予測補正

<p class="cap mt-5">観測期間内の残差再構成と、成分ごとの働きの診断</p>

<div class="mt-6 text-lg leading-relaxed">

日本経営工学会 2026年 秋季大会

東京都市大学 三川研究室

有馬 翔太

2026年10月24日

</div>

<!--
【0:15】
東京都市大学の有馬です。
「中心化制約付き残差成分分解を用いた小売需要の時間別予測補正」について発表いたします。
本発表では、将来予測に向けた前段階として、観測期間の残差を分けて再構成し、各成分の働きを調べます。よろしくお願いいたします。
-->

---
clicks: 2
---

# <span class="sec">1. 背景</span>経営判断は予測から、予測は販売実績の「読み方」から

<p class="lead">発注・在庫・人員の判断は需要予測に基づき、その土台は<b>店舗 × 商品の販売実績</b>である。</p>

<div class="flex items-center justify-center gap-3 mt-5">
  <div class="card text-center py-2 px-4" style="border-color:#b4231f">
    <h3>販売実績</h3>
    <SalesChart kind="day" :stage="0" :width="230" :height="100" />
    <div class="cap">店舗 × 商品ごと、ふつうは<b>日ごとの合計</b>で見る</div>
  </div>
  <div class="text-3xl text-gray-500">→</div>
  <div class="card text-center py-3 px-5">
    <h3>需要予測</h3>
    <div class="mt-3 text-sm leading-relaxed">いつ・どれだけ<br>売れるか</div>
  </div>
  <div class="text-3xl text-gray-500">→</div>
  <div class="card text-center py-3 px-5" style="border-color:#6250d6">
    <h3>経営判断</h3>
    <div class="flex gap-2 mt-3 text-sm">
      <span class="pill">発注</span><span class="pill">在庫</span><span class="pill">人員</span>
    </div>
  </div>
</div>

<div class="msg red mt-4" v-show="$clicks >= 1">販売実績の変動を理解することが、需要予測と経営判断の出発点</div>

<div class="flex items-center justify-center gap-5 mt-2" v-show="$clicks >= 2">
  <div class="flex items-center gap-2">
    <SalesChart kind="day" :stage="0" :width="170" :height="80" />
    <div class="text-sm text-left leading-snug"><b>日ごとの合計</b>で読む<br><span class="cap">1 日 1 つの数字。<br>いつ売れたかは見えない</span></div>
  </div>
  <div class="text-xl text-gray-500">vs</div>
  <div class="flex items-center gap-2">
    <SalesChart kind="hour" :stage="0" :width="170" :height="80" />
    <div class="text-sm text-left leading-snug"><b>時間帯ごと</b>まで読む<br><span class="cap">1 日 24 個の数字。<br>売れ方の「形」が見える</span></div>
  </div>
</div>
<div class="hook" v-show="$clicks >= 2">本研究では、販売実績を<b>日と時間帯に分けて読む方法</b>を検証する</div>

<StoryBar :step="1" />

<!--
【0:30】
まず、研究背景について説明します。
スーパーやコンビニなどの小売現場では、発注・在庫・人員配置といった経営判断を、需要予測に基づいて行いたいという要請があります。
その予測の土台になるのが、店舗ごと・商品ごとの販売実績で、ふつうは日ごとの合計で見られています。
(click 1) 販売実績の変動を理解することが、需要予測や経営判断を改善するための出発点になります。本研究では、そのための実績の読み方を検討します。
(click 2) ここで「読み方」と言っているのは、どこまで細かく読むか、ということです。日ごとの合計で読めば1日1つの数字で、いつ売れたかは見えません。時間帯ごとまで読めば1日24個の数字になり、売れ方の形が見えます。
同じ実績でも、どこまで細かく読むかで見えるものが変わります。では、判断に効く違いはどこに出るのか。次のスライドで具体例を見ます。
-->

---
clicks: 3
---

# <span class="sec">1. 背景</span>同じ日次売上でも、時間帯の「形」が違えば打ち手が変わる

<p class="lead" style="min-height:2.4em">
  <span v-if="$clicks === 0">実績は<b>日次</b>で追うのが基本。A店とB店は、この日この商品が同じ数だけ売れた。同じ判断でよいか？</span>
  <span v-else-if="$clicks === 1">しかし<b>時間帯</b>で見ると、売れ方の「形」はまったく違う。</span>
  <span v-else-if="$clicks === 2">補充や人員配置を考えるとき、<b>時間帯の違いも判断材料になる</b>。</span>
  <span v-else>時間帯の形を<b>店舗を横断して</b>見比べれば、実績の理解が深まる —— これが本研究の仮定。</span>
</p>

<div class="mx-auto" style="max-width:860px"><StoreCompare :stage="Math.min($clicks, 2)" /></div>

<div class="hook" v-show="$clicks >= 3">ただし、店舗ごとに<b>売上の規模</b>が違うと、形をそのまま重ねて比べられない</div>

<StoryBar :step="2" />

<!--
【0:40】
販売実績の捉え方として、時系列を日次で追うのが基本です。
例えばA店とB店で、ある商品がこの日、同じ数だけ売れたとします。日次で見る限り、2店舗は同じ状況に見えます。
(click 1) しかし、どの時間帯に売れたかを見ると、A店は朝、B店は夕方に売上が集中しており、売れ方の形はまったく違います。
(click 2) 補充のタイミングや人員配置を考える際には、この時間帯の違いも判断材料になります。ただし、本発表では実際の発注や人員配置の改善効果までは評価していません。
(click 3) そこで、時間帯で見た売れ方の形を、1店舗だけでなく店舗を横断して見比べることで、実績の理解が深まるのではないか。これが本研究の仮定です。
ただし、店舗を横断して比べようとすると、店舗ごとに売上の規模そのものが違うという問題が出てきます。
-->

---
clicks: 3
---

# <span class="sec">1. 背景</span>水準を分けた残差を、「日のずれ」と「時間帯のずれ」として読む

<p class="lead" style="min-height:2.4em">
  <span v-if="$clicks === 0">大型店と小型店では売上の<b>水準</b>が違い、時間帯の形をそのまま重ねて比べられない。</span>
  <span v-else-if="$clicks === 1">そこで、店舗・商品ごとの売上水準を<b>基準値</b>として分ける。</span>
  <span v-else-if="$clicks === 2">基準値からの<b>残差</b>で、系列ごとの平均水準を分け、その上下の変動を見る。</span>
  <span v-else>同じ店でも、残差は<b>日によって</b>上下にずれる。残差には「日のずれ」と「時間帯のずれ」が重なっている。</span>
</p>

<div class="mx-auto" style="max-width:860px"><BaselineResidual :stage="$clicks" /></div>

<div class="msg mt-1" v-show="$clicks >= 3">この残差を、<b>日のずれ</b>・<b>時間帯のずれ</b>など、共有される範囲ごとの表現に分けて学習し、解釈性を高めたい</div>

<StoryBar :step="$clicks >= 3 ? 4 : 3" />

<!--
【0:55】
大型店と小型店では売れる数の桁が違うため、時間帯の売れ方をそのまま重ねても比べにくいわけです。
(click 1) そこで、店舗・商品ごとの基本的な販売水準を基準値として用意します。グラフの破線がその基準値です。
(click 2) 基準値を差し引くと、系列ごとの平均水準を分けて、基準値より売れた時間帯を正、売れなかった時間帯を負として見られます。ただし、振幅の規模差は残ります。形だけを比較するためには、振幅の扱いも別に検討する必要があります。
(click 3) さらに、同じ店の残差を複数の日で重ねると、形は似ていても、日によって全体が上下にずれます。
つまり残差には、時間帯による形のずれと、日による上下のずれが重なって含まれています。
時系列を、トレンド・季節・不規則といった複数の成分の和として読む考え方自体は、古くからあります。ただ、それは時間軸1本に沿った分解です。本研究では残差を日×時間帯の2軸の格子として捉え、「どの範囲で共有されるか」で成分を分けます。
この残差を単なる誤差として一括で扱うのではなく、日のずれ、時間帯のずれといった、共有される範囲ごとの表現に分けて学習し、解釈性を高めることを目指します。次のスライドで、その範囲を数え上げます。
-->

---
clicks: 5
---

# <span class="sec">2. 問題設定</span>残差には、共有される範囲の異なる変動が混ざっている

<p class="lead" style="min-height:2.4em">
  <span v-if="$clicks === 0">1店舗・1商品の 28日 × 24時間帯 の残差（入力）。この中には<b>共有される範囲の異なる変動</b>が混ざっている。範囲は 4 通り —</span>
  <span v-else-if="$clicks === 1">まず、<b style="color:#6b6b6b">全セルに共通</b>するずれ。日にも時間帯にも依らない、系列全体への一定の補正。</span>
  <span v-else-if="$clicks === 2">雨の日や販促日のように、<b style="color:#eb6834">ある日</b>の売上が複数の時間帯で同じ向きにずれる。</span>
  <span v-else-if="$clicks === 3">夕方のピークのように、<b style="color:#6250d6">ある時間帯</b>が複数日にわたって同じ向きにずれる。</span>
  <span v-else-if="$clicks === 4">販促日の夕方に売れ方が変わるなど、<b style="color:#008300">特定の日 × 時間帯</b>にしか現れないずれもある。</span>
  <span v-else>日と時間帯の 2 軸について、<b>全体・日・時間帯・交互作用</b>の 4 成分として表す。</span>
</p>

<div class="flex justify-center items-start gap-6 mt-1">
  <div class="flex flex-col items-center">
    <ResidualGrid mode="r" :cell="7" :axes="true" />
    <div class="cap mt-1"><b>入力</b>：1系列の観測残差（赤：正、青：負）</div>
  </div>
  <div class="flex gap-4 mt-3">
    <div class="flex flex-col items-center transition-opacity duration-300" :class="$clicks < 1 ? 'opacity-10' : ''">
      <div class="p-0.5 border-2 rounded" style="border-color:#6b6b6b"><ResidualGrid mode="g" :cell="4.5" :dim="false" /></div>
      <div class="mt-2 font-bold" style="color:#6b6b6b">全期間に共通</div>
      <div class="cap">全セルが<br>同じ向きにずれる</div>
    </div>
    <div class="flex flex-col items-center transition-opacity duration-300" :class="$clicks < 2 ? 'opacity-10' : ''">
      <div class="p-0.5 border-2 rounded border-transparent"><ResidualGrid mode="r" :cell="4.5" highlight="row" /></div>
      <div class="mt-2 font-bold" style="color:#eb6834">ある日に共通</div>
      <div class="cap">同じ日の複数の時間帯で<br>同じ向きにずれる</div>
    </div>
    <div class="flex flex-col items-center transition-opacity duration-300" :class="$clicks < 3 ? 'opacity-10' : ''">
      <div class="p-0.5 border-2 rounded border-transparent"><ResidualGrid mode="r" :cell="4.5" highlight="col" /></div>
      <div class="mt-2 font-bold" style="color:#6250d6">ある時間帯に共通</div>
      <div class="cap">複数日の同じ時間帯で<br>同じ向きにずれる</div>
    </div>
    <div class="flex flex-col items-center transition-opacity duration-300" :class="$clicks < 4 ? 'opacity-10' : ''">
      <div class="p-0.5 border-2 rounded border-transparent"><ResidualGrid mode="r" :cell="4.5" highlight="cell" /></div>
      <div class="mt-2 font-bold" style="color:#008300">日 × 時間帯に固有</div>
      <div class="cap">特定の組合せだけ<br>大きくずれる</div>
    </div>
  </div>
</div>

<div class="flex justify-center items-center gap-3 mt-3" v-show="$clicks >= 5">
  <div class="card py-1 px-3 text-sm shrink-0 whitespace-nowrap" style="border-color:#b4231f;background:#fff3f2">
    <b>推定残差</b> ＝ <b style="color:#6b6b6b">全期間</b> ＋ <b style="color:#eb6834">日</b> ＋ <b style="color:#6250d6">時間帯</b> ＋ <b style="color:#008300">交互作用</b>
  </div>
  <div class="cap text-left" style="max-width:330px">日・時間帯・交互作用は平均 0 に固定。<br>全格子上の推定残差の平均は<b style="color:#6b6b6b">全期間成分</b>になる</div>
</div>

<!--
【1:00】
ここから問題設定です。1つの店舗と1つの商品の組合せを1つの系列として、28日×24時間帯の残差を色で示したのが左の図で、これがモデルの入力です。
この残差には、共有される範囲の異なる変動が混ざっています。範囲は4通りあります。
(click 1) 1つ目は、全セルに共通するずれです。日にも時間帯にも依らない、基準値からの水準のずれです。
(click 2) 2つ目は、ある日に共通する変動です。雨の日や販促日のように、その日の複数の時間帯が同じ向きにずれます。
(click 3) 3つ目は、ある時間帯に共通する変動です。夕方のピークのように、複数の日にわたって同じ時間帯が同じ向きにずれます。
(click 4) 4つ目が、特定の日と時間帯の組合せに固有の変動です。販促日の夕方に売れ方が変わる、といった、日と時間帯の主効果だけでは説明できないずれです。
(click 5) なぜ4つなのか。日と時間帯の2軸について、全体平均、日ごとの主効果、時間帯ごとの主効果、その組合せの交互作用として表すと4成分になります。これは出力を整理するための分解であり、真の需要要因が4種類あると仮定するものではありません。
なお、日・時間帯・交互作用の成分は後ほど平均を0に固定するので、全格子上で推定した残差の平均は全期間成分になります。この項が実データで何を補正しているかは、考察で確認します。
-->
---
clicks: 2
---

# <span class="sec">3. 研究目的</span>残差を 4 成分として推定する手法を提案し、精度と成分回復で有効性を示す

<span class="key">この発表の中心</span>

<div class="goal goal-big">
  <div class="goal-k">目的</div>
  <div>残差を<b>共有範囲の異なる 4 成分の和として推定する手法</b>を提案し、<br><b>再構成精度</b>と<b>成分の回復</b>で有効性を示す。成分別に読めることも確認する</div>
</div>

<p class="lead mt-3 mb-1 transition-opacity duration-300" :class="$clicks < 1 ? 'opacity-15' : ''">なぜ合計の補正量 1 つではなく、4 成分に分けて推定するのか</p>

<div class="grid grid-cols-3 gap-4 transition-opacity duration-300" :class="$clicks < 1 ? 'opacity-15' : ''">
  <div class="card" style="border-color:#eb6834">
    <h3>① 打ち手が違う</h3>
    <p class="text-sm">終日の増減は<b>補充量</b>、時間帯の偏りは<b>配置やタイミング</b>に関わる。合計の補正量 1 つでは、この区別が消える。</p>
  </div>
  <div class="card" style="border-color:#6250d6">
    <h3>② 共有される範囲が違う</h3>
    <p class="text-sm">日のずれは<b>同じ日の 24 時間帯</b>で、時間帯の形は<b>28 日間の同じ時間帯</b>で共有される。この構造を出力の形として持たせ、中心化で担当範囲を固定する。</p>
  </div>
  <div class="card" style="border-color:#008300">
    <h3>③ 非線形に推定する</h3>
    <p class="text-sm">観測残差と共変量から、<b>成分ごとの潜在表現を経て NN で推定</b>する。平均の線形分解では持てない、共変量との関係を各成分に持たせる。</p>
  </div>
</div>

<div class="card mt-3 transition-opacity duration-300" :class="$clicks < 2 ? 'opacity-15' : ''" style="border-color:#b4231f">
  <div class="flex items-center gap-4">
    <h3 class="whitespace-nowrap" style="margin:0">示すこと</h3>
    <div class="text-sm"><b>① 再構成できる</b>：実データで誤差を比較　<b>② 成分を回復できる</b>：合成データで真の成分との相関<br><b>③ 分けて読める</b>：量と形の区別、時間帯の形の軸、全期間成分の中身を示す</div>
  </div>
</div>

<!--
【1:00】
本研究の目的は、残差を共有範囲の異なる4成分の和として推定する手法を提案し、再構成精度と成分の回復で有効性を示すことです。あわせて、分けた成分が成分別に読めることを確認します。
(click 1) なぜ合計の補正量1つではなく分けるのか、理由は3つです。
1つ目、終日の増減と時間帯の偏りは、補充量と配置という別の打ち手に関わります。合計1つではこの区別が消えます。
2つ目、日のずれと時間帯の形では共有される範囲が違います。この構造を出力の形として持たせ、中心化で担当範囲を固定します。
3つ目、各成分は潜在表現を経てニューラルネットで推定するので、共変量との非線形な関係を成分ごとに持たせられます。
(click 2) 示すことは3つです。実データで再構成誤差を比較し、合成データで真の成分との相関を見て、最後に、分けたからこそ読めること、量と形の区別、時間帯の形の軸、全期間成分の中身を示します。
-->

---
clicks: 3
---

# <span class="sec">3. 研究目的</span>モデルの骨格：何を、どう推定するか

<div class="grid grid-cols-2 gap-5 mt-1 formulas">
<div>
<div class="card">
<h3>① 残差を定義する</h3>

$r_{i,d,h} = y_{i,d,h} - b_i$

<div class="text-sm">

$y_{i,d,h}$：店舗×商品 $i$ の、日 $d$・時間帯 $h$ の売上<br>$b_i$：系列平均（欠品セルを除く）＝ 売上の<b>水準</b>

</div>
</div>
<div class="card mt-3 transition-opacity duration-300" :class="$clicks < 1 ? 'opacity-15' : ''">
<h3>② 残差を 4 成分の和で表す</h3>

$\hat r_{i,d,h} = \hat g_i + \hat a_{i,d} + \hat t_{i,h} + \hat u_{i,d,h}$

<div class="text-sm">

<span style="color:#6b6b6b">$\hat g_i$ 全期間</span>　／　<span style="color:#eb6834">$\hat a_{i,d}$ 日</span>　／　<span style="color:#6250d6">$\hat t_{i,h}$ 時間帯</span>　／　<span style="color:#008300">$\hat u_{i,d,h}$ 交互作用</span>

</div>
</div>
</div>
<div>
<div class="card transition-opacity duration-300" :class="$clicks < 2 ? 'opacity-15' : ''">
<h3>③ 各成分は潜在表現の非線形関数</h3>

$\hat a_{i,d} = f_a(z_{a,i,d}),\qquad \hat t_{i,h} = f_t(z_{t,i,h})$

$\hat g_i = f_g(z_{g,i}),\qquad \hat u_{i,d,h} = f_u(z_{u,i,d,h})$

<div class="text-sm">

$z$：Encoder が残差と共変量から得る<b>成分ごとの潜在表現</b><br>$f$：MLP。「和」なのは成分どうしで、<b>各成分の中身は非線形</b>

</div>
</div>
<div class="card mt-3 transition-opacity duration-300" :class="$clicks < 3 ? 'opacity-15' : ''" style="border-color:#b4231f">
<h3>④ 学習と使い方</h3>

$\min \sum_{d,h} m_{i,d,h}\,\bigl|\, r_{i,d,h} - \hat r_{i,d,h} \bigr|$

<div class="text-sm">

観測セル上の絶対誤差を最小化（$m$：観測マスク、欠品は 0）<br>中心化制約は $\hat a, \hat t, \hat u$ に適用。推定値は $\hat y_{i,d,h} = b_i + \hat r_{i,d,h}$

</div>
</div>
</div>
</div>

<div class="msg mt-3" v-show="$clicks >= 3">式 1 本の「分解」ではなく、<b>潜在表現 → 非線形な成分 → 和</b> という内部構造を持つモデル</div>

<!--
【0:50】
目的を式で書くと、このようになります。
まず①、店舗×商品 i の、日 d・時間帯 h の売上 y から、系列平均の基準値 b を引いたものを残差 r と定義します。基準値は観測期間の平均水準で、残差はその上下の変動です。残差にも振幅の違いは残ります。
(click 1) ②、この残差を、全期間成分 g、日成分 a、時間帯成分 t、交互作用成分 u の4つの和として表します。添え字を見ていただくと、g は系列に1つ、a は日ごと、t は時間帯ごと、u は日と時間帯の組合せごとに値を持ちます。
(click 2) ③、ここが従来の線形な分解と違う点で、各成分は潜在表現 z から MLP で推定される非線形な関数です。和になっているのは成分どうしの関係であって、各成分の中身は非線形に表現できます。
(click 3) ④、学習は、観測されたセル上で、観測残差と推定残差の絶対誤差を最小化して行います。欠品セルはマスクで除きます。中心化制約は a, t, u に適用します。得られた推定残差を基準値に足せば、時間別売上の推定値になります。
つまりこのモデルは、式1本の分解ではなく、潜在表現から非線形な成分を作り、それを足し合わせるという内部構造を持っています。
-->

---
clicks: 3
---

# <span class="sec">4. 従来研究</span>Global / Local 分離表現学習

<p class="lead">Tonekaboni ら (2022) は、1本の時系列を窓に分け、<b>時間不変な Global</b> と<b>窓ごとに変化する Local</b> を分けて学習した。</p>

<div class="flex justify-center mt-1">
  <div style="width: 760px"><GLRFigure :stage="$clicks" /></div>
</div>

<div class="cap mt-1">正解ラベルなしで 2 種類の潜在表現に分け、反実仮想正則化で両者の情報の重複を抑える</div>

<div class="foot">Tonekaboni et al., "Decoupling Local and Global Representations of Time Series," AISTATS 2022</div>

<!--
【0:50】
ここで、関連する従来研究について説明します。
Tonekaboniらは、時系列データに含まれる時間不変な特徴と、時間とともに変化する状態を分離して学習する手法を提案しています。
(click 1) この研究では、1つの時系列を一定の時間幅で分割し、それぞれの区間を「窓」と呼びます。各窓で変化する状態をLocal表現として学習します。
(click 2) そして、系列全体に共通する時間不変な特徴をGlobal表現として学習します。
これにより、変動要因を示す正解ラベルを直接与えずに、時間不変な特徴と時間変動する特徴を異なる潜在表現に持たせることを促しています。
(click 3) また、反実仮想正則化によって、両表現に情報が重複することを抑えています。
本研究は、この「共有される範囲の違う変動を分けて持つ」という考え方を引き継ぎます。
-->

---
clicks: 3
---

# <span class="sec">4. 従来研究</span>この枠組みを日 × 時間帯の残差にそのまま使うと、何が起きるか

<p class="lead" style="min-height:2.4em">
  <span v-if="$clicks === 0">比較対象の構造では、時間変動は<b>窓ごとの Local 表現 1 系列</b>にまとめて持たせる。28日 × 24時間帯 を 1 本に並べて窓に切ると —</span>
  <span v-else-if="$clicks === 1">「雨の日の全時間帯の落ち込み」と「毎日の夕方ピーク」が<b>同じ Local 表現に混ざって</b>入る。どちらが効いたかを分けて持つ場所がない。</span>
  <span v-else-if="$clicks === 2">さらに、潜在表現のままでは<b>補正量への寄与</b>が読めず、成分の和にしても内訳が一意に定まらない。</span>
  <span v-else>そこで本研究は、共有範囲ごとに成分を<b>明示的に定義</b>し、<b>中心化制約</b>で内訳を固定する。</span>
</p>

<div class="grid grid-cols-2 gap-6 mt-1">
  <div class="card transition-opacity duration-300" :class="$clicks < 1 ? 'opacity-15' : ''">
    <h3>① 変動が共有される<span style="color:#b4231f">範囲</span></h3>
    <div class="flex items-center justify-center gap-3 mt-1">
      <div class="flex flex-col items-center">
        <div style="width:250px"><GLRFigure :stage="2" :compact="true" /></div>
        <div class="cap">比較対象：窓の並び 1 次元の Local</div>
      </div>
      <div class="text-2xl text-gray-400">vs</div>
      <div class="flex flex-col items-center">
        <ResidualGrid mode="r" :cell="4.5" highlight="rowcol" />
        <div class="cap">本研究：<span style="color:#eb6834">日方向</span>と<span style="color:#6250d6">時間帯方向</span>の 2 種類の共有</div>
      </div>
    </div>
    <p class="text-sm mt-2">Local は窓の並びに沿った 1 次元。「同じ日の複数時間帯」と「複数日の同じ時間帯」という 2 方向の共有を、別々の成分として明示的に定義していない。</p>
  </div>
  <div class="card transition-opacity duration-300" :class="$clicks < 2 ? 'opacity-15' : ''">
    <h3>② 各成分の<span style="color:#b4231f">寄与</span>を明確にすること</h3>
    <div class="flex justify-center mt-1">
      <SplitBars />
    </div>
    <p class="text-sm mt-2">潜在表現からは各変動の寄与を直接読み取れるとは限らない。補正量を複数成分の和で表すと、内訳が一意に定まらない。</p>
  </div>
</div>

<div class="msg red mt-3" v-show="$clicks >= 3">→ 本研究：残差の 4 成分分解 ＋ 中心化制約</div>

<!--
【0:50】
この枠組みを、日×時間帯の残差にそのまま使うと何が起きるかを考えます。
比較対象の構造では、時間変動は窓ごとのLocal表現という1系列にまとめて持たせます。小売の28日×24時間帯を1本に並べて窓に切ると、
(click 1) 雨の日に全時間帯で落ち込む変動と、毎日夕方にピークが来る変動が、同じLocal表現の中に混ざって入ります。日方向の共有と時間帯方向の共有を、別々の成分として分けて持つ場所がありません。これが1つ目の着目点です。
(click 2) 2つ目は、各成分の寄与です。潜在表現のままでは、各変動が補正量にどれだけ寄与したかを直接読み取れるとは限りません。さらに、補正量を複数成分の和で表しても、成分間で値を移せば合計は変わらないので、内訳が一意に定まりません。
(click 3) そこで本研究では、共有範囲ごとに成分を明示的に定義し、中心化制約で内訳を固定します。
-->

---
clicks: 2
---

# <span class="sec">5. 提案手法</span>青写真：分解する → 非線形に表現する → 足し合わせる

<span class="key">全体像</span>

<div class="flex items-center justify-center gap-2 mt-2">
  <div class="bp">
    <div class="bp-t">観測残差</div>
    <ResidualGrid mode="r" :cell="4" />
    <div class="cap">店舗×商品ごと<br>28日×24時間帯</div>
  </div>
  <div class="bp-arrow"><span>① 分解</span>→</div>
  <div class="bp" style="border-color:#6250d6">
    <div class="bp-t">共有範囲の異なる 4 成分</div>
    <div class="flex gap-2 mt-1">
      <div class="flex flex-col items-center"><div class="p-0.5 border-2 rounded" style="border-color:#6b6b6b"><ResidualGrid mode="g" :cell="2.2" /></div><div class="cap" style="color:#6b6b6b">全期間</div></div>
      <div class="flex flex-col items-center"><div class="p-0.5 border-2 rounded" style="border-color:#eb6834"><ResidualGrid mode="a" :cell="2.2" /></div><div class="cap" style="color:#eb6834">日</div></div>
      <div class="flex flex-col items-center"><div class="p-0.5 border-2 rounded" style="border-color:#6250d6"><ResidualGrid mode="t" :cell="2.2" /></div><div class="cap" style="color:#6250d6">時間帯</div></div>
      <div class="flex flex-col items-center"><div class="p-0.5 border-2 rounded" style="border-color:#008300"><ResidualGrid mode="u" :cell="2.2" /></div><div class="cap" style="color:#008300">交互作用</div></div>
    </div>
  </div>
  <div class="bp-arrow"><span>② 表現</span>→</div>
  <div class="bp" style="border-color:#6250d6">
    <div class="bp-t">成分ごとの潜在表現 → 非線形</div>
    <div class="text-sm leading-relaxed mt-1 text-left">
      <div><span class="zpill" style="border-color:#6b6b6b;color:#6b6b6b">z<sub>g</sub></span> → MLP → ĝ</div>
      <div><span class="zpill" style="border-color:#eb6834;color:#eb6834">z<sub>a,d</sub></span> → MLP → â<sub>d</sub></div>
      <div><span class="zpill" style="border-color:#6250d6;color:#6250d6">z<sub>t,h</sub></span> → MLP → t̂<sub>h</sub></div>
      <div><span class="zpill" style="border-color:#008300;color:#008300">z<sub>u,d,h</sub></span> → MLP → û<sub>d,h</sub></div>
    </div>
  </div>
  <div class="bp-arrow"><span>③ 加算</span>→</div>
  <div class="bp">
    <div class="bp-t">推定残差</div>
    <ResidualGrid mode="r" :cell="4" />
    <div class="cap">＋ 基準値<br>→ 売上の推定値</div>
  </div>
</div>

<div class="grid grid-cols-2 gap-4 mt-4">
  <div class="card transition-opacity duration-300" :class="$clicks < 1 ? 'opacity-15' : ''" style="border-color:#b4231f">
    <h3>残差を扱う役割：平均水準を分ける</h3>
    <p class="text-sm">系列平均を基準値として分け、その上下の変動を学習する。振幅の規模差は残るため、形の比較では別に扱う。</p>
  </div>
  <div class="card transition-opacity duration-300" :class="$clicks < 2 ? 'opacity-15' : ''" style="border-color:#b4231f">
    <h3>中心化制約の役割：日・時間帯・交互作用を分離する</h3>
    <p class="text-sm">和で表すだけでは内訳が決まらない。各成分の平均を対応する方向で 0 に固定し、担当範囲を一意にする。</p>
  </div>
</div>

<!--
【0:50】
提案手法の全体像を1枚で示します。
入力は、店舗×商品ごとの28日×24時間帯の観測残差です。
①これを、共有範囲の異なる4成分、全期間・日・時間帯・交互作用に分解します。
②各成分は、それぞれ専用の潜在表現 z を持ち、そこからMLPで非線形に推定します。
③最後に4成分を足し合わせて推定残差とし、基準値に加えて売上の推定値を得ます。
この青写真の中で、2つの要素が特に重要です。
(click 1) 1つは、残差を扱うことの役割です。系列ごとの平均水準を基準値として分けることで、その上下の変動に着目できます。平均を引くだけでは振幅の規模差までは除かれません。
(click 2) もう1つは、中心化制約の役割です。4成分の和で表すだけでは内訳が決まりません。各成分の平均を対応する方向で0に固定することで、日・時間帯・交互作用の担当範囲を一意にします。
以降、この青写真に沿って各要素を説明します。
-->

---

# <span class="sec">5. 提案手法</span>概要：3 つの特徴

<div class="grid grid-cols-3 gap-5 mt-2">
  <div class="card flex flex-col items-center">
    <span class="tag" style="background:#0b0b0b">①</span>
    <h3 class="mt-1">残差に着目</h3>
    <SalesChart kind="hour" :stage="2" :width="270" :height="170" />
    <p class="text-sm text-center mt-1">観測売上を直接ではなく、<br><b>基準値を差し引いた残差</b>をモデル化</p>
  </div>
  <div class="card flex flex-col items-center">
    <span class="tag" style="background:#0b0b0b">②</span>
    <h3 class="mt-1">4 成分を非線形に推定し、足す</h3>
    <div class="flex items-center gap-2 mt-3" style="height:150px">
      <div class="flex flex-col items-center"><div class="p-0.5 border-2 rounded" style="border-color:#6b6b6b"><ResidualGrid mode="g" :cell="2.4" /></div><div class="cap" style="color:#6b6b6b">全期間</div></div>
      <div class="flex flex-col items-center"><div class="p-0.5 border-2 rounded" style="border-color:#eb6834"><ResidualGrid mode="a" :cell="2.4" /></div><div class="cap" style="color:#eb6834">日</div></div>
      <div class="flex flex-col items-center"><div class="p-0.5 border-2 rounded" style="border-color:#6250d6"><ResidualGrid mode="t" :cell="2.4" /></div><div class="cap" style="color:#6250d6">時間帯</div></div>
      <div class="flex flex-col items-center"><div class="p-0.5 border-2 rounded" style="border-color:#008300"><ResidualGrid mode="u" :cell="2.4" /></div><div class="cap" style="color:#008300">交互作用</div></div>
    </div>
    <p class="text-sm text-center mt-1">成分ごとの潜在表現から MLP で推定。<br>和は成分どうし、<b>各成分の中身は非線形</b></p>
  </div>
  <div class="card flex flex-col items-center">
    <span class="tag" style="background:#b4231f">③</span>
    <h3 class="mt-1">中心化制約</h3>
    <div class="flex flex-col items-center justify-center gap-1" style="height:150px">
      <div class="px-4 py-1 rounded-full text-lg font-bold" style="background:#fff3f2;border:2px dashed #b4231f;color:#b4231f">日方向の平均 = 0</div>
      <div class="px-4 py-1 rounded-full text-lg font-bold" style="background:#fff3f2;border:2px dashed #b4231f;color:#b4231f">時間帯方向の平均 = 0</div>
      <div class="px-4 py-1 rounded-full text-lg font-bold" style="background:#fff3f2;border:2px dashed #b4231f;color:#b4231f">交互作用は両方向で 0</div>
    </div>
    <p class="text-sm text-center mt-1">出力するだけでは定まらない<br><b>成分の役割</b>を共有構造に対応させる</p>
  </div>
</div>

<!--
【0:35】
提案手法の特徴を3つにまとめます。
1つ目は、観測売上を直接モデル化するのではなく、基準値を差し引いた残差に着目することです。
2つ目は、残差を共有範囲の異なる4成分として、それぞれ潜在表現からMLPで非線形に推定し、足し合わせることです。線形な主効果の和とは違い、各成分の中身は共変量との非線形な関係を持てます。
3つ目は、推定された各補正成分に中心化制約を適用することです。これにより、単に4つの成分を出力するだけでは定まらない、それぞれの成分の役割を共有構造に対応させます。
-->

---

# <span class="sec">5. 提案手法</span>各成分の意味

<p class="lead">各成分は、残差が<b>どの範囲で共有されるか</b>に対応する。</p>

<div class="mt-1">
  <DecompFigure :stage="4" :cell="5.5" :captions="false" :hl="true" />
</div>

<div class="grid grid-cols-4 gap-3 mt-4 text-sm" style="margin-left: 150px">
  <div class="card" style="border-color:#6b6b6b"><b style="color:#6b6b6b">全期間成分</b><br>全セルへ同じ値を加える項。基準値の水準ずれを吸収する</div>
  <div class="card" style="border-color:#eb6834"><b style="color:#eb6834">日成分</b><br>ある日の複数の時間帯に共通する変動</div>
  <div class="card" style="border-color:#6250d6"><b style="color:#6250d6">時間帯成分</b><br>複数日の同じ時間帯に共通して現れる変動</div>
  <div class="card" style="border-color:#008300"><b style="color:#008300">交互作用成分</b><br>日・時間帯では説明できない、特定の組合せに固有の変動</div>
</div>

<!--
【0:35】
4成分の意味を確認します。
全期間成分は、日にも時間帯にも依らない項で、全セルへ同じ値を加える補正です。基準値の水準ずれを吸収します。この項が実データで何を集めていたかは、考察で触れます。
日成分は、ある日の複数時間帯に共通する変動です。
時間帯成分は、複数日にわたって同じ時間帯に共通して現れる変動です。
そして交互作用成分は、日成分と時間帯成分だけでは説明できない、特定の日と時間帯の組合せに固有の変動です。
これらの成分に対応する潜在表現を学習し、そこから補正成分を推定することで、残差全体を再構成します。
-->

---
clicks: 5
---

# <span class="sec">5. 提案手法</span>モデルの全体像：Encoder → 潜在表現 → Decoder → 中心化 → 加算

<p class="lead" style="min-height:2.4em">
  <span v-if="$clicks === 0">入力は、店舗・商品ごとの 28日 × 24時間帯 の<b>観測残差</b>と共変量。</span>
  <span v-else-if="$clicks === 1">Encoder は<b>共有範囲に合わせた方向</b>で集約（平均・標準偏差）し、<b>成分ごとの NN</b> で潜在表現へ。</span>
  <span v-else-if="$clicks === 2">各成分に対応する<b>潜在表現 z</b> を得る。交互作用は z<sub>a</sub> と z<sub>t</sub> を結合して MLP で作る。</span>
  <span v-else-if="$clicks === 3">Decoder（成分ごとの <b>MLP</b>）が、潜在表現から <b>4 つの残差補正成分</b>を非線形に推定する。</span>
  <span v-else-if="$clicks === 4">そのまま加算せず、各成分に<b>中心化制約</b>を適用する。</span>
  <span v-else>中心化された 4 成分を加算して<b>推定残差</b>とし、基準値に加えて売上の推定値を得る。</span>
</p>

<ModelFigure :stage="$clicks" />

<!--
【1:20】
こちらが、提案モデルの全体像です。左から、Encoder、潜在表現、Decoder、中心化、加算という流れです。
(click 0) 入力は、店舗・商品ごとの28日×24時間帯の観測残差と、欠品情報や曜日、販促、天候などの共変量です。
(click 1) Encoderは、各成分が担当する共有範囲に合わせた方向で情報を集約します。全期間成分は表全体から、日成分は日ごとに、時間帯成分は時間帯ごとに、観測セルの平均と標準偏差を集約特徴として取ります。
集約特徴は、成分ごとの小さなニューラルネットに通して潜在表現にします。
(click 2) こうして成分ごとの潜在表現 z が得られます。交互作用については、日と時間帯の潜在表現を結合してMLPに通し、日×時間帯ごとの潜在表現を作ります。
(click 3) 次に、Decoderです。成分ごとに用意したMLPが、潜在表現から4つの残差補正成分を非線形に推定します。
(click 4) ここで重要なのが、これらの成分をそのまま加算するのではなく、中心化制約を適用することです。
(click 5) 最後に、中心化された4成分を加算して推定残差を得ます。この推定残差を基準値に加えることで、時間別売上の推定値が得られます。
この構造は、入力の残差を成分ごとの低次元な潜在表現に圧縮し、そこから残差を再構成するオートエンコーダになっています。次にこの点を説明します。
-->

---
clicks: 3
---

# <span class="sec">5. 提案手法</span>肝：オートエンコーダ構造で、成分ごとの潜在表現を獲得する

<span class="key">提案の核心</span>

<div class="flex items-center justify-center gap-2 mt-2">
  <div class="bp">
    <div class="bp-t">入力</div>
    <ResidualGrid mode="r" :cell="3.5" />
    <div class="cap">観測残差 ＋ 共変量</div>
  </div>
  <div class="bp-arrow"><span>Encoder</span>→</div>
  <div class="bp" style="border-color:#6250d6;background:#f4f1ff">
    <div class="bp-t">潜在表現（成分ごと・低次元）</div>
    <div class="text-sm leading-relaxed text-left mt-1">
      <div><span class="zpill" style="border-color:#6b6b6b;color:#6b6b6b">z<sub>g</sub></span> 系列に 1 本（10 次元）</div>
      <div><span class="zpill" style="border-color:#eb6834;color:#eb6834">z<sub>a,d</sub></span> 日ごとに 1 本（28 本 × 10 次元）</div>
      <div><span class="zpill" style="border-color:#6250d6;color:#6250d6">z<sub>t,h</sub></span> 時間帯ごとに 1 本（24 本 × 10 次元）</div>
      <div><span class="zpill" style="border-color:#008300;color:#008300">z<sub>u,d,h</sub></span> z<sub>a</sub> ⊕ z<sub>t</sub> から（28 × 24 本 × 8 次元）</div>
    </div>
  </div>
  <div class="bp-arrow"><span>Decoder</span>→</div>
  <div class="bp">
    <div class="bp-t">4 成分 → 中心化 → Σ</div>
    <div class="flex items-center gap-1 mt-1">
      <div class="p-0.5 border-2 rounded" style="border-color:#6b6b6b"><ResidualGrid mode="g" :cell="1.7" /></div><span class="text-xs">+</span>
      <div class="p-0.5 border-2 rounded" style="border-color:#eb6834"><ResidualGrid mode="a" :cell="1.7" /></div><span class="text-xs">+</span>
      <div class="p-0.5 border-2 rounded" style="border-color:#6250d6"><ResidualGrid mode="t" :cell="1.7" /></div><span class="text-xs">+</span>
      <div class="p-0.5 border-2 rounded" style="border-color:#008300"><ResidualGrid mode="u" :cell="1.7" /></div>
    </div>
    <div class="cap">→ 推定残差（入力を再構成）</div>
  </div>
</div>

<div class="grid grid-cols-3 gap-3 mt-4 text-sm">
  <div class="card transition-opacity duration-300" :class="$clicks < 1 ? 'opacity-15' : ''"><b>① 「どこが効いたか」が成分ごとに残る</b><br>出力を成分別に持つため、推定した補正量と誤差への影響を、共有範囲ごとに調べられる。</div>
  <div class="card transition-opacity duration-300" :class="$clicks < 2 ? 'opacity-15' : ''"><b>② 中心化で出力の担当範囲を固定</b><br>各成分の平均を対応する方向で 0 にし、全格子上で出力の内訳を一意にする。潜在 z の次元の意味までは定めない。</div>
  <div class="card transition-opacity duration-300" :class="$clicks < 3 ? 'opacity-15' : ''" style="border-color:#6250d6"><b>③ 成分の回復を直接検証できる</b><br>出力が成分別なので、真の成分を埋め込んだ合成データで、意図した成分を回復したかを相関で測れる。</div>
</div>

<!--
【0:50】
提案手法の肝は、このオートエンコーダ構造で、成分ごとの潜在表現を獲得することです。
入力の観測残差と共変量をEncoderに通すと、成分ごとに分かれた低次元の潜在表現が得られます。全期間は系列に1本、日は日ごとに1本、時間帯は時間帯ごとに1本、交互作用は日と時間帯の潜在表現を結合して、セルごとに1本です。
Decoderはこれらから4成分を作り、中心化して足し合わせ、入力の残差を再構成します。
なぜこの構造が研究目的につながるのか、3点あります。
(click 1) 1つ目、出力を成分ごとに持つので、どの成分がどれだけ補正しているか、どの誤差に関わるかを調べられます。
(click 2) 2つ目、中心化により、全格子上で出力成分の担当範囲が定まります。定まるのは出力の内訳で、潜在の各次元の意味までは定めません。
(click 3) 3つ目、出力が成分別なので、真の成分を埋め込んだ合成データで、意図した成分を回復したかを相関で直接測れます。潜在空間で分ける方式では、この検証自体ができません。
【質疑用】未知日への拡張は、観測残差を入力に使えないため、利用できる情報に合わせた学習と未来日を隠した評価が必要。本発表の主評価は同期間の再構成。
-->

---
clicks: 4
---

# <span class="sec">5. 提案手法</span>中心化制約 (1/2)：和で表すだけでは、内訳が一意に決まらない

<p class="lead" style="min-height:2.4em">
  <span v-if="$clicks <= 1">ある 1 つの時間帯に絞り、3 日分の残差を <b style="color:#6b6b6b">全期間</b> ＋ <b style="color:#eb6834">日</b> の 2 成分で表してみる。</span>
  <span v-else-if="$clicks <= 3">成分間で値を<b>移しても</b>、足した残差は同じ。<b>内訳 A・B・C はどれも正解</b>になってしまう。</span>
  <span v-else>移せる量 ＝ <b style="color:#eb6834">日成分の平均</b>。これを <b style="color:#b4231f">0 に固定</b>すれば移せなくなり、内訳は A に定まる。</span>
</p>

<div class="mt-2"><IdentFigure :stage="$clicks" /></div>

<div class="grid grid-cols-2 gap-4 mt-3 text-sm">
  <div class="card py-1" style="border-color:#9a9a9a">
    <b>読み方</b>：日成分に全日共通の定数を足すと、全期間成分と区別がつかない。<br>その定数が「日成分の平均」として現れる。
  </div>
  <div class="card py-1 transition-opacity duration-300" :class="$clicks < 4 ? 'opacity-15' : ''" style="border-color:#b4231f;background:#fff3f2">
    <b>時間帯成分・交互作用成分でも同じこと</b>が起きる。<br>→ 次ページ：成分ごとに、どの方向の平均を 0 にするかを決める
  </div>
</div>

<!--
【0:50】
ここで、中心化制約がなぜ必要なのかを説明します。説明のために、ある1つの時間帯に絞り、3日分の残差を、全期間成分と日成分の2つの和で表してみます。
(click 1) 内訳Aは、全期間が+2、日が−1、0、+1で、残差+1、+2、+3を再現しています。
(click 2) ここで、全期間から2を取って、各日に+2ずつ移します。内訳Bです。足した残差は全く変わりません。
(click 3) 逆に、各日から3ずつ取って全期間に移した内訳Cでも、残差は同じです。
つまり、和で表すだけでは、A・B・Cのどれも正解になってしまい、各成分が意図した役割を担っているとは限りません。
読み方としては、日成分に全日共通の定数を足すと全期間成分と区別がつかず、その定数が日成分の平均として現れる、ということです。
(click 4) そこで、移せる量である日成分の平均を0に固定します。すると値を移せなくなり、内訳はAに定まります。
時間帯成分や交互作用成分についても同じことが起きるので、次のページで成分ごとにどの方向の平均を0にするかを決めます。
-->

---
clicks: 3
---

# <span class="sec">5. 提案手法</span>中心化制約 (2/2)：各成分の担当範囲を固定する

<p class="lead">日成分は<b style="color:#eb6834">日方向</b>、時間帯成分は<b style="color:#6250d6">時間帯方向</b>、交互作用成分は<b style="color:#008300">両方向</b>で平均を 0 にする。</p>

<div class="mt-2"><CenterConstraintFigure :stage="$clicks" /></div>

<div class="msg red mt-3" v-show="$clicks >= 3">中心化制約は、残差の合計を求めるためではなく、<b>内訳を明確にする</b>ための仕組み</div>

<!--
【0:45】
(click 1) そこで、日成分については日方向の平均を0に、
(click 2) 時間帯成分については時間帯方向の平均を0にします。
(click 3) さらに、交互作用成分については、日方向と時間帯方向のどちらについても平均が0となるように制約を設けます。
これにより、各成分に重複して含まれる変動を抑え、日・時間帯・交互作用という共有範囲に応じた役割を定めます。
つまり中心化制約は、残差の合計値を求めるためだけではなく、その内訳を明確にするための仕組みです。
【質疑用・時間があれば】古典的な季節分解でも、季節成分は1周期で和がゼロという制約を置いて識別性を確保します。本研究の中心化制約は、その考え方を日と時間帯の2軸に広げたものです。分散分析型の分解と何が違うのか、と聞かれたらこの対応を軸に答える。
-->

---

# <span class="sec">6. 実験</span>実験設定

<div class="grid grid-cols-2 gap-4 mt-1">
  <div class="card">
    <h3>実データ：FreshRetailNet-50K（生鮮小売の公開データ）</h3>
    <div class="flex items-center gap-3 mt-1">
      <ResidualGrid mode="r" :cell="2.6" />
      <div class="text-sm">店舗 × 商品 ＝ 1 系列、28日 × 24時間帯<br>観測残差を入力し、<b>同じ期間の残差を再構成</b></div>
    </div>
    <div class="mt-2 text-sm font-bold">データ分割（系列数）</div>
    <div class="flex w-full h-6 rounded overflow-hidden text-xs font-bold text-white mt-1">
      <div class="flex items-center justify-center" style="flex:6000;background:#6250d6">学習 6,000</div>
      <div class="flex items-center justify-center" style="flex:1500;background:#8f82e0">検証 1,500</div>
      <div class="flex items-center justify-center" style="flex:1500;background:#b8b0ec">評価 1,500</div>
    </div>
    <div class="mt-2 text-sm"><b>評価指標</b>　MAE ／ 残差 Top10 MAE（残差が大きい上位 10% セルの誤差）</div>
  </div>
  <div class="flex flex-col gap-3">
    <div class="card">
      <h3>比較手法</h3>
      <div class="flex flex-col gap-1 mt-1 text-sm">
        <div class="flex items-center gap-2"><span class="w-4 h-4 rounded" style="background:#9a9a9a"></span><b>基準値のみ</b>：残差補正なし</div>
        <div class="flex items-center gap-2"><span class="w-4 h-4 rounded" style="background:#eb6834"></span><b>中心化なし</b>：4 成分モデル（制約を外す）</div>
        <div class="flex items-center gap-2"><span class="w-4 h-4 rounded" style="background:#6250d6"></span><b>提案</b>：4 成分モデル ＋ 中心化制約</div>
      </div>
    </div>
    <div class="card">
      <h3>合成データ：成分が正しく取り出せるか</h3>
      <div class="flex items-center gap-2 mt-1">
        <div class="p-0.5 border-2 rounded" style="border-color:#6b6b6b"><ResidualGrid mode="g" :cell="1.7" /></div>
        <div class="p-0.5 border-2 rounded" style="border-color:#eb6834"><ResidualGrid mode="a" :cell="1.7" /></div>
        <div class="p-0.5 border-2 rounded" style="border-color:#6250d6"><ResidualGrid mode="t" :cell="1.7" /></div>
        <div class="p-0.5 border-2 rounded" style="border-color:#008300"><ResidualGrid mode="u" :cell="1.7" /></div>
        <div class="text-sm ml-1"><b>真の 4 成分</b>から生成し、<br>中心化の有無で再構成誤差と<br><b>成分回復（相関）</b>を比較</div>
      </div>
    </div>
  </div>
</div>

<div class="card mt-3 text-xs" style="border-color:#6250d6">
  <div class="flex flex-wrap gap-x-5 gap-y-1 items-center">
    <span class="font-bold text-sm" style="color:#6250d6">学習条件</span>
    <span><b>Encoder</b>　集約特徴（平均・標準偏差）→ 成分ごとの NN、隠れ 160</span>
    <span><b>潜在次元</b>　全期間 10・日 10・時間帯 10・交互作用 8</span>
    <span><b>Decoder</b>　成分ごとに 2 層 MLP（ReLU, Dropout 0.1）</span>
    <span><b>損失</b>　観測セル上の絶対誤差（欠品除外）</span>
    <span><b>最適化</b>　AdamW, lr 1e-3, weight decay 1e-4, batch 128</span>
    <span><b>epoch</b>　最大 60、検証損失で早期終了（patience 8）</span>
    <span><b>試行</b>　5 seed の平均</span>
    <span class="cap">詳細は Appendix</span>
  </div>
</div>

<!--
【0:50】
提案手法の評価について説明します。実データと合成データを用いた2種類の実験を行いました。
実データには、生鮮小売の公開データセットであるFreshRetailNet-50Kを使用しています。店舗と商品の組合せを1系列とし、28日×24時間帯のデータとして扱います。
データは、学習用6,000系列、検証用1,500系列、評価用1,500系列に分割しました。観測残差を入力し、同じ観測期間の残差を再構成します。
比較手法は、残差補正を行わない基準値のみ、中心化制約なしの4成分モデル、そして中心化制約ありの提案モデルの3つです。評価指標にはMAEと残差Top10 MAEを使用しました。
合成データについては真の4成分を設定し、中心化制約の有無による再構成誤差と成分回復性能を比較しました。
学習条件は下段のとおりです。主結果のEncoderは、集約特徴を成分ごとのニューラルネットに通し、隠れ層は160次元、潜在次元は全期間・日・時間帯が10、交互作用が8です。Decoderは成分ごとの2層MLPで、損失は観測セル上の絶対誤差、AdamWで最大60epoch、検証損失で早期終了し、5つのseedの平均で評価しています。詳細はAppendixにまとめています。
-->

---
clicks: 2
---

# <span class="sec">6. 実験</span>実データ：残差再構成誤差

<p class="lead" style="min-height:2.4em">
  <span v-if="$clicks === 0">この学習条件では、4 成分モデルは基準値より低誤差で、中心化ありはさらに低い。</span>
  <span v-else-if="$clicks === 1">残差が大きいセルに絞った Top10 MAE でも、提案モデルが最も低い。</span>
  <span v-else>対象条件で<b>残差再構成誤差が改善</b>。中心化の改善幅は学習予算にも依存する。</span>
</p>

<div class="mt-2"><ResultBars :stage="$clicks" /></div>

<div class="cap mt-2">2-Exp-40：最大 60 epoch／patience 8、5 seed 平均。同じ観測期間の再構成を評価</div>

<!--
【1:00】
こちらが実データを用いた実験結果です。左側は全体のMAE、右側は残差Top10 MAEを示しています。どちらも値が小さいほど誤差が小さいことを表しています。
まず左側のMAEに注目します。基準値のみでは0.06966だったのに対し、中心化制約なしのモデルでは0.05422となり、約22%低下しました。
さらに中心化制約を導入した提案モデルでは、MAEが0.04828となりました。これは、制約なしのモデルと比較して約11%、基準値のみと比較すると約31%の低減に相当します。
(click 1) また、右側の残差Top10 MAEについても、提案モデルが最も低い値を示しています。
(click 2) 以上の結果から、共有範囲に基づく残差の4成分推定と中心化制約の導入が、対象条件で観測期間内の残差再構成誤差を低減しました。後続の長時間学習では中心化あり・なしの差が縮んでおり、この11%は今回の学習条件付きの値です。
-->

---
clicks: 2
---

# <span class="sec">6. 実験</span>合成データ：意図した成分を回復できているか

<p class="lead" style="min-height:2.4em">
  <span v-if="$clicks === 0">実データでは真の成分が分からないため、<b>真の 4 成分を埋め込んだ合成データ</b>で、推定成分と真の成分の相関を評価。</span>
  <span v-else-if="$clicks === 1">中心化なしは、再構成はできる（残差 MAE 0.1068）が、成分間の回転を許して最良に合わせても<b>全期間 0.64・交互作用 0.30</b> 止まり。</span>
  <span v-else>中心化ありは 4 成分すべて <b>0.97 以上</b>。<b>再構成誤差が小さい ≠ 成分が正しい</b>。</span>
</p>

<div class="flex justify-center items-start gap-4 mt-1">
  <div style="width: 660px"><CorrBars :stage="$clicks" /></div>
  <div class="flex flex-col gap-2 text-sm" style="width: 250px">
    <div class="card py-1">
      <b>残差 MAE</b>
      <div class="mt-1"><span class="inline-block w-3 h-3 rounded mr-1" style="background:#6250d6"></span>中心化あり（提案）<b class="ml-2">0.0963</b></div>
      <div><span class="inline-block w-3 h-3 rounded mr-1" style="background:#eb6834"></span>中心化なし<b class="ml-2">0.1068</b></div>
      <div><span class="inline-block w-3 h-3 rounded mr-1" style="background:#9a9a9a"></span>潜在空間で分解<b class="ml-2">0.1680</b></div>
      <div class="cap">潜在空間で分解：4 つの潜在表現を連結して 1 つの Decoder で残差を出力（成分別の出力を持たない）</div>
    </div>
    <div class="card py-1 transition-opacity duration-300" :class="$clicks < 1 ? 'opacity-15' : ''">
      <b>相関の求め方</b>
      <div class="cap mt-1">観測セル上で、真の成分と推定成分の Pearson 相関（全系列をまとめて計算）。<b>中心化なしは、推定 4 成分に直交 Procrustes 回転をかけて真の成分に最も近づけてから計算</b>（全体の二乗誤差が最小となる回転。相関の上限ではない）。式は付録</div>
    </div>
  </div>
</div>

<!--
【1:00】
続いて、合成データを用いた実験結果です。
実データでは、残差に含まれる真の成分が分からないため、各成分を正しく取り出せているかを直接評価できません。そこで、真の4成分を埋め込んだ合成データを用意し、推定成分と真の成分の相関を評価しました。
(click 1) 中心化なしでも残差MAEは0.1068で、ある程度の再構成はできています。ただ、中心化なしでは成分の取り違えや符号の反転が起こり得るので、推定した4成分に直交回転をかけて真の成分に最も近づけた上で、相関を取っています。真値を使った回転後の診断でも、全期間成分は0.64、交互作用成分は0.30でした。ただし、この回転が各成分の相関を最大化するわけではありません。
(click 2) 一方、中心化ありでは、回転なしで4成分すべてが0.97以上の相関を示しました。残差MAEも、この合成条件の比較では0.0963と最も小さい結果でした。12 epoch、1 seedの結果であり、他方式との収束後の優劣や実データの真の要因回復まで示したものではありません。
再構成誤差が小さいというだけでは、意図した成分が回復できているとは限りません。中心化制約が、成分の役割を定めるうえで効いていることが分かります。
-->

---
clicks: 2
---

# <span class="sec">7. 考察 (1/3)</span>中心化により、日成分は「量」、交互作用は「形」の成分になる

<div class="grid grid-cols-2 gap-4 mt-1 defrow">
  <div class="card" style="border-color:#eb6834"><b style="color:#eb6834">量 ＝ 日成分</b>　24 時間帯で同じ値 → その日のカーブ全体を上下させる＝<b>その日の総量</b></div>
  <div class="card" style="border-color:#008300"><b style="color:#008300">形 ＝ 交互作用</b>　その日の合計が 0 → 時間帯の間で配分を移す＝<b>その日の配分</b></div>
</div>

<div class="grid gap-4 mt-2" style="grid-template-columns: 1.3fr 1fr">
  <div>
    <QuantShapeCovFigure />
    <div class="cap text-left" style="margin-top:-2px">模式図：1 系列の 28 日分。棒＝提案モデルの成分、灰点＝実測のみ（生の残差の日平均と、日平均を引いた RMS）</div>
  </div>
  <div class="card transition-opacity duration-300" :class="$clicks < 1 ? 'opacity-15' : ''" style="border-color:#6b6b6b">
    <h3>その日の共変量と突き合わせる</h3>
    <p class="text-sm">1 点 ＝（系列, 日）。評価 1,500 系列 × 28 日の各点で、その日の共変量と、その日の量・形の相関をとる。</p>
    <div class="abl-t text-sm mt-2"><table><tbody>
      <tr><th></th><th style="color:#eb6834">量</th><th style="color:#008300">形</th></tr>
      <tr><td>休日</td><td><b>+0.25</b></td><td>+0.10</td></tr>
      <tr><td>割引の深さ</td><td>+0.10</td><td><b>+0.21</b></td></tr>
    </tbody></table></div>
    <p class="text-sm mt-2"><b style="color:#eb6834">休日</b>は総量を持ち上げる。<b style="color:#008300">割引</b>は総量より、時間帯の配分を動かす。</p>
    <div class="cap text-left mt-1">240 epoch・5 seed 平均、5 seed すべて同じ向き。実測のみでも向きは同じ（Appendix）</div>
  </div>
</div>

<div class="msg mt-2" v-show="$clicks >= 2">共変量ごとに、効くのが<b>量</b>か<b>形</b>かを分けて読める。総量に関わる打ち手と、時間帯配分に関わる打ち手を分けて検証できる</div>

<style>
.defrow .card { font-size: 0.86rem; padding: 0.35rem 0.7rem; line-height: 1.4; }
</style>

<!--
【0:50】
ここからは、分けて推定したから言えることです。中心化のおかげで、日成分と交互作用は役割のはっきりした成分になります。日成分は24時間帯で同じ値なので、その日のカーブ全体を上下させる。つまりその日の総量、「量」です。交互作用はその日の合計がゼロなので、時間帯の間で配分を移す。つまりその日の「形」です。
図は1系列の28日分です。上が、その日の共変量。網掛けが休日、紫が割引の深さ。真ん中が量、つまり日成分。下が形、つまり交互作用の大きさです。灰色の点は、モデルを使わずに生の残差から直接出した日平均とばらつきです。
(click 1) この量と形を、同じ日の共変量と突き合わせます。1点が系列と日の組で、1500系列かける28日の点で相関をとります。休日は量との相関が0.25で形は0.10。休日の日は、図の網掛けの日で橙の棒が高いように、総量が持ち上がります。割引の深さは逆で、形との相関が0.21、量は0.10。割引が深い日は、紫の棒の日で緑の棒が高いように、総量よりも時間帯の配分が動きます。向きは5 seedすべてで同じで、生の残差から直接出した灰点でも同じ向きです。
(click 2) つまり共変量ごとに、効くのが量なのか形なのかを分けて読めます。総量に関わる打ち手と、時間帯配分に関わる打ち手を分けて検証できる、ということです。どの打ち手を対応づけるかは運用側の判断で、この数字から直接は出ません。

言えないこと（質疑用）：
- 因果ではない。値引きは無作為でなく、「夕方に売れ残りそうな日に値引きする」逆向きを排除できない。
- 「形が動く」の中身は限定的。イベント別の時間帯プロファイル差は休日 ±0.010、雨 0.005、値引き 0.003 と大きさは違うが、形は4つともほぼ同じ（相互相関 0.97 以上、朝 9 時台と 15〜17 時が上がり深夜が下がる）。イベントごとに違う形が出るのではなく、共通の 1 つの形を強弱で呼び出している。
- 実測の「形」には volume の混入がある（売上が多い日は絶対値のばらつきも大きい）。ただしそれだけなら休日も形との相関が高く出るはずで、実際は逆。これが内部対照。
- 量 vs 形の散布図と、イベント別の交互作用プロファイルの実図は Appendix 探索図。
- 象限で見ると、販促日は「量↑形↑」が 31%（非販促日 20%）、販促日の 25% は量が動かず形だけ動く＝総量が増えずに時間帯だけ移動した候補。
出典：ユーザー提供メモ（2026-10-23）。量 = day_component[i,d,0]、形 = √mean_h u[i,d,h]²、day_covariates.npy。【要照合】run ID。240 epoch の値を主表に使っているので、主結果（60 epoch）との条件差を聞かれたら「60 epoch でも同順（0.092/0.214、0.239/0.063）」と答える。
-->

---
clicks: 1
---

# <span class="sec">7. 考察 (2/3)</span>時間帯成分の違いは、3 つの特徴に集約される

<p class="lead">Decoder が出した 1,479 系列の時間帯成分を主成分分析。<b>系列ごとの違いは 3 軸でほぼ尽きる</b>。</p>

<div class="pchd grid grid-cols-3 mt-1" style="max-width:800px;margin-left:auto;margin-right:auto">
  <div><span class="num">①</span>ピークの高さ<span class="sh">82%</span></div>
  <div><span class="num">②</span>朝型 ⇔ 夕方型<span class="sh">6%</span></div>
  <div><span class="num">③</span>午後の山の有無<span class="sh">3%</span></div>
</div>
<div class="flex justify-center"><img src="/figures/crop_pca_hour_axes_top.png" style="width:100%;max-width:800px" /></div>
<div class="cap" style="margin-top:-2px">黒：平均カーブ　赤：この軸の +2SD　青破線：−2SD</div>

<div class="grid grid-cols-3 gap-4 mt-2 pcq" style="max-width:860px;margin-left:auto;margin-right:auto">
  <div><b>山がどれだけ高いか</b><br>山の位置は変わらず、カーブ全体が伸び縮み<br><span class="who" style="color:#6250d6">商品で決まる</span></div>
  <div><b>山が朝か夕方か</b><br>朝が伸びると夕方が沈むシーソー<br><span class="who" style="color:#52514e">商品でも店舗でも決まりきらない</span></div>
  <div><b>午後にもう一山あるか</b><br>14〜16 時に山が立つ<br><span class="who" style="color:#b4231f">店舗で決まる</span></div>
</div>

<div class="card text-sm mt-3 transition-opacity duration-300" :class="$clicks < 1 ? 'opacity-15' : ''" style="border-color:#6b6b6b;padding:0.4rem 0.9rem;max-width:860px;margin-left:auto;margin-right:auto">
  系列間の違いはほぼ<b>「山の高さ」</b>で、<b>「いつ売れるか」の違いは小さい</b>。店舗らしさが出るのは午後の山だけ。この 3 軸は <b>seed を変えても同じ</b>に出る。
</div>

<style>
.pchd > div { text-align: center; font-weight: 700; font-size: 1rem; }
.pchd .num { color: #6250d6; margin-right: 6px; }
.pchd .sh { color: #b4231f; margin-left: 8px; }
.pcq > div { text-align: center; font-size: 0.86rem; line-height: 1.4; color: #52514e; }
.pcq b { color: #0b0b0b; font-size: 0.92rem; }
.pcq .who { font-weight: 700; }
</style>

<!--
【0:40】
2つ目は時間帯成分です。Decoderが出した1479系列の時間帯成分を主成分分析しました。系列ごとの違いは3つの軸でほぼ尽きます。
1つ目は山の高さ。山の位置は変わらず、カーブ全体が伸び縮みします。これだけで82%。これは商品で決まります。
2つ目は山が朝か夕方か。朝が伸びると夕方が沈むシーソーで、6%。商品でも店舗でも決まりきりません。
3つ目は午後にもう一山あるか。3%と小さいですが、唯一店舗で決まる軸です。
(click 1) まとめると、系列間の違いはほぼ山の高さで、いつ売れるかの違いは小さい。店舗らしさが出るのは午後の山だけです。この3軸はseedを変えても同じに出るので、学習の偶然ではなく、分離した時間帯成分が毎回同じ形に落ちている証拠になります。

質疑用（数値は Appendix「時間帯成分の主成分分析：手順と数値」）：
- 山の高さの「商品で決まる」は売上水準込み。水準を除くと商品 R² 0.21。
- 3 軸で分散 91%。5 seed で軸は 6° 以内、座標の相関 0.95 以上。
- K-means は群に分かれず（シルエット 0.08）。型ではなく連続な軸。
- 所有者が商品→店舗の階層なので、時間帯の形を商品で共有し店舗差を補正とする設計の根拠になる（全期間成分で基準値が定まったのと同じ型）。
-->

---
clicks: 2
---

# <span class="sec">7. 考察 (3/3)</span>成分ごとに精査すると、次に直す場所が決まる

<p class="lead">各成分は意図した担当範囲を保っている。<b>その中身を見ると、設計の次の一手が見える</b>。</p>

<div class="grid grid-cols-3 gap-4 mt-3">
  <div class="card" style="border-color:#6b6b6b">
    <h3>残る過小推定は、全期間成分 1 つに集まった</h3>
    <div class="abl-t text-sm mt-2"><table><tbody>
      <tr><th>観測セル上の相対 bias</th><th>5 seed</th></tr>
      <tr><td>予測全体</td><td><b>−0.262</b></td></tr>
      <tr><td>うち全期間成分 g</td><td><b>−0.305</b></td></tr>
      <tr><td>残り 3 成分</td><td>+0.043</td></tr>
    </tbody></table></div>
    <p class="text-sm mt-2">「全セル共通のずれの受け皿」という役割どおり。集まった中身は需要の水準ではなく、<b>平均基準と L1 損失の組合せが生む系統誤差</b>（最適値は残りの中央値）。中心化なしでは試行ごとに担当が入れ替わり、特定できない。</p>
    <div class="cap text-left mt-1">→ 直す場所は基準値。中央値にすればこの成分は空になる見込み</div>
  </div>
  <div class="card transition-opacity duration-300" :class="$clicks < 1 ? 'opacity-15' : ''" style="border-color:#eb6834">
    <h3>日成分は、理由のつく動きだけを残していた</h3>
    <div class="abl-t text-sm mt-2"><table><tbody>
      <tr><th>実測の日ごとのずれと比べて</th><th style="white-space:nowrap"></th></tr>
      <tr><td>相関</td><td style="white-space:nowrap"><b>0.91〜0.95</b></td></tr>
      <tr><td>振幅</td><td style="white-space:nowrap">約 1/2</td></tr>
      <tr><td style="white-space:normal">共変量で説明<br>できる割合</td><td style="white-space:nowrap">7% → <b>11%</b></td></tr>
    </tbody></table></div>
    <p class="text-sm mt-2">雑音を落とし、割引・休日・天候で説明のつく部分を保持している。<b>観測のない日にも共変量から日成分を出す足場</b>になる。</p>
    <div class="cap text-left mt-1">未知日での精度は未検証。2-Exp-47</div>
  </div>
  <div class="card transition-opacity duration-300" :class="$clicks < 2 ? 'opacity-15' : ''" style="border-color:#b4231f">
    <h3>今回の結果から言える範囲</h3>
    <p class="text-sm"><b>言える</b><br>全格子上で出力の担当範囲が定まる。同期間の残差を再構成し、成分別に読める。</p>
    <p class="text-sm mt-2"><b>言えない</b><br>未知日の予測精度、販促などの因果効果、発注・配置への効果。成分別の読みも同じ 28 日の中の話（過去窓 → 将来窓は検証中）。</p>
    <p class="text-sm mt-2"><b>条件つき</b><br>中心化の精度差 11% は学習予算で縮む（240 epoch で −0.0015、Appendix）。観測セル上では成分間の漏れが残る。</p>
  </div>
</div>

<!--
【0:55】
各成分は意図した担当範囲を保っています。その中身を精査すると、設計の次の一手が見えました。
1つ目、全期間成分です。補正後もまだ26%ほど低めに出る癖が残りますが、これは4成分のうち全期間成分だけが持っていました。全セル共通のずれの受け皿という役割どおりです。ただ、集まった中身は需要の水準ではなく、平均を基準値にしてL1損失で学習したことで生じる系統誤差でした。他成分を固定すると最適値は残りの中央値になるからです。中心化がないと、この担当が試行ごとに入れ替わって特定できません。直す場所は基準値で、中央値にすればこの成分は空になる見込みです。
(click 1) 2つ目、日成分です。実測の日ごとのずれとの相関は0.91から0.95と高いまま、振幅は半分で、共変量で説明できる割合は実測の7%より高い11%でした。雑音を落として、理由のつく動きだけを残しています。これは、まだ観測のない日にも割引や天気から日成分を出す足場になります。未知日での精度はこれからです。
(click 2) 3つ目、言える範囲です。言えるのは、全格子上で担当範囲が定まること、同期間の残差を再構成し成分別に読めることです。未知日の予測、因果効果、発注や配置への効果は示していません。成分別の読みも同じ28日の中の話で、過去窓から将来窓を予測できるかは検証中です。中心化による精度差は学習予算で縮み、観測セル上では成分間の漏れも残ります。

言い回しのメモ：全期間成分は「想定と違った」ではなく「役割どおりに受け皿として働き、集まった中身が基準値と損失の組合せ由来だと分かった」。設計の方向は変えず、基準値の中央値化が次の一手、という道半ばの位置づけで話す。
出典：bias は PR #50 / 2-Exp-44（rel_bias_total = sum(r_hat-r)/sum(|sales|)、rel_bias_k = sum(c_k)/sum(|sales|)。残り3成分 +0.043 は −0.262492−(−0.305049) の丸め。ユーザーメモの「他3成分は合計しても ±13%」とは一致しないので、どの量かを本人に確認）。
【要照合】日成分の相関 0.91〜0.95・振幅約1/2・共変量説明率 7%→11% はユーザー提供メモの値で、run ID と指標の定義（R²？どの共変量集合？）を確認してから本番に使う。
学習予算は 2-Exp-40 / 48（PR #55）、240 epoch では中心化あり 4/5 run が上限で未収束。g の最適定数と学習値の比較図は Appendix（PR #58）。観測セル上の漏れ 0.165 は Appendix 追加検証（PR #56）。
質疑メモ：事後に g を抜く ablation は MAE +0.0056 悪化、RMSE は改善、bias −0.262 → +0.043。他3成分の全セル平均は中心化で厳密に 0 なので、水準を担える成分は g だけ。b＋g は絶対シフトなので運用量としては出さない（相対では中央値 −41%、1.3% の系列で負）。
https://github.com/ari-show/decoupling/pull/50
https://github.com/ari-show/decoupling/pull/55
https://github.com/ari-show/decoupling/pull/58
-->

---

# <span class="sec">8. まとめ</span>担当範囲の定まる 4 成分で残差を推定し、精度と成分回復を示した

<div class="grid grid-cols-3 gap-4 mt-4">
  <div class="card" style="border-color:#6250d6">
    <h3>提案したこと</h3>
    <div class="flex items-center justify-center gap-1 mt-4">
      <div class="p-0.5 border-2 rounded" style="border-color:#6b6b6b"><ResidualGrid mode="g" :cell="1.7" /></div><span>+</span>
      <div class="p-0.5 border-2 rounded" style="border-color:#eb6834"><ResidualGrid mode="a" :cell="1.7" /></div><span>+</span>
      <div class="p-0.5 border-2 rounded" style="border-color:#6250d6"><ResidualGrid mode="t" :cell="1.7" /></div><span>+</span>
      <div class="p-0.5 border-2 rounded" style="border-color:#008300"><ResidualGrid mode="u" :cell="1.7" /></div>
    </div>
    <p class="text-sm mt-4">残差を共有範囲の異なる 4 成分の和として非線形に推定。</p>
    <p class="text-sm mt-3"><b>中心化制約で、成分の担当範囲を一意に固定した。</b></p>
  </div>
  <div class="card" style="border-color:#eb6834">
    <h3>実験で示したこと</h3>
    <p class="text-sm mt-4"><b>実データの再構成</b><br>MAE は基準値比 約31%、中心化なし比 約11% 低減。</p>
    <div class="cap text-left mt-2">最大 60 epoch の条件。長時間学習では差は縮小。</div>
    <p class="text-sm mt-4"><b>合成データの成分回復</b><br>4 成分すべて相関 0.97 以上（中心化なしは 0.30〜0.97）。</p>
    <div class="cap text-left mt-2">12 epoch・1 seed。中心化なしは回転後の値。</div>
  </div>
  <div class="card" style="border-color:#6b6b6b">
    <h3>分けたことで読めたこと</h3>
    <p class="text-sm mt-4">中心化により日成分は<b>量</b>、交互作用は<b>形</b>の成分になる。休日は量を、割引は形を動かす。</p>
    <p class="text-sm mt-3">時間帯成分は<b>3 軸で書け、seed によらず同じ軸</b>に落ちる。ピークの高さは商品、午後の山は店舗の性質。</p>
    <p class="text-sm mt-3">残る過小推定は全期間成分 1 つに集まり、<b>直す場所（基準値）が定まった</b>。</p>
  </div>
</div>

<div class="msg mt-5">今後：基準値の中央値化、未知日への一般化、発注・配置への有効性の検証</div>
<div class="cap mt-2">本発表の主評価は、観測残差を入力した同期間の再構成と成分回復。</div>

<!--
【0:50】
まとめです。本研究では、残差を共有範囲の異なる4成分の和として非線形に推定するモデルを提案し、中心化制約で成分の担当範囲を一意に固定しました。
実データでは再構成誤差が基準値比で約31%、中心化なし比で約11%低減し、合成データでは4成分すべてを相関0.97以上で回復しました。中心化なしでは、回転をかけても0.30から0.97に留まります。
分けたことで、日成分が量、交互作用が形の成分になり、休日は量を、割引は形を動かすこと、時間帯成分は3軸で書けてseedによらず同じ軸に落ちることが読めました。残る過小推定は全期間成分1つに集まり、直す場所が基準値だと定まりました。
今後は、基準値の中央値化、未知日への一般化、発注や配置への有効性を検証します。以上で発表を終わります。ありがとうございました。

出典：2-Exp-40 / 29 / 44 / 47 / 48、PR #58。将来予測・経営指標の改善を本発表の主実験の達成事項に含めない。
-->

---

# <span class="sec">Appendix</span>実験条件の詳細

<div class="text-xs appendix">

| 項目 | 実データ（FreshRetailNet-50K） | 合成データ |
| --- | --- | --- |
| データ | 店舗×商品 ＝ 1 系列、28日 × 24時間帯。学習 6,000 ／ 検証 1,500 ／ 評価 1,500 系列 | 1,500 系列、35日 × 24時間帯。真の 4 成分 ＋ ノイズ（σ = 0.12）、欠品率 3% |
| 基準値 | 系列平均（欠品セルを除く） | 直近 7 日の同時間帯平均 |
| 入力 | 28日 × 24時間帯 × 13チャネル：残差・欠品フラグ・日次共変量7本・周期特徴4本（次頁） | 同構成 |
| Encoder | チャネル別マスクで平均・SDを集約。全期間・時間帯：MLP、日：GRU、交互作用：日・時間帯潜在を連結したMLP（詳細は付録） | 同構成 |
| Decoder | 成分ごとに Linear(→160)–ReLU–Dropout(0.1)–Linear(→1) | 同構成 |
| 中心化 | 日成分：日方向平均 0、時間帯成分：時間帯方向平均 0、交互作用成分：両方向平均 0 | 同構成 |
| 損失 | 観測セル上の絶対誤差（欠品除外）＋ 潜在表現間の共分散ペナルティ（重み 0.01） | 同構成 |
| 最適化 | AdamW（lr 1e-3、weight decay 1e-4）、batch 128、勾配クリップ 1.0、混合精度 | 同構成 |
| epoch | 最大 60、検証再構成損失で早期終了（patience 8）、最良検証エポックを採用 | 12 |
| 試行 | 5 seed（17, 23, 31, 47, 59）の平均 | 1 seed |
| 比較手法 | 基準値のみ／中心化なし／提案 | 中心化なし／提案／潜在空間で分解（4 潜在表現を連結し 1 つの Decoder で残差を出力、成分別出力なし） |
| 評価 | MAE・残差Top10 MAE（定義は付録「評価指標」） | 残差MAE・真の成分との相関。中心化なしは事後の直交整合後（定義と前処理の注意は付録「成分回復」） |

</div>

<!--
質疑用。実データの条件は configs/2-Exp-40_jima_main_results_freshretailnet.json、合成データは 2-Exp-29_synthetic_component_recovery_figure.json に基づく。
-->

---

# <span class="sec">Appendix</span>記号と入力：観測値・マスク・潜在表現を区別する

<div class="grid grid-cols-2 gap-6 text-sm appendix-math notation">
<div>

**対象：実データ主実験（系列平均基準）**

| 記号 | 定義・形 |
| --- | --- |
| $i=1,\ldots,N$ | 店舗 × 商品の系列。$N$ は対象集合の系列数 |
| $d=0,\ldots,D-1$ | 入力期間の相対日番号、$D=28$ |
| $h=0,\ldots,H-1$ | 時間帯、$H=24$ |
| $j=0,\ldots,F-1$ | 入力チャネル、$F=13$ |
| $y_{i,d,h},\ b_i,\ r_{i,d,h}$ | 売上、固定した基準値、残差（スカラー） |
| $s_{i,d,h},\ m_{i,d,h}$ | 欠品フラグ（1：欠品）、観測マスク（1：観測） |
| $\mathbf x_{i,d,h}\in\mathbb R^{13}$ | セルの入力ベクトル。$x_{i,d,h,j}$ は第 $j$ チャネル |
| $\mathbf X_i,\mathbf M_i$ | 入力とチャネル別マスク。形は $D\times H\times F$ |

太字はベクトル・行列・テンソル、$[\,\cdot\,;\,\cdot\,]$ は連結。<br>
$\mathbf z$：潜在ベクトル、$\tilde a,\tilde t,\tilde u$：中心化前、$\hat g,\hat a,\hat t,\hat u$：最終出力。

</div>
<div>

**基準値と残差**（観測セルの平均）

$$m_{i,d,h}=\mathbb 1\{s_{i,d,h}\ne1\}$$
$$b_i=\frac{\sum_{d,h}m_{i,d,h}y_{i,d,h}}{\max(\sum_{d,h}m_{i,d,h},1)},\qquad r_{i,d,h}=y_{i,d,h}-b_i$$

**13 チャネルの内訳**

$$\mathbf x_{i,d,h}=[\,r_{i,d,h};\ s_{i,d,h};\ \mathbf v_{i,d};\ \boldsymbol\phi_h;\ \boldsymbol\psi_d\,]$$

$\mathbf v_{i,d}\in\mathbb R^7$：割引・休日・販促・降水・気温・湿度・風（日内で一定）。

$$\boldsymbol\phi_h=[\sin(2\pi h/H);\cos(2\pi h/H)]$$
$$\boldsymbol\psi_d=[\sin(2\pi q_d/7);\cos(2\pi q_d/7)],\quad q_d=d\bmod7$$

$q_d$ は実装上の相対的な 7 日周期位置。暦上の曜日そのものとは限らない。

$$M_{i,d,h,j}=\begin{cases}m_{i,d,h}&j=0\\1&j=1,\ldots,12\end{cases}$$

**損失は $m$、Encoder の集約はチャネル別の $M$ を使う。**

</div>
</div>

<!--
質疑用。主実験の記号をここで定義する。以降、範囲を省略した d,h の総和は、それぞれ0からD−1、0からH−1まで。成分添字kはg,a,t,u、入力チャネル添字jとは別。
data.py の frame_to_examples は売上・欠品フラグ・7つの日次共変量・4つの周期特徴を入力する。residual_batch がチャネル0を残差に置換する。Mの0番だけが観測マスクで、他チャネルは1。欠品時にも欠品フラグと共変量は入力集約に使う。
_time_features(day_index) は日付から曜日を取得せず、day_index % 7 を使う。このため周期位置qと暦上の曜日を区別する。
基準値の分母は実装どおりmax(count,1)。対象はseries_mean設定の主実験であり、別基準値や未知日マスクの実験では定義・マスクを変更する。
出典：src/decoupled_ts/data.py（_time_features, observed_from_stock, frame_to_examples）、residual_experiments.py（_series_mean_torch, residual_batch）、configs/2-Exp-40_jima_main_results_freshretailnet.json。
-->

---

# <span class="sec">Appendix</span>Encoder の前処理：何を、どの方向で集約するか

<div class="grid grid-cols-2 gap-6 text-sm appendix-math notation">
<div>

**集約するセル集合 $S$**（1 系列内）

$$S_g=\{0,\ldots,D-1\}\times\{0,\ldots,H-1\}$$
$$S_{a,d}=\{(d,h'):h'=0,\ldots,H-1\}$$
$$S_{t,h}=\{(d',h):d'=0,\ldots,D-1\}$$

| 集合 | 集約する範囲 | 残る単位 |
| --- | --- | --- |
| $S_g$ | 28 日 × 24 時間帯 | 系列ごとに 1 本 |
| $S_{a,d}$ | 日 $d$ の 24 時間帯 | 日ごとに 1 本 |
| $S_{t,h}$ | 時間帯 $h$ の 28 日 | 時間帯ごとに 1 本 |

**集約特徴**（$\boldsymbol\mu_i(S),\boldsymbol\sigma_i(S)\in\mathbb R^F$）

$$\boldsymbol\eta_i(S)=[\boldsymbol\mu_i(S);\boldsymbol\sigma_i(S)]\in\mathbb R^{2F}$$

ここで $F=13$ なので、NN に入る要約は **26 次元**。<br>
平均・標準偏差への集約は固定処理で、学習パラメータを持たない。

</div>
<div>

**チャネル $j$ ごとの平均・標準偏差**

$$n_{i,j}(S)=\max\!\left(\sum_{(d,h)\in S}M_{i,d,h,j},\ 1\right)$$
$$\mu_{i,j}(S)=\frac{\sum_{(d,h)\in S}M_{i,d,h,j}\,x_{i,d,h,j}}{n_{i,j}(S)}$$
$$\tau_{i,j}(S)=\frac{\sum_{(d,h)\in S}M_{i,d,h,j}\bigl(x_{i,d,h,j}-\mu_{i,j}(S)\bigr)^2}{n_{i,j}(S)}$$
$$\sigma_{i,j}(S)=\sqrt{\tau_{i,j}(S)+\varepsilon},\qquad\varepsilon=10^{-6}$$

$\tau$：分散、$\varepsilon$：平方根の安定化定数。分散の分母は観測数（不偏分散ではない）。

**各 Encoder に見える共変量**

- 日：その日の $\mathbf v_{i,d}$ と、ほぼ 0 の日内 SD。
- 時間帯：日次共変量の期間平均・SD は全時間帯で共通。残差・欠品フラグの統計と時間帯の周期特徴は時間帯ごとに異なる。
- 全期間：共変量の期間平均・SD を受け取る。

**共変量は日 Encoder だけに入るわけではない。**<br>
日ごとの情報と、期間全体に要約された情報を区別する。

</div>
</div>

<!--
質疑用。Sは1系列の中のセル集合。jごとに異なるMで集約するので、残差以外の特徴量を欠品マスクmでまとめて落とす旧式は実装と一致しない。
日内で共変量が一定の場合、日Encoderへ入る平均はその日の値、SDはepsilon込みで厳密には0ではなく0.001。時間帯Encoderと全期間Encoderも、日次共変量の期間平均・SDを受け取る。よって「割引情報はz_aにしか乗らない」という旧ノートは不正確。
一方、日ごとの割引の配置は時間帯Encoderで平均される。交互作用への入力は日潜在と時間帯潜在であり、セルの入力特徴を直接再投入しない。日 Encoder は日ごとに同じ MLP を適用するので、日の順序は曜日の周期特徴 ψ_d を通してしか入らない。
平均・SDが同じ入力の違いは、この集約だけでは区別できない。この情報圧縮はモデルの制約でもある。
出典：src/decoupled_ts/retail_models.py の GlobalEncoder, DayEncoder, HourEncoder。
-->

---

# <span class="sec">Appendix</span>Encoder の構造と潜在表現の形

<div class="cap text-left mb-2">以下は全 MLP 版（2-Exp-45）の構造。主結果（2-Exp-40）は日 Encoder に GRU を含む。</div>

<div class="text-sm appendix notation">

$E_g,E_a,E_t,E_u$ は別の MLP。潜在次元は $L_g=L_a=L_t=10,\ L_u=8$。各 Encoder 内で重みを共有する。

| 成分 | Encoder が受け取るもの | ネットワーク | 系列 $i$ の潜在表現 |
| --- | --- | --- | --- |
| 全期間 | $\boldsymbol\eta_i(S_g)\in\mathbb R^{26}$ | Linear(26→160) → ReLU → Linear(160→10) | $\mathbf z_{g,i}\in\mathbb R^{10}$ |
| 日 | $\boldsymbol\eta_i(S_{a,d})\in\mathbb R^{26}$（日ごと） | Linear(26→160) → ReLU → Linear(160→10) | $\mathbf Z_{a,i}\in\mathbb R^{28\times10}$ |
| 時間帯 | $\boldsymbol\eta_i(S_{t,h})\in\mathbb R^{26}$ | Linear(26→160) → ReLU → Linear(160→10) | $\mathbf Z_{t,i}\in\mathbb R^{24\times10}$ |
| 交互作用 | $[\mathbf z_{a,i,d};\mathbf z_{t,i,h}]\in\mathbb R^{20}$ | Linear(20→160) → ReLU → Linear(160→8) | $\mathbf Z_{u,i}\in\mathbb R^{28\times24\times8}$ |

</div>

<div class="grid grid-cols-2 gap-6 text-sm appendix-math notation mt-4">
<div>

**Encoder の中身（$k\in\{g,a,t\}$ で共通の形）**

$$\mathbf p=\mathrm{ReLU}\!\left(W_k^{\rm in}\boldsymbol\eta_i(S)+\mathbf b_k^{\rm in}\right)$$
$$E_k(\boldsymbol\eta_i(S))=W_k^{\rm out}\mathbf p+\mathbf b_k^{\rm out}$$

$\mathbf p\in\mathbb R^{160}$。$W^{\rm in}\in\mathbb R^{160\times26}$、$W^{\rm out}\in\mathbb R^{L_k\times160}$。$\mathbf b^{\rm in}\in\mathbb R^{160},\mathbf b^{\rm out}\in\mathbb R^{L_k}$ は学習するバイアス（基準値 $b_i$ とは別）。日 Encoder は $S_{a,d}$ を日ごとに、時間帯 Encoder は $S_{t,h}$ を時間帯ごとに、同じ重みで処理する。

</div>
<div>

**各範囲の特徴から潜在表現へ**

$$\mathbf z_{g,i}=E_g(\boldsymbol\eta_i(S_g))$$
$$\mathbf z_{a,i,d}=E_a(\boldsymbol\eta_i(S_{a,d})),\quad\mathbf z_{t,i,h}=E_t(\boldsymbol\eta_i(S_{t,h}))$$
$$\mathbf z_{u,i,d,h}=E_u([\mathbf z_{a,i,d};\mathbf z_{t,i,h}])$$

$\mathbf Z_a$ の第 $d$ 行が $\mathbf z_{a,i,d}^{\top}$、$\mathbf Z_t$ の第 $h$ 行が $\mathbf z_{t,i,h}^{\top}$。$\mathbf Z_u$ はセルごとの潜在ベクトルを並べたもの。

**日単位の出力でも、潜在の各次元の意味は固定されない。**

</div>
</div>

<!--
質疑用。式は全 MLP 構成（日 Encoder も Linear–ReLU–Linear）で書いている。MLPにDropoutはない。Wとバイアスはすべて学習する。曜日や天気など各変数が潜在の特定次元に対応する保証はない。
【出所の注意】リポジトリの DayEncoder（retail_models.py）は Linear–ReLU–GRU(160)–Linear で、主表 2-Exp-40 の数値はその構成。全 MLP は 2-Exp-45（PR #51、0.04780 ± 0.00077）で同等だったため、発表では MLP に統一して説明する。GRU 構成について聞かれたら「日の列を順に読む版も試したが精度は同等で、簡単な方を採用」と答える。
潜在の形はバッチ軸を省略したもの。バッチBを付けると全期間B×10、日B×28×10、時間帯B×24×10、交互作用B×28×24×8。
実装名はz_global, z_day, z_hour, z_interaction。式のg,a,t,uに対応する。E_uはInteractionEncoder、次ページのf_uはスカラーを出すinteraction_headであり別の関数。
出典：src/decoupled_ts/retail_models.py、configs/2-Exp-40_jima_main_results_freshretailnet.json。
-->

---

# <span class="sec">Appendix</span>Decoder と中心化：生出力と最終成分を区別する

<div class="grid grid-cols-2 gap-6 text-sm appendix-math notation">
<div>

**成分別 Decoder $f_k:\mathbb R^{L_k}\to\mathbb R$**

$k\in\{g,a,t,u\}$。各 $f_k$ は別の重みを持つ。<br>
Linear($L_k$→160) → ReLU → Dropout(0.1) → Linear(160→1)

$$\hat g_i=f_g(\mathbf z_{g,i}),\qquad\tilde a_{i,d}=f_a(\mathbf z_{a,i,d})$$
$$\tilde t_{i,h}=f_t(\mathbf z_{t,i,h}),\qquad\tilde u_{i,d,h}=f_u(\mathbf z_{u,i,d,h})$$

**中心化後の成分を加算**

$$\hat r_{i,d,h}=\hat g_i+\hat a_{i,d}+\hat t_{i,h}+\hat u_{i,d,h}$$
$$\hat y_{i,d,h}=b_i+\hat r_{i,d,h}$$

| 成分 | スカラー出力の共有範囲 |
| --- | --- |
| $\hat g_i$ | 全 $D\times H$ セル |
| $\hat a_{i,d}$ | 同じ日 $d$ の全時間帯 |
| $\hat t_{i,h}$ | 同じ時間帯 $h$ の全日 |
| $\hat u_{i,d,h}$ | そのセル |

</div>
<div>

**全格子上で平均 0 にする（マスクを使わない）**

$$\hat a_{i,d}=\tilde a_{i,d}-\frac1D\sum_{d'}\tilde a_{i,d'}$$
$$\hat t_{i,h}=\tilde t_{i,h}-\frac1H\sum_{h'}\tilde t_{i,h'}$$
$$\begin{aligned}\hat u_{i,d,h}={}&\tilde u_{i,d,h}-\frac1D\sum_{d'}\tilde u_{i,d',h}\\&-\frac1H\sum_{h'}\tilde u_{i,d,h'}+\frac1{DH}\sum_{d',h'}\tilde u_{i,d',h'}\end{aligned}$$

$d',h'$ は総和用の添字。$\hat g_i$ は中心化しない。

$$\sum_d\hat a_{i,d}=0,\qquad\sum_h\hat t_{i,h}=0$$
$$\sum_d\hat u_{i,d,h}=0\ (\forall h),\quad\sum_h\hat u_{i,d,h}=0\ (\forall d)$$

したがって $\frac1{DH}\sum_{d,h}\hat r_{i,d,h}=\hat g_i$。<br>
**固定した推定面の内訳を定める制約**であり、潜在次元の意味や観測セル上の直交性を保証しない。

</div>
</div>

<!--
質疑用。旧記法ではhat a=f_a(z_a)と書いた後、同じhat aを上書きしていた。今回、tildeを中心化前、hatを中心化後に分けて、式を代入操作ではなく定義として読めるようにした。
交互作用の二重中心化は、実装で日方向平均を引き、続いて時間帯方向平均を引く処理と同じ。各平均を別々に引くだけでは全体平均を二重に引くため、展開形では全体平均を一度足し戻す。
実装は除いた平均をgに自動で移しているわけではない。中心化した出力の和を学習する中でgが水準を担当する。中心化前後で同じ和を保存する後処理ではない。
全格子の等重みで成立する性質。観測マスクを掛けた部分集合では各成分の平均や交差項が0とは限らない。固定した推定面の一意分解と、欠損セルの推定値やパラメータの識別性も別。
出典：src/decoupled_ts/residual_models.py の OutputDecompositionResidualModel.decode_from_encoded。
-->

---

# <span class="sec">Appendix</span>学習損失：再構成誤差と潜在表現の共分散

<div class="grid grid-cols-2 gap-6 text-sm appendix-math notation">
<div>

**ミニバッチ $\mathcal B$（系列集合、$B=|\mathcal B|$）**

$$\mathcal L_{\mathcal B}=\mathcal L_{\rm rec}+\lambda\mathcal L_{\rm cov},\qquad\lambda=0.01$$
$$\mathcal L_{\rm rec}=\frac{\sum_{i\in\mathcal B}\sum_{d,h}m_{i,d,h}|r_{i,d,h}-\hat r_{i,d,h}|}{\max(\sum_{i\in\mathcal B}\sum_{d,h}m_{i,d,h},1)}$$

欠品セルを除いたセル単位の平均。系列ごとに MAE を平均する式とは異なる。

**系列ごとに要約する潜在ベクトル**

$$\bar{\mathbf z}_{g,i}=\mathbf z_{g,i}$$
$$\bar{\mathbf z}_{a,i}=\frac1D\sum_d\mathbf z_{a,i,d},\qquad\bar{\mathbf z}_{t,i}=\frac1H\sum_h\mathbf z_{t,i,h}$$

この平均は全日・全時間帯で取り、観測マスクを使わない。対象は **$g,a,t$ の 3 ブロック**。交互作用 $u$ はこのペナルティに含めない。

</div>
<div>

**バッチ内で系列間の共分散を計算**

$$\boldsymbol\nu_k=\frac1B\sum_{i\in\mathcal B}\bar{\mathbf z}_{k,i},\qquad k\in\{g,a,t\}$$
$$\mathbf V_{kl}=\frac{\sum_{i\in\mathcal B}(\bar{\mathbf z}_{k,i}-\boldsymbol\nu_k)(\bar{\mathbf z}_{l,i}-\boldsymbol\nu_l)^\top}{\max(B-1,1)}$$

$\mathbf V_{kl}\in\mathbb R^{L_k\times L_l}$ は交差共分散行列。

$$\mathcal P=\{(g,a),(g,t),(a,t)\}$$
$$\mathcal L_{\rm cov}=\sum_{(k,l)\in\mathcal P}\frac{\|\mathbf V_{kl}\|_F^2}{L_kL_l}$$

$\|A\|_F^2=\sum_{p,q}A_{p,q}^2$：全要素の二乗和。<br>
$L_kL_l$ で割るため、各共分散行列の二乗要素平均を足す。

**出力中心化と、潜在の共分散ペナルティは別。**<br>
前者は恒等的な制約、後者は学習時の罰則。無相関や統計的独立を厳密に保証するものではない。

</div>
</div>

<!--
質疑用。covariance_penaltyは潜在を系列ごとに平均し、バッチ内で列平均を引いた後、a.T @ b / max(B-1,1) を計算する。各共分散の二乗要素平均を3対について足す。標準偏差で割らないため、相関ペナルティとは異なる。
主設定ではバッチ128。residual_bias_weight、series_residual_bias_weight、component_constraint_weightは0、swap_regularizationも無効。AdamWのweight decayは最適化設定であり、ここに別のデータ損失として追加していない。
潜在zそのものを出力と同じ方向で中心化する操作ではない。出力の役割を定める中心化と、潜在間の線形共変動を抑える罰則を混同しない。
出典：src/decoupled_ts/residual_experiments.py の residual_loss、residual_models.py の residual_decouple_penalty、retail_models.py の covariance_penalty、2-Exp-40のloss設定。
-->

---

# <span class="sec">Appendix</span>評価指標：誤差・分散比・成分除去

<div class="grid grid-cols-2 gap-6 text-sm appendix-math notation">
<div>

**評価するセル集合を固定**

$$\Omega=\{(i,d,h):i\in\mathcal I_{\rm eval},\ m_{i,d,h}=1\}$$

$\mathcal I_{\rm eval}$：評価系列の集合。$\boldsymbol r,\hat{\boldsymbol r}\in\mathbb R^{|\Omega|}$ は同じ順序で残差を並べたベクトル。

**残差予測ベクトル $\boldsymbol p$ に対する MAE**

$$\ell_\Omega(\boldsymbol p)=\frac1{|\Omega|}\sum_{n=1}^{|\Omega|}|r_n-p_n|$$

主実験では $\hat y=b+\hat r$ なので、$\ell_\Omega(\hat{\boldsymbol r})$ は売上の MAE と一致する。

**残差 Top10 MAE**

$|r|$ の観測セル上の 90% 分位点以上を選び、その集合で同じ MAE を計算。同値を含むため、セル数が厳密に 10% とは限らない。

**成分を抜いたときの変化**（再学習なし）

$$\Delta_k=\ell_\Omega(\hat{\boldsymbol r}-\hat{\boldsymbol c}_k)-\ell_\Omega(\hat{\boldsymbol r})$$

$\Delta_k>0$：除去すると悪化。$\hat{\boldsymbol c}_k$ は右欄で定義。

</div>
<div>

**成分を全セルへ展開し、$\Omega$ 上に並べる**

$$\begin{aligned}\hat c_{g,i,d,h}&=\hat g_i,&\hat c_{a,i,d,h}&=\hat a_{i,d},\\\hat c_{t,i,d,h}&=\hat t_{i,h},&\hat c_{u,i,d,h}&=\hat u_{i,d,h}\end{aligned}$$

$\hat{\boldsymbol c}_k\in\mathbb R^{|\Omega|}$、$k\in\{g,a,t,u\}$。以下の分散・共分散はすべて $\Omega$ 上、同じ正規化で計算。

$$s_k=\frac{\operatorname{Var}_\Omega(\hat{\boldsymbol c}_k)}{\operatorname{Var}_\Omega(\boldsymbol r)},\quad q_{kl}=\frac{2\operatorname{Cov}_\Omega(\hat{\boldsymbol c}_k,\hat{\boldsymbol c}_l)}{\operatorname{Var}_\Omega(\boldsymbol r)}$$
$$\sum_k s_k+\sum_{k<l}q_{kl}=\frac{\operatorname{Var}_\Omega(\hat{\boldsymbol r})}{\operatorname{Var}_\Omega(\boldsymbol r)}$$

$k<l$ は $(g,a,t,u)$ の順で重複しない全 6 対。

$$R^2=1-\frac{\sum_n(r_n-\hat r_n)^2}{\sum_n(r_n-\bar r_\Omega)^2},\quad\bar r_\Omega=\frac1{|\Omega|}\sum_n r_n$$

**分散比の合計は $R^2$ ではない。** 全格子上の中心化も、$\Omega$ 上の交差項ゼロを保証しない。分母の分散が正の場合の定義。

</div>
</div>

<!--
質疑用。MAEの引数が予測値か真値か不明だった旧Delta式を、真の残差を固定した関数ell_Omegaで定義し直した。成分ごとに異なる元の形を、同じセル集合上のベクトルへ展開してから分散や相関を計算する。
Top10はresidual_experiments.pyのnp.quantile(abs_residual,0.9)以上のセル。系列ごとに上位を選ぶのではなく、評価対象の観測セルをまとめて選ぶ。
分散比と交差項の恒等式は加法分解から従う。全格子内では出力成分の中心化による直交性があるが、欠品除外後に同じことを主張しない。全期間成分gも系列間では変動する。
出典：src/decoupled_ts/residual_experiments.py の評価処理、2-Exp-44の成分診断。これらは同期間再構成の指標で、将来予測の性能を直接表すものではない。
-->

---

# <span class="sec">Appendix</span>成分回復：相関と直交整合の記号

<div class="grid grid-cols-2 gap-6 text-sm appendix-math notation">
<div>

**合成データの真の成分との比較**

前ページと同じ方法で、真の成分 $\boldsymbol c_k$ と推定成分 $\hat{\boldsymbol c}_k$ を観測セル集合 $\Omega$ 上に並べる。

$$\rho_k=\operatorname{corr}(\boldsymbol c_k,\hat{\boldsymbol c}_k),\qquad k\in\{g,a,t,u\}$$

$\operatorname{corr}$：Pearson 相関。成分ベクトルの分散が正の場合に定義。中心化ありの結果は回転なしで比較する。

**列中心化した行列を別の記号で定義**

$$\mathbf C=[\boldsymbol c_g\ \boldsymbol c_a\ \boldsymbol c_t\ \boldsymbol c_u],\quad\hat{\mathbf C}=[\hat{\boldsymbol c}_g\ \hat{\boldsymbol c}_a\ \hat{\boldsymbol c}_t\ \hat{\boldsymbol c}_u]$$
$$\mathbf J=I_n-\frac1n\mathbf1_n\mathbf1_n^\top,\qquad n=|\Omega|$$
$$\mathbf A=\mathbf J\mathbf C,\qquad\hat{\mathbf A}=\mathbf J\hat{\mathbf C}$$

$\mathbf C,\hat{\mathbf C},\mathbf A,\hat{\mathbf A}\in\mathbb R^{n\times4}$。<br>
$I_n$：単位行列、$\mathbf1_n$：全要素 1 のベクトル。$\mathbf J$ は定義上の表記で、巨大行列の実生成は不要。

</div>
<div>

**直交 Procrustes 整合（列中心化の場合の定義）**

$$\hat{\mathbf A}^{\top}\mathbf A=U\Sigma V^\top\quad\text{（特異値分解）}$$
$$Q^\star\in\underset{Q^\top Q=I_4}{\arg\min}\|\hat{\mathbf A}Q-\mathbf A\|_F^2,\qquad Q^\star=UV^\top$$

$U,V,Q^\star\in\mathbb R^{4\times4}$、$\Sigma$：特異値を並べた対角行列。$\|\cdot\|_F$ は Frobenius ノルム。

$$\rho_k^{\rm rot}=\operatorname{corr}\bigl((\hat{\mathbf A}Q^\star)_{:,k},\mathbf A_{:,k}\bigr)$$

$(:,k)$ は $(g,a,t,u)$ に対応する第 $k$ 列を表す。

- 真値を使った事後の診断。直交変換には反転も含む。
- 全列の二乗誤差を最小化する。各成分の相関の最大化や、その上限を保証しない。
- 尺度差や任意の線形混合を除去するものではない。

<div class="cap text-left mt-2">図の再解析で列標準化も行ったかは未照合。上式は列中心化のみの場合を明示したもの。</div>

</div>
</div>

<!--
質疑用。中心化前の成分行列Cと、列中心化したAを別記号にする。入力チャネル数はF、成分行列は太字Cで区別。R^2との混同を避け、直交整合の行列はQとする。
SVDの向きをhat A^T A=U Sigma V^Tとした場合、右から掛ける最適直交行列の1つはUV^T。最適解が一意とは限らないのでargminへの所属として書いた。det Q=1は課していないため反転も含む。
元スライドのProcrustes再解析の数値は保持するが、当該再解析スクリプトの列標準化有無はこのローカルソースでは確認できていない。列のSDで割る場合には、Aとhat Aをさらに標準化した行列に置き換えて解く必要があり、整合行列は一般に変わる。図の手順とこの定義を同一と断言しない。
-->

---

# <span class="sec">Appendix</span>学習予算による変化

<div class="flex justify-center mt-4">
  <div class="card" style="width:560px">
    <h3>中心化の改善幅は学習予算に依存</h3>
    <div class="abl-t text-sm mt-3"><table><tbody>
      <tr><th>corrected MAE</th><th>60 / 8</th><th>240 / 24</th></tr>
      <tr><td>経験的 ANOVA</td><td>0.05443</td><td>0.05443</td></tr>
      <tr><td>中心化なし</td><td>0.05422</td><td>0.04832</td></tr>
      <tr><td>中心化あり</td><td><b>0.04828</b></td><td><b>0.04679</b></td></tr>
      <tr><td>あり−なし</td><td>−0.00594</td><td>−0.00153</td></tr>
    </tbody></table></div>
    <p class="text-sm mt-3">各列は最大epoch / patience。中心化ありは5 seed全勝を維持するが、差は縮む。</p>
    <p class="text-sm mt-2"><b>240 epochでも未収束</b>（中心化あり4/5 runが上限）。収束後の優劣は確定していない。</p>
    <p class="text-sm mt-2">学習予算で動く所見（日と交互作用の分散比の順序、性能差の大きさ）は主張に使わない。担当範囲の固定は中心化の帰結で、予算に依らない。</p>
  </div>
</div>

<div class="cap mt-4">2-Exp-40 / 48（PR #55）、5 seed。</div>

<!--
質疑用。学習量が揃っても収束が保証されるわけではない。主結果は最大60/patience8の早期停止時点の値。
https://github.com/ari-show/decoupling/pull/55
Encoder 構成：主表は日 GRU（0.04828 ± 0.00032）。日 MLP は 0.04780 ± 0.00077（2-Exp-45、PR #51）で同等、軽量化の候補。本編では GRU/MLP の話はしない。聞かれたら「成分ごとの小さな NN で、構成の違いは精度に効かなかった」と答える。
中心化により精度が常に11%改善する、とは言わない。
-->

---

# <span class="sec">Appendix</span>追加検証：成分差し替えと日マスク学習

<div class="grid grid-cols-2 gap-5 mt-4">
  <div class="card" style="border-color:#6250d6">
    <h3>日潜在を差し替えたときの軸間漏れ</h3>
    <div class="abl-t text-sm mt-3"><table><tbody>
      <tr><th>漏れ比</th><th>全格子</th><th>観測セル</th></tr>
      <tr><td>中心化あり</td><td><b>6.5×10⁻⁷</b></td><td><b>0.165</b></td></tr>
      <tr><td>中心化なし</td><td>0.568</td><td>0.543</td></tr>
      <tr><td>潜在分割のみ</td><td>0.400</td><td>0.397</td></tr>
    </tbody></table></div>
    <p class="text-sm mt-3">全格子での漏れほぼゼロは、中心化した出力構造の帰結。実装と比較手法との差を確認した。</p>
    <p class="text-sm mt-2"><b>欠品を除いた観測セル上では漏れが残る。</b> 潜在次元の意味や因果的分離まで保証しない。</p>
  </div>
  <div class="card" style="border-color:#008300">
    <h3>日マスク学習の効果は用途によって異なる</h3>
    <div class="abl-t text-sm mt-3"><table><tbody>
      <tr><th>診断</th><th>2-Exp-49の結果</th></tr>
      <tr><td>短履歴の時間帯推定</td><td>7日で相関0.551<br>経験＋最適縮小0.548</td></tr>
      <tr><td>店舗間移植の強化</td><td>支持されず</td></tr>
      <tr><td>隠した日の day 相関</td><td>0.012 → 0.137<br>事前閾値0.30未達</td></tr>
      <tr><td>再構成MAEの退行</td><td>M1 +5.35%<br>tail7 +2.39%</td></tr>
    </tbody></table></div>
    <p class="text-sm mt-3">短履歴での改善と全窓の精度を両立する条件を検討する。未知日への一般化は未達。</p>
  </div>
</div>

<div class="cap mt-4">左：2-Exp-50（PR #56）、5 seed　右：2-Exp-49（PR #57）、5 seed。比較条件は実験ごとに異なる。</div>

<!--
質疑用。主表と別条件の追加検証。左の漏れ比は時間帯プロファイルの変化量／日プロファイルの変化量として実験側で定義した指標。全格子と観測セルで集計範囲が異なる。
https://github.com/ari-show/decoupling/pull/56
右のM1はrandom_days、tail7は末尾7日マスク。退行の許容上限は3%。隠した日のdayの0.012は2-Exp-49の対照M0で、旧checkpoint再解析の−0.014とは別の値。
短履歴での対照M0はマスクなしで学習しているため、差には分布外入力の不利の解消も含む。学習マスクの効果を独立に同定したとは言わない。H1は実験の事前基準で支持、H2は棄却、H3は方向のみ。
https://github.com/ari-show/decoupling/pull/57
-->

---

# <span class="sec">Appendix</span>探索解析：潜在情報と店舗をまたいだ再利用

<div class="grid grid-cols-2 gap-5 mt-4">
  <div class="card">
    <h3>店舗・商品 ID と潜在表現の関連</h3>
    <div class="abl-t text-sm mt-3"><table><tbody>
      <tr><th>系列間の分散</th><th>店舗で説明</th><th>残りを商品で説明</th></tr>
      <tr><td>z<sub>g</sub></td><td>75.5%</td><td>15.6%</td></tr>
      <tr><td>z<sub>a</sub> の平均</td><td>10.3%</td><td>62.5%</td></tr>
      <tr><td>z<sub>u</sub> の平均</td><td>25.5%</td><td>56.2%</td></tr>
    </tbody></table></div>
    <p class="text-sm mt-3">潜在ブロックごとにIDとの関連は異なる。ただし、店舗と商品の因果的な要因分離を示すものではない。</p>
    <p class="text-sm mt-2">z<sub>g</sub> に店舗情報が含まれても、出力スカラー g が店舗の需要水準を表すとは限らない。</p>
  </div>
  <div class="card" style="border-color:#6250d6">
    <h3>他店舗の同じ商品から残差格子を復元</h3>
    <div class="abl-t text-sm mt-3"><table><tbody>
      <tr><th>方法</th><th>残差MAE</th><th>対経験法の勝率</th></tr>
      <tr><td>経験プロファイル加算</td><td>0.0628</td><td>—</td></tr>
      <tr><td>潜在・中心化あり</td><td><b>0.0566</b></td><td>97.2%</td></tr>
      <tr><td>潜在・中心化なし</td><td>0.0582</td><td>74.6%</td></tr>
    </tbody></table></div>
    <p class="text-sm mt-3">同じ情報源を用いたleave-one-series-outの探索評価で、表現の再利用可能性を示唆。</p>
    <p class="text-sm mt-2">利得を中心化やDecoderの非線形性だけに帰属するには、要因を分けた比較が必要。</p>
  </div>
</div>

<div class="cap mt-4">評価1,500系列、5 seed。IDとの関連と移植の精度は別の診断であり、一方から他方の原因を確定しない。</div>

<!--
質疑用・探索結果。元スライドの保存済みcheckpoint再解析の数値を保持。
左：2-Exp-44 / 35、stage1〜8.py、out-of-fold。24店舗・348商品を含む疎なクロス構造で、全組合せがあるわけではない。
右：stage15〜19.py、fig3.py。潜在をどう平均・合成したかと、経験法のlevel+day+hourの作り方は原解析に依存する。
この編集では原stageスクリプトと全出力の再計算は行っていない。主発表の結論をこの探索表だけに依存させない。PR #57は移植診断の後続検証であり、マスク学習による移植性強化は支持しなかった。
-->

---

# <span class="sec">Appendix</span>探索図：量と形、イベントが動かす時間帯、店舗の午後ピーク

<div class="grid grid-cols-3 gap-4 mt-3">
  <div>
    <img src="/figures/crop_amount_vs_shape.png" alt="量（日成分）と形（交互作用の RMS）の散布図" class="w-full rounded border" style="border-color:#d9d9d4" />
    <div class="cap text-left mt-1"><b>量 vs 形</b>（系列 × 日、評価 1,500 系列）。横：日成分、縦：その日の交互作用の RMS。赤：割引の深さ &gt; 0.15。考察 (1/3) の 2 軸をそのまま描いたもの。</div>
  </div>
  <div>
    <img src="/figures/crop_event_hours.png" alt="イベント日と他の日の交互作用の差" class="w-full rounded border" style="border-color:#d9d9d4" />
    <div class="cap text-left mt-1"><b>イベントが動かす時間帯</b>。イベント日と他の日の交互作用の差。休日（青）は大きく、雨・割引・販促は<b>同じ形を弱く呼び出す</b>（相互相関 0.97 以上）。</div>
  </div>
  <div>
    <img src="/figures/crop_store_peaks.png" alt="店舗平均の正規化残差プロファイル" class="w-full rounded border" style="border-color:#d9d9d4" />
    <div class="cap text-left mt-1"><b>店舗の午後ピーク</b>。店舗平均の正規化残差プロファイル。赤：午後ピーク店舗（都市 5・15 の 5 店舗）。考察 (2/3) PC3 に対応する店舗側の軸。形の分散に占める店舗差は 8%。</div>
  </div>
</div>

<div class="card mt-3 text-sm" style="border-color:#b4231f">
  <b>振幅の「商品」帰属には売上水準の効果が含まれる</b>：商品の日内振幅は平均売上とほぼ比例（約 98% が水準効果）。水準で割った相対振幅でも商品側に帰属するが R² は 0.21。PC1「ピークの高さは商品の性質」は水準込みの言い方で、水準を除いた商品固有の性質はその一部。
</div>

<div class="cap mt-2">左・中：2-Exp-44 seed 17（exploratory）　右・注意書き：潜在の店舗軸・商品軸分解（5 seed、評価 1,500 系列）</div>

<!--
質疑用。元図は public/figures/exp44_seed17_amount_shape.png（A・B・C 週周期・D rank-1 形状）と public/figures/latent_store_product_axes.png（a 潜在の店舗/商品帰属、b 振幅は商品・タイミングは店舗、c 店舗の午後ピーク、d 振幅と水準）。
左図の V 字は、|量| が大きい日ほど形も大きいこと。量と形は独立ではなく、大きさは連動する。考察 (1/4) で言っているのは「動かせるものが違う」という役割の排他性で、大きさの独立ではない。
中図：イベントごとに違う時間帯パターンが出るのではなく、共通の 1 つの形（朝 9 時台と 15〜17 時が上がり深夜が下がる）をイベントが強弱で呼び出している。
右図 (b) の「タイミングは店舗の性質」と、PCA の PC2（朝型⇔夕方型）が商品 0.32／店舗 0.11 で商品寄りなのは一見食い違う。(b) の shape は振幅で割った形の全体、PC2 は分散 6% の 1 軸なので、同じ量ではない。聞かれたら「形の軸のうち午後の山（PC3）が店舗側」と答える。
(d) の注意：振幅は水準にほぼ比例するので、PC1 の商品帰属 0.86 は水準効果込み。
-->





---

# <span class="sec">Appendix</span>量・形の定義と、共変量との相関（全表）

<div class="grid gap-4 mt-2" style="grid-template-columns: 1fr 1.05fr">
  <div>
    <QuantShapeFigure />
    <div class="cap text-left mt-2">量 ＝ その日の日成分（24 時間帯で同じ値）　形 ＝ その日の交互作用の RMS。<br>中心化があるから、総量と配分を別々の成分として読める。</div>
  </div>
  <div class="card" style="border-color:#eb6834">
    <h3>割引は形に、休日は量に効く。実測のみでも同じ向き</h3>
    <div class="abl-t text-sm mt-1"><table><tbody>
      <tr><th rowspan="2">共変量との相関</th><th colspan="2" style="text-align:center">提案モデル</th><th colspan="2" style="text-align:center;color:#52514e">実測のみ</th></tr>
      <tr><th>量</th><th>形</th><th style="color:#52514e">量</th><th style="color:#52514e">形</th></tr>
      <tr><td>割引の深さ</td><td>+0.10</td><td><b>+0.21</b></td><td style="color:#52514e">+0.12</td><td style="color:#52514e"><b>+0.38</b></td></tr>
      <tr><td>休日</td><td><b>+0.25</b></td><td>+0.10</td><td style="color:#52514e"><b>+0.16</b></td><td style="color:#52514e">+0.10</td></tr>
      <tr><td>販促フラグ</td><td>+0.10</td><td>+0.01</td><td style="color:#52514e">+0.09</td><td style="color:#52514e">+0.01</td></tr>
      <tr><td>降水量</td><td>+0.14</td><td>+0.05</td><td style="color:#52514e">+0.13</td><td style="color:#52514e">+0.06</td></tr>
    </tbody></table></div>
    <p class="text-sm mt-2">向きは 4 つとも実測と一致。休日×量は 0.16 → 0.25 と鮮明になる。割引×形の実測 0.38 には毎日同じ基本の形（時間帯成分）が混ざり、モデルの 0.21 はそれを除いた日固有の配分の動き。</p>
    <div class="cap text-left mt-1">評価 1,500 系列 × 28 日。240 epoch・5 seed 平均、5 seed すべて同じ向き。60 epoch でも同順。実測＝生の残差の日平均と、日平均を引いた RMS。割引の深さ＝1−価格比</div>
  </div>
</div>

<!--
質疑用。考察 (1/3) の全表と、量・形の定義の模式図。
出典：ユーザー提供メモ（2026-10-23）。量 = day_component[i,d,0]、形 = √mean_h u[i,d,h]²、day_covariates.npy。【要照合】run ID。60 epoch でも同順（0.092/0.214、0.239/0.063）。
-->
---

# <span class="sec">Appendix</span>量・形と共変量の相関：何と何を突き合わせているか

<div class="grid gap-4 mt-1" style="grid-template-columns: 1.15fr 1fr">
  <div>
    <QuantShapeCovFigure />
    <div class="cap text-left mt-1">模式図：1 系列の 28 日分。棒＝提案モデルの成分、灰点＝実測のみ（生の残差の日平均と、日平均を引いた RMS）</div>
  </div>
  <div class="covx">
    <div class="card" style="border-color:#6b6b6b">
      <h3>1 点 ＝（系列, 日）</h3>
      <p>評価 1,500 系列 × 28 日 = 42,000 点。各点に<b>その日の</b>共変量（休日、割引の深さ…）と、その日の<b>量</b>・<b>形</b>がある。ずらしは無し。相関はこの 42,000 点でのピアソン相関。</p>
    </div>
    <div class="card mt-2" style="border-color:#eb6834">
      <h3>読み方</h3>
      <p><b style="color:#eb6834">休日×量 +0.25</b>：休日の日は、その日の総量の持ち上がりが大きい。</p>
      <p><b style="color:#008300">割引×形 +0.21</b>：割引が深い日は、時間帯の間の配分の動きが大きい（総量とは別に）。</p>
    </div>
    <div class="card mt-2" style="border-color:#6250d6">
      <h3>「雑音を落とす」の中身</h3>
      <p>実測の日平均には<b>セル固有の揺れ</b>が残り、実測の RMS には<b>毎日同じ基本の形（時間帯成分）</b>も混ざる。モデルの量・形はどちらも除いた値。向きは同じまま、休日×量は 0.16 → 0.25 に上がる。</p>
    </div>
  </div>
</div>

<style>
.covx { font-size: 0.8rem; line-height: 1.4; }
.covx .card { padding: 0.4rem 0.7rem; }
.covx h3 { font-size: 0.9rem; margin-bottom: 0.15rem; }
</style>

<!--
質疑用。考察 (1/3) の相関表の計算の仕方。
- 量 = day_component[i,d,0]（24 時間帯で同じ値なので 1 日 1 つ）、形 = √mean_h u[i,d,h]²。
- 共変量は day_covariates（割引の深さ = 1−価格比、休日フラグ、販促フラグ、降水量）。全て (i,d) の値で、ラグ無し。
- 実測のみ：量_raw = mean_h r[i,d,h]、形_raw = √mean_h (r[i,d,h] − mean_h r)²。形_raw には時間帯成分 t_h が毎日混ざる（日によらない基本の形）ので、割引×形は実測 0.38 > モデル 0.21。モデル側は日固有の配分の動きだけ。
- 休日×量 0.16 → 0.25：日平均に残るセル固有の揺れを日成分が落としている（日成分は実測の日ごとのずれと相関 0.91〜0.95、振幅は約 1/2）。
【要照合】run ID、系列数と日数（評価 1,500 × 28 = 42,000 点か、欠測除外後か）。
-->

---

# <span class="sec">Appendix</span>量・形と共変量：実データの 1 系列（28 日）

<div class="flex justify-center mt-1"><img src="/figures/quant_shape_cov_real_s86.png" style="height:400px" /></div>
<div class="cap mt-1">店舗 1 × 商品 58（評価系列 #86）。棒＝提案モデルの日成分（量）と交互作用の RMS（形）、灰点＝実測のみ。割引の深さ＝1−価格比。2-Exp-35 seed 17（系列平均基準、主結果と同じ構成だが別 run）</div>

<!--
質疑用。考察 (1/3) の模式図と同じ構成を実データで描いたもの。
- 出所：runs/2-Exp-35_freshretailnet_component_tsne/series_mean_all/seed_17/output_decomp_centered（day_component / interaction_component / residual）＋ data/freshretailnet/cache の評価 100 系列キャッシュ（static_ids で順序一致を確認済み）。
- この run・評価 1,500 系列での相関（量/形、seed 17/23/31）：休日 +0.34/+0.05、+0.26/+0.04、+0.27/+0.05。割引の深さ +0.13/+0.22、+0.10/+0.23、+0.12/+0.22。
  → 本編の表（2-Exp-44、240 epoch：休日 +0.25/+0.10、割引 +0.10/+0.21）と同じ向き・同じ順序。ローカル run でも再現する。
  実測のみ（1,500 系列）：休日 +0.10/+0.09、割引 −0.26/+0.38。割引×形 +0.38 は本編の表と一致。休日×量（本編 +0.16）と割引×量（本編 +0.12）は値が違う【要照合】：本編の「実測のみ」の量の定義（マスク扱い、観測値か残差か）を確認。
  先頭 100 系列だけで取ると割引は量 +0.20／形 +0.10 と順序が逆になる。系列を絞った相関は使わない。
- 灰点の「形」は時間帯成分（毎日同じ基本の形）を含むので、モデルの形より一桁大きい。
- 生成：doc/conference/jima2026/presen-jima2026fall/fig/quant_shape_cov_real.py --series 86 --cache data/freshretailnet/cache/eval_eval-target_d30_w24_f2_city_id_store_id-product_id_1500.pt（uv run --with matplotlib）。seed 別の図は fig/quant_shape_cov_real_s86_seed{17,23,31}.png。
-->
---

# <span class="sec">Appendix</span>時間帯成分の主成分分析：手順と数値

<div class="steps mt-1">
  <div><span class="st">見た</span>Decoder が出した時間帯成分。1,479 系列 × 24 時間帯（2-Exp-44）</div>
  <div><span class="st">した</span>平均カーブを引いて主成分分析。座標を店舗 ID・商品 ID で帰属（out-of-fold R²）。5 seed で軸を比較</div>
  <div><span class="st">出た</span>3 軸で分散の 91%（82 / 6 / 3%）。軸は 5 seed すべてで 6° 以内、座標の相関 0.95〜0.999 で一致</div>
  <div><span class="st" style="background:#b4231f">言える</span>時間帯成分は<b>名前のつく 3 つの数で書ける形</b>。真値のない実データでも、学習のたび同じ成分に落ちる</div>
</div>

<div class="grid grid-cols-3 gap-3 mt-3 text-sm">
  <div class="pcs" style="border-color:#6250d6"><div class="own" style="color:#6250d6">PC1 ピークの高さ　帰属 R²：商品 0.86 ／ 店舗 −0.03</div>系列間の違いは<b>いつ売れるかではなく、ピークの高さ</b>。ただし高さは売上水準にほぼ比例（水準を除くと商品 R² 0.21）。荷重は平均プロファイルとの相関 +0.98。</div>
  <div class="pcs" style="border-color:#6250d6"><div class="own" style="color:#6250d6">PC2 朝型 ⇔ 夕方型　帰属 R²：商品 0.32 ／ 店舗 0.11</div>ピークの<b>時刻</b>の違いはここに集まるが小さい。荷重は朝(6–11時) +1.45、昼〜夕 −0.81、夜 −0.91。</div>
  <div class="pcs" style="border-color:#b4231f"><div class="own" style="color:#b4231f">PC3 午後の山の有無　帰属 R²：商品 −0.11 ／ 店舗 +0.16</div><b>店舗の性質として出る形はここだけ</b>。午後ピーク店舗の平均 +0.041、他店舗 −0.009 のずれで、店舗群として分離はしない。</div>
</div>

<div class="card text-sm mt-3" style="border-color:#6b6b6b;padding:0.4rem 0.8rem">
  <b>所有者は商品 → 店舗の階層</b>。時間帯の形は商品で共有し、店舗差は小さな補正とする設計の根拠になる（全期間成分で基準値が定まったのと同じ型）。同じデータの K-means はシルエット 0.08、seed 間 ARI 0.37〜0.89 で群に分かれず、<b>型ではなく連続な軸</b>。中央値で各カーブの 74% が 3 つの数で復元できる。
</div>

<style>
.steps { display: grid; grid-template-columns: 1fr; gap: 3px 10px; font-size: 0.88rem; }
.steps > div { line-height: 1.4; }
.steps .st { display: inline-block; background: #6250d6; color: #fff; font-weight: 700; font-size: 0.74rem; padding: 0 6px; border-radius: 4px; margin-right: 6px; vertical-align: 1px; }
.steps b { color: #b4231f; }
.pcs { border: 1.5px solid #d9d9d4; border-radius: 8px; padding: 0.3rem 0.6rem; background: #fff; line-height: 1.35; }
.pcs b { color: #b4231f; }
.pcs .own { font-size: 0.8rem; font-weight: 700; }
</style>

<!--
質疑用。考察 (2/3) の裏付け。
- 導出：X（1479 × 24）から列平均を引いて SVD。V の列が軸、s²/Σs² が分散シェア、US が座標。符号は任意。PC3 0.032 と PC4 0.018 は固有値が近く順序が入れ替わりうるが、部分空間として一致。
- PCA はモデルの一部ではなく後付けの記述道具。潜在 10 次元のうち出力が実際に使う自由度を、モデルに手を入れずに測る。
- 「3 つの型」と以前言ったのは便宜的な切り方で、実体は連続量。
- 「効く系列は観測データだけから事前に分かる」（二元配置の平方和シェアと相対改善率の相関 +0.60/+0.46/−0.70）はモデルを使わないデータ側の考察なので本編から外した（scratchpad の removed-prescreen-slide.md）。
出典：ユーザー提供メモ（2026-10-23）、~/Downloads/pca-noise.png（2026-10-24）。【要照合】run ID、系列数 1,479（評価 1,500 のうち欠落 21 の理由）。
-->
---

# <span class="sec">Appendix</span>探索図：時間帯成分の 3 軸（全体）

<div class="flex justify-center mt-1"><img src="/figures/pca_hour_axes.png" style="height:430px" /></div>
<div class="cap mt-1">上段：各軸に沿った ±2SD。下段：分散シェア、座標の帰属（店舗 ID・商品 ID、out-of-fold R²）、PC2–PC3 散布（赤：午後ピーク店舗 5 店）。2-Exp-44、1,479 系列、5 seed で軸は 6° 以内。</div>

<!--
質疑用。考察 (2/3) の実図全体。下段中央の帰属の棒で「軸が小さくなるほど所有者が商品から店舗へ移る」を示す。右下の散布は PC3 の平均が午後ピーク店舗で +0.041、他店舗で −0.009 とずれるが、群としては分離しない。
出典：~/Downloads/pca-noise.png（2026-10-24）。
-->
---

# <span class="sec">Appendix</span>全期間成分の学習値と、系列別の最適定数

<p class="lead">平均水準を持つ b に対し、<b>g は全セルへ同じ値を加える補正</b>として働く。</p>

<img src="/figures/global_component_vs_series_level.png" alt="学習済み全期間成分と、他成分を固定して系列ごとに求めた最適定数の比較" class="mx-auto mt-2" style="width:850px" />

<div class="cap mt-1">青：学習済み g（5 seed をプール）　赤：他成分を固定した系列別の最適定数（seed 17）</div>

<div class="grid grid-cols-2 gap-4 mt-3 text-sm">
  <div class="card" style="border-color:#6b6b6b">
    <b>L1 学習との関係</b><br>他成分を固定すると、最適な g は<b>残った残差の中央値</b>。平均基準からの補正には、損失関数の選択が関わる。
  </div>
  <div class="card" style="border-color:#6250d6">
    <b>読み取りの限界</b><br>この図では学習値の分布が狭い。<b>系列の忙しさを表す指標とは解釈しにくい</b>。赤との開きが未知データで埋まるかは未検証。
  </div>
</div>

<!--
質疑用（旧・考察 2/3）。
全期間成分は1系列に1つの値で、全セルへ同じ補正を加えます。系列の平均水準は基準値bが持っています。
図の青が学習済みのg、赤が日・時間帯・交互作用を固定したうえで、その評価系列のMAEを最小化する定数です。赤は評価対象の実測値から求めた診断用の比較です。予測器として使える基準ではありません。
L1損失では、この最適定数は他成分を引いた残りの中央値になります。したがって、平均基準とL1損失の組合せが、全期間成分の負の補正に関わるという解釈ができます。売上の平均と中央値の差そのものと同一ではありません。
学習値の分布は赤より狭く、系列水準の大きな違いに比べて変化が小さくなっています。このgを店舗や商品の忙しさの指標と読むのは難しいと考えます。ただし、この開きが学習不足なのか共有学習による縮小なのかは未確定で、未知データでの改善余地を直接示したものでもありません。
成分を分けることで、需要構造に加え、モデルが損失を下げるために加えた補正とその限界も見えました。

図：PR #58、commit 916bf6423fc746881af88d9fe0b5a8a9f65606b3。元図をそのまま使用。
https://github.com/ari-show/decoupling/pull/58
図の比較は青7500点（1500系列×5 seed）、赤1500点（seed17）で、ヒストグラムは密度でなく件数。棒の高さを群間で比較しない。IQRも同一seed対応比較ではないため、本文で効果量として主張しない。両側をseedごとに対応させる確認が今後必要。
赤のg*はmedian(r-a-t-u)を観測セルで計算。gの潜在z_globalに店舗情報が含まれることと、スカラー出力gが店舗水準を表すことを区別する。
-->

---

# <span class="sec">Appendix</span>全期間成分の最適定数と、解釈の条件

<p class="lead">日・時間帯・交互作用を固定したとき、g の L1 最適値は残りの中央値。</p>

$$g_i^\star=\operatorname{median}_{(d,h)\in\Omega_i}\left(r_{i,d,h}-\hat a_{i,d}-\hat t_{i,h}-\hat u_{i,d,h}\right)$$

<div class="cap">

$\Omega_i=\{(d,h):m_{i,d,h}=1\}$：系列 $i$ の観測セル集合（非空）。$g_i^\star$ は L1 最小化解の一つで、中央値が一意でない場合もある。

</div>

<div class="grid grid-cols-2 gap-5 mt-6">
  <div class="card">
    <h3>基準値と損失の組合せ</h3>
    <p class="text-sm">b は観測売上の系列平均。g は他成分を考慮した後の定数補正なので、単純な「売上中央値−平均」とは一般に一致しない。</p>
    <p class="text-sm mt-3">基準値を中央値へ変えても、残りの中央値が0になる保証はない。gが不要になるかは再学習して検証する。</p>
  </div>
  <div class="card">
    <h3>図から分かる範囲</h3>
    <p class="text-sm">PR #58の赤は評価対象の実測値から求めた最適値。青との開きは、未知データで達成できる改善量を示さない。</p>
    <p class="text-sm mt-3">学習値の分布が狭い理由は未確定。学習量、モデル容量、共有学習による縮小などを切り分ける。</p>
  </div>
</div>

<div class="msg mt-5">出力の担当範囲が定まることと、実世界の要因として解釈できることを区別する</div>

<!--
質疑用。上式は他成分を固定し、観測セルごとに等しい重みで絶対誤差を最小化する定数の解。ニューラルネットの共有パラメータと他成分を同時学習したgが、各系列のg*と等しくなる保証はない。
観測セルでの残差平均はほぼ0でも、全格子上の推定残差平均gが0になるとは限らない。中心化する集合と評価する集合も異なる。
事後にgを引く操作は学習済み出力の診断であり、gを持たないモデルの再学習と等価とは言わない。
https://github.com/ari-show/decoupling/pull/58
-->
