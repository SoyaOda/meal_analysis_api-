# Lesson: v17 describe-shape identity discipline gives a CONSISTENT but small wrong_food reduction (replicated 2x); mild conviction up, near the n=40 noise floor; small calorie cost

- Date: 2026-06-02
- v17 (`...ver_v17_identity_discipline_20260602.txt`, sha 38cc086a) = v13 + ONLY two changes: (1) a "Pass 2 (identity): before naming, note distinguishing visual features (grain shape/size, sauce color/opacity, surface dry/glazed/fried, cooked/raw) and choose the food matching those features, not the most common guess"; (2) a cooked-default line in AMBIGUITY POLICY. Isolated from v16 (dropped the visible_evidence field + whole-plate-scan + grounding rule that RAISED hallucination — see [[20260602_v16_grounding_mixed_identity_helps_evidence_field_backfires]]).

## Result (dev40, v13 vs v17, both fresh VLM, judge sonnet-4.6 rubric v2, advisory)
| metric | v13 | v17 |
|---|---|---|
| conviction | 31.47 | 33.67 |
| recognition | 2.10 | 2.15 |
| naming_db_match | 1.725 | 1.675 |
| per-dish wrong_food | 78 | **68** |
| per-dish correct% | 13.6 | **15.4** |
| hallucinated_items/img | 1.68 | 1.82 |
| missed_gt_items/img | 2.27 | 2.25 |
| cal_MAE% | 16.13 | 20.90 |

## Findings
- **describe-shape REPEATABLY reduces wrong_food**: v16 76->61 and v17 78->68 — two independent fresh-VLM runs both show the identity discipline cuts mis-identification (the shape/feature cue helps look-alike confusions: round pasta pearls vs rice grains, broccoli vs cabbage, sauce-coated vs plain). This is the most reproducible recognition signal found.
- conviction +2.2, correct% +1.8, recognition +0.05 — all in the right direction but SMALL and within the n=40 judge noise band (every arm this session sits at conviction 31-34).
- COST: cal_MAE 16.13 -> 20.90 (the cooked-default biases toward denser cooked records; within the wide single-run CI but a consistent direction across v16/v17). naming -0.05 and hallucination +0.14 are within noise.

## Status: CANDIDATE, not promoted
Per the project's promote bar (50-image full eval + Ground-truth total-calorie comparison + stability), v17 is NOT yet adoptable: the conviction/recognition gains are near the noise floor and there is a mild calorie-MAE cost. The wrong_food reduction is real (replicated) but the net conviction effect is marginal.

## Meta-finding (this session)
Across the reranker bug-fix A/B and v16/v17, **user-conviction sits at a ~32/100 ceiling for gemini-3-flash and NO single prompt/reranker lever has moved it beyond n=40 judge noise.** The ceiling is VLM-recognition-capability-bound. Bigger levers (a 2nd-call self-verification pass for precision, a stronger VLM tier, or multi-sample self-consistency) are the realistic path to a non-marginal gain, and are larger investments to be decided explicitly.

## Action / next options
1. To adopt v17: run a 50-image full eval + a stability repeat + confirm the calorie-MAE direction is acceptable (the cooked-default may need softening). Only then promote.
2. Bigger lever: implement the self-verification 2nd pass (generate -> confirm/drop each item) behind a config flag — the research's top precision lever, ~2x VLM cost.
3. Or accept that gemini-3-flash is near its recognition ceiling and revisit model choice.

## Related
- [[20260602_v16_grounding_mixed_identity_helps_evidence_field_backfires]]
- [[20260602_reranker_instruction_was_inert_bug_fixed]]
- [[20260602_v15_natural_names_rejected_matching_is_capability_bound]]
