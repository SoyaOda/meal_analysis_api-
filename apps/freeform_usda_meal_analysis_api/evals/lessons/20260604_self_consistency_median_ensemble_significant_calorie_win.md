# Lesson: self-consistency (median-of-K ensemble) — pure variance-reduction effect is REAL and generalizes (−3 to −4pt at fixed temp), but the NET win is temperature-confounded and did NOT replicate on N5k (NVReal-only at temp 0.5)

> **TL;DR — FINAL (settled by the temp-0.3 test)**: median-of-3 self-consistency gives a ROBUST but MODEST ~2pt realistic-range MAE reduction. The decisive recipe is **flash, PRODUCTION temp 0.3, K=3 different seeds, median of the total-calorie**. Different seeds at temp 0.3 give enough diversity (CV ~0.10) WITHOUT the temp-0.5 accuracy penalty. Pooled across NVReal+N5k (n=128): median-of-3 vs expected single = **−2.1pt, 95% CI [−3.94, −0.35], p=0.02 (significant)**. The earlier temp-0.5 "−7pt significant on NVReal" was inflated by temperature luck + small n; the robust value is ~2pt. Adoptable IF 3x inference cost/latency is acceptable for ~2pt (3x flash ≈ 1x pro cost, but more accurate than single pro). Needs a pipeline self-consistency wrapper.

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

## ⚠️ N5k generalization (2026-06-04) — the NET win did NOT replicate; temperature is a confound
Same recipe (flash, temp 0.5, K=5 seeds 1-5) on N5k 100 imgs (run `20260604_124142`, 55 in realistic range), baseline = N5k production temp-0.3 single (run `191805`):
| N5k realistic 200-1500 (n=55) | MAE |
|---|---:|
| production temp-0.3 single | 37.8% |
| temp-0.5 single | 43.8% (temp 0.5 HURTS here) |
| K=3 median ensemble | 40.9% |
| K=3 median vs production single | **+3.2pt, CI[-3.1,9.8] NS (NOT better)** |

- **Decompose**: the pure ENSEMBLE effect (same temp 0.5: single→K3-median) is POSITIVE on BOTH sets (NVReal −4.3pt, N5k −2.9pt) → variance reduction generalizes. BUT raising temp 0.3→0.5 to get diversity COSTS single-sample accuracy, and that cost is distribution-dependent: ~0 on NVReal (so net win), but **+6pt on N5k** (so it cancels the −2.9pt ensemble gain → net slightly worse).
- **Revised conclusion**: self-consistency's NET benefit is NOT robust at temp 0.5 — it helped NVReal partly by temperature luck + small n. The ensemble (variance-reduction) effect is real and generalizes; the open problem is getting diversity WITHOUT a single-sample temp penalty. **Do NOT adopt temp-0.5 K=3 as-is.**
- **Next to settle it**: a temp sweep — test K=3 median at temp 0.3 and 0.4 vs temp-0.3 single on BOTH sets. If a lower temp gives enough diversity for the ensemble to net-win on both, that is the robust recipe; if not, self-consistency is parked. (Alternatively diversify via prompt-paraphrase or seed-only at temp 0.3, decoupling diversity from the accuracy-hurting temp.)

## DECISIVE temp-0.3 test (2026-06-04) — settles it: robust but modest ~2pt
To remove the temperature confound, ran flash at PRODUCTION temp 0.3 with K=3 DIFFERENT seeds (1-3) on both sets (runs `20260604_141309` NVReal, `20260604_151623` N5k). Different seeds give diversity (CV ~0.10) without raising temp.
| realistic 200-1500 | expected single | K=3 median | Δ |
|---|---:|---:|---:|
| NVReal (n=73) | 23.0% | 20.2% | −2.8pt |
| N5k (n=55) | 40.7% | 39.6% | −1.1pt |
| **POOLED (n=128)** | — | — | **−2.1pt, CI [−3.94,−0.35], p=0.02 SIG** |

- **Verdict: median-of-3 at temp 0.3 (seed diversity) robustly cuts realistic-range MAE ~2pt** (pooled significant, both sets same direction, NO temp penalty). The per-set tests are individually NS (n too small) but the pooled effect is significant and the direction is consistent across all 4 measurements (NVReal/N5k × temp0.3/0.5).
- The vs-production-single (seed7) comparison is muddied by seed luck (seed7 is a good draw on N5k, a bad draw on NVReal) — that's exactly the per-image variance the ensemble reduces; compare ensemble to the EXPECTED single, not one lucky/unlucky seed.
- **Recommended recipe: flash, temp 0.3, K=3 seeds, median(total_calorie).** Modest (~2pt) but real and distribution-robust. Adopt only if 3x inference (cost+latency, parallelizable) is justified for ~2pt — a product call. Needs a pipeline self-consistency wrapper.

## Related
- [[20260604_realistic_range_error_decomposition_grams_vs_density]] (showed the error is variance → motivated this; variance IS partly reducible after all, via diverse sampling + median)
- [[20260604_v14_portion_scaling_helps_slope_but_not_realistic_range]] (prompt lever that failed — contrast)
- `docs/MOZU_PDCA_SUMMARY_20260604.md` (next-steps item: variance reduction = this)
