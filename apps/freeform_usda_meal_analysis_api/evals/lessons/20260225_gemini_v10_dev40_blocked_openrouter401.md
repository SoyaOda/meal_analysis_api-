# Lesson: Gemini v10 dev40 blocked by OpenRouter 401

- Date: 2026-02-25
- Run directory: `apps/freeform_usda_meal_analysis_api/evals/runs/20260225_003213`
- Config: `apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v10_dev40_20260225.json`
- Scope: `gemini3_flash_v9b_recall_balance` vs `gemini3_flash_v10a_energy_density_sanity`

## What changed
- Added candidate prompt:
  - `freeform_prompt_usda_format_ver_v10a_gemini_energy_density_sanity_20260225.txt`
- Added dev split config:
  - `pdca_gemini_prompt_sweep_v10_dev40_20260225.json`

## What happened
- Both candidates failed all 40 images (`success_count=0`, `failure_count=40`).
- First failures were OpenRouter auth errors:
  - `401 {"error":{"message":"User not found.","code":401}}`
- After repeated failures, circuit breaker opened and later requests failed fast.

## Reproduction check
- Same runtime settings key also failed direct auth endpoint check:
  - `GET https://openrouter.ai/api/v1/auth/key`
  - status: `401`

## Decision
- This run is invalid for model/prompt comparison.
- Do not use `20260225_003213` for promotion decisions.

## Next action
1. Replace runtime `OPENROUTER_API_KEY` with a valid key.
2. Restart local API process (reset circuit breaker).
3. Re-run the same dev40 command:
   - `python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v10_dev40_20260225.json --api-url http://localhost:8006 --image-index-file apps/freeform_usda_meal_analysis_api/evals/splits/dev_40_v1.txt --required-image-count 40 --no-use-vlm-cache --concurrency 2`
