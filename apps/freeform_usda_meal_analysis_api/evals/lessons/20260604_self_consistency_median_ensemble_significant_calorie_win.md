# Lesson: self-consistency (median-of-K ensemble) SIGNIFICANTLY cuts realistic-range calorie MAE — the first real-world calorie lever found

- Date: 2026-06-04
- After the decomposition showed the realistic-range (200-1500 kcal) error is near-zero-bias VARIANCE, tested variance reduction via self-consistency: sample flash K=5 times (temp 0.5, seeds 1-5, same v13) and aggregate the total-calorie estimate. Config `pdca_flash_selfconsistency_k5_20260604.json`, run `20260604_105446`, NVReal first 60 images (40 in the realistic range). Baseline = production temp-0.3 single (run `20260603_232505` flash, same images).

## Result (realistic 200-1500 kcal, n=40, same images)
| method | MAE |
|---|---:|
| production temp-0.3 single (baseline) | 28.6% |
| temp-0.5 single (avg of 5) | 25.9% |
| K=2 median ensemble | 23.1% |
| **K=3 median ensemble** | **21.6%** |
| K=4 median ensemble | 21.2% |
| K=5 median ensemble | 21.8% |
| K=5 MEAN ensemble | 23.1% (median beats mean) |

- **K=3 median vs production single: Δ = −6.9pt, paired bootstrap 95% CI [−13.7, −0.7] → SIGNIFICANT** (CI excludes 0; n=40). Full-set (n=60) all-range: 40.9% single → 36.6% K=5 median.
- Per-image sample CV (multiplicative spread) median 0.13 at temp 0.5 → enough diversity for ensembling to bite.

## Findings
1. **Self-consistency is the FIRST significant real-world calorie lever found this session** (pro-adoption, calibration, portion-scaling, grams/density nudges all failed). It cuts the realistic-range MAE from ~28-29% to ~21.6%.
2. **MEDIAN aggregation beats MEAN** (21.6% vs 23.1% at K=5) — median is robust to occasional wild samples. Use median of the total-calorie estimates.
3. **K=3 is the sweet spot**: K=4/5 add nothing (21.6 → 21.2 → 21.8, flat). 3 samples capture the gain.
4. **Diversity is required**: the gain needs temp ~0.5 (CV 0.13). Production temp 0.3 is too reproducible (52% identical run-to-run) for ensembling to help much — so the recipe is temp ~0.5 + K=3 median, not just re-sampling at 0.3. Decomposing the −7pt: ~−4.3pt is the pure ensemble effect (temp-0.5 single 25.9 → K=3 median 21.6), ~−2.7pt is the temp shift (within small-n noise).
5. **Cost/benefit**: K=3 flash = 3x flash inference ≈ the cost of a SINGLE pro call (pro is 3.2x flash) — but more accurate than pro (21.6% vs pro's ~27%+ on this set). So K=3-median-flash dominates single-pro on both accuracy and (roughly) cost.

## Implications / actions
- **Strong candidate for adoption**: flash, temp ~0.5, K=3 samples, take the MEDIAN total-calorie estimate. Needs a self-consistency wrapper in the pipeline (call VLM 3x, aggregate). Latency rises ~3x (parallelizable) — acceptable for a high-value tracker; confirm UX.
- **Confirm before productionizing**: single set (NVReal eye-level), n=40, CI is significant but wide. Re-run on N5k (overhead) and/or more images to confirm the gain generalizes and to tune temp (sweep 0.4-0.7) and K.
- Open question: does the gain hold for RECOGNITION too (median/union of foods across samples)? Worth checking — could also reduce the lobster/jam misses via sample coverage.

## Related
- [[20260604_realistic_range_error_decomposition_grams_vs_density]] (showed the error is variance → motivated this; variance IS partly reducible after all, via diverse sampling + median)
- [[20260604_v14_portion_scaling_helps_slope_but_not_realistic_range]] (prompt lever that failed — contrast)
- `docs/MOZU_PDCA_SUMMARY_20260604.md` (next-steps item: variance reduction = this)
