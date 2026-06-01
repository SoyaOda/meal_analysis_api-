# Lesson: Gemini prompt sweep blocked by OpenRouter 401

- Date: 2026-02-24
- Run directory: `apps/freeform_usda_meal_analysis_api/evals/runs/20260224_225556`
- Config: `apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v9_20260224.json`
- Scope: Gemini 3 Flash (`v7` baseline vs `v9a` / `v9b`)

## What happened
- All candidates failed (`success_count=0`, `failure_count=15` each).
- First failure was `401 User not found` from OpenRouter.
- After repeated failures, circuit breaker opened and subsequent requests failed fast.

## Reproduction check
- Direct API check confirmed auth issue:
  - `POST https://openrouter.ai/api/v1/chat/completions`
  - Response: `HTTP 401 {"error":{"message":"User not found.","code":401}}`

## Decision
- This run is invalid for prompt comparison.
- Do not use `20260224_225556` for promotion decisions.

## Next action
1. Reissue/replace `OPENROUTER_API_KEY`.
2. Restart API server to clear circuit breaker state.
3. Re-run:
   - short screening: `--limit 15`
   - full eval (winner): `--limit 50`
