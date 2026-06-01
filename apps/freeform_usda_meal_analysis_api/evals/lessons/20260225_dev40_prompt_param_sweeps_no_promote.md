# Dev40 Prompt/Param Sweeps (No Promote)

- Date: 2026-02-25
- Run directory:
  - `/Users/odasoya/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api/evals/runs/20260225_010510`
  - `/Users/odasoya/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api/evals/runs/20260225_012704`
  - `/Users/odasoya/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api/evals/runs/20260225_015141`
  - `/Users/odasoya/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api/evals/runs/20260225_015954`
  - `/Users/odasoya/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api/evals/runs/20260225_021457`
  - `/Users/odasoya/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api/evals/runs/20260225_022819` (full50 drift check)

## What changed
- Prompt changes:
  - `v10b` (compartment + energy-density rules)
  - `v9c` (v9b minimal stability add-ons)
- Param changes:
  - `reasoning_effort`: medium vs high
  - `temperature`: 0.0 / 0.1 / 0.2 / 0.3
  - `stage1_top_k`: 30 / 50 / 80 (temp=0.1)
- Evaluator robustness:
  - Added retry for transient API failures (429/5xx and status=0) in `run_pdca_batch_eval.py`

## What improved
- One transient run (`v9c_temp02`, run `20260225_012704`) showed strong provisional metrics:
  - `calorie_mae_percent=10.5053`
  - `high_error_rate_30_percent=2.6316`
- However this was not reproducible in recheck.
- Full50 drift check for current baseline prompt stayed near historical baseline:
  - `mae=12.6663` vs baseline `12.51` (`+0.1563pt`)
  - `high_error_rate_30_percent=6.0` (unchanged)

## What regressed
- `v10b` severely regressed (`mae=17.3124`, `high30=12.5`).
- `reasoning_effort=high` regressed vs same prompt with medium.
- Most temperature/top_k sweeps regressed vs promoted baseline.
- Best of later sweeps still regressed:
  - `v9b_temp01`: `mae=13.4439`, `high30=10.0`
  - `v9b_temp01_top50`: `mae=13.771`, `high30=7.5`

## Failure pattern
- Non-deterministic infra errors occurred during sweeps:
  - DeepInfra reranker 500
  - status=0 transient failure
- `v10b` introduced catastrophic query drift on some images (example: fat-heavy pork DB match causing >100% error on `test_food32`).

## Likely root cause
- Stronger prompt constraints increased semantic drift in USDA query selection (over-specific/high-fat entries).
- Gemini 3 Flash preview behavior shows notable run-to-run variance on dev40.
- Infra transients can distort candidate ranking without retries.

## Next hypothesis
- Keep prompt close to `v9b` and avoid large instruction expansions.
- Compare candidates using repeated runs (>=2) and aggregate (mean/median + variance) before promote decision.
- If candidate appears improved but has failures, rerun failed indices and merge only for diagnostic, not promotion.

## Decision
- Decision: Hold / Reject (no promotable candidate)
- Baseline remains `gemini3_flash_v9b_recall_balance`.

## Candidate factors (structured)
- `model_family=openrouter:google/gemini-3-flash-preview`
- `reasoning_effort=medium` was consistently better than `high`
- `temperature` sweep did not produce stable gains
- `stage1_top_k` sweep did not produce gains
- `use_vlm_cache=false` maintained eval integrity

## Effective factors (worked)
- Conservative prompt complexity (`v9b` style)
- Retry handling in evaluator for transient upstream failures

## Ineffective factors (did not work)
- Aggressive prompt additions for compartment/density balancing (`v10b`)
- Lowering temperature alone
- Increasing/decreasing stage1_top_k alone
- Raising reasoning effort to high

## Overfitting check
- Prompt leakage check passed: yes
- Holdout or full50 confirmation run: not executed (no stable dev40 improvement)
- `failure_count == 0` and `coverage_complete == true`: not satisfied for promising `v9c_temp02` candidate across rechecks
