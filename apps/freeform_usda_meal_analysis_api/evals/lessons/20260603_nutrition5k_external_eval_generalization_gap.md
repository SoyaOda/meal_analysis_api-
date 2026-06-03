# Lesson: Nutrition5k external eval (N=250, independent measured GT) — the frozen-50 MASSIVELY overstates calorie accuracy; pro beats flash SIGNIFICANTLY; affine calibration fit on N5k FAILS

> ## ⚠️ 2026-06-03 UPDATE after re-run (read [[20260603_n5k_pro_advantage_test_retest_borderline]])
> A second independent N5k-250 run (`20260603_191805`) does NOT reproduce the significance. Run-1's significant CI was an optimistic single draw. The ROBUST claim (denoised 2-run avg): pro lowers calorie MAE ~7pt (flash 67.4% / pro 60.2%) but the paired CI is **[-15.2, +0.9], p=0.076 → BORDERLINE, not significant**. Direction (pro better, less over-bias) is consistent across both runs; statistical significance is fragile to VLM sampling noise. Also: pro is **substantially less run-to-run reproducible** than flash (52% vs 20% of images bit-identical between runs). Treat every "SIGNIFICANT" below as "directionally consistent, borderline significant".

- Date: 2026-06-03
- First evaluation on an EXTERNAL, independent-ground-truth set: Nutrition5k 250 dishes (overhead RGB, lab-weighed calories/mass/macros, CC BY 4.0), built via `build_nutrition5k_evalset.py`, run on the harness with `--images-dir/--labels-dir`. Run `20260603_162853`. gemini-3.1-pro vs gemini-3-flash, same v13 prompt, cache off, no judge (calorie + recognition are deterministic).

## Result (N5k 250)
| metric | flash_v13 | pro_v13 |
|---|---|---|
| total-calorie MAE | 68.4% | **58.4%** |
| MAE 95% CI | [58.1, 83.3] | [49.8, 70.6] |
| signed bias | **+49.3%** | **+30.7%** (both OVER-estimate) |
| abs_kcal_mae | 120.9 | 112.6 |
| recognition F1 (token) | 0.329 | 0.325 |
| high_error_rate_30% | 60.4% | 56.8% |
- **Paired |error| delta (pro − flash): −9.97pt, 95% BCa CI [−18.54, −1.33] → pro is STATISTICALLY SIGNIFICANTLY better** (CI excludes 0; n=250). On the frozen-50 this was non-significant.

## Findings (high value, honest)
1. **The frozen-50 MASSIVELY OVERSTATES real-world calorie accuracy.** Same models + v13 prompt: frozen-50 (Western plated) cal_MAE ~18-20%, Nutrition5k cal_MAE **58-68% (~3x worse)**. The user's overfitting/generalization worry is CONFIRMED: a narrow in-distribution eval is wildly optimistic.
2. **pro's calorie advantage HOLDS and is now SIGNIFICANT on independent data** (−9.97pt, CI excludes 0) — the pro adoption is validated beyond the 50; on the 50 the gain was directional-but-NS, here it is significant at N=250.
3. **Calorie bias FLIPS by distribution**: frozen-50 pro UNDER-estimates (−5.3%); N5k pro OVER-estimates (+30.7%). So a calibration fit on one distribution will NOT transfer to another.
4. **The affine calibration fit on N5k FAILS**: fit on N5k 1-150, validate on 151-250 → RAW MAE 53.0% but CAL MAE **132.6% (much WORSE)**, signed +116%. The Theil-Sen affine (slope 0.75, intercept 77) is destroyed by N5k's wide calorie range incl. small dishes (the +77 intercept inflates low-calorie predictions). The over-bias is ~multiplicative, not affine, and a single affine map cannot fix it here. → calibration is distribution-specific AND its current affine form is inadequate for a wide-range distribution.

## Caveats (do not over-read)
- **Nutrition5k is OVERHEAD/cafeteria** — a different camera angle than typical phone meal photos and different from the frozen-50 (eye-level). Part of the 58-68% is angle/distribution shift, so N5k is a PESSIMISTIC stress-test, not a direct mozu estimate. The real mozu number is likely BETWEEN the 50 (~18%, optimistic) and N5k (~58%, pessimistic) — only real mozu-user data resolves it.
- **recognition/portion deterministic metrics are unreliable on N5k**: Nutrition5k ingredient names ("olive oil", "soy sauce") do not token-match the VLM's USDA-style names, so the matcher under-counts. The CALORIE MAE (total, name-independent) is the trustworthy axis here; the F1 0.329 vs 0.325 (pro not ahead) should be discounted.

## Implications / actions
- **Keep pro** (significantly better on independent calorie GT) — adoption strengthened.
- **Do NOT enable the N5k calibration** (it fails). Calibration must be fit on the REAL target distribution (mozu users); consider a multiplicative (slope-only, intercept=0) or per-calorie-band form before trusting it.
- **Update the mozu Exit Criteria / expectations**: report calorie accuracy as a RANGE (50: ~18%, N5k: ~58%) and treat real-world accuracy as materially worse than the 50 implied. A real-user labeled set remains the only true gate.
- Optional next autonomous step: recognition-only cross-cuisine check (UEC-Food256) for the hallucination/wrong-food generalization axis (the calorie axis is now externally tested).

## Related
- [[20260603_gemini31pro_promote_hold_adversarial_verified]] / [[20260603_pro_stability_confirmed_and_calorie_bias_calibrated]] (the frozen-50 pro evidence this externally tests)
- [[20260602_calorie_calibration_layer_implemented]] (the affine layer that fails on N5k's range)
- `docs/EXTERNAL_TESTSET_PLAN_20260603.md`
