# Lesson: Broad VLM sweep — thinking/pro models DON'T win on raw MAE but DO improve calibration slope (and win after calibration)

- Date: 2026-06-02
- Run: `evals/runs/20260602_092436` (dev40, LOCAL fixed-retrieval, v13 prompt FIXED, 8 models, paired BCa gate + Theil-Sen slope, `use_vlm_cache=false`)
- Decision: **Revises the earlier "freeze model" conclusion.** Raw MAE: no significant winner. After calibration: stronger thinking models win via higher slope.

## Raw results (v13 prompt fixed)
| model | MAE% | high30 | signed% | TS slope | lat(s) | ok/fail |
|---|---|---|---|---|---|---|
| gemini-3-flash high | 20.05 | 20.0 | -6.2 | 0.53 | 28.7 | 40/0 |
| gemini-3.1-pro | 20.22 | 22.5 | -12.2 | **0.67** | 27.0 | 40/0 |
| glm-4.6v | 21.24 | 35.0 | -8.6 | 0.45 | 75.0 | 40/0 |
| gemini-3-flash medium (current) | 21.25 | 17.5 | -6.4 | 0.40 | 20.4 | 40/0 |
| gpt-5.1 | 22.80 | 35.0 | -7.0 | 0.47 | 27.5 | 40/0 |
| gemini-3.5-flash | 24.90 | 32.5 | -15.8 | 0.24 | 22.6 | 40/0 |
| qwen3-vl-235b-thinking | 29.51 | 27.5 | +15.6 | 0.42 | 42.2 | 40/0 |
| kimi-k2.5 | 55.04 | 52.5 | -41.4 | 0.00 | 69.2 | 40/0 |
- All paired Δ(vs current) CIs straddle 0 → NO model significantly beats current on RAW MAE.

## Model + calibration (2-fold CV on dev40, Theil-Sen)
| model | RAW MAE | + CALIB MAE | raw slope |
|---|---|---|---|
| gemini-3.1-pro | 20.22 | **14.72** | 0.67 |
| gemini-3-flash high | 20.05 | 15.77 | 0.53 |
| gemini-3-flash medium (current) | 21.25 | 16.42 | 0.40 |
| gpt-5.1 | 22.80 | 16.25 | 0.47 |

## Findings (answers the "is thinking best?" hypothesis)
- **The thinking hypothesis is VALIDATED via SLOPE, not raw MAE.** More thinking (gemini-3-flash high: slope 0.40->0.53) and a pro reasoner (gemini-3.1-pro: slope 0.67) measurably improve portion DISCRIMINATION (calibration slope). Raw MAE hides this because all models share a similar ~-6% bias that dominates the metric.
- **Slope is the part calibration CANNOT fix** (calibration only removes bias). So a higher-slope model + calibration = lower calibrated MAE: gemini-3.1-pro+calib ~14.7% > flash-high+calib ~15.8% > current flash-medium+calib ~16.4%.
- This REVISES the earlier "freeze gemini-3-flash, model swap won't help" conclusion (`PIPELINE_IMPROVEMENT_PROPOSALS_20260601.md`): that held for RAW MAE, but is WRONG once calibration is in play — the model matters via discrimination.
- Losers confirmed: gemini-3.5-flash worse (slope 0.24); kimi-k2.5 catastrophic (55%, slope 0); qwen3-vl-235b over-estimates (+15.6%); gpt-5.1 mediocre.

## Trade-offs
- gemini-3.1-pro: best discrimination but ~4x cost ($2/$12 vs flash $0.5/$3) + slower (27s vs 20s).
- gemini-3-flash high: cheap (same model, ~$0.0077), slope 0.53, slower (28.7s from more thinking) — a low-risk config-only upgrade.

## Caveats
- dev40 2-fold CV (n=20 folds, n=40 total) is noisy; calibrated-MAE numbers have overlapping CIs though the slope ordering is clear and consistent. Confirm on full50 with an EXTERNAL held-out calibration fit before adopting.

## Next steps
1. full50 confirm: gemini-3-flash(high) and gemini-3.1-pro vs current(medium), each with externally-fit calibration; judge by slope + calibrated MAE + cost/latency.
2. Cheap immediate test worth taking: reasoning_effort=high on the current model (config-only, ~same cost, slope 0.40->0.53).
3. If accuracy > cost: gemini-3.1-pro is the strongest calibrated option (~14.7% dev40 CV).
