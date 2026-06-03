# CLAUDE.md

このリポジトリで作業する Claude Code 向けガイド。リポジトリ全体の方針は次を参照。

@AGENTS.md

## 応答・MCP
- 必ず**日本語**で応答すること。
- serena MCP も日本語で対応すること。

## Apps（monorepo）
`apps/` 配下に6つの API がある。編集対象アプリの dir 内で Claude を起動すると、そのアプリ + root の指示だけが読み込まれる。各アプリの詳細は各 `README.md`、起動・エンドポイント例は `docs/API_QUICKSTART.md` を参照。全コマンドは `PYTHONPATH=/Users/odasoya/meal_analysis_api_2` 前提。

| App | Port | 説明 |
|-----|------|------|
| `word_query_api` | 8002 | MyNetDiary版 単語検索 |
| `meal_analysis_api` | 8001 | MyNetDiary版 食事分析 |
| `barcode_api` | 8003 | バーコード検索 |
| `usda_word_query_api` | 8004 | USDA FNDDS版 単語検索 |
| `usda_meal_analysis_api` | 8005 | USDA FNDDS版 食事分析（8004必須） |
| `freeform_usda_meal_analysis_api` | 8006 | USDA版 自由形式・写真カロリー推定（PDCA運用あり） |

## freeform_usda_meal_analysis_api のPDCA運用（重要）
このアプリを触る場合は先に読むこと:
- `apps/freeform_usda_meal_analysis_api/AGENTS.md` / `CLAUDE.md`
- `apps/freeform_usda_meal_analysis_api/docs/PDCA_SESSION_START_CHECKLIST.md` / `PDCA_BEST_PRACTICES_20260224.md`
- 全体レビュー & 改善ロードマップ: `apps/freeform_usda_meal_analysis_api/docs/DEEP_REVIEW_20260601.md`

精度PDCAに着手する前に `/pdca-bootstrap`（または `scripts/pdca_session_bootstrap`）を実行し、`evals/knowledge/session_bootstrap_latest.md` を確認する。
- **採用候補モデル（mozu, 2026-06-03〜）: `openrouter:google/gemini-3.1-pro-preview`**（recognition が flash 比 4/4 再現で向上・レイテンシ同等・コスト ~3.2x。詳細 `apps/freeform_usda_meal_analysis_api/docs/MOZU_MODEL_DECISION_20260603.md`）。flash は安価代替として残す。
- 採用判定は原則50例フル評価 + Ground truth総カロリー比較 + 安定性確認
- 過学習防止: prompt に評価データ固有情報（test image id / label値 / ground truth）を含めない
- PDCA評価は原則 `use_vlm_cache=false`

## Tooling（Claude Code）
- Skills: `/pdca-bootstrap` `/pdca-run` `/pdca-check`（freeform）, `/handoff`（`plans/current.md` 更新）
- Subagent: `pdca-runner`（50画像evalを隔離実行し要約のみ返す）
- Hooks: `Write|Edit` 後に *.py を `ruff format` + `python -m py_compile`（`.claude/settings.json`）
- 引き継ぎSSOT: 各アプリの `plans/current.md`

## 実装の上でのポイント
- 一度に複数の機能を同時実装しない。機能ごとにテスト・確認してから次へ進む。
- Fallback のような実装はせず、きちんとエラーを出して止める。
- 修正後は `python -m py_compile` で構文エラーを確認する。
- 未使用コード・import は削除。本番コードでのデバッグ出力禁止。マジックナンバーは定数化。
- 作業者側で必要な情報があれば、その都度確認する。
