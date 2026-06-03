# CLAUDE.md (freeform_usda_meal_analysis_api)

このディレクトリで作業するエージェントは、まず `AGENTS.md` を読むこと。

## Primary Goal
写真カロリー推定の精度改善を、再現可能なPDCAで継続する。
- 採用判定は「原則50例フル評価 + Ground truth総カロリー比較 + 安定性確認」を必須にする。
- `seed` は再現性補助として使うが、provider 非決定性を前提に反復評価で最終判断する。
- 過学習防止のため、promptに評価データ固有情報（`test_foodXX` や label値）を埋め込まない。
- PDCA評価は原則 `use_vlm_cache=false` で実施し、キャッシュ混入を避ける。

## Current Model Focus (2026-06-03〜, mozu)
このアプリは **mozu**（Finch 型の高単価 calorie tracker app）用 API。採用候補モデルを最適化する。
- **`openrouter:google/gemini-3.1-pro-preview`（default, 採用候補）** — flash 比で recognition が 4/4 run 再現的に向上、レイテンシ同等、コスト ~3.2x。calorie under-bias は calibration（外部held-out fit後に有効化）で補正。決定根拠: `docs/MOZU_MODEL_DECISION_20260603.md`。
- `openrouter:google/gemini-3-flash-preview`（安価代替）— コスト優先時のフォールバック。

## First 5 Minutes Checklist
1. `apps/freeform_usda_meal_analysis_api/AGENTS.md` を確認
2. `apps/freeform_usda_meal_analysis_api/docs/PDCA_SESSION_START_CHECKLIST.md` を確認
3. セッションbootstrapを実行して現行状態を取得
   - `python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap --api-url https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app`
4. `evals/knowledge/session_bootstrap_latest.md` を確認（baseline / latest lessons / remote config）
5. 実験configを `evals/configs/` に作成/更新
6. チューニング時は `evals/splits/dev_40_v1.txt` を使用し、採用時は50件を必ず評価（中断時は分割実行して全件を揃える）
7. 実験後に `evals/runs/` と `evals/lessons/` を更新し、必要に応じて `evals/knowledge/` を再生成
8. 昇格候補は `scripts/run_pdca_repeated_eval.py` で最低2反復の安定性を確認

## Runbook
```bash
# API起動（例）
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8006 \
python -m apps.freeform_usda_meal_analysis_api.main

# OpenRouter候補同期
python -m apps.freeform_usda_meal_analysis_api.scripts.sync_openrouter_candidates \
  --thinking-only --max-prompt-price 3.0 --max-completion-price 15.0

# バッチ評価
python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v9_20260224.json \
  --api-url http://localhost:8006 --limit 50 --no-use-vlm-cache

# 中断時の分割実行例（最終的に50件分を統合して判定）
python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v9_20260224.json \
  --api-url http://localhost:8006 --start-index 1 --end-index 25 --no-use-vlm-cache

python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v9_20260224.json \
  --api-url http://localhost:8006 --start-index 26 --end-index 50 --no-use-vlm-cache

# 分割runを統合して正式判定
python -m apps.freeform_usda_meal_analysis_api.scripts.merge_pdca_runs \
  --runs \
  apps/freeform_usda_meal_analysis_api/evals/runs/<run_1_25> \
  apps/freeform_usda_meal_analysis_api/evals/runs/<run_26_50> \
  --required-image-count 50

# 開発中チューニング（過学習抑止）
python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v9_20260224.json \
  --api-url http://localhost:8006 \
  --image-index-file apps/freeform_usda_meal_analysis_api/evals/splits/dev_40_v1.txt \
  --required-image-count 40 \
  --no-use-vlm-cache

# 反復評価（安定性確認）
python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_repeated_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v9_20260224.json \
  --api-url http://localhost:8006 \
  --repeats 2 \
  --image-index-file apps/freeform_usda_meal_analysis_api/evals/splits/holdout_10_v1.txt \
  --required-image-count 10 \
  --no-use-vlm-cache

# セッション開始スナップショット（必須）
python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap \
  --api-url https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app
```

## Non-Negotiables
- 結果を保存せずに「改善した」と判断しない
- ベースライン未比較で本命採用しない
- 50件全体（または分割統合で等価50件）を満たさない評価で採用しない
- Ground truth総カロリー比較を必ず確認する
- 新しい失敗パターンは `evals/lessons/` に必ず残す
- APIパラメータ変更時は旧スクリプト互換を維持する
- `failure_count > 0` または `coverage_complete=false` のrunで採用しない
- Admin UI の `Local` タブは相対パス運用。保存先は現在開いているドメインになるため、保存後は `/admin/api/config?refresh=true` で必ず確認する
