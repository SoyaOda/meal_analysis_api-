# Lesson: Retrieval weight sweep on FIXED fusion (Track B) — no promote

- Date: 2026-06-01
- Run: `evals/runs/20260601_211040` (dev40, LOCAL server with Track B retrieval fix, v13 prompt, `use_vlm_cache=false`, paired BCa gate, concurrency 3)
- Decision: **Hold all. No weight config beats current.** Retrieval weights are not the calorie-MAE bottleneck.

## Context
Track B fixed the dense score (`1/(1+d)` distance-transform → direct cosine similarity) + added query L2-normalization. The fusion weights (bm25=0.4/vector=0.6/rrf_k=60/rrf_weight=0.55/stage1_top_k=50) were tuned against the OLD distorted objective, so re-swept on the fixed retrieval.

## Result (dev40, paired vs weights_current)
| candidate | mae% | high30 | Δ(vs current) 95%CI | p |
|---|---|---|---|---|
| topk_80 (stage1_top_k=80) | 19.14 | 22.5 | [-6.41, +1.37] | 0.32 |
| rrf_dominant (rrf_k=30, rrf_w=1.0, bm25=0.3, vec=0.3) | 20.28 | 22.5 | [-4.23, +1.77] | 0.59 |
| weights_current (0.4/0.6/60/0.55/50) | 21.14 | 22.5 | — | — |
| more_bm25 (0.5/0.5) | 21.55 | 25.0 | [-4.82, +5.15] | 0.87 |
| more_vector (0.3/0.7) | 21.82 | 22.5 | [-2.00, +3.56] | 0.64 |
| lower_rrf_k (rrf_k=30) | 22.25 | 22.5 | [-1.36, +3.51] | 0.39 |

- **All paired Δ CIs straddle 0; all p>0.3** → no weight config significantly changes calorie MAE.
- paired gate correctly held all candidates (no false promote on point-estimate noise).

## What worked
- Track B fix is **safe**: fixed-retrieval current weights = 21% on dev40, consistent with v11b/v13 ~20% on full50 (run 20260601_204037). The fix did not degrade calorie accuracy.
- paired BCa gate prevented adopting topk_80 on a non-significant -2pt point estimate.

## What did not work
- No retrieval-weight reconfiguration improves calorie MAE. Consistent with: VLM portion estimation (and current model/infra drift) dominates calorie error, not food→DB match weighting.

## Action taken
- Hold current weights (code defaults unchanged: bm25=0.4/vector=0.6/rrf_k=60/rrf_weight=0.55/stage1_top_k=50).
- Track B math fix retained (it is a correctness fix; relative MAE neutral but removes an undocumented provider-normalization dependency + the inverted score transform).

## Next hypotheses
1. **Re-baseline first** (see `20260601_v13_vs_v11b_tie_and_baseline_regression.md`): the ~20% is dominated by model/infra drift; weight tuning cannot recover the 11%→20% loss.
2. Retrieval quality is better measured by per-dish match accuracy (Hungarian dish-match metric from the DEEP_REVIEW roadmap), not aggregate calorie MAE — the calorie metric is too insensitive to retrieval changes to drive weight tuning.
3. If pursuing weights later: confirm topk_80 on full50 only if a per-dish-match metric also favors it; otherwise not worth the latency.
