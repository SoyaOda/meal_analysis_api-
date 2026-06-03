# Lesson: gemini-3.1-pro promote = HOLD (adversarial-verified). Real recognition + tail gains, but headline KPIs non-significant, naming regresses, calorie under-bias introduced, 4x cost — decision is the user's.

- Date: 2026-06-03
- Clean single-variable A/B: gemini-3.1-pro-preview vs gemini-3-flash-preview, SAME v13 prompt (verified identical prompt_sha256 c8d2fb97, temp 0.3, seed 7, max_tokens 12288, reasoning_effort medium, cache off; only vlm_model_id differs). full50 run `20260603_100421` + dev40 run `20260602_235020`. Judge = sonnet-4.6 rubric v2 (ADVISORY: passed 0.944 discriminative gate, NOT golden-calibrated).
- A 4-agent adversarial review (steelman-for / steelman-against / skeptical fact-check / synthesis) was run on the promote decision and CAUGHT two overclaims in my first analysis (see Corrections).

## What is PROVEN (verified from artifacts)
- **Recognition improves on a deterministic, credit-free, judge-INDEPENDENT metric**, same direction on both splits and on BOTH recall and precision: full50 F1 0.226->0.245 (recall .238->.264, prec .221->.237); dev40 0.204->0.266. LLM-judge per-dish correct% agrees: 13.5%->16.5% full50 (42->55 dishes), 13.5%->18.0% dev40. This is the first lever this session to move recognition at all.
- **Worst-tail calorie improves** (point estimates): high_error_rate_30% 18.0->14.0, abs_kcal_mae 136->122, matched-weight MAE 24g->16g.
- **The harness gate verdict was HOLD for BOTH candidates.** pro did NOT clear the promote bar.

## What is NOT established (and CORRECTIONS to the first draft)
- **Conviction (headline KPI) is NOT significant**: 30.22 [25.5,35.1] -> 32.32 [27.0,37.3], CIs overlap at n=50. (An earlier rubric-v1 dev40 run even had pro/flash essentially tied.)
- **Raw total-calorie MAE is NOT significant**: 19.54->17.32 but paired BCa CI [-10.99,+3.02], sign-flip p=0.56 -> the promote bar's required ground-truth calorie comparison is a null.
- **CORRECTION 1 — slope advantage NOT established here.** The full50 artifact OLS slope is flash 0.550 -> pro **0.513 (pro LOWER)**. My ad-hoc Theil-Sen gave pro higher (0.61); the estimators DISAGREE, so "pro has better portion discrimination" is not robust on this run. The earlier sweep's TS 0.67 did not reproduce on the clean same-prompt full50.
- **CORRECTION 2 — calibrated-MAE win NOT established.** "16.38->15.15" was my ad-hoc 2-fold CV calc, NOT a run artifact; the project's own lesson flags CV-calibrated MAE as noisy at n<=50. Discard it as a promote argument.
- **Regressions**: naming_db_match 1.74->1.64 (DOWN; this is a judge-RELIABLE dim, kappa 0.67 — a legitimate caution, and naming is the diagnosed #1 conviction bottleneck). calorie signed bias flips +1.17% -> **-5.31% (systematic under-estimation)** — a model swap would push production totals low. hallucinated/img 1.74->1.82 (up; partly a mechanical consequence of pro listing more dishes, 310->334). nutrient_validity 1.96->1.86 dip lives on the judge's LEAST-calibrated dim (kappa 0.22) -> discount it.
- **Stability untested**: a single non-deterministic n=50 run; the promote bar requires >=2 repeats.

## Recommendation: HOLD — surface to the user as a cost-gated generator-quality bet
Do NOT switch production to pro on this evidence. pro is a genuine candidate (the only recognition + tail lever found), but on the project's own bar it does not promote (conviction NS, calorie NS, harness=hold, stability untested), it regresses naming and introduces a calorie under-bias, at ~4x cost. The decision is the user's.

### If pursuing pro, the conditions are:
1. >=2 stability repeats (`run_pdca_repeated_eval`) reproducing the recognition-F1 direction.
2. Fix/检查 the -5.3% calorie under-bias (fit the existing calibration layer on disjoint data; do NOT ship a low-biased model raw).
3. Cheaper alternative FIRST: if the motivation is calorie accuracy, enable the calibration layer on flash and measure it — the slope advantage that would justify pro is absent on this run.
4. Upgrade the judge toward golden calibration before trusting any conviction-based promote number.

## Meta
The adversarial review materially improved the conclusion — it caught that I'd imported the earlier-sweep slope (0.67) and an ad-hoc calibrated-MAE into a run where neither holds. Lesson for the PDCA loop: cite ONLY the run's own artifacts for promote claims; cross-run figures are context, not evidence.

## Related
- [[20260603_gemini31pro_breaks_recognition_ceiling_deterministic]] (the recognition result; corrected)
- [[20260602_judge_conviction_usda_matching_is_top_bottleneck]] (naming = #1 bottleneck; pro nudges it the wrong way)
- [[20260603_v17_full50_rejected_calorie_regression]]
