# PDCA Session Bootstrap Snapshot

- generated_at_utc: 2026-06-11T07:24:05.388280+00:00
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
- file: `evals/lessons/20260606_jfb_real_indomain_eval_integrated_overprediction_and_e2_confirmed.md`
  - title: # Lesson: JFB (1,000 real eye-level mobile-user photos, CC-BY-4.0) integrated as the in-domain eval set — and it immediately surfaced what the curated sets hid: on real user photos v13 calorie MAE is ~54% with a systematic +44% OVER-prediction (vs ~16% on the curated dev set). E2 floor-20 is now triple-confirmed (significant on JFB small dishes too). The E13 quick-win.
  - 2026-06-06
  - -
  - -
- file: `evals/lessons/20260606_e2_floor20_validated_small_dish_over_prediction_fix.md`
  - title: # Lesson: E2 weight floor 80→20 is a VALIDATED, SAFE, targeted fix for small-dish (<300 kcal) over-prediction — pooled lt_300 (n=87 across N5k+NVReal) calorie-MAE −20.75pt (CI[−40.8,−0.1], SIGNIFICANT), signed bias +84→+56, via the confirmed mechanism (the floor was forcing small portions up; lowering it drops their weight), with NO regression on ≥300 dishes. The first clean positive prompt-lever of the exploration phase. Closes the prior E2 lesson's open precondition.
  - 2026-06-06
  - -
  - -
- file: `evals/lessons/20260606_e1_v18_identity_separation_set_specific_deflation_not_generalizing.md`
  - title: # Lesson: E1 v15/v18 (identity-first schema separation + anti-dense-default) is NOT a generalizing calorie win — its pooled −6.21pt is a SET-SPECIFIC calorie DEFLATION that only fixes N5k's small-dish over-prediction (lt_300 97→77%), is a wash on the mozu-representative eye-level sets, and WORSENS large-meal slope. The intended recognition lever did not generalize. Confirms the design pre-mortem; prompt/schema cannot deliver a distribution-robust calorie win.
  - 2026-06-06
  - -
  - -
- file: `evals/lessons/20260606_e14_conditional_calibration_poc_works_indomain_but_lab_data_does_not_transfer.md`
  - title: # Lesson: E14 conditional-calibration PoC — the machinery WORKS in-domain (JFB held-out calorie MAE 56.6→38.1, −18.5pt; conditional beats global on real photos) BUT a calibration fit on the WEIGHED LAB sets (NVReal+N5k) does NOT transfer to real eye-level photos (applied to JFB it is WORSE than raw, 53.8→55.5). ⇒ E14 is viable, and a mozu-domain in-domain labeled set (E13) is REQUIRED to fit it — existing weighed lab data is insufficient.
  - 2026-06-06
  - -
  - -
- file: `evals/lessons/20260605_e7_topk_density_mixture_robust_calorie_win_adopted.md`
  - title: # Lesson: E7 top-k density mixture is a ROBUST, significant calorie-MAE win (~−3pt) — the session's first real accuracy lever. ADOPTED as default (reranker.top_n=5). Frozen-VLM isolation made it measurable where VLM-draw noise killed E2/E12.
  - 2026-06-05
  - -
  - -

## Latest Repeat Summaries (top 3)
- `evals/repeat_runs/20260225_122414/repeated_summary.md`
- `evals/repeat_runs/20260225_100132/repeated_summary.md`

## Remote Config Check
- api_url: `https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app`
- updated_at: `2026-06-06T03:12:23.292730`
- updated_by: `deploy_e2_floor20_sc_k3_20260606`
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
