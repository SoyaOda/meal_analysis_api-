# AGENTS.md

## Repository-wide defaults
- 日本語で応答すること
- 変更は小さく、レビューしやすく保つこと
- テスト/静的チェックを実行して完了すること
- **開発OS憲法 `ssot/DEVELOPMENT_OS.md` に従うこと**（SSOT 階層・read-before-write・propose-then-ratify: `ssot/`・`.claude/`・採用ゲートの変更は提案止まりでユーザー批准必須）
- データセット/GT を扱う前に `ssot/DATASETS.md` の provenance tier と使用規則を確認すること

## App-specific instructions
- `apps/barcode_api` の運用 SSOT は `apps/barcode_api/plans/current.md`、データ更新は `apps/barcode_api/docs/DATA_REFRESH_RUNBOOK.md`（本番反映はユーザー明示指示必須）
- freeform_usda の新実験・新調査の前に `scripts/check_prior_art` で `evals/knowledge/negative_results.json`（do-not-retry registry）と `evals/lessons/INDEX.md` を照合すること（read-before-write）
- `apps/freeform_usda_meal_analysis_api` のPDCA運用は以下を優先:
  - `apps/freeform_usda_meal_analysis_api/AGENTS.md`
  - `apps/freeform_usda_meal_analysis_api/CLAUDE.md`
  - `apps/freeform_usda_meal_analysis_api/docs/PDCA_SESSION_START_CHECKLIST.md`
- freeform_usda（= mozu 用 API）の採用モデルは `openrouter:google/gemini-3-flash-preview`（2026-06-05〜, code 既定・本番とも flash）。pro（`gemini-3.1-pro-preview`）は撤回済（独立実測 GT で flash への頑健優位なし・3 セットで符号 flip）。決定根拠は `apps/freeform_usda_meal_analysis_api/docs/MOZU_MODEL_DECISION_20260603.md`
- freeform_usda の採用判定は「原則50例フル評価（Ground truth総カロリー比較）」を必須とする
- freeform_usda のPDCAでは過学習防止を必須化（評価データ固有情報をpromptへ埋め込まない）
- freeform_usda のPDCA評価は原則 `use_vlm_cache=false` を維持する
- freeform_usda の新規セッション開始時は、必ず次を実行して現行baseline/lesson/configを確認する:
  - `python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap --api-url https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app`
