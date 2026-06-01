# PDCA Lesson: v12 Prompt + v11b Temp/Seed Sweeps (No New Promote)

- Date: 2026-02-25
- Scope:
  - `v12` prompt trial (density/partition guard)
  - `v11b` prompt fixed with temperature/seed sweep
  - full50 repeated stability check for current best config

## Runs
- v12 vs v11b (dev40):
  - `apps/freeform_usda_meal_analysis_api/evals/runs/20260225_114003`
- v11b temp/seed sweep (dev40):
  - `apps/freeform_usda_meal_analysis_api/evals/runs/20260225_115900`
- v11b temp03 full50 repeated eval (2 runs):
  - `apps/freeform_usda_meal_analysis_api/evals/runs/20260225_121605`
  - `apps/freeform_usda_meal_analysis_api/evals/runs/20260225_122028`
  - aggregate: `apps/freeform_usda_meal_analysis_api/evals/repeat_runs/20260225_122414`

## What worked
- Prompt complexity was best kept at `v11b` level; expanding rules (`v12`) hurt both MAE and high-error rate.
- In dev40 single-run (`20260225_115900`), `v11b temp03 no-seed` was the strongest:
  - `mae=10.1106`, `high30=0.0`.

## What did not work
- `v12` (both temp03/temp02) regressed clearly:
  - temp03: `mae=14.2028`, `high30=10.0`
  - temp02: `mae=13.6467`, `high30=10.0`
- `v11b` with seed (`7/21/42`) was consistently worse than no-seed on dev40.
- `v11b temp0.25` also regressed versus temp0.3.

## Stability finding (critical)
- full50 repeated run for same `v11b temp03` config showed large run-to-run spread:
  - run A (`20260225_121605`): `mae=9.9481`, `high30=0.0`
  - run B (`20260225_122028`): `mae=13.2825`, `high30=8.0`
  - aggregate mean/std (`20260225_122414`):
    - `mae_mean=11.6153`, `mae_std=2.3578`
    - `high30_mean=4.0`, `high30_std=5.6569`
- Conclusion: provider-side non-determinism remains large; single-run wins are not sufficient for promotion.

## Decision
- No new promotion in this cycle.
- Keep baseline as is (`v11b temp03` baseline from prior stable adoption flow).

## Action items for next cycle
- Continue using repeated eval as primary gate (not single-run best).
- Avoid adding large prompt rule blocks unless dev40 + full50 both show improvement.
- Prioritize variance-reduction experiments (without dataset-specific hints), not per-image heuristic tuning.
