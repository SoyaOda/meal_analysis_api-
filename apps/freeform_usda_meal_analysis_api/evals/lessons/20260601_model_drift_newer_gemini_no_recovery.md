# Lesson: Newer Gemini models do NOT recover accuracy; ~20% is stable across models & retrieval versions

- Date: 2026-06-01
- Run: `evals/runs/20260601_221426` (full50, LOCAL fixed-retrieval, v13 prompt, paired BCa gate, `use_vlm_cache=false`)
- Decision: **Keep `gemini-3-flash-preview`** (no newer model improves). Drift root-cause NOT yet localized.

## Question
2026-02-25 baseline = 11.38% MAE (v11b). 2026-06-01 the same config reproduces ~20%. Hypothesis: `gemini-3-flash-preview` is a Dec-2025 preview that drifted; a newer Gemini should recover accuracy.

## Result (full50, paired vs gemini-3-flash-preview)
| model | mae% | high30 | latency | Δ(vs preview) 95%CI | p |
|---|---|---|---|---|---|
| gemini-3-flash-preview | 20.65 | 22.0 | 15.8s | — | — |
| gemini-3.5-flash | 24.95 | 28.0 | 17.6s | [-2.25, +10.30] | 0.19 |
| gemini-3.1-flash-lite | 20.86 | 26.0 | 31.1s | [-5.63, +5.09] | 0.94 |

## Findings
- **Newer Gemini models do NOT help**: 3.5-flash trends WORSE (point +4.3pt, p=0.19); 3.1-flash-lite is statistically identical (point +0.2pt, p=0.94) and 2x slower. Neither paired CI clears 0. → hypothesis REFUTED.
- **~20% is stable & reproducible**: gemini-3-flash-preview = 20.27% (remote, old retrieval, run 20260601_204037) and 20.65% (local, FIXED retrieval, this run). std ~0.3pt — far tighter than Feb's 2.36pt. The ~20% is the robust current reality.
- **Not retrieval** (Track B fix did not change it) and **not model-version** (newer don't help). The 11→20 gap is broad across the Gemini-flash family.

## What worked
- paired BCa gate correctly held all (no model promotes) and quantified the newer models as not-better.
- Two independent full50 measurements (remote 20.27 / local 20.65) corroborate ~20.5% → the new reality is well-established (effectively stability-confirmed).

## Open / unresolved
- Root cause of 11.38%→20% NOT localized. Remaining suspects: (a) broad Gemini-flash portion-estimation degradation over 3 months; (b) a pipeline/data difference between the Feb-deployed prod and the current code/data (hard to test without the Feb deployment).
- The aggregate calorie MAE is too coarse to localize this.

## Next hypotheses (recommended)
1. **Decompose the metric** (DEEP_REVIEW Track A P1): add signed bias + calibration slope + per-dish weight MAE + Hungarian dish-match. This tells whether the 20% is portion OVER/UNDER-estimation (model behavior) vs wrong-record matching (retrieval/DB) — the only way to localize the regression.
2. Keep `gemini-3-flash-preview` as the model (best available; cheapest; fastest; tied-or-better vs newer).
3. Re-baseline current_baseline.json to the current reality (~20.5%) so PDCA has a valid reference; treat recovery toward 11% as the goal once #1 localizes the cause.
