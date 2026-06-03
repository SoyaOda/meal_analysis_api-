# Lesson: gemini-3.1-pro recognition gain is STABLE (pro>flash in 4/4 runs) and its calorie under-bias is FIXABLE by calibration (-13.5% -> -1.6% held-out). Promote case strengthened; naming regression persists.

- Date: 2026-06-03
- Follow-up to the HOLD ([[20260603_gemini31pro_promote_hold_adversarial_verified]]), addressing the two gaps the adversarial review flagged: (1) stability untested, (2) pro introduces a calorie under-bias.

## Workstream 1 — STABILITY (4 independent runs: dev40 x3 + full50, fresh VLM, cache off)
Deterministic recognition F1 (credit-free, judge-independent) — pro vs flash:
| run | flash F1 | pro F1 | Δ |
|---|---|---|---|
| dev40_orig | 0.204 | 0.266 | +0.062 |
| dev40_rep1 | 0.252 | 0.268 | +0.016 |
| dev40_rep2 | 0.231 | 0.262 | +0.032 |
| full50 | 0.226 | 0.245 | +0.019 |
**pro > flash on recognition F1 in 4/4 runs** (and pro's F1 is tighter, 0.245-0.268, vs flash's 0.204-0.252). The recognition improvement is STABLE and reproducible — this was the missing stability evidence.

LLM-judge (rubric v2) across all 4 runs, pro vs flash:
- conviction Δ: +1.93, +1.52, +2.39, +2.10 -> **pro higher in 4/4 runs, mean +1.99**, consistent DIRECTION (though each run's CI overlaps -> NS individually; 4/4 same-direction is itself notable).
- naming_db_match Δ: -0.10, -0.15, -0.15, -0.10 -> **pro consistently LOWER on naming (4/4, mean -0.125)** — a real, reproducible small regression, not noise. (naming is a judge-reliable dim, kappa 0.67, and the #1 diagnosed conviction bottleneck.)
- per-dish correct% Δ: +4.5, -0.5, +1.7, +2.9 -> pro higher in 3/4 (noisier than F1, one flip).
- calorie MAE direction is NOT stable (pro better in 3/4, worse in 1) — consistent with the NS paired CI.

## Workstream 2 — CALORIE BIAS (calibration fit on DISJOINT data: fit dev40 -> test holdout10)
`fit_calorie_calibration.py` Theil-Sen, written to `evals/calorie_calibration_pro_v13.json` (enabled=false):
| held-out (n=10, disjoint) | RAW MAE | RAW signed | CAL MAE | CAL signed |
|---|---|---|---|---|
| pro_v13 | 16.48% | -13.53% | **13.98%** | **-1.59%** |
| flash_v13 | 20.58% | -14.51% | 15.61% | -6.58% |
- Calibration CORRECTS pro's under-estimation bias (-13.5% -> -1.6%) and, on this held-out set, **pro+calib (13.98%) beats flash+calib (15.61%)** with near-zero residual bias. (This is the PROPER disjoint validation via the script — distinct from the earlier ad-hoc 2-fold figure that was discarded. n=10 held-out is small, so treat the ~1.6pt MAE gap as suggestive, the bias correction as solid.)

## Updated assessment
The two HOLD conditions are now substantially met: (1) the recognition gain REPRODUCES (4/4); (2) the calorie under-bias is REMOVABLE by calibration (and pro+calib edges flash+calib on held-out). What REMAINS against pro: a small but consistent naming_db_match regression (-0.1, 3/3), conviction gains that are directionally consistent but individually non-significant, recognition F1 still a low-absolute token proxy, and ~4x cost.

## Recommendation (updated)
- pro is now a **validated recognition + calibrated-calorie improvement** with a reproducible-direction (NS) conviction lift and one reproducible downside (naming). It is a defensible upgrade IF the user accepts ~4x cost and ships calibration ON (fit on disjoint data). It is NOT a slam-dunk: the headline conviction is still not significant and naming regresses.
- Before a production switch: (a) decide the 4x cost is worth a recognition/calorie-with-calibration bet (conviction is not a proven lever); (b) ship the pro calibration config (corrects the -5.3% bias — do NOT deploy pro raw); (c) ideally re-confirm on a fresh held-out beyond holdout10 for the calibrated-MAE gap.
- The naming regression is worth a cheap follow-up: pro + the (now-fixed, bug-free) reranker instruction may recover naming, since reranking acts after the VLM name.

## Related
- [[20260603_gemini31pro_promote_hold_adversarial_verified]] (the HOLD this updates)
- [[20260603_gemini31pro_breaks_recognition_ceiling_deterministic]]
- [[20260602_calorie_calibration_layer_implemented]] (the calibration layer used here)
- [[20260602_reranker_instruction_was_inert_bug_fixed]] (reranker fix may recover pro's naming dip)
