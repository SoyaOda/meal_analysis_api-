# Lesson: v17 (describe-shape identity) REJECTED on full 50 — confirmed calorie-MAE regression (+4.6pt) from the bundled cooked-default

- Date: 2026-06-03
- Promote validation of the dev40 candidate v17 (describe-shape identity discipline + cooked-default). Run `20260602_235007`, FULL 50, v13 vs v17, use_vlm_cache=false.

## Result (deterministic, full 50)
| metric | v13_baseline | v17_identity |
|---|---|---|
| cal_MAE% | 18.14 | **22.78 (+4.6pt)** |
| high_error_rate_30% | 12.0 | 14.6 |
| portion_score_0_5 | 2.58 | 2.96 |
| recognition F1 | 0.2383 | 0.2508 |
| success | 50 | 48 |

(LLM-judge recognition/conviction NOT available — OpenRouter credit cap hit this session; see [[20260603_gemini31pro_breaks_recognition_ceiling_deterministic]].)

## Findings
- **The calorie-MAE regression is real and larger at n=50 (+4.6pt) than dev40 (~+4-5pt)** — consistent across three runs (v16, v17 dev40, v17 full50). The cooked-default clause ("prefer cooked/prepared form") systematically matches denser cooked records, inflating calories. recognition F1 is only marginally up (0.238 -> 0.251, within noise), and the dev40 conviction gain was already near the judge noise floor.
- The cost/benefit is clearly negative: a near-noise recognition nudge for a confirmed multi-point calorie regression.

## Action
- **Do NOT promote v17.** Keep v13 as the production prompt.
- The describe-shape identity component (which repeatably cut wrong_food in v16/v17) is still interesting, but it must be tested WITHOUT the cooked-default clause to avoid the calorie cost — and only if a generator upgrade (gemini-3.1-pro) does not already subsume the gain (pro improves recognition far more; see related lesson).
- Net: inference-time prompt tweaks on gemini-3-flash are exhausted as a conviction lever; the generator upgrade is the path.

## Related
- [[20260602_v17_describe_shape_identity_mild_win_near_noise]] (dev40 candidate)
- [[20260603_gemini31pro_breaks_recognition_ceiling_deterministic]] (the real lever)
