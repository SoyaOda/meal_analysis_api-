# Lesson: E3 uncertainty diagnosis — NO available uncertainty signal predicts calorie error (output proxies AND seed-dispersion both fail across 3 sets, pooled AUC 0.51), because error is systematic bias (portion/density) invisible to sample variance → E9/E18 cheap-signal versions are NOT viable. SAME run incidentally confirms self-consistency median-of-K is a ROBUST ~+2.5–3.2pt variance-reduction win at pooled N=253 (resolves the E12 question the n=50 draw-noise had hidden).

- date: 2026-06-05
- scope: Phase 3.2 / E3 (uncertainty diagnosis) of `plans/PDCA_ROADMAP_3AI_REVIEW_20260604.md`. Data-independent (no overfitting): measures correlations, tunes nothing on the eval.
- model/config: flash, v13 prompt (adopted text override), light stack (Qwen3-Embedding-0.6B + Qwen3-Reranker-0.6B), **E7 reranker.top_n=5**, cache=false.
- experiment: 5 seed-varied samples (seeds 1..5, each sc_k=1) per image on **3 sets** — frozen-50 (n=49 joined), NutritionVerse-Real eye-level (n=104), Nutrition5k test-100 (n=100). **Pooled N=253**, ≈1265 fresh VLM analyses. Runs (gitignored): `20260605_182320` (50), `20260605_201855` (nvreal), `20260605_201931` (n5k). Plus the free-proxy stage reused adopted-config runs `20260605_150654`/`154256`/`153348`.

## Question
E3 asks: does any uncertainty signal predict per-image calorie error? If yes → E9 (ask 1 question when uncertain), E18 (tiered routing / Pro as uncertainty detector), E12-selective (SC only on uncertain images) become viable. The 3-AI review called this the core remaining data-independent lever.

## GATE-1 — free output proxies (no re-run, from existing artifacts): NULL
9 proxies recoverable per image (n_pred, total_weight, total_cal, mean_item_cal, max_cal_share, mean/max weight, frac_extreme_weight, nutrient_self_consistency) vs |calorie %err|, 254 images on adopted config, 3 sets:
- Spearman ≈ 0 for all; the few whose bootstrap CI excluded 0 **sign-flipped across sets** (mean_item_cal +0.26 nvreal / −0.10 n5k). Pooled |ρ| ≤ 0.09.
- High-error AUC ≈ 0.43–0.55 (≈ random). Best (mean_item_cal 0.67 nvreal) was 0.37 (anti-predictive) on n5k.
- Selective abstention: only `max_cal_share` showed any repeatable lift, weak and set-dependent.

## GATE-2 — self-consistency dispersion (the strongest single-model signal): NULL for error
Per image, CV = std/mean of the K=5 total-calorie estimates; ensemble = median-of-5; error = |median − GT|/GT.

**Q1: does dispersion predict ENSEMBLE error?**
| set | n | CV ρ (Spearman) | AUC>median | AUC>30% |
|---|---|---|---|---|
| frozen-50 | 49 | +0.108 (ns) | 0.55 | 0.64 |
| NVReal | 104 | **−0.014 (ns)** | 0.48 | 0.44 |
| N5k | 100 | +0.085 (ns) | 0.52 | 0.52 |
| **POOLED (within-set rank-norm)** | **253** | **+0.048 CI[−0.08,+0.17]** | **0.51** | — |

- Direction is **not consistent** — NVReal (highest-quality eye-level real-measured GT) is zero/slightly negative. Pooled ρ≈0.05, **AUC 0.51 ≈ a coin flip**. The weak frozen-50 hint (ρ+0.11) does NOT generalize.
- Selective abstention by CV captured only ~0.17–0.24 of the oracle MAE-reduction on average (N5k f10 was −0.02). Not usable for E9.

**Why — the "confidently wrong" failure mode.** Among above-median-error images, **46% / 52% / 46%** (50 / nvreal / n5k) have **below-median CV**: the model is *stably* wrong. Example (frozen-50 `test_food3`): 5 seeds = [715,733,745,739,742] (CV 0.014, the most stable image) yet GT=1000 → 26% error. Calorie error is dominated by **systematic portion/density bias**, which is identical across stochastic samples → **invisible to any variance-based uncertainty**.

## Verdict (E3)
- **No readily-available uncertainty signal predicts calorie error.** Output proxies (null) and seed-dispersion (pooled ρ 0.05, AUC 0.51) both fail, robustly, across 3 sets.
- **E9 (clarify-when-uncertain) and E18 (tiered routing / Pro-as-uncertainty-detector) cheap-signal versions are NOT viable** — flagging high-dispersion/high-proxy images would not target the actually-wrong (confidently-wrong) answers.
- **Strategy redirect** (matches the 3-AI review's deeper claim): the real levers are **calibration (E14) and input information (E8 user_context / E13 real-data)**, not uncertainty self-detection. Bias needs correction, not abstention.
- **Untested, lower-probability signals** (left open, honest scoping): (a) VLM self-reported `confidence` — but the v13 prompt floors it at 0.70/0.60, compressing its range, and LLM confidence is typically poorly calibrated; (b) cross-MODEL disagreement (E18's actual mechanism) — but pro was already shown to make flash-correlated errors (pro撤回), so disagreement likely tracks the same confidently-wrong cases. A confidence test needs an additive `IngredientDetail.confidence` field + 1 instrumented eval (~$2.4); deferred unless requested.

## BONUS (same run) — self-consistency median-of-K is a ROBUST variance-reduction win at pooled N
median-of-5 vs the average single seed's MAE:
| set | n | avg single MAE | median-of-5 MAE | SC gain |
|---|---|---|---|---|
| frozen-50 | 49 | 15.7 | 13.2 | **+2.50pt** |
| NVReal | 104 | 42.9 | 39.7 | **+3.22pt** |
| N5k | 100 | 70.8 | 68.2 | **+2.54pt** |

- **Positive on all 3 independent sets** → this **resolves the contradiction** between `20260604_self_consistency_median_ensemble_significant_calorie_win` (pooled win) and `20260605_e12_self_consistency_v2_parallel_no_reproduce_at_n50` (didn't reproduce at n=50). The n=50 single-draw was too noisy (±3pt VLM-draw variance); at **pooled N=253 the K-median win is real and consistent (~+2.5–3.2pt).**
- **Q2: dispersion predicts where SC HELPS** — pooled Spearman(CV, sc_gain) = **+0.260 CI[+0.12,+0.39]** (significant; NVReal +0.332*). **Caveat: partly mechanical** (more sample spread ⇒ more reducible by averaging), and it is NOT a free selective lever — you must pay for the K samples to know the dispersion, and GATE-1/2 showed no cheap pass predicts it. So this supports "K-median works by variance reduction", not "selective SC is cheap".
- **Cost/accuracy curve (free, computed from the same K=5 data by averaging median-ensemble MAE over all C(5,K) seed subsets — matches production's seed convention):**

| set | K=1 | K=2 | K=3 | K=4 | K=5 |
|---|---|---|---|---|---|
| frozen-50 (n=49) | 15.70 | 14.19 | 13.89 | 13.45 | 13.20 |
| NVReal (n=104) | 42.88 | 41.73 | 40.74 | 40.39 | 39.65 |
| N5k (n=100) | 70.79 | 69.77 | 67.50 | 67.24 | 68.25 |
| **pooled (n-weighted)** | **48.64** | 47.48 | **46.11** | 45.78 | 45.83 |

  - **K=1→K=3 = −2.53pt (robust, all 3 sets); K=3→K=5 = only −0.28pt (and N5k K5>K4 = tail noise).** **K=3 is the sweet spot** — ~90% of the achievable variance-reduction benefit at 3× VLM cost; beyond K=3 is diminishing returns.
- **ADOPTED as CODE default (2026-06-05, user-approved cost):** `VLMConfig.self_consistency_k` default flipped **1 → 3** (admin/config_manager.py). Latency already neutralized to ~1.15× by E12-v2 parallelization (committed 8557d94); cost = 3× VLM (accepted).
- **Production-safety hardening shipped with the default flip:** the SC dispatcher now runs the K samples with `asyncio.gather(return_exceptions=True)` and ensembles over the **survivors** (`pipeline._select_resilient`) — a single transient sample failure no longer 500s the whole meal analysis (the e12-lesson failure mode). Hard-fails only if ALL K samples fail (no fallback); cooperative `CancelledError` is re-raised. 4 new unit tests; pytest 82 pass / ruff clean.
- **Prod deploy still pending (explicit instruction):** prod Firestore is still `self_consistency_k=1`, so /health now shows an intended `vlm.self_consistency_k` drift (served=1 vs default=3) that flags the pending deploy. To activate in prod: PUT `vlm.self_consistency_k=3` to Firestore (+ optionally re-deploy the image carrying the resilience fix).

## Follow-ups
- If pursuing accuracy regardless of VLM cost: A/B K=3 vs K=5 vs K=1 on pooled sets for the cost/accuracy curve, then decide default K.
- Pivot uncertainty effort away from self-detection toward **E14 conditional/hierarchical calibration** (food-group × container × size × the confidently-wrong systematic bias this lesson exposed) and **E8 user_context** — but both need E13 real measured data (still the blocker).
- Optional 100%-closure: instrument `IngredientDetail.confidence` (additive) + 1 eval to bury self-reported confidence too.
- Tooling (gitignored, /tmp): `e3_free_proxy_analysis.py`, `e3_dispersion_pooled.py`. Diagnostic config committed-eligible: `evals/configs/pdca_e3_sc_dispersion_diag_k5_20260605.json`.
