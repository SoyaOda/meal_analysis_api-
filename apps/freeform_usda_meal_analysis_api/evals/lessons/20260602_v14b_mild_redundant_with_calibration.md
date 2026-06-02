# Lesson: v14b (mild uncap+anchor) de-biases without over-correction, but is redundant with calibration → hold

- Date: 2026-06-02
- Run: `evals/runs/20260602_090935` (dev40, LOCAL fixed-retrieval, paired BCa gate + decomposition + Theil-Sen, `use_vlm_cache=false`)
- Decision: **HOLD v14b. Keep v13.** Calibration layer (on v13) is the cleaner lever.

## v14b vs v13 (dev40, raw)
| candidate | MAE% | high30 | signed_mean% | TS slope |
|---|---|---|---|---|
| v13_baseline | 20.59 | 17.5 | -6.68 (under) | 0.32 |
| v14b_mild | 20.78 | 20.0 | +0.77 (neutral) | 0.40 |
- paired Δ(v14b−v13) CI = [-4.91, +6.47], p=0.95 → no significant MAE difference.

## Calibration combo (2-fold CV on dev40, Theil-Sen)
| candidate | RAW MAE | + CALIBRATION (held-out CV) |
|---|---|---|
| v13_baseline | 20.59 | **16.89** (-3.7pt) |
| v14b_mild | 20.78 | 17.58 |

## Findings
- v14b fixed v14's over-correction: it de-biased (signed -6.68% -> +0.77%) WITHOUT flipping to large over-estimation (v14 was +14.8%), and nudged slope 0.32->0.40.
- BUT v14b does NOT beat v13 on MAE (20.78 vs 20.59, p=0.95): de-biasing the MEAN doesn't cut MAE because per-image VARIANCE (R^2~0.16) dominates.
- **v14b's prompt-level de-biasing is REDUNDANT with the calibration layer** - both remove the systematic bias. Stacking them slightly over-corrects (v14b+calib 17.58 > v13+calib 16.89). The calibration layer does the bias removal more cleanly and is re-fittable.

## Conclusion (prompt vs calibration for portion)
- Prompt-level portion edits are NOT the lever: v14 over-corrects, v14b is redundant. **Keep the conservative v13 prompt + apply the calibration layer.**
- The calibration layer (v13 + calib) reaches ~16-17% on dev40 CV (~15% on the earlier holdout10) - the real recovery toward the ~15% band.
- Remaining headroom (slope/variance, R^2~0.16) needs better portion DISCRIMINATION (e.g. DB household-measure mass anchoring, or depth/fine-tune), which prompting cannot provide.

## Action
- Hold v14 and v14b. v13 stays the prompt. Calibration layer remains the productionization path (needs external held-out fit before enabling).
