# Lesson: E1 v15/v18 (identity-first schema separation + anti-dense-default) is NOT a generalizing calorie win — its pooled −6.21pt is a SET-SPECIFIC calorie DEFLATION that only fixes N5k's small-dish over-prediction (lt_300 97→77%), is a wash on the mozu-representative eye-level sets, and WORSENS large-meal slope. The intended recognition lever did not generalize. Confirms the design pre-mortem; prompt/schema cannot deliver a distribution-robust calorie win.

- date: 2026-06-06
- scope: Phase 3 / E1 (roadmap "E1 v15 schema separation"). The "v15" prompt filename was already taken by the rejected natural-names experiment, so this is named **v18**.
- model/config: flash gemini-3-flash, light 0.6B stack, E7 reranker.top_n=5, K=1, use_vlm_cache=false. v13 (adopted) vs v18, paired within-run, pooled 3 sets.

## What v18 was
A risk-aware redesign (built by a workflow that mined 9 past schema-failure lessons + an adversarial pre-mortem). v18 = v13 + an internal 3-stage "separation of concerns": (A) commit food IDENTITY from distinguishing shape/surface features before naming; (B) PORTION grams independent of density; (C) DENSITY via `description` with an explicit **anti-cooked-default guard** ("when prep form is ambiguous, prefer the median/plain USDA variant, do NOT default to fried/full-fat/cooked-prepared"). Confidence change DROPPED to isolate the lever; v13 caps/anchors kept. No new parser-visible fields (query_extraction only reads search_name/description/weight_g/confidence). The pre-mortem verdict was **HOLD** — predicted to repeat the v17 +4.6pt regression — gated behind a cheap dev40 precondition.

## Process (cheap → escalate)
- **dev40 directional read (n=40, K=1):** v18 −1.63pt MAE (paired CI[−6.8,+2.4], p=0.50 = NS), recall +0.033, BUT signed bias shifted +2.86→−2.62 (−5.48pt = the density-steering engaged). Encouraging-but-noisy; escalated to pooled.
- **Full frozen-50 flipped the dev40 sign** (−1.63 → +0.46) from 10 extra images + a fresh draw = pure ±3pt draw noise. Reinforces: never trust n≤50 single-draw deltas.

## Pooled result (N=254, paired per-image)
| set | v13 MAE | v18 MAE | paired ΔMAE [CI] | signed bias v13→v18 | theil-slope v13→v18 | recall v13→v18 |
|---|---|---|---|---|---|---|
| frozen-50 (eye-level) | 15.97 | 16.43 | **+0.46** [−3.9,+4.7] NS | +3.23 → −3.07 | 0.664 → 0.412 | 0.280 → 0.320 |
| NVReal-104 (eye-level) | 45.20 | 43.51 | −1.69 [−8.7,+4.2] NS | +7.16 → +3.37 | 0.353 → 0.335 | 0.119 → 0.113 |
| N5k-100 (overhead, small) | 74.75 | 60.49 | **−14.26** [−27.5,−3.3] * | +58.4 → +43.6 | 0.928 → 0.953 | 0.280 → 0.288 |
| **POOLED** | | | **−6.21** [−12.0,−1.1] * | +26.6 → +17.9 (−8.6) | — | mixed |

## Verdict: REJECT (not a generalizing win)
- **The pooled −6.21pt is significant but SET-SPECIFIC** — cross-set ΔMAE signs are {+0.46, −1.69, −14.26} (sign-flip), driven almost entirely by **N5k's small-dish bucket: lt_300 MAE 97→77% (n=66)**. v18 is a near-uniform calorie **DEFLATION** (signed bias drops on every set, pooled −8.6pt) that:
  - HUGELY helps where v13 massively over-predicts (N5k small overhead dishes — the 1.27x small-dish pathology);
  - is a **wash on the two mozu-representative EYE-LEVEL sets** (frozen-50 +0.46 worse, NVReal −1.69 NS);
  - **WORSENS large meals** — NVReal gte_1500 74→76, frozen-50 700_1500 15→17, and pushes the frozen-50 slope DOWN 0.66→0.41 (more compression = the WRONG direction; the aggregate lessons want slope → 1.0).
- **The intended lever (identity discipline → recognition) did NOT generalize**: recall moved only on frozen-50 (+0.04); NVReal flat/down (−0.006), N5k flat (+0.008). The calorie effect is the density-deflation side-channel, not recognition.
- This is **prompt-level de-biasing**, which prior lessons (v14b) showed is redundant with — and stacks badly on — the calibration layer. A blanket deflation is exactly a negative calibration intercept and is distribution-specific by construction.

## Takeaways
- **CONFIRMS the design pre-mortem and the meta-finding**: a prompt/schema change cannot deliver a distribution-robust calorie win. The realistic-range residual is a ~20-24% variance floor; the systematic bias is set-specific (over on small overhead dishes, under on large meals) and CANCELS in aggregate — so any global prompt nudge helps one distribution and hurts another. The real lever is **conditional calibration (E14) on real measured data (E13)**, not prompt wording.
- **One useful nugget (NOT standalone-adoptable):** the anti-dense-default / "prefer median variant" guidance is a genuine, large fix for **small-dish OVER-prediction** (N5k lt_300 −20pt). This is the same target as **E2** (main_food 80g→20g floor). If mozu's real distribution is small-portion-heavy, a TARGETED small-dish lever (E2 floor + conditional "lean default for small items") is worth testing — but only conditioned on dish size, never as a global deflation (it worsens large meals).
- **Method**: judge calorie-touching prompts by SIGNED BIAS + SLOPE + per-bucket + CROSS-SET SIGN, not pooled MAE — the pooled −6.21* would have looked like a "win" without the per-set/bucket decomposition that exposed it as N5k-deflation.
- Artifacts (gitignored): runs 20260606_064313 (dev40), 065251 (frozen-50), 065312 (NVReal), 065337 (N5k). Config pdca_e1_v18_identity_separation_dev40_20260606.json. Tooling /tmp/e1_pooled_analyze.py. Design workflow result in the session transcript.
