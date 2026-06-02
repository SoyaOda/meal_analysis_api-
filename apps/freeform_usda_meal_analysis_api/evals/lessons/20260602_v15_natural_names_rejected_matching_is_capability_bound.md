# Lesson: USDA-matching errors are VLM food-ID bound, NOT naming-style — v15 natural-names rejected

- Date: 2026-06-02
- Runs: retrieval probe (manual /retrieve), v13-vs-v15 eval `evals/runs/20260602_133904` + judge (20 imgs, sonnet-4.6, advisory)
- Decision: **Reject v15. Keep v13.** The prompt-naming lever for matching quality is exhausted; validate the judge before further judge-driven optimization.

## Diagnosis (why matching looked bad)
- In every failed case, predicted ingredient_name == matched_db_description EXACTLY → retrieval faithfully matches whatever name it is given (the VLM effectively picks the USDA record via its name).
- **/retrieve probe with CLEAN GT names returns the CORRECT record ~8/9**: "potato salad"->Potato salad (not raw potato), "yellow squash"->summer squash yellow, "macaroni and cheese"->macaroni/noodles with cheese, "prosciutto"->Ham prosciutto, "figs"->figs, "broccoli"->broccoli, "asparagus"->asparagus, "mixed salad greens"->mixed salad greens. (Only "cherry tomatoes"->cherries failed.)
- => Retrieval is NOT the bottleneck for matching quality given a correct name.

## Hypothesis tested (v15)
Make the VLM output NATURAL names + put prep in `description` (let retrieval map to USDA), instead of v13's "USDA-style comma naming" (which makes the VLM guess DB records badly). Generic style examples only (no eval-derived foods; anti-overfit).

## Result (v13 vs v15)
- Deterministic token-overlap: v15 recognition F1 0.263->0.292 (precision 0.253->0.337 up, recall slightly down). Mild.
- **Judge (semantic, 20 imgs): NO improvement.** conviction 44.7->41.7 (overlapping CI), naming_db_match 1.9->1.8, recognition 2.4->2.2. `wrong_food_identity` still fires on ~20/20 images for BOTH.

## Findings
- **Naming STYLE is not the lever.** The dominant failure `wrong_food_identity` (~every image) is not fixed by natural vs USDA-style names. It is bound by: (a) the VLM's actual food IDENTIFICATION (capability — the broad model sweep showed conviction ties across models), (b) recognition completeness (missed sides), and (c) granular GT + a strict judge.
- **Token-F1 and the judge DISAGREED** on v15 (token said mild-better, judge said tied/worse). This is the textbook risk of optimizing against an UNVALIDATED judge: v15 is a live example. Until the judge is golden-validated, its absolute levels (conviction ~40, wrong_food on every image) and any judge-driven prompt decision are untrustworthy.

## Action / next
1. **Keep v13.** Do not adopt v15. The prompt-style lever for matching is exhausted.
2. **Validate the judge FIRST** (golden 15-25 imgs, weighted kappa>=0.6 + perturbation gate) before any further judge-driven optimization. Part of the wrong_food_identity rate may be judge strictness on granular GT (e.g. counting fine sub-items) rather than real errors.
3. Real matching/recognition levers (after judge validation): recognition recall vs precision balance (missed sides), per-food-class disambiguation in retrieval for the few genuine retrieval misses (e.g. "cherry tomatoes"->cherries), and accepting that food-ID is partly VLM-capability-bound (models tie).
4. The retrieval system itself is sound (correct record for correct name) — no reranker/fusion change warranted for matching quality.
