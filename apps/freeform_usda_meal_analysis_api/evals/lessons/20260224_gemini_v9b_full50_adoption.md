# Lesson: Gemini v9b adopted after full-50 + stability check

- Date: 2026-02-24
- Model: `openrouter:google/gemini-3-flash-preview`
- Promoted prompt: `freeform_prompt_usda_format_ver_v9b_gemini_recall_balance_20260224.txt`

## Runs used
- Full-50 merged run (v9a vs v9b):
  - merge output: `apps/freeform_usda_meal_analysis_api/evals/runs/20260224_234407`
  - source chunks:
    - `apps/freeform_usda_meal_analysis_api/evals/runs/20260224_232202` (1-25)
    - `apps/freeform_usda_meal_analysis_api/evals/runs/20260224_233232` (26-50)
- v9b stability repeat (full-50 equivalent):
  - merge output: `apps/freeform_usda_meal_analysis_api/evals/runs/20260224_234926`
  - source chunks:
    - `apps/freeform_usda_meal_analysis_api/evals/runs/20260224_234432` (1-25)
    - `apps/freeform_usda_meal_analysis_api/evals/runs/20260224_234556` (26-50)

## Full-50 merged result (primary decision)
- `gemini3_flash_v9a_compact_schema`
  - calorie_mae_percent: `17.1158`
  - high_error_rate_30_percent: `12.0`
  - avg_latency_sec: `24.6355`
  - avg_cost_usd: `0.007355`
- `gemini3_flash_v9b_recall_balance`
  - calorie_mae_percent: `12.51`
  - high_error_rate_30_percent: `6.0`
  - avg_latency_sec: `25.5451`
  - avg_cost_usd: `0.007762`

## Baseline comparison (`current_baseline` before update)
- Previous baseline: `gemini3_flash_v7_exp_meal_title`
  - calorie_mae_percent: `21.9784`
  - high_error_rate_30_percent: `24.0`
  - avg_latency_sec: `21.5895`
  - avg_cost_usd: `0.01063`
- v9b delta:
  - calorie_mae_percent: `-9.4684 pt`
  - high_error_rate_30_percent: `-18.0 pt`
  - avg_latency_sec: `+3.9556 sec` (within +20% gate)
  - avg_cost_usd: `-0.002868`

## Stability check (policy)
- Compared first full-50 v9b vs repeat full-50 v9b:
  - delta_calorie_mae_percent: `0.0`
  - delta_high_error_rate_30_percent: `0.0`
  - stable_by_policy: `true` (thresholds: MAE <= 1.0pt, 30%+ <= 2.0pt)

## Important note
- Repeat run was executed on the same API process; VLM cache can reduce latency.
- Therefore latency stability is not used as the primary stability signal here.
- Accuracy stability (MAE / 30%+ error rate) is considered valid for adoption.

## Action taken
- Updated baseline files:
  - `apps/freeform_usda_meal_analysis_api/evals/baselines/baseline_20260224_gemini3_flash_v9b_recall_balance.json`
  - `apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json`
