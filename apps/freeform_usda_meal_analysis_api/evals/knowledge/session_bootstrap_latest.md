# PDCA Session Bootstrap Snapshot

- generated_at_utc: 2026-06-04T13:23:20.404224+00:00
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
- file: `evals/lessons/20260604_v14_portion_scaling_helps_slope_but_not_realistic_range.md`
  - title: # Lesson: v14 portion-scaling raises the calorie slope but does NOT improve the realistic meal range — range-compression lives only in the unrealistic giant-plate tail
  - 2026-06-04
  - -
  - -
- file: `evals/lessons/20260604_self_consistency_median_ensemble_significant_calorie_win.md`
  - title: # Lesson: self-consistency (median-of-K ensemble) — pure variance-reduction effect is REAL and generalizes (−3 to −4pt at fixed temp), but the NET win is temperature-confounded and did NOT replicate on N5k (NVReal-only at temp 0.5)
  - 2026-06-04
  - -
  - -
- file: `evals/lessons/20260604_recognition_union_self_consistency_not_clean_win.md`
  - title: # Lesson: recognition self-consistency (union of K samples) trades recall for wrong-food — NOT a clean win; recognition misses are mostly SYSTEMATIC, not variance
  - 2026-06-04
  - -
  - -
- file: `evals/lessons/20260604_recognition_clean_gt_pro_no_edge_flash_cost_rational.md`
  - title: # Lesson: recognition on CLEAN independent GT (NVReal COCO) — pro has NO edge over flash (tie/slightly worse). The last pillar of the pro case collapses → flash is cost-rational.
  - 2026-06-04
  - -
  - -
- file: `evals/lessons/20260604_realistic_range_error_decomposition_grams_vs_density.md`
  - title: # Lesson: realistic-range (200-1500 kcal) calorie error decomposed — near-ZERO bias, ~50/50 grams vs density, the two systematic edges CANCEL → single-lever fixes don't help
  - 2026-06-04
  - -
  - -

## Latest Repeat Summaries (top 3)
- `evals/repeat_runs/20260225_122414/repeated_summary.md`
- `evals/repeat_runs/20260225_100132/repeated_summary.md`

## Remote Config Check
- api_url: `https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app`
- updated_at: `2026-02-26T09:54:30.334035`
- updated_by: `admin`
- vlm_model_id: `openrouter:google/gemini-3-flash-preview`
- vlm_prompt_file: `freeform_prompt_usda_format_ver_v7_experimental_with_meal_title_20251207.txt`
- vlm_prompt_text_len: `2841`
- vlm_temperature: `0.3`
- vlm_max_tokens: `12288`
- vlm_reasoning_effort: `medium`
- search.stage1_top_k: `50`
- warning: Prompt Text Override is active (Prompt File is ignored).

## Guardrails
- Never promote from dev-only split results. Promotion requires full50 coverage.
- Keep `use_vlm_cache=false` for evaluation runs.
- Never include `test_foodXX`/ground-truth hints in prompts.
- Admin panel `Local` tab uses current origin (relative path), not guaranteed localhost.
