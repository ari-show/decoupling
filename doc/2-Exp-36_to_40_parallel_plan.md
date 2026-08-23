# 2-Exp-36〜40: git worktree による並列仮説検証計画

作成日: 2026-08-22
関連: [proposal/unified_model_direction.md](proposal/unified_model_direction.md)、
GitHubプロジェクト（users/ari-show/projects/11）、
[proposal/research_direction_2026-08.md](proposal/research_direction_2026-08.md)

## 1. ナンバリングとボード対応

| Exp | 内容 | ボード項目 | 締切 | コード変更 | ブランチ |
|---|---|---|---|---|---|
| 2-Exp-36 | 潜在次元感度 {2,4,8,16} | JIMA-03 (P0) | JIMA 08-31 | なし（config のみ） | `Experiments/2-Exp-36` |
| 2-Exp-37 | 主要ハイパーパラメータ探索 | JIMA-02 支援 | JIMA 08-31（間に合う範囲） | なし（config のみ） | `Experiments/2-Exp-37` |
| 2-Exp-38 | 共有 backbone（Stage A/B ladder） | H-EXT-05 | APIEMS 09-30 | あり（モデル） | `Experiments/2-Exp-38` |
| 2-Exp-39 | hard vs soft centering | H-EXT-07 | APIEMS 09-30 | あり（損失） | `Experiments/2-Exp-39` |
| 2-Exp-40 | 軸別 swap / counterfactual 正則化 | H-EXT-08 | APIEMS/修論 | あり（損失） | `Experiments/2-Exp-40` |
| （実験なし） | 2軸 Global/Local 定式化の文書化 | T-EXT-02 | JIMA motivation | なし（doc のみ） | `conf/t-ext-02` |

JIMA-01/04/05/06 は原稿作業のため実験番号を振らず、`conf/jima-fall` 系ブランチで扱う。
JIMA-02（主結果系列の決定）は分析・意思決定が主だが、追試が必要になった場合は
2-Exp-37 の結果を利用する。

## 2. 各実験の設計概要

### 2-Exp-36: 潜在次元感度（JIMA-03）

- 主モデル `output_decomp_centered`、`series_mean` residual、同一分割・同一 epoch。
- 次元 {2, 4, 8, 16} を series/day/hour に適用（interaction は各次元の 0.8 倍を丸めるか、
  同値にするかを design doc で固定）。
- seed は 2-Exp-32 系に合わせ 5 seed。
- 指標: corrected MAE / WAPE / top10 MAE、seed 間分散、パラメータ数、学習時間。
  可能なら synthetic の component corr も。
- 完了条件（ボード準拠）: 全条件完走、平均±SD または CI の1表、10/10/10/8 採用根拠の記述。

### 2-Exp-37: ハイパーパラメータ探索

- 対象は主結果条件（`output_decomp_centered` × `series_mean`）の頑健性確認。
- 探索対象（各1軸ずつの感度、グリッド全探索はしない）:
  - 学習率
  - epoch 数（early stopping 挙動）
  - bias 制約 weight（λ_bias / λ_series_bias）
  - calibration 有無（JIMA-02 の raw vs calibration 分離に対応）
- 指標: corrected MAE / WAPE / top10 MAE / bias、seed 間分散。
- 目的は最良値探しではなく「主結果が HP 選択に敏感でないこと」の提示。
  JIMA には「感度が小さい」ことを appendix 1表で示せれば十分。

### 2-Exp-38: 共有 backbone（H-EXT-05）

- 比較: 現行4系統 / 共有 Encoder + 軸別 head（Stage A）/ 共有 Enc+Dec + 中心化射影（Stage B）。
- 容量を揃えた比較と、非劣性マージンの事前固定。
- 指標: corrected MAE / WAPE / top10 MAE、成分相関、パラメータ数、学習・推論時間、GPU メモリ。

### 2-Exp-39: hard vs soft centering（H-EXT-07）

- 比較: hard（現行 `center_components`）/ soft（λ sweep）/ 制約なし。
- 完全格子 synthetic + 欠損偏在 synthetic + FreshRetailNet `series_mean`。
- 指標: 中心化違反量、成分相関、profile corr、ARI/NMI、corrected MAE。

### 2-Exp-40: 軸別 swap 正則化（H-EXT-08）

- 比較: なし / day 軸のみ / hour 軸のみ / 両軸。
- 成分既知 synthetic → FreshRetailNet。
- 指標: 成分間相関、leakage、成分相関、corrected MAE、seed 間分散。

## 3. 並列化の構成

### worktree 配置

```text
~/decoupling            main（統合・レビュー用。実験はしない）
~/worktrees/exp36       Experiments/2-Exp-36
~/worktrees/exp37       Experiments/2-Exp-37
~/worktrees/exp38       Experiments/2-Exp-38
...
```

### セットアップ手順（実験ごと）

```bash
git -C ~/decoupling worktree add ~/worktrees/exp36 -b Experiments/2-Exp-36
ln -s ~/decoupling/data ~/worktrees/exp36/data
ln -s ~/decoupling/runs ~/worktrees/exp36/runs
```

- `data/` は前処理キャッシュ（981M）を共有するため symlink 必須。読み取り専用運用。
- `runs/` は出力ディレクトリ名が `runs/2-Exp-NN_...` で実験ごとに分かれるため、
  symlink で共有しても衝突しない。集約時に main 側から全実験の結果が見える利点を優先する。
- `.venv` は worktree ごとに `uv sync` で作る（symlink しない。依存が分岐し得るため）。

### 並列実行の波（依存関係）

```text
Wave 1（今すぐ・完全並列）:
  2-Exp-36（config のみ）
  2-Exp-37（config のみ）
  T-EXT-02 doc（doc のみ）
  → 互いに独立。コード変更がないため衝突しない。

Wave 2（Wave 1 と並行可・コード変更あり）:
  2-Exp-38（retail_models.py / residual_models.py を変更）

Wave 3（2-Exp-38 の merge 後に開始）:
  2-Exp-39, 2-Exp-40
  → どちらも損失・centering 周りを触るため、38 のアーキテクチャ変更と
    同じファイルで衝突する。38 を先に merge し、rebase してから始める。
    ただし 39 は現行アーキテクチャでも実施可能なため、38 が遅れる場合は
    現行モデル上で先行させ、統一モデル上での再確認を後続にする。
```

### 計算資源の運用

- smoke（CPU・数分）: 各 worktree でローカル並列実行してよい。
- 本番（GPU・`ssh my`）: GPU が単一ボトルネックのため、worktree 並列の対象は
  「設計・実装・smoke・解析」であり、本番学習はキュー運用で直列にする。
  実行順は締切順: 36 → 37 → 38 → 39 → 40。

### 衝突ホットスポットと規約

| ファイル | リスク | 規約 |
|---|---|---|
| `doc/README.md` の索引表 | 全ブランチが行を追加 | 各ブランチでは触らず、main への merge 時にまとめて追記する |
| `configs/` | 低（追加のみ） | ファイル名に必ず `2-Exp-NN_` プレフィックス |
| `src/decoupled_ts/` | 38/39/40 で競合 | Wave 制御（上記）。フラグ追加は default off で後方互換に保つ |

## 4. 実験ごとの標準フロー

既存の実験文化（design doc → smoke → 本番 → 結果を doc に追記 → PR）を踏襲する。

```text
1. worktree + ブランチ作成
2. doc/2-Exp-NN_<name>.md を作成（目的・仮説・条件・指標・成功条件を事前固定）
3. configs/2-Exp-NN_<name>_smoke.json を作成し、ローカルで smoke 完走を確認
4. configs/2-Exp-NN_<name>_freshretailnet.json（本番）を作成し、GPU キューへ
5. 結果・読み取り・限界を同じ design doc に追記
6. PR → main へ merge、doc/README.md の索引に行を追加
7. ボードの対応項目（JIMA-03 / H-EXT-05 等）を Done へ
```

## 5. 直近のマイルストーン（JIMA 08-31 逆算）

| 期日 | 内容 |
|---|---|
| 08-23 | Wave 1 の worktree 作成、2-Exp-36/37 design doc + smoke config |
| 08-24 | 36/37 smoke 完走 → 本番投入（GPU 直列） |
| 08-26 | 36 の結果集約・表化（JIMA-03 完了条件を満たす） |
| 08-27 | 37 の結果集約（appendix 用）。T-EXT-02 doc を formulation.md へ統合 |
| 08-28〜 | JIMA 原稿へ反映（conf/jima-fall）。38 以降は APIEMS スコープとして継続 |
