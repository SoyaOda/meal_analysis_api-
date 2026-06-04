# Lesson: realistic-range (200-1500 kcal) calorie error decomposed — near-ZERO bias, ~50/50 grams vs density, the two systematic edges CANCEL → single-lever fixes don't help

- Date: 2026-06-04
- Free (no-API) decomposition of the realistic-meal-range calorie error, using existing run `20260604_090008` (flash v13, NutritionVerse-Real). Goal: after v14 portion-scaling failed to move the realistic range, find what actually drives the ~27% MAE there. Method: calorie ratio factorizes as `pred/GT = (pred_grams/GT_grams) x (pred_density/GT_density)`, with GT grams from manifest `total_food_weight_g`, pred grams = sum of pred_items weight_g, density = kcal/g.

## Result (realistic 200-1500 kcal, n=73)
| quantity | median | IQR |
|---|---:|---|
| calorie ratio pred/GT | **0.98** | [0.83, 1.26] |
| grams ratio (portion) | 0.88 (mild UNDER) | [0.77, 1.05] |
| density ratio kcal/g (matching) | 1.14 (mild OVER) | [0.97, 1.35] |

- Error contribution (mean \|log ratio\|): **grams 50% : density 50%** — equal.
- Counterfactual MAE: actual **27.1%**; if grams perfect → 23.7% (density-only); if density perfect → 19.7% (grams-only). Neither single fix gets below ~20%.
- Densities: GT median 1.76 kcal/g (range 0.69–4.40, wide food variety); pred median 2.09 kcal/g.

## Findings
1. **The realistic range has essentially NO calorie bias** (median ratio 0.98). The 27% MAE is almost pure per-dish VARIANCE: the model nails ~half the dishes and is ±25–35% off on the rest. There is no systematic offset to calibrate away.
2. **grams-under (0.88) and density-over (1.14) CANCEL** to give the unbiased 0.98 calorie ratio. This is a trap: **fixing only one lever breaks the cancellation and makes calorie WORSE** (e.g., correct the density-over alone → calorie ratio falls to ~0.88 under-biased). Any real improvement must fix BOTH in a coordinated way, or reduce variance.
3. **density-over (1.14x) = the USDA matching/reranker tends to pick calorie-DENSER food variants** (fried/full-fat over lean/median). This is the recognition/reranker axis, and it connects to the earlier "full-fat-default" reranker observation. A median-density matching bias would lower density toward 1.0 — but only helps if grams is simultaneously raised toward 1.0.
4. **grams-under (0.88x) = mild portion under-estimation** in the realistic range (far milder than the giant-plate compression v14 targeted, which is why v14 barely moved this range).
5. **~20-24% MAE survives even a perfect single lever** → photo-only estimation has an intrinsic variance floor here; prompt edits can shave the small systematic edges but not the variance.

## Implications / actions
- **No cheap prompt win remains for realistic-range calorie.** The bias is ~0; the error is balanced variance. Single-lever prompt/reranker fixes risk unbalancing the grams/density cancellation.
- **Variance-reduction is the only large lever left without new data**: e.g., self-consistency / multi-sample averaging (pro's higher run-to-run variance makes this especially relevant), or multiple-view aggregation. These cost latency/compute, not prompt effort.
- **A coordinated grams+density calibration needs real measured data** (per-food-type density priors + portion priors) → again points to the real-mozu-data bottleneck.
## Cross-set confirmation (N5k, overhead, free re-run)
Same decomposition on N5k realistic 200-1500 kcal (n=138, run `191805` flash v13): **calorie ratio median 1.02 (near-zero bias — CONFIRMS NVReal's 0.98), grams:density contribution 54:46 (CONFIRMS ~50/50)**. So the two ROBUST, generalizing facts are: (a) the realistic range is near-UNBIASED in calorie, (b) error splits ~50/50 portion vs density.
However N5k's individual edges are grams 1.01 / density 1.03 — both ~1.0, vs NVReal's 0.88 / 1.14. → **the specific systematic edges are SET-SPECIFIC (distribution/angle dependent), not a general bias.** This kills any "global grams or density nudge" idea: there is no general systematic edge to correct, only set-specific ones that a prompt can't target without overfitting. The remaining realistic-range error is intrinsic per-photo VARIANCE.

## Related
- [[20260604_v14_portion_scaling_helps_slope_but_not_realistic_range]] (why portion-scaling didn't move this range — answered here: grams is only half, and it's near-unbiased)
- [[20260604_nutritionverse_real_eyelevel_eval_pro_calorie_edge_not_robust]] (the eval) / `docs/MOZU_PDCA_SUMMARY_20260604.md`
