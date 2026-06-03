# Lesson: N5k pro-vs-flash test-retest — pro's calorie advantage is DIRECTIONALLY consistent but only BORDERLINE significant; pro is less reproducible than flash

- Date: 2026-06-03
- Two independent full N5k-250 runs, same v13 prompt, cache OFF, temp 0.3 seed 7, no judge (calorie deterministic). Run-1 `20260603_162853`, Run-2 `20260603_191805`. Motivation: CLAUDE.md mandates stability confirmation before adoption; Run-1 alone reported a SIGNIFICANT pro calorie win and we needed to know if it reproduces.

## Per-run results
| metric | Run-1 flash | Run-1 pro | Run-2 flash | Run-2 pro |
|---|---:|---:|---:|---:|
| total-calorie MAE | 68.4% | 58.4% | 66.4% | 61.9% |
| signed bias | +49.3% | +30.7% | +46.1% | +34.3% |
| paired Δ(pro−flash) | −9.97pt | | −2.69pt | |
| paired 95% CI | [−18.5, −1.3] **sig** | | [−13.2, +7.8] **NS** (p=0.42) | |

## Denoised (per-image avg of the two runs) — the robust estimate
- flash MAE **67.4%**, pro MAE **60.2%**, point gap **−7.2pt** (pro better).
- paired bootstrap 95% CI **[−15.2, +0.9], sign-flip p=0.076 → BORDERLINE (CI grazes 0)**.
- Pooling both runs as 500 paired obs gives CI [−13.7, −0.4] (nominally sig) but that double-counts the same 250 images → optimistic; the denoised CI is the honest one.

## Findings
1. **The Run-1 "SIGNIFICANT" was an optimistic single draw.** Direction is stable (pro better in BOTH runs), magnitude is stable (~7pt), but significance flips run-to-run. Honest statement: **pro lowers N5k calorie MAE by ~7pt (≈60% vs ≈67%), consistently, at borderline significance.** Do not claim a clean p<0.05 calorie win from one run.
2. **Reproducibility asymmetry (production-relevant).** Between the two runs, images with bit-identical abs%-error: **flash 131/250 (52%), pro 50/250 (20%)**; median run-to-run |Δ|: flash **0pt**, pro **10pt**; max tail: flash 308pt, pro **941pt**. → pro is materially noisier sample-to-sample. For a calorie tracker (same photo should give the same kcal), pro's higher run-to-run variance is a real cost, not just statistical noise. (Cache was OFF in both runs — confirmed cache_hit 0%, and flash still varied on ~40% of images, so this is genuine generation stochasticity, not cache reuse.)
3. **What DOES reproduce cleanly:** (a) N5k systematically OVER-estimates calories (flash +46–49%, pro +31–34%); (b) **pro over-estimates LESS than flash** in both runs; (c) recognition F1 ≈ flat (0.32–0.33) — discount it on N5k (ingredient-name mismatch).

## Implications / actions
- **Keep pro, but DOWNGRADE the calorie claim** in the SSOT: from "significantly better at N=250" to "directionally consistent ~7pt lower MAE + less over-bias, borderline significant, at the cost of higher run-to-run variance." pro adoption still rests on: lower point MAE, smaller over-bias, comparable recognition — not on a single-run p-value.
- **Stability gate going forward:** require ≥2 full runs and report the DENOISED paired CI, never a single-run CI, before any calorie-based promote (matches CLAUDE.md "反復評価で最終判断").
- **The reproducibility gap is its own follow-up:** if pro ships, consider averaging/self-consistency or lower temperature to cut its run-to-run kcal variance; quantify the user-visible variance on real data.

## Related
- [[20260603_nutrition5k_external_eval_generalization_gap]] (Run-1; its "SIGNIFICANT" is corrected here)
- [[20260603_frozen50_gt_is_gpt5pro_estimate_two_gate_strategy]] (two-gate eval; N5k is GATE A)
- [[20260603_pro_stability_confirmed_and_calorie_bias_calibrated]] (frozen-50 stability — different distribution)
