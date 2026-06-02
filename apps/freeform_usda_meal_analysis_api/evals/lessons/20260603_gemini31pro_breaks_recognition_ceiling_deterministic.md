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
- pro also has a better worst-tail calorie (high30 17.5 -> 12.5) and slightly better mean MAE — consistent with the earlier slope finding (pro TS slope 0.67 vs flash 0.40, [[20260602_broad_vlm_sweep_thinking_helps_slope]]). With calibration, pro was projected best (~14.7% calibrated MAE).
- **The LLM-judge (recognition/naming/conviction) could NOT be run**: the OpenRouter account hit its credit cap mid-run ($160/$160 used; pro judge 0/40 with HTTP 402, flash judge only 31/40). The deterministic F1 stands on its own (it needs no API), but the holistic conviction confirmation is pending a credit top-up.

## Action / recommendation
1. **gemini-3.1-pro is the most promising lever found** — promote-track it: top up OpenRouter, re-run the LLM judge on run 20260602_235020 (the outputs are saved; judge re-runs in minutes), then run pro on FULL 50 + fit the calorie calibration (pro's high slope makes calibration especially effective).
2. Cost tradeoff: pro is ~4x flash. The recognition + slope gains likely justify it for the conviction KPI, but confirm calibrated MAE + conviction on 50 before switching the production model (model change -> deploy is the user's call).
3. The inference-time levers (reranker bug-fix shipped; v17 rejected on calorie regression) remain as documented; none substitute for the generator upgrade.

## Related
- [[20260602_self_verification_implemented_same_tier_verifier_ineffective]] (meta: ~32 ceiling, capability-bound)
- [[20260602_broad_vlm_sweep_thinking_helps_slope]] (pro best portion slope 0.67; calibration projection)
- [[20260603_v17_full50_rejected_calorie_regression]] (v17 promote rejected)
