# docs/ INDEX — freeform_usda_meal_analysis_api

**updated: 2026-07-08**。status の意味: **CURRENT-SSOT** = その情報種別の正典 / **RUNBOOK** = 手順書（現役） / **DECISION** = 決定記録（不変・再 litigate 禁止） / **HISTORICAL** = 価値ある歴史・negative evidence（現役の判断には current.md / registry を見る） / **STALE** = superseded（banner あり）。
運用規約: 新 doc は日付入り filename で追加し、**同一 diff で本 INDEX に行を足す**（未登録は `/os-audit` が検知）。superseded にしたら banner + status 変更。

## 読む順序（精度 PDCA を始める人向け）
`plans/current.md` → `ssot/DEVELOPMENT_OS.md`（repo root）→ `MODEL_REFRESH_OS_20260611.md` §6（SSOT マップ）→ 必要な正典へ。

## 一覧

| doc | 日付 | status | 内容（1行） |
|-----|------|--------|-------------|
| `MOZU_PDCA_COMPLETE_20260606.md` | 2026-06-06 | **CURRENT-SSOT** | PDCA 全史の包括総括（診断・採用・天井・時系列・lesson 索引） |
| `MODEL_REFRESH_OS_20260611.md` | 2026-06-11 | **CURRENT-SSOT** | model-refresh 運用 OS + SSOT マップ + 第1サイクル総括 |
| `MODEL_REFRESH_PROTOCOL_20260611.md` | 2026-06-11 | **CURRENT-SSOT** | model-refresh のゲート数値・手順・教訓の正典（`/model-refresh` が参照） |
| `E13_DATA_COLLECTION_PLAN_20260606.md` | 2026-06-06 | **CURRENT-SSOT** | 本命 lever = 実測データ収集の設計（weigh-as-you-plate / 層化 / n 設計） |
| `MOZU_APP_E13_E14_UIUX_HANDOFF_20260607.md` | 2026-06-07 | **CURRENT-SSOT** | E13 をアプリ機能として作る実装ハンドオフ + E14 fit パイプライン |
| `EXTERNAL_TESTSET_PLAN_20260603.md` | 2026-06-03 | **CURRENT-SSOT** | eval rotation（frozen-50/NVReal/N5k/JFB）のコマンド・baseline 正典 |
| `PDCA_SESSION_START_CHECKLIST.md` | 2026-02 | **CURRENT-SSOT** | セッション開始チェックリスト |
| `PDCA_BEST_PRACTICES_20260224.md` | 2026-02-24 | **CURRENT-SSOT** | PDCA 実運用ガイド（eval-first・anti-overfit・昇格ゲート） |
| `API_DOCUMENTATION.md` / `openapi.json` | — | CURRENT | API 仕様（自スコープの正典） |
| `CLOUD_RUN_DEPLOYMENT_GUIDE.md` | — | RUNBOOK | Cloud Run デプロイ一般手順 |
| `DEPLOY_RUNBOOK_E7_LIGHT_20260605.md` | 2026-06-05 | RUNBOOK | E7+light デプロイ実録 + **現行 rollback 手順**（current.md が参照） |
| `EVAL_RUBRIC.md` | 2026-06 | CURRENT | LLM-judge rubric（advisory・未 golden 検証） |
| `MOZU_MODEL_DECISION_20260603.md` | 2026-06-03 | **DECISION** | pro 採用→撤回の決定記録（flash 採用の根拠） |
| `DEEP_REVIEW_20260601.md` | 2026-06-01 | HISTORICAL | 前フェーズ全体レビュー & 改善ロードマップ（P1 retry-over-breaker は未修正のまま残存） |
| `DRIVE_DATASET_INVENTORY_20260607.md` | 2026-06-07 | HISTORICAL | Drive 全域データ棚卸し（結論: scraped は E13 代替不可）→ 台帳は `ssot/DATASETS.md` |
| `ENGLISH_RECIPE_SOURCE_SURVEY_20260607.md` | 2026-06-07 | HISTORICAL | 英語レシピソース 22 サイト実態調査（同上の結論） |
| `EMBEDDING_RERANKER_RESEARCH_20260604.md` | 2026-06-04 | HISTORICAL | E5/E6 設計調査（結論は lessons へ） |
| `JUDGE_EVAL_DESIGN_20260602.md` | 2026-06-02 | HISTORICAL | LLM-judge 設計 |
| `GOLDEN_LABELING_GUIDE.md` | 2026-06 | HISTORICAL | golden ラベリング手引き（judge 検証用・未運用） |
| `PIPELINE_IMPROVEMENT_PROPOSALS_20260601.md` | 2026-06-01 | HISTORICAL | 改善提案集（採否は current.md / registry が正） |
| `PROMPT_OPTIMIZATION_WEB_RESEARCH_20260224.md` | 2026-02-24 | HISTORICAL | prompt 最適化 web 調査 |
| `CODEX_TASK_nutritionverse_real.md` | 2026-06 | HISTORICAL | NVReal 構築タスク指示書（id-join バグの経緯は lesson 参照） |
| `VOICE_INTEGRATION_PLAN.md` | 2025-12 | HISTORICAL | 音声入力の統合計画（mozu 転換前。現行性未確認） |
| `MOZU_PDCA_SUMMARY_20260604.md` | 2026-06-04 | **STALE** | → `MOZU_PDCA_COMPLETE_20260606.md` に superseded（banner あり） |
| `INDEX.md` | 2026-07-08 | — | 本ファイル |
