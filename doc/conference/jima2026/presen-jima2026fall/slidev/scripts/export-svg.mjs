// スライドで使っている図を単体 SVG として書き出す。
//   node scripts/export-svg.mjs            → ../fig/svg/*.svg
//
// 仕組み: 図を 1 枚 1 スライドで並べた figs.md を生成し、Slidev の dev サーバを
// 起動して Brave(Playwright) で開き、
//   - 純 SVG の図       : <svg> を複製し、CSS で指定されていた色・フォント等を属性にインライン化
//   - HTML 混在の図     : dom-to-svg で DOM 全体を SVG 化（テキストは <text> のまま残る）
// Keynote にドラッグ＆ドロップすれば図形・テキストとして編集できる。
import { spawn } from 'node:child_process'
import { mkdirSync, writeFileSync, rmSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright-core'
import * as esbuild from 'esbuild'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(__dirname, '..')
const OUT = resolve(ROOT, '../fig/svg')
const DECK = resolve(ROOT, 'figs.md')
const PORT = 3031
const BRAVE = process.env.BROWSER_PATH ?? '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
const FONT = 'Hiragino Sans'

// ---- 書き出す図の一覧（name, テンプレート, 抽出モード） -------------------------
const range = n => Array.from({ length: n + 1 }, (_, i) => i)
const E = []
const add = (name, tpl, mode = 'svg') => E.push({ name, tpl, mode })

range(4).slice(1).forEach(s => add(`storybar_step${s}`, `<div style="position:relative;width:900px;height:36px"><StoryBar :step="${s}" /></div>`, 'dom'))
range(2).forEach(s => add(`storecompare_stage${s}`, `<div style="width:860px"><StoreCompare :stage="${s}" /></div>`))
range(3).forEach(s => add(`baselineresidual_stage${s}`, `<div style="width:860px"><BaselineResidual :stage="${s}" /></div>`))
add('residualgrid_r_axes', `<ResidualGrid mode="r" :cell="8" :axes="true" />`)
for (const h of ['row', 'col', 'cell', 'rowcol']) add(`residualgrid_r_hl_${h}`, `<ResidualGrid mode="r" :cell="6" highlight="${h}" />`)
for (const m of ['r', 'g', 'a', 't', 'u']) add(`residualgrid_${m}`, `<ResidualGrid mode="${m}" :cell="6" />`)
range(4).forEach(s => add(`decomp_stage${s}`, `<DecompFigure :stage="${s}" :cell="5.5" />`, 'dom'))
add('decomp_hl_nocap', `<DecompFigure :stage="4" :cell="5.5" :captions="false" :hl="true" />`, 'dom')
range(3).forEach(s => add(`glr_stage${s}`, `<div style="width:760px"><GLRFigure :stage="${s}" /></div>`))
add('glr_compact', `<div style="width:250px"><GLRFigure :stage="2" :compact="true" /></div>`)
range(3).forEach(s => add(`saleschart_hour_stage${s}`, `<SalesChart kind="hour" :stage="${s}" :width="270" :height="170" />`))
add('saleschart_day_stage2', `<SalesChart kind="day" :stage="2" :width="270" :height="170" />`)
add('splitbars', `<SplitBars />`)
range(5).forEach(s => add(`modelfigure_stage${s}`, `<div style="width:900px"><ModelFigure :stage="${s}" /></div>`))
range(4).forEach(s => add(`identfigure_stage${s}`, `<IdentFigure :stage="${s}" />`, 'dom'))
range(3).forEach(s => add(`centerconstraint_stage${s}`, `<CenterConstraintFigure :stage="${s}" />`, 'dom'))
range(2).forEach(s => add(`resultbars_stage${s}`, `<ResultBars :stage="${s}" />`, 'dom'))
range(2).forEach(s => add(`corrbars_stage${s}`, `<div style="width:720px"><CorrBars :stage="${s}" /></div>`))
add('quantshape', `<div style="width:620px"><QuantShapeFigure /></div>`, 'dom')
add('quantshape_day', `<div style="width:310px"><QuantShapeFigure part="day" /></div>`, 'dom')
add('quantshape_inter', `<div style="width:310px"><QuantShapeFigure part="inter" /></div>`, 'dom')
add('hourpca', `<div style="width:900px"><HourPCAFigure /></div>`, 'dom')

// ---- HTML 混在の構成図（slides.md の該当部分を静的に再現） ----------------
const panel = (hl, color, title, cap, grid) => `<div class="flex flex-col items-center">
  <div class="p-0.5 border-2 rounded" style="border-color:${color}">${grid}</div>
  <div class="mt-2 font-bold" style="color:${color}">${title}</div><div class="cap">${cap}</div></div>`
add('p5_shared_ranges', `<div class="flex justify-center items-start gap-6" style="width:900px">
  <div class="flex flex-col items-center"><ResidualGrid mode="r" :cell="7" :axes="true" /><div class="cap mt-1"><b>入力</b>：1系列の観測残差（赤：正、青：負）</div></div>
  <div class="flex gap-4 mt-3">
    ${panel('all', '#6b6b6b', '全期間に共通', '全セルが<br>同じ向きにずれる', '<ResidualGrid mode="g" :cell="4.5" :dim="false" />')}
    ${panel('row', 'transparent', '<span style="color:#eb6834">ある日に共通</span>', '同じ日の複数の時間帯で<br>同じ向きにずれる', '<ResidualGrid mode="r" :cell="4.5" highlight="row" />')}
    ${panel('col', 'transparent', '<span style="color:#6250d6">ある時間帯に共通</span>', '複数日の同じ時間帯で<br>同じ向きにずれる', '<ResidualGrid mode="r" :cell="4.5" highlight="col" />')}
    ${panel('cell', 'transparent', '<span style="color:#008300">日 × 時間帯に固有</span>', '特定の組合せだけ<br>大きくずれる', '<ResidualGrid mode="r" :cell="4.5" highlight="cell" />')}
  </div></div>`, 'dom')
add('p5_sum_badge', `<div class="card py-1 px-3 text-sm" style="border-color:#b4231f;background:#fff3f2;display:inline-block">
  <b>推定残差</b> ＝ <b style="color:#6b6b6b">全期間</b> ＋ <b style="color:#eb6834">日</b> ＋ <b style="color:#6250d6">時間帯</b> ＋ <b style="color:#008300">交互作用</b></div>`, 'dom')
const mini = (m, c, cell) => `<div class="flex flex-col items-center"><div class="p-0.5 border-2 rounded" style="border-color:${c}"><ResidualGrid mode="${m}" :cell="${cell}" /></div><div class="cap" style="color:${c}">${{ g: '全期間', a: '日', t: '時間帯', u: '交互作用' }[m]}</div></div>`
const zp = (c, t) => `<span class="zpill" style="border-color:${c};color:${c}">${t}</span>`
add('p10_blueprint', `<div class="flex items-center justify-center gap-2" style="width:940px">
  <div class="bp"><div class="bp-t">観測残差</div><ResidualGrid mode="r" :cell="4" /><div class="cap">店舗×商品ごと<br>28日×24時間帯</div></div>
  <div class="bp-arrow"><span>① 分解</span>→</div>
  <div class="bp" style="border-color:#6250d6"><div class="bp-t">共有範囲の異なる 4 成分</div>
    <div class="flex gap-2 mt-1">${mini('g','#6b6b6b',2.2)}${mini('a','#eb6834',2.2)}${mini('t','#6250d6',2.2)}${mini('u','#008300',2.2)}</div></div>
  <div class="bp-arrow"><span>② 表現</span>→</div>
  <div class="bp" style="border-color:#6250d6"><div class="bp-t">成分ごとの潜在表現 → 非線形</div>
    <div class="text-sm leading-relaxed mt-1 text-left">
      <div>${zp('#6b6b6b','z<sub>g</sub>')} → MLP → ĝ</div>
      <div>${zp('#eb6834','z<sub>a,d</sub>')} → MLP → â<sub>d</sub></div>
      <div>${zp('#6250d6','z<sub>t,h</sub>')} → MLP → t̂<sub>h</sub></div>
      <div>${zp('#008300','z<sub>u,d,h</sub>')} → MLP → û<sub>d,h</sub></div></div></div>
  <div class="bp-arrow"><span>③ 加算</span>→</div>
  <div class="bp"><div class="bp-t">推定残差</div><ResidualGrid mode="r" :cell="4" /><div class="cap">＋ 基準値<br>→ 売上の推定値</div></div>
</div>`, 'dom')
add('p14_autoencoder', `<div class="flex items-center justify-center gap-2" style="width:940px">
  <div class="bp"><div class="bp-t">入力</div><ResidualGrid mode="r" :cell="3.5" /><div class="cap">観測残差 ＋ 共変量</div></div>
  <div class="bp-arrow"><span>Encoder</span>→</div>
  <div class="bp" style="border-color:#6250d6;background:#f4f1ff"><div class="bp-t">潜在表現（成分ごと・低次元）</div>
    <div class="text-sm leading-relaxed text-left mt-1">
      <div>${zp('#6b6b6b','z<sub>g</sub>')} 系列に 1 本（10 次元）</div>
      <div>${zp('#eb6834','z<sub>a,d</sub>')} 日ごとに 1 本（28 本 × 10 次元）</div>
      <div>${zp('#6250d6','z<sub>t,h</sub>')} 時間帯ごとに 1 本（24 本 × 10 次元）</div>
      <div>${zp('#008300','z<sub>u,d,h</sub>')} z<sub>a</sub> ⊕ z<sub>t</sub> から（28 × 24 本 × 8 次元）</div></div></div>
  <div class="bp-arrow"><span>Decoder</span>→</div>
  <div class="bp"><div class="bp-t">4 成分 → 中心化 → Σ</div>
    <div class="flex items-center gap-1 mt-1">
      <div class="p-0.5 border-2 rounded" style="border-color:#6b6b6b"><ResidualGrid mode="g" :cell="1.7" /></div><span class="text-xs">+</span>
      <div class="p-0.5 border-2 rounded" style="border-color:#eb6834"><ResidualGrid mode="a" :cell="1.7" /></div><span class="text-xs">+</span>
      <div class="p-0.5 border-2 rounded" style="border-color:#6250d6"><ResidualGrid mode="t" :cell="1.7" /></div><span class="text-xs">+</span>
      <div class="p-0.5 border-2 rounded" style="border-color:#008300"><ResidualGrid mode="u" :cell="1.7" /></div></div>
    <div class="cap">→ 推定残差（入力を再構成）</div></div>
</div>`, 'dom')

// ---- figs.md 生成 --------------------------------------------------------------
const head = `---
theme: default
title: figure export
drawings:
  enabled: false
transition: none
mdc: true
colorSchema: light
aspectRatio: 16/9
canvasWidth: 980
fonts:
  sans: ${FONT}
  local: ${FONT}
---
`
const body = E.map(e => `\n<div class="flex items-center justify-center" style="height:100%">\n<div id="fig" data-name="${e.name}" style="display:inline-block">\n${e.tpl}\n</div>\n</div>\n`).join('\n---\n')
writeFileSync(DECK, head + body + `\n<style>.slidev-layout{padding:0}</style>\n`)

// ---- dev サーバ -----------------------------------------------------------------
const server = spawn('npx', ['slidev', 'figs.md', '--port', String(PORT)], { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] })
server.stdout.on('data', d => process.env.DEBUG && process.stdout.write(d))
server.stderr.on('data', d => process.stderr.write(d))
const waitServer = async () => {
  for (let i = 0; i < 120; i++) {
    try { const r = await fetch(`http://localhost:${PORT}/1`); if (r.ok) return } catch {}
    await new Promise(r => setTimeout(r, 500))
  }
  throw new Error('slidev dev server did not start')
}

// ---- ブラウザ側で使うコード --------------------------------------------------
const domToSvgBundle = (await esbuild.build({
  stdin: { contents: `export { elementToSVG } from 'dom-to-svg'`, resolveDir: ROOT },
  bundle: true, format: 'iife', globalName: 'domToSvg', write: false, platform: 'browser',
})).outputFiles[0].text

const SVG_PROPS = ['fill', 'fill-opacity', 'stroke', 'stroke-width', 'stroke-opacity', 'stroke-dasharray', 'stroke-linecap', 'stroke-linejoin',
  'opacity', 'font-size', 'font-weight', 'font-family', 'font-style', 'text-anchor', 'dominant-baseline', 'letter-spacing']

function extractInBrowser({ mode, name }) {
  const fig = document.querySelector(`#fig[data-name="${name}"]`)
  if (!fig) throw new Error('#fig not found')
  if (mode === 'dom') {
    const doc = window.domToSvg.elementToSVG(fig)
    return new XMLSerializer().serializeToString(doc)
  }
  const src = fig.querySelector('svg')
  const dst = src.cloneNode(true)
  const walk = (a, b) => {
    const cs = getComputedStyle(a)
    const isSvgRoot = a === src
    for (const p of SVG_PROPS) {
      if (isSvgRoot && p === 'opacity') continue
      let v = cs.getPropertyValue(p)
      if (!v) continue
      if (a.tagName !== 'text' && a.tagName !== 'tspan' && p.startsWith('font') || p === 'text-anchor' && a.tagName !== 'text' && a.tagName !== 'tspan') continue
      if (p === 'opacity' && v === '1') continue
      if (p === 'fill-opacity' && v === '1') continue
      if (p === 'stroke-opacity' && v === '1') continue
      if (p === 'stroke' && v === 'none') continue
      if (p === 'stroke-dasharray' && v === 'none') continue
      if (p === 'letter-spacing' && v === 'normal') continue
      if (p === 'font-style' && v === 'normal') continue
      if (p === 'dominant-baseline' && v === 'auto') continue
      if (p === 'fill' && a.tagName === 'g') continue
      if (p === 'stroke' && a.tagName === 'g') continue
      if (p === 'stroke-width' && (a.tagName === 'g' || cs.getPropertyValue('stroke') === 'none')) continue
      b.setAttribute(p, v)
    }
    b.removeAttribute('class')
    for (const at of [...b.attributes]) if (at.name.startsWith('data-v-')) b.removeAttribute(at.name)
    const ac = [...a.children], bc = [...b.children]
    ac.forEach((c, i) => walk(c, bc[i]))
  }
  walk(src, dst)
  const vb = (src.getAttribute('viewBox') || '').split(/[\s,]+/).map(Number)
  if (vb.length === 4) {
    const r = src.getBoundingClientRect()
    dst.setAttribute('width', String(Math.round(r.width) || vb[2]))
    dst.setAttribute('height', String(Math.round(r.height) || vb[3]))
  }
  dst.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  dst.removeAttribute('style')
  return new XMLSerializer().serializeToString(dst)
}

// ---- Node 側の後処理 -------------------------------------------------------
function postprocess(svg, name, mode) {
  svg = svg.replace(/\s(data-v-[0-9a-f]+|data-name)="[^"]*"/g, '')
  if (mode === 'dom') {
    // dom-to-svg が付ける解析用属性・空要素を除去
    svg = svg.replace(/\s(data-stacking-context|data-stacking-layer|data-tag|data-z-index|aria-owns|class|id)="[^"]*"/g, '')
    svg = svg.replace(/<!--[\s\S]*?-->/g, '').replace(/<style\/>/g, '')
    for (let i = 0; i < 5; i++) svg = svg.replace(/<g(\s[^>]*)?\/>/g, '').replace(/<g(\s[^>]*)?><\/g>/g, '')
    // viewBox に余白を足し、原点を 0,0 に
    svg = svg.replace(/width="([\d.]+)" height="([\d.]+)" viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"(>)/, (m, w, h, x, y, vw, vh, gt) => {
      const pad = 8
      const W = Math.ceil(+vw + pad * 2), H = Math.ceil(+vh + pad * 2)
      return `width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><g transform="translate(${(pad - x).toFixed(2)} ${(pad - y).toFixed(2)})">`
    }).replace(/<\/svg>\s*$/, '</g></svg>')
  }
  // フォント: Noto Sans JP / Hiragino 系 → Hiragino Sans に統一、KaTeX_Math → serif イタリック
  svg = svg.replace(/font-family="[^"]*"/g, m => /KaTeX_Math/i.test(m) ? `font-family="Times New Roman, serif"` : `font-family="${FONT}"`)
  svg = svg.replace(/font-family:\s*[^;"]*(Noto Sans JP|Hiragino)[^;"]*/g, `font-family: ${FONT}`)
  svg = svg.replace(/font-family:\s*KaTeX_Math[^;"]*/g, `font-family: Times New Roman, serif`)
  if (!svg.startsWith('<?xml')) svg = `<?xml version="1.0" encoding="UTF-8"?>\n` + svg
  return svg.replace(/<svg /, `<svg data-figure="${name}" `)
}

// ---- 実行 -----------------------------------------------------------------
mkdirSync(OUT, { recursive: true })
await waitServer()
const browser = await chromium.launch({ executablePath: BRAVE, headless: true })
try {
  const page = await browser.newPage({ viewport: { width: 980, height: 552 }, deviceScaleFactor: 1 })
  await page.goto(`http://localhost:${PORT}/1`, { waitUntil: 'networkidle' })
  await page.addScriptTag({ content: domToSvgBundle })
  await page.addScriptTag({ content: `window.SVG_PROPS = ${JSON.stringify(SVG_PROPS)}; window.extractInBrowser = ${extractInBrowser.toString()}` })
  for (let i = 0; i < E.length; i++) {
    const e = E[i]
    await page.goto(`http://localhost:${PORT}/${i + 1}`, { waitUntil: 'networkidle' })
    await page.waitForSelector(`#fig[data-name="${e.name}"]`)
    await page.waitForSelector(`#fig[data-name="${e.name}"] svg, #fig[data-name="${e.name}"] [class]`)
    await page.waitForFunction(n => { const el = document.querySelector(`#fig[data-name="${n}"]`); const r = el.getBoundingClientRect(); return r.width > 10 && r.height > 10 }, e.name)
    await page.evaluate(() => document.fonts.ready)
    await page.waitForTimeout(700) // transition / animation 待ち
    if (i === 0) {
      const scale = await page.evaluate(() => getComputedStyle(document.querySelector('#slide-content') ?? document.body).transform)
      console.log('slide transform:', scale)
    }
    if (!(await page.evaluate(() => !!window.domToSvg))) {
      await page.addScriptTag({ content: domToSvgBundle })
      await page.addScriptTag({ content: `window.SVG_PROPS = ${JSON.stringify(SVG_PROPS)}; window.extractInBrowser = ${extractInBrowser.toString()}` })
    }
    const raw = await page.evaluate(arg => window.extractInBrowser(arg), { mode: e.mode, name: e.name })
    const out = resolve(OUT, `${e.name}.svg`)
    writeFileSync(out, postprocess(raw, e.name, e.mode))
    console.log(`${String(i + 1).padStart(2)}/${E.length} ${e.mode.padEnd(3)} ${e.name}.svg`)
  }
} finally {
  await browser.close()
  server.kill('SIGTERM')
  rmSync(DECK, { force: true })
}
