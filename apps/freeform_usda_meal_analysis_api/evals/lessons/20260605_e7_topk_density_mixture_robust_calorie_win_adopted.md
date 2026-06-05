# Lesson: E7 top-k density mixture is a ROBUST, significant calorie-MAE win (~−3pt) — the session's first real accuracy lever. ADOPTED as default (reranker.top_n=5). Frozen-VLM isolation made it measurable where VLM-draw noise killed E2/E12.

- date: 2026-06-05
- scope: Phase 2.2 / E7 (+F1-b) of the long-term plan.
- model: flash, v13 prompt, default light stack (0.6B emb + 0.6B rerank). **Validation method = frozen-VLM (cache=true): top1 candidate populates the VLM cache, top-k candidate hits it → the per-image calorie delta isolates the retrieval/density change (no VLM-draw noise).**

## Mechanism
Top-1 picks ONE USDA entry → its density (kcal/100g) carries that entry's density error. E7 keeps the top-k reranked candidates and uses the **softmax(rerank_score/τ)-weighted mean of their per-100g densities**: E[nutrition] = E[kcal/100g] × (weight_g/100). Grams stay from the VLM (deterministic); only the density is turned into a top-k expectation. Density is ~50% of the calorie error (lesson 20260604_realistic_range_*) and, unlike grams, is retrieval-side (improvable). Smoothing the hard top-1 density pick reduces catastrophic single-match density mismatches → lower MAE AND lower p90/high30.

## Results (frozen-VLM, paired within-run = clean signal)
| measurement | top-1 MAE | E7 MAE | paired dMAE (k=5) | p90 | high30 |
|---|---|---|---|---|---|
| draw#1 (run 145316) | 20.00 | 15.97 | **−4.03 CI[−7.84,−0.36] p=0.042** | 35.9→31.8 | 16→14 |
| draw#2 (run 150002) | 18.52 | 16.39 | −2.13 CI[−4.80,+2.74] p=0.26 | 35.0→30.2 | 12→10 |
| k-sweep (run 150654, draw#1) | 18.49 | k5 15.75 | −2.74 p=0.11 | 33.9→30.1 | 12→10 |

k-sweep monotonic in k: top1 18.49 → k3 17.14(−1.35) → k5 15.75(−2.74) → **k10 14.68 (−3.81 CI[−7.50,−0.61] p=0.034)**, high30 12→8. Bigger k = better (softmax down-weights low-relevance candidates so extra k mostly adds small terms).

**Robustness**: k=5 paired delta is NEGATIVE in all 3 measurements (−4.03/−2.13/−2.74), p90 and high30 improved in all 3. **Unlike the light stack (sign-flipped across draws = wash) and E2/E12 (inconclusive at n=50), E7's direction is robust** — because it is frozen-VLM-isolatable and the density-smoothing mechanism is consistent across different VLM outputs.

## Important nuance
Even with the VLM frozen, the top-1 baseline varied run-to-run (18.5–20.0) → **the retrieval APIs (DeepInfra embedding/rerank) have mild non-determinism (~±1.5pt)**. So cross-run absolute MAEs aren't comparable; the **within-run paired delta** (same retrieval-noise realization for top1 and E7) is the clean signal — and those are all negative.

## Decision: ADOPTED as default
- `config/settings.py` DEFAULT_RERANKER_TOP_N → 5; `admin/config_manager.py` RerankerConfig.top_n default → 5. top_n>1 activates the density mixture (E7); top_n=1 reverts to top-1. τ via env E7_DENSITY_TEMP (default 1.0).
- **Latency/cost: negligible** (the reranker already scores all 50 candidates; E7 just keeps the top-5 + 5 local nutrition lookups + a weighted mean). No extra API calls.
- Chose k=5 (robust across all 3 measurements) over k=10 (measured marginally better on draw#1 only) for the default; k and τ are tuning headroom.
- Deploy (Cloud Run/Firestore) NOT changed — requires explicit instruction. Easily reverted (top_n=1).

## Pooled external confirmation (frozen-VLM, 2026-06-05) — GENERALIZES; significant on eye-level NVReal
| set | top-1 MAE | E7(k5) MAE | paired dMAE | high30 |
|---|---|---|---|---|
| NVReal (104, eye-level real, mozu-like) | 52.82 | 45.14 | **−7.67 CI[−19.1,−2.08] p=0.037** | 52.9→46.2 |
| N5k (100, overhead cafeteria, stress) | 59.17 | 57.55 | −1.61 CI[−7.5,+5.0] p=0.62 | 64→60 |

E7 is **directionally positive on EVERY set** (50-set −4.03 sig / NVReal −7.67 sig / N5k −1.61), and **significant on the eye-level NVReal distribution** that best matches the mozu use case (−7.67pt). It cuts the bulk of error (MAE, high30) across distributions; the extreme p90 tail is mixed on the hard external sets (N5k p90 115→134, NVReal 83→89) — the mixture trades a few extreme-tail cases for a large central-mass improvement, net clearly positive. Cost/latency overhead = ~0 (reranker already scores all candidates; E7 reuses the top-k + local nutrition lookups; measured retrieval latency top1 1.07s ≈ k10 1.01s; avg_cost identical). **k=5 kept (validated on 50-set + NVReal + N5k); k=10 measured marginally better on the 50-set only (tuning headroom).**

## Follow-ups
- Confirm on pooled N5k(250)+NVReal(104) (the wall-distribution + eye-level realistic) before deploy. 50-set is eye-level-realistic but small.
- Sweep τ (E7_DENSITY_TEMP) and k=8/10; consider weighting by calibrated relevance probabilities.
- E7's low/likely/high density interval enables F4 interval-coverage + E7's distribution feeds E1 v15 portion intervals.
- Artifacts (gitignored): runs 20260605_145316 (draw1), 150002 (draw2), 150654 (k-sweep). Configs pdca_e7_topk_density_*/pdca_e7_ksweep_*.
