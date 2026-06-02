# Lesson: Rubric v3 (mechanical portion) does NOT pin portion — portion should be a DETERMINISTIC metric, not an LLM-judge dimension

- Date: 2026-06-02
- Rubric: `evals/judge/judge_rubric_v3.txt` (EXPERIMENTAL, **not promoted**; default stays v2). Diff vs v2 = portion_plausibility block only.
- Re-validation: fresh fast judge (sonnet-4.6) `judge_gemini3flash_medium_v3.json` AND fresh Opus-4.8 draft `golden_set.draft_claude_v3.jsonl`, both on the same 20 outputs (run `20260602_092436`).

## What v3 tried
Replace v2's qualitative portion bands ("most / several / mixed") with a MECHANICAL rule: build the matched-item set (status correct/coarse_ok), compute `rel_err = |pred_g - gt_g|/gt_g` per item, bucket within_10/within_25/over_25, then score by an exact `f25`/`f10` threshold table. Goal: kill the v2 systematic +1 offset (v2 portion r=0.63 but kappa=0.19).

## Result: it made portion WORSE, and exposed the real problem
| portion (judge vs Opus draft) | v2 | v3 |
|---|---|---|
| weighted kappa | 0.19 | 0.27 |
| Pearson r | **0.63** | **0.42** |
- v2 disagreement was an almost-pure +1 offset (17/20 exactly +1). v3 disagreement is SCATTERED: |diff| 0/1/2/>=3 = 6/5/5/3, with wild per-image swings (test_food7 judge=1 vs draft=5; test_food17 judge=1 vs draft=4; test_food13 judge=5 vs draft=3).
- The mechanical rule REQUIRES the judge to (a) decide which pred item matches which GT item and (b) do per-item arithmetic. **The fast judge (sonnet) cannot execute this reliably** — one mis-matched or mis-read item flips `f25` across a threshold and the score jumps 2-4 points. We traded a stable offset (good r) for matching/arithmetic noise (bad r).

## n≈20 self-agreement is too noisy to gate
nutrient_validity rubric was UNCHANGED v2→v3, yet on fresh re-runs its judge-vs-draft mean-diff moved +0.60→+1.05 and the golden kappa fell 0.64→0.41. An unchanged rubric should not move that much — so the n≈20 Claude-vs-Claude signal has a ±0.4 / ±0.2-kappa run-to-run noise band. The v2 "nutrient kappa 0.64" was partly lucky; **do not treat a single n=20 self-agreement kappa as a hard gate.**

## The actual fix: portion is a NUMBERS question — compute it deterministically
`run_pdca_batch_eval.dish_match_metrics` already computes `portion_bands` (within_10/within_25/gross) via Hungarian matching, with the SAME thresholds the v3 rubric asked the LLM to apply. Deriving a 0-5 portion score from those bands gives a signal that is:
- **perfectly stable** (zero run variance -> self-agreement kappa = 1.0 by construction), and
- **closer to the careful Opus pass than the fast judge is**:

| portion agreement vs Opus-draft-v3 | weighted kappa |
|---|---|
| fast LLM judge (v3) | 0.27 |
| **deterministic metric** | **0.50** |

The deterministic metric's residual gap to the Opus draft is a MATCHING problem: the default token/char similarity (threshold 0.75) misses semantic matches and emits spurious 0s (test_food11, test_food13 -> det=0 where Opus matched semantically and scored 3). `dish_match_metrics(similarity_fn=...)` is already pluggable; an embedding similarity_fn would close most of that gap (and also improves recall/precision and naming, the shared upstream lever).

## Actions
1. **Do NOT promote v3.** Keep rubric v2 as default. v3 kept only as the documented experiment artifact (selectable via `--rubric-version v3`).
2. **Recommendation (needs sign-off — it changes the conviction KPI composition):** gate `portion_plausibility` on the deterministic `portion_bands` score, and downgrade the LLM judge's portion to ADVISORY (drop or de-weight it in the `overall_conviction` geometric mean, currently 0.20). The LLM judge keeps the dimensions only it can do: recognition, naming, nutrient macro-plausibility, conviction.
3. Next lever for BOTH deterministic portion accuracy AND naming: upgrade `_default_pred_gt_similarity` from token/char overlap to an embedding match (new dependency -> ask first).
4. Human golden labels remain the real arbiter for the LLM dimensions (n=20 self-agreement is advisory only).

## Related
- [[20260602_rubric_v2_stabilizes_nutrient]] (v2 fixed nutrient; flagged portion as the remaining unstable dim)
- [[20260602_golden_kit_and_judge_self_agreement]] (built the kit; first flagged portion/nutrient instability)
- [[20260602_judge_conviction_usda_matching_is_top_bottleneck]] (naming/matching is the conviction bottleneck — same upstream matcher lever)
