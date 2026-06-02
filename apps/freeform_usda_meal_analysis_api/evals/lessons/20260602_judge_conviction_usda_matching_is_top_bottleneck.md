# Lesson: User-conviction judge reveals USDA-matching quality as the top bottleneck (models tie)

- Date: 2026-06-02
- Run judged: `evals/runs/20260602_092436` (broad sweep, v13 prompt, dev40, pred_items present)
- Judge: `anthropic/claude-sonnet-4.6` via OpenRouter, rubric v1, advisory (NOT golden-validated)
- Artifacts: `evals/runs/20260602_092436/judge_<candidate>.json`, `judge_summary.json`
- Decision: **Advisory only.** Surfaces a KPI-aligned finding that calorie MAE hid.

## user-conviction comparison (dev40, geometric-mean 0-100)
| model | conviction | CI | recog | naming | portion | nutrient | total | edits/img | human_review |
|---|---|---|---|---|---|---|---|---|---|
| gemini-3-flash-preview | 39.4 | [36,42] | 2.1 | 1.6 | 2.5 | 2.3 | 1.7 | 5.0 | 45% |
| gemini-3.1-pro | 39.0 | [37,41] | 2.2 | 1.6 | 2.2 | 2.5 | 1.6 | 5.3 | 45% |
| gemini-3.5-flash | 37.7 | [35,40] | 2.1 | 1.6 | 2.1 | 2.4 | 1.6 | 5.5 | 55% |

## failure_tag counts (gemini-3-flash, 40 imgs)
bad_usda_match 39 · wrong_food_identity 38 · missed_side 30 · hallucinated_item 29 · portion_underestimate 24 · raw_vs_cooked_mismatch 23 · compensating_error 21 · nutrient_inconsistent 20 · missed_main_food 10 · double_counting 8

## Findings
- **Model choice does NOT move user-conviction**: all three ~38-39/100 with overlapping CIs. (Contrast: for calibrated calorie MAE, gemini-3.1-pro was better via slope. Conviction is model-insensitive here.)
- **naming_db_match (1.6) is the weakest dimension** and the dominant conviction killer: `bad_usda_match` fires on 39/40 images, `wrong_food_identity` 38, `raw_vs_cooked_mismatch` 23. The user SEES the matched food name; a wrong/unacceptable USDA record destroys trust even when calories happen to be close (via compensating errors, tag count 21).
- **This REVISES the earlier "retrieval is not the bottleneck" conclusion — per KPI**: it is true for CALORIE MAE (the weight sweep moved MAE ~0), but FALSE for USER-CONVICTION, where USDA-matching QUALITY (right record: food identity + raw/cooked + specificity) is a top bottleneck. The calorie metric masked this; the conviction KPI is exactly what exposes it.
- Recognition is also weak (2.1: missed sides 30, hallucinations 29). Portion under-estimate (24) confirms the known bias. ~5 edits/image and 45% human-review = low current conviction.

## Caveats (honesty)
- Judge is ADVISORY: not yet validated against a human golden set (weighted kappa / perturbation gate per docs/EVAL_RUBRIC.md). The ABSOLUTE level (~39, ~5 edits) may be harsh/miscalibrated; the RELATIVE pattern (naming weakest; models tie; matching-failure tags dominate) is the robust signal. Validate before trusting absolute numbers or gating.
- 0 judge failures (all 120 calls parsed at max_tokens=4000). Cost ~$1.5/model (Sonnet vision).

## Next hypotheses (now KPI-aligned)
1. **Attack USDA-matching quality (the #1 conviction lever)** — distinct from calorie: improve food-identity + raw/cooked + specificity of the matched record. Levers: reranker instruction tuned for preparation-method & identity (not just name), source-tier priors (FNDDS vs SR Legacy), prepared-form disambiguation, and surfacing matched_db_description quality in eval. Re-judge to confirm naming_db_match rises.
2. **Recognition completeness** — reduce missed sides / hallucinations (prompt recall vs precision balance).
3. **Validate the judge** (golden 15-25 imgs) to make conviction gate-able, then add to the multi-objective gate (naming floor).
4. Optional: Opus judge + multi-sample for the validated pass; embedding-based recognition F1 for the cheap Tier0 layer.
