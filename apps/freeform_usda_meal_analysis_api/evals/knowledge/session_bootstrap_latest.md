# PDCA Session Bootstrap Snapshot

- generated_at_utc: 2026-02-25T03:57:32.465966+00:00
- scope: apps/freeform_usda_meal_analysis_api

## Must Read (in order)
1. `apps/freeform_usda_meal_analysis_api/AGENTS.md`
2. `apps/freeform_usda_meal_analysis_api/CLAUDE.md`
3. `apps/freeform_usda_meal_analysis_api/docs/PDCA_SESSION_START_CHECKLIST.md`
4. `apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json`
5. latest 5 lessons listed below

## Current Baseline
- file: `apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json`
- candidate: `gemini3_flash_v11b_component_density_temp03_full50_repeat`
- model: `openrouter:google/gemini-3-flash-preview`
- calorie_mae_percent: `11.3765`
- high_error_rate_30_percent: `4.0`
- avg_latency_sec: `14.2772`
- avg_cost_usd: `0.007189`
- source_run: `/Users/odasoya/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api/evals/runs/20260225_112102`
- note: `Promoted after full50 gate pass (20260225_105950) and repeat stability confirmation (20260225_112102).`

## Latest Lessons (top 5)
- file: `evals/lessons/20260225_v12_and_v11b_param_sweeps_no_promote.md`
  - title: # PDCA Lesson: v12 Prompt + v11b Temp/Seed Sweeps (No New Promote)
  - 2026-02-25
  - -
  - -
- file: `evals/lessons/20260225_gemini_v11b_temp03_full50_adoption.md`
  - title: # Lesson: Gemini v11b temp03 adopted after full50 + repeat stability
  - 2026-02-25
  - -
  - `freeform_prompt_usda_format_ver_v11b_gemini_component_density_20260225.txt`
- file: `evals/lessons/20260225_gemini_v10_dev40_blocked_openrouter401.md`
  - title: # Lesson: Gemini v10 dev40 blocked by OpenRouter 401
  - 2026-02-25
  - -
  - -
- file: `evals/lessons/20260225_dev40_prompt_param_sweeps_no_promote.md`
  - title: # Dev40 Prompt/Param Sweeps (No Promote)
  - 2026-02-25
  - Hold / Reject (no promotable candidate)
  - -
- file: `evals/lessons/20260224_seed_from_20251221.md`
  - title: # Seed Lesson (from 2025-12-21 research)
  - -
  - -
  - -

## Latest Repeat Summaries (top 3)
- `evals/repeat_runs/20260225_122414/repeated_summary.md`
- `evals/repeat_runs/20260225_100132/repeated_summary.md`

## Remote Config Check
- api_url: `https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app`
- updated_at: `2026-02-25T03:44:00.597406`
- updated_by: `admin`
- vlm_model_id: `openrouter:google/gemini-3-flash-preview`
- vlm_prompt_file: `freeform_prompt_usda_format_ver_v7_experimental_with_meal_title_20251207.txt`
- vlm_prompt_text_len: `2733`
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
