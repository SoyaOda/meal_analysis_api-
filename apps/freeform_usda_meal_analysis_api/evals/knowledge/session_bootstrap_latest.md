# PDCA Session Bootstrap Snapshot

- generated_at_utc: 2026-06-05T07:24:17.150809+00:00
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
- file: `evals/lessons/20260605_e7_topk_density_mixture_robust_calorie_win_adopted.md`
  - title: # Lesson: E7 top-k density mixture is a ROBUST, significant calorie-MAE win (~−3pt) — the session's first real accuracy lever. ADOPTED as default (reranker.top_n=5). Frozen-VLM isolation made it measurable where VLM-draw noise killed E2/E12.
  - 2026-06-05
  - -
  - -
- file: `evals/lessons/20260605_e2_weight_floor20_inconclusive_50set_no_small_dish_data.md`
  - title: # Lesson: E2 weight floor 80→20 — harmless overall (−0.68pt, NS) but the small-dish target (<300 kcal) is UNTESTABLE on the 50-set (no GT<300 images). Plus E12, this confirms the meta-finding: small data-independent levers cannot be validated on the 50-set; they need pooled N5k+NVReal.
  - 2026-06-05
  - -
  - -
- file: `evals/lessons/20260605_e12_self_consistency_v2_parallel_no_reproduce_at_n50.md`
  - title: # Lesson: E12 self-consistency v2 — parallelization SHIPPED (latency ~1.15× not 3×), but K=3 median did NOT reproduce the −2pt calorie win at n=50 (a lucky-good single baseline draw → median regresses to mean). K=3's value is variance reduction (needs pooled large-N to show), not a single-run guarantee. K=1 kept as default.
  - 2026-06-05
  - -
  - -
- file: `evals/lessons/20260605_cross_provider_retrieval_no_clean_win.md`
  - title: # Lesson: cross-provider "best regardless of provider" retrieval A/B — NO premium embedding or reranker cleanly beats the free open lightweight models for USDA calorie estimation. The retrieval slot is at its useful ceiling; the real levers are the VLM + input info (E8/E13/E14).
  - 2026-06-05
  - -
  - -
- file: `evals/lessons/20260604_v14_portion_scaling_helps_slope_but_not_realistic_range.md`
  - title: # Lesson: v14 portion-scaling raises the calorie slope but does NOT improve the realistic meal range — range-compression lives only in the unrealistic giant-plate tail
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
