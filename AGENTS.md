# AGENTS.md

## Repository-wide defaults
- 日本語で応答すること
- 変更は小さく、レビューしやすく保つこと
- テスト/静的チェックを実行して完了すること

## App-specific instructions
- `apps/freeform_usda_meal_analysis_api` のPDCA運用は以下を優先:
  - `apps/freeform_usda_meal_analysis_api/AGENTS.md`
  - `apps/freeform_usda_meal_analysis_api/CLAUDE.md`
  - `apps/freeform_usda_meal_analysis_api/docs/PDCA_SESSION_START_CHECKLIST.md`
- freeform_usda（= mozu 用 API）の採用候補モデルは `openrouter:google/gemini-3.1-pro-preview`（2026-06-03〜, 既定）。`gemini-3-flash-preview` は安価代替。決定根拠は `apps/freeform_usda_meal_analysis_api/docs/MOZU_MODEL_DECISION_20260603.md`
- freeform_usda の採用判定は「原則50例フル評価（Ground truth総カロリー比較）」を必須とする
- freeform_usda のPDCAでは過学習防止を必須化（評価データ固有情報をpromptへ埋め込まない）
- freeform_usda のPDCA評価は原則 `use_vlm_cache=false` を維持する
- freeform_usda の新規セッション開始時は、必ず次を実行して現行baseline/lesson/configを確認する:
  - `python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap --api-url https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app`
