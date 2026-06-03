# PDCA Session Bootstrap Snapshot

- generated_at_utc: 2026-06-03T12:48:40.660635+00:00
- scope: apps/freeform_usda_meal_analysis_api

## Must Read (in order)
1. `apps/freeform_usda_meal_analysis_api/AGENTS.md`
2. `apps/freeform_usda_meal_analysis_api/CLAUDE.md`
3. `apps/freeform_usda_meal_analysis_api/docs/PDCA_SESSION_START_CHECKLIST.md`
4. `apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json`
5. latest 5 lessons listed below

## Current Baseline
- file: `apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json`
- candidate: `gemini3flash_preview`
- model: `openrouter:google/gemini-3-flash-preview`
- calorie_mae_percent: `20.6506`
- high_error_rate_30_percent: `22.0`
- avg_latency_sec: `15.8077`
- avg_cost_usd: `0.007159`
- source_run: `apps/freeform_usda_meal_analysis_api/evals/runs/20260601_221426`
- note: `Reality-reset 2026-06-01: the prior 11.38% baseline (v11b, 2026-02-25) NO LONGER reproduces; gemini-3-flash-preview + v13 + fixed retrieval now measures ~20.5% (corroborated: 20.27% remote run 20260601_204037, 20.65% local run 20260601_221426). Newer Gemini models do not recover (3.5-flash worse, 3.1-flash-lite equal+slower; lesson 20260601_model_drift_newer_gemini_no_recovery). Root cause not yet localized; recovery toward 11% is the goal once decomposed metrics localize it. Old baseline kept at baseline_20260225_gemini3_flash_v11b_component_density_temp03.json.`

## Latest Lessons (top 5)
- file: `evals/lessons/20260603_v17_full50_rejected_calorie_regression.md`
  - title: # Lesson: v17 (describe-shape identity) REJECTED on full 50 — confirmed calorie-MAE regression (+4.6pt) from the bundled cooked-default
  - 2026-06-03
  - -
  - -
- file: `evals/lessons/20260603_pro_stability_confirmed_and_calorie_bias_calibrated.md`
  - title: # Lesson: gemini-3.1-pro recognition gain is STABLE (pro>flash in 4/4 runs) and its calorie under-bias is FIXABLE by calibration (-13.5% -> -1.6% held-out). Promote case strengthened; naming regression persists.
  - 2026-06-03
  - -
  - -
- file: `evals/lessons/20260603_pro_naming_reranker_form_did_not_recover.md`
  - title: # Lesson: form-tuned reranker instruction does NOT recover pro's naming regression (raw_vs_cooked got WORSE), though it improves deterministic calorie MAE (likely via full-fat default)
  - 2026-06-03
  - -
  - -
- file: `evals/lessons/20260603_nutrition5k_external_eval_generalization_gap.md`
  - title: # Lesson: Nutrition5k external eval (N=250, independent measured GT) — the frozen-50 MASSIVELY overstates calorie accuracy; pro beats flash SIGNIFICANTLY; affine calibration fit on N5k FAILS
  - 2026-06-03
  - -
  - -
- file: `evals/lessons/20260603_n5k_pro_advantage_test_retest_borderline.md`
  - title: # Lesson: N5k pro-vs-flash test-retest — pro's calorie advantage is DIRECTIONALLY consistent but only BORDERLINE significant; pro is less reproducible than flash
  - 2026-06-03
  - -
  - -

## Latest Repeat Summaries (top 3)
- `evals/repeat_runs/20260225_122414/repeated_summary.md`
- `evals/repeat_runs/20260225_100132/repeated_summary.md`

## Remote Config Check
- skipped/failed: timeout: The read operation timed out

## Guardrails
- Never promote from dev-only split results. Promotion requires full50 coverage.
- Keep `use_vlm_cache=false` for evaluation runs.
- Never include `test_foodXX`/ground-truth hints in prompts.
- Admin panel `Local` tab uses current origin (relative path), not guaranteed localhost.
