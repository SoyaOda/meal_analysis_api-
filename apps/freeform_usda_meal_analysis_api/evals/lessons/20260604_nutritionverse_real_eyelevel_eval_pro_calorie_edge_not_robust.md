# Lesson: NutritionVerse-Real eye-level eval (N=104, measured GT) — pro's calorie edge does NOT replicate; across 3 independent sets the pro−flash sign FLIPS

- Date: 2026-06-04
- Third independent external eval, the first **eye-level + measured-GT** set: NutritionVerse-Real 104 **content-verified** dishes (built via the corrected COCO-content-join converter, see [[20260603_nutritionverse_real_broken_id_mapping]]). Run `20260603_232505`. gemini-3.1-pro vs gemini-3-flash, same v13 prompt, cache off, no judge. Cost note: required swapping in fresh OpenRouter+DeepInfra keys (old keys 401'd mid-session).

## Result (NVReal 104, eye-level plated meals, measured GT)
| metric | flash_v13 | pro_v13 |
|---|---:|---:|
| total-calorie MAE | **40.0%** | 42.2% |
| MAE 95% CI | [33.6, 50.9] | [36.3, 51.4] |
| paired Δ (pro−flash) | — | **+2.2pt, CI [-2.4, +6.5], p=0.35 → NS (tie)** |
| signed bias mean / median | -0.04% / -9.1% | **-13.6% / -27.5% (UNDER)** |
| high-error-rate 30% | 44.2% | 58.7% |
| calib_slope (OLS) | 0.127 | 0.116 |
| abs_kcal_mae | 475 | 508 |
| dish F1 (token) | 0.12 | 0.13 |

## Findings
1. **pro's calorie advantage does NOT replicate here.** flash is the slightly better point estimate (40.0 vs 42.2; flash wins 64/104 images) but the paired CI straddles 0 → statistically a TIE. So on eye-level measured GT, pro is NOT better on calorie.
2. **Across 3 independent sets the pro−flash calorie delta FLIPS SIGN** — there is no robust pro calorie edge:
   - frozen-50 (GPT-5-pro *estimated* labels, eye-level): pro ≈ flash, paired NS (pro slightly better).
   - Nutrition5k (overhead, measured): pro −7pt, denoised CI [-15.2, +0.9] → borderline better.
   - NutritionVerse-Real (eye-level, measured): flash slightly better, +2.2pt NS.
   → The calorie ranking is **distribution-dependent**; the single-run N5k "pro better" does not generalize.
3. **Bias direction is also distribution-dependent** (calibration remains hopeless without target data): frozen-50 pro UNDER −5%; N5k both OVER +30–49%; NVReal flash ~0% but **pro UNDER −13.6%** (median −27%). pro systematically under-calls on this set.
4. **Both models badly under-predict LARGE dishes** (calib_slope ≈ 0.12, ts_slope 0.31–0.47): a 3724-kcal multi-item plate is predicted as a fraction of its size, so abs_kcal error is large (475–508 kcal) even though MAPE is "only" 40% (the dataset has big denominators; median GT 565 kcal). Portion estimation for big multi-component plates is the real weakness, shared by both models.
5. **Recognition F1 ≈ 0.12** — unreliable here too (NutritionVerse vocab `costco-california-sushi-roll`, `stack-of-tofu-4pc` does not token-match USDA-style VLM names). Calorie totals remain the only trustworthy axis on this set.

## Implications / actions
- **The "pro for calorie accuracy" case is now WEAK.** It does not hold across independent distributions. **pro adoption now rests almost entirely on the frozen-50 recognition gain (4/4 runs, deterministic)** — a real but narrow signal that we cannot externally re-measure (vocab mismatch on both measured sets).
- **Do NOT cite a pro calorie advantage in the SSOT as if robust.** Report the 3-set picture honestly: tie / borderline / tie-with-flash-ahead.
- **Calibration stays VOID** — bias sign flips across all three distributions; only real mozu-domain data can fix it.
- The decisive arbiter remains a **real mozu-user measured set**. The three external sets agree on one thing: real-world calorie MAE is materially worse (~40–60%) than the frozen-50 implied (~18%), and neither model has a robust edge.
- Optional: a 2nd NVReal run for a denoised paired CI (single run here; direction unlikely to flip given the clean tie, but stability is the standing rule).

## Related
- [[20260603_nutritionverse_real_broken_id_mapping]] (how this 104-dish content-verified set was built after the id-mapping bug)
- [[20260603_n5k_pro_advantage_test_retest_borderline]] (N5k: pro borderline better — the opposite-leaning set)
- [[20260603_nutrition5k_external_eval_generalization_gap]] / [[20260603_frozen50_gt_is_gpt5pro_estimate_two_gate_strategy]]
