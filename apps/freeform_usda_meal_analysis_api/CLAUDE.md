# CLAUDE.md (freeform_usda_meal_analysis_api)

このディレクトリで作業するエージェントは、まず `AGENTS.md` を読むこと。

## Primary Goal
写真カロリー推定の精度改善を、再現可能なPDCAで継続する。
- 採用判定は「原則50例フル評価 + Ground truth総カロリー比較 + 安定性確認」を必須にする。
- `seed` は再現性補助として使うが、provider 非決定性を前提に反復評価で最終判断する。
- 過学習防止のため、promptに評価データ固有情報（`test_foodXX` や label値）を埋め込まない。
- PDCA評価は原則 `use_vlm_cache=false` で実施し、キャッシュ混入を避ける。

## Current Model Focus (2026-06-05〜, mozu)
このアプリは **mozu**（Finch 型の高単価 calorie tracker app）用 API。
- **`openrouter:google/gemini-3-flash-preview`（default, 採用済み）** — code 既定・本番(Cloud Run/Firestore)とも flash。
- **pro は撤回済**（`openrouter:google/gemini-3.1-pro-preview`）: 独立実測 GT（N5k 俯瞰 / NutritionVerse-Real eye-level / NVReal COCO 食材クリーン GT）で **calorie も recognition も flash への頑健優位なし**（3 セットで pro−flash 符号 flip、recognition clean-GT は pro やや劣）。frozen-50 の pro 優位は GPT-5-pro 推定 GT のアーティファクト。→ **同等精度・約1/3コストの flash を採用**。
  - 経緯: `docs/MOZU_MODEL_DECISION_20260603.md`（pro 採用時の根拠・後に撤回）+ lessons `20260604_recognition_clean_gt_pro_no_edge_flash_cost_rational` / `20260604_nutritionverse_real_eyelevel_eval_pro_calorie_edge_not_robust`。
- 高単価モデル(pro 等)は将来 **tiered routing の不確実性検知器**（E18・設計のみ凍結）として再評価の余地あり。

## First 5 Minutes Checklist
1. `apps/freeform_usda_meal_analysis_api/AGENTS.md` を確認
2. `apps/freeform_usda_meal_analysis_api/docs/PDCA_SESSION_START_CHECKLIST.md` を確認
3. セッションbootstrapを実行して現行状態を取得
   - `python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap --api-url https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app`
4. `evals/knowledge/session_bootstrap_latest.md` を確認（baseline / latest lessons / remote config）
5. 実験configを `evals/configs/` に作成/更新
6. チューニング時は `evals/splits/dev_40_v1.txt` を使用し、採用時は50件を必ず評価（中断時は分割実行して全件を揃える）
   - **小lever の採用判定は pooled rotation で行う**（n=50 単独は draw-noise ±3pt）。rotation = frozen-50 / NVReal-104 / N5k-100 / **JFB-100（実 eye-level ユーザー写真・in-domain proxy, `build_jfb_evalset.py` で再構築）**。詳細・コマンド・各 baseline は `docs/EXTERNAL_TESTSET_PLAN_20260603.md`
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
