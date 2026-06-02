# Lesson: Post-hoc calorie calibration layer implemented + held-out validated (default OFF)

- Date: 2026-06-02
- Held-out validation run: `evals/runs/20260601_221426` (gemini-3-flash-preview + v13, full50, fixed retrieval)
- Decision: **Implemented + validated, shipped DISABLED.** Enable only after fitting on an EXTERNAL held-out set.

## What was built
- `core/calorie_calibration.py`: affine map `corrected = slope*raw + intercept`, applied as a clamped per-meal scale factor (`scale_factor`, guard rails min/max). Loads `config/calorie_calibration.json` (default `enabled=false`, no-op).
- `services/pipeline.py`: `_apply_calorie_calibration(dishes, total)` scales total + per-dish + per-ingredient nutrition AND weight_g by ONE factor so the response stays internally consistent (verified: sum of dishes == total). Wired after both `_calculate_total_nutrition` sites; loaded in `__init__`. No-op when disabled (default).
- `scripts/fit_calorie_calibration.py`: robust Theil-Sen fit of `true ≈ slope*pred + intercept` on a FIT split, held-out validation on a disjoint TEST split, writes the config (enabled=false by default).
- Tests: 8 cases incl. pipeline integration + clamp + disabled no-op. Full suite 43 passed under the project venv.

## Held-out validation (fit dev_40 → test holdout_10, disjoint)
- Fit (Theil-Sen): slope=0.3322, intercept=469.17.
- HELD-OUT holdout_10: RAW MAE 18.73% → **CAL MAE 14.95%**; signed bias **-6.48% → -0.45%**.
- → The layer removes the systematic under-estimation bias and cuts held-out MAE ~3.8pt (into the ~15% "stretch" band).

## Honest limits
- The improvement is mostly **bias removal (mean-shift)**: pred-vs-true R^2 is only ~0.16, so the fitted slope is weak and the intercept dominates. Calibration cannot create discrimination the model lacks — it corrects the systematic offset, NOT the inability to tell large from small meals. For that, portion estimation (R^2) must improve.
- holdout_10 is n=10 (noisy point estimate) and dev_40 is part of the eval-50 → this is a MECHANISM demonstration, NOT a production fit. Per anti-overfit rule, production (slope, intercept) MUST be fit on data DISJOINT from any benchmark used to judge it.
- Shipped `enabled=false`. Demo params written to `config/calorie_calibration.demo_dev40fit.json` (not the live config).

## Next steps to productionize
1. Acquire an EXTERNAL held-out set (Nutrition5k subset / fresh labels, weighted to large/dense/oily meals).
2. `fit_calorie_calibration.py --run-dir <ext-run> --fit-split <ext> --test-split <frozen-50-or-other>`; review held-out MAE + slope.
3. Set `enabled=true` in `config/calorie_calibration.json`; re-validate on the frozen 50; record in baseline + lesson.
4. Re-fit after any prompt change (each shifts the slope).
5. Combine with a mild portion prompt (v14b, no over-correction) so the prompt lifts slope toward ~0.65 and calibration lands the residual bias.
