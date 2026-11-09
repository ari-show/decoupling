# JIMA 2026 秋季大会 発表スライド（Slidev）

## 使い方

```bash
npm install          # ~/.npm に root 所有ファイルがあり失敗する場合: npm install --cache /tmp/npmcache
npm run dev          # ブラウザでプレビュー（クリックで段階表示）
npm run build        # 静的ビルド（コンパイル確認）
```

PDF / PNG 書き出しは playwright-chromium が必要。Chromium を落とさずにローカルの Brave を使う場合:

```bash
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install --no-save playwright-chromium
npx slidev export slides.md --output ../JIMA2026秋_draft.pdf \
  --executable-path "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
```

## 構成

2026-10-24改訂：本文23枚、質疑用付録14枚（計37枚）。

- 付録25–31：記号と入力、集約の定義、Encoder構造、Decoderと中心化、学習損失、評価指標、成分回復
- 入力チャネル別マスクと損失の観測マスクを区別。中心化前はチルダ、最終成分はハットで表記する
- 主結果の日EncoderはGRU。付録27の構造表は全MLP版（2-Exp-45）であることを明記。周期特徴は暦上の曜日ではなく相対日番号の7日周期位置
- 付録32–37：学習予算、成分差し替えと日マスク、潜在情報と移植、探索図、全期間成分の解釈
- Procrustes再解析の列標準化の有無は未照合。付録の式は列中心化のみの定義であることを明記

主表のモデル構成は日GRU・時間帯MLP。全MLPの後続結果とは分けて説明する。数値と根拠の対応、図の集計条件は [evidence/README.md](evidence/README.md) を参照。

- `slides.md` … スライド本体。各スライドの `<!-- -->` に発表カンペ（時間配分つき）を入れてあるので、プレゼンターモード（`?`→`presenter`）で読める
- `components/` … 図はすべて SVG コンポーネント。`:stage="$clicks"` で段階表示
  - `ResidualGrid` … 28日×24時間帯の残差ヒートマップ（mode: r / g / a / t / u、highlight: row / col / cell）
  - `SalesChart` … 背景用の売上グラフ（観測 → 基準値 → 残差の塗り分け）
  - `DecompFigure` … r = g + a + t + u の 5 枚組
  - `GLRFigure` … Tonekaboni らの Global / Local の概念図
  - `SplitBars` / `IdentFigure` … 加法分解の非一意性（同じ合計・異なる内訳）
  - `ModelFigure` … 提案モデル全体像（Encoder の集約方向 → 潜在表現 → Decoder → 中心化 → Σ）
  - `CenterConstraintFigure` … どの方向で平均 0 にするか
  - `ResultBars` / `CorrBars` … 実データ・合成データの結果
- `src/synth.ts` … 図用の疑似残差データ（決定的）と配色
- `scripts/export-svg.mjs` … スライドで使う図を単体 SVG として `../fig/svg/` に書き出す（`npm run export:svg`、Brave が必要。別ブラウザは `BROWSER_PATH=...`）。
  図 1 枚 1 スライドの `figs.md` を一時生成 → dev サーバを Playwright で開き、純 SVG の図は CSS を属性にインライン化して抽出、HTML 混在の図（DecompFigure / IdentFigure / CenterConstraintFigure / ResultBars / StoryBar）は dom-to-svg で SVG 化する。
  HTML で組んだ構成図（問題設定の 4 共有範囲 `p5_shared_ranges`、青写真 `p10_blueprint`、オートエンコーダ構造 `p14_autoencoder`）は slides.md の該当部分をスクリプト内に写して dom-to-svg で書き出す。slides.md 側を直したら同じ変更をスクリプトにも入れる。
  段階表示は `*_stageN.svg` として別ファイル。フォントは Keynote で使える Hiragino Sans に統一してある。
  Keynote にドラッグ＆ドロップすると編集可能な図形・テキストになる（矢印マーカー・透過も再現されることを確認済み）

## 配色

- 残差: 正 = 赤 `#e34948`、負 = 青 `#2a78d6`（発散カラー）
- 成分: 全期間 = 灰 `#6b6b6b`、日 = 橙 `#eb6834`、時間帯 = 紫 `#6250d6`、交互作用 = 緑 `#008300`
- 手法: 基準値のみ = 灰、中心化なし = 橙、提案 = 紫

## 注意：SVG の `opacity` 属性

UnoCSS の attributify モードが SVG の `opacity="1"` / `:opacity="..."` を `opacity-1`（= 0.01）などのユーティリティとして解釈し、線がほぼ消えることがある。
コンポーネント内では `style="opacity: .45"` や `:style="{ opacity: ... }"` のようにインラインスタイルで指定する。
