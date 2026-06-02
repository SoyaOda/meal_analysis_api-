# Lesson: Metric decomposition localizes the 20% to portion UNDER-estimation (calibration slope ~0.47)

- Date: 2026-06-01
- Tooling: `compute_decomposed_metrics` / `dish_match_metrics` / `extract_pred_items` / `load_label_items` added to `scripts/run_pdca_batch_eval.py` (no extra API; computed from already-stored `label`+`prediction`).
- Applied retroactively to runs `20260601_204037` (remote) and `20260601_221426` (local fixed retrieval).

## The decomposition (full50)
| config | mae% | signed_mean% | signed_median% | calib_slope | abs_kcal | fat MAE% |
|---|---|---|---|---|---|---|
| v11b (remote) | 20.3 | -3.4 | -7.2 | 0.46 | 138 | 39 |
| v13 (remote) | 20.7 | -6.2 | -13.3 | 0.47 | 145 | 38 |
| gemini-3-flash-preview + v13 (local fixed) | 20.7 | -6.7 | -13.3 | 0.48 | 145 | 41 |
| gemini-3.5-flash | 24.9 | -15.0 | -17.8 | 0.21 | 178 | 54 |

## Localization (the key result)
- **The ~20% is systematic portion UNDER-estimation, worst for large meals.** signed mean/median are negative across ALL configs; **calibration slope ≈ 0.47** (ideal 1.0) with intercept ~300 → `pred ≈ 300 + 0.47·true`: a 1500 kcal meal is predicted ~1010 (-33%). Low R² (~0.16) = noisy too.
- **It is a VLM portion/mass problem, NOT retrieval/matching** — consistent with: Track B retrieval fix didn't move MAE, and the weight sweep found no significant weight effect.
- Matches external research exactly ("VLMs systematically underestimate as portion grows, bias slopes -0.23..-0.50"; our slope 0.47 ⇒ bias slope ~-0.53).
- **fat is the worst macro** (38-41%, hidden cooking oils/fats) — a concrete prompt target.
- gemini-3.5-flash is worse on every axis (slope 0.21, signed -15%) — confirms not upgrading.

## What worked
- Decomposition turned an opaque 20% MAE into a specific, actionable diagnosis using data already on disk (zero new API cost).
- The signed bias + calibration slope cleanly separate "direction + scale of error" from aggregate magnitude.

## Action taken
- Added decomposition + Hungarian dish-match (scipy) to the eval; future runs auto-emit `decomposed` + `dish_match_agg` in summary + a "Diagnostic decomposition" markdown section; per-image `pred_items`/`dish_match` persisted (PART A) so dish-level identification-vs-portion error is measurable going forward.

## Next hypotheses (now well-targeted)
1. **Portion-estimation prompting** (highest ROI): plate/bowl-diameter scale anchor; explicit density reasoning for rice/pasta/piled foods; account for invisible cooking oils/fats (targets the fat MAE); an explicit upward correction / sanity-check for large plated meals. A/B with the hardened paired gate + judge by whether calibration_slope moves toward 1.0 (not just MAE).
2. **Calibration**: slope is remarkably stable (~0.47) → a held-out linear calibration could recover much of the loss, but prefer the prompt fix (avoid overfitting the 50-set; never embed eval-specific calibration constants per anti-overfit rule).
3. Use the new dish-match recall/precision once a fresh run captures `pred_items`, to confirm identification is fine and portion is the lever.
