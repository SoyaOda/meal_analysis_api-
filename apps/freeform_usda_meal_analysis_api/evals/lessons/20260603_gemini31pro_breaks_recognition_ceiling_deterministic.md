# Lesson: gemini-3.1-pro NOTABLY improves recognition (deterministic F1 +30%, recall AND precision up) — the first lever to break the ~32 conviction ceiling. (LLM-judge confirmation blocked on OpenRouter credits.)

- Date: 2026-06-03
- Test: gemini-3.1-pro-preview vs gemini-3-flash-preview, SAME v13 prompt (model is the only variable), dev40, use_vlm_cache=false. Run `20260602_235020`. Config `pdca_gemini31pro_vs_flash_dev40_20260602.json`.
- Motivation: across reranker / v16 / v17 / self-verification, conviction sat at a ~32/100 ceiling and NO inference-time lever moved recognition beyond n=40 judge noise (capability-bound). This tests the recommended real lever: a stronger GENERATOR.

## Result (deterministic dish-match metrics — NO OpenRouter, credit-free)
| metric | flash_v13 | pro_v13 |
|---|---|---|
| recognition F1 (Hungarian pred↔GT) | 0.2043 | **0.2661** (+30% rel) |
| recall | 0.2185 | **0.2910** |
| precision | 0.1968 | **0.2524** |
| cal_MAE% | 18.21 | 17.75 |
| high_error_rate_30% | 17.5 | **12.5** |
| nutrient_self_consistency | 0.990 | 0.994 |

## Findings
- **pro improves recognition on BOTH axes**: recall up (fewer missed real foods) AND precision up (fewer phantom/wrong dishes). F1 +30% relative is the FIRST notable recognition gain this session — every inference-time lever (reranker instruction, v16/v17 prompts, same-tier self-verification) was near-noise. This directly supports the meta-conclusion: the conviction ceiling is generator-capability-bound, and a stronger generator is the lever.
- pro also improves worst-tail calorie: high_error_rate_30% 17.5 -> 12.5 (dev40), 18.0 -> 14.0 (full50), abs_kcal_mae 136 -> 122.

## UPDATE (full50 + LLM judge, after credit top-up) — and a CORRECTION
Ran the full50 pro-vs-flash + the LLM judge (run 20260603_100421 + the credit-restored judges). An adversarial review (steelman-for / against / fact-check) caught TWO overclaims in the first draft of this lesson:
- **CORRECTION — the slope/calibration advantage does NOT reproduce on this clean full50.** The run artifact's OLS calibration slope is flash 0.550 -> pro **0.513 (pro LOWER)**; an ad-hoc Theil-Sen gave pro higher (0.61), i.e. the slope comparison is ESTIMATOR-DEPENDENT and not robust here. The earlier sweep's TS 0.67 ([[20260602_broad_vlm_sweep_thinking_helps_slope]]) did NOT cleanly reproduce. The "calibrated MAE 15.15 vs 16.38" figure was an ad-hoc 2-fold calc, NOT a run artifact — treat it as unproven.
- What IS solid on full50: recognition F1 flash 0.226 -> pro 0.245 (recall+precision both up); per-dish correct% 13.5% -> 16.5% (42 -> 55 correct dishes); worst-tail high30 18 -> 14.
- What is NOT significant / regresses: conviction 30.22 [25.5,35.1] -> 32.32 [27.0,37.3] (CIs OVERLAP, NS); raw calorie MAE 19.54 -> 17.32 but paired BCa CI [-10.99, +3.02], p=0.56 (NS); naming_db_match 1.74 -> 1.64 (DOWN, on a judge-reliable dim); calorie signed bias flips +1.17% -> **-5.31% (systematic under-estimation)**; hallucinated/img 1.74 -> 1.82 (up). **The harness gate recorded decision='hold' for BOTH candidates.**

## Action / recommendation (corrected)
1. **Do NOT auto-promote on this single n=50 run** — it does not clear the promote bar (conviction NS, calorie comparison NS/hold, stability untested). See [[20260603_gemini31pro_promote_hold_adversarial_verified]].
2. pro IS a genuine generator-quality candidate: it is the only lever this session to move recognition (deterministic F1 + correct%, judge-independent) and it cuts worst-tail error. But it regresses naming and introduces a -5.3% calorie under-bias, at ~4x cost.
3. If portion/calorie accuracy is the goal, the slope advantage that would have justified pro is NOT present here, so enable the existing calibration layer on FLASH first (cheaper) and measure it before a model change.
4. To promote pro: >=2 stability repeats reproducing the recognition direction + check/fix the calorie under-bias (calibration on disjoint data) + the user accepts 4x cost as a recognition/tail bet (NOT a proven conviction win).

## Related
- [[20260603_gemini31pro_promote_hold_adversarial_verified]] (the adversarial promote review)
- [[20260602_self_verification_implemented_same_tier_verifier_ineffective]] (meta: ~32 ceiling)
- [[20260602_broad_vlm_sweep_thinking_helps_slope]] (earlier sweep TS slope 0.67 — did NOT reproduce on this clean full50)
- [[20260603_v17_full50_rejected_calorie_regression]] (v17 promote rejected)
