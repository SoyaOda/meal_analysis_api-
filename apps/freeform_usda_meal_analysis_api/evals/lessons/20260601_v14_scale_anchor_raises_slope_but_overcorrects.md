# Lesson: v14 (uncap + scale anchor) raises calibration slope 0.42→0.66 but OVER-corrects bias → hold

- Date: 2026-06-01
- Run: `evals/runs/20260601_232440` (dev40, LOCAL fixed-retrieval, paired BCa gate, decomposition + Theil-Sen slope, `use_vlm_cache=false`)
- Decision: **HOLD v14. Keep v13.** But the experiment validated the diagnosis and the lever.

## What v14 changed (vs v13)
Removed the weight_g hard caps (80-400 / 5-120), added a numeric plate/bowl-diameter SCALE ANCHOR, emphasized food HEIGHT/piling (volume = footprint × thickness), and explicit hidden cooking-oil / added-fat accounting. Kept v13's grams output, 3-pass CoT, beverage handling. Generic (no eval-specific info).

## Result (dev40, paired vs v13)
| candidate | mae% | high30 | signed_mean% | OLS slope | TS slope | macro MAE% (P/F/C) |
|---|---|---|---|---|---|---|
| v13_baseline | 22.06 | 20.0 | -5.3 (under) | 0.350 | 0.422 | 20.6/41.3/25.0 |
| v14_scale_anchor | 23.88 | 32.5 | +14.8 (OVER) | 0.427 | 0.664 | 30.3/42.3/35.3 |
- paired Δ(v14−v13) calorie-error CI = [-5.63, +10.62], p=0.66 → NOT significant on MAE.

## Findings
- **The lever works (diagnosis confirmed)**: removing the caps + scale anchor lifted Theil-Sen calibration slope 0.42 → 0.66 (toward the research-predicted ~0.6-0.7 prompting ceiling). This PROVES the v13 weight caps were a slope-flattening / regression-to-prior mechanism.
- **But prompt-only OVER-corrects**: signed bias flipped from -5.3% (under) to +14.8% (over); MAE rose 22.06→23.88, high30 20→32.5, p90 42→54, and macro MAE worsened (protein 20.6→30.3, carbs 25→35). Uncapping + "scale up large portions" + hidden-oil together pushed portions too high.
- → Confirms the architecture conclusion: a prompt can move the SLOPE but cannot land the BIAS at 1:1; the principled fix is a **post-hoc calibration layer fit on a held-out set** (slope+intercept), with the prompt providing only a mild, non-overshooting slope lift.

## What worked
- The new decomposition + Theil-Sen slope made the over-correction immediately visible — MAE alone (+1.8pt, p=0.66) would have read as "noise / no change", hiding that the error STRUCTURE flipped under→over. Judging by slope + signed bias (not MAE) was essential.

## Caveat
- dish_match recall is low (0.08-0.10) because difflib name similarity cannot match USDA-style predicted names ("Chicken, broilers...") to short GT search_names ("chicken breast"). The dish-match metric needs SEMANTIC name similarity (embedding) to be trustworthy; until then the reliable diagnostic is the calorie-level slope/signed bias, not dish recall/weight MAE.

## Next hypotheses
1. **Milder v14b**: keep uncap + numeric scale anchor, but DROP the aggressive "scale up large portions" wording and soften hidden-oil, to raise slope toward ~0.6 WITHOUT flipping bias to over. A/B judged by signed_mean staying near 0 AND slope rising.
2. **Post-hoc calibration layer (the real fix)**: acquire an external held-out set (Nutrition5k subset / fresh labels), fit Theil-Sen slope+intercept on it, apply `corrected=(raw-b)/m` after Step 4, validate on the frozen 50. This is the only lever that lands slope at ~1.0 regardless of prompt overshoot.
3. Upgrade dish_match to embedding-based name similarity to make identification-vs-portion separable.
