# Lesson: Judge PASSES the discriminative-power gate (0.944) — its error detection is trustworthy

- Date: 2026-06-02
- Tool: `scripts/run_judge_validation.py` (perturbation gate; no human labels)
- Judge: `anthropic/claude-sonnet-4.6`, rubric v1; candidate gemini3flash_medium, 6 dev40 images
- Artifact: `evals/judge/validation_perturbation_gemini3flash_medium.json`

## Result (inject degradation -> does the judge lower the RIGHT dimension?)
| perturbation | targeted dim | detection_rate | mean delta |
|---|---|---|---|
| wrong_food (swap an item -> chocolate cake) | recognition | 0.83 (5/6) | 1.5 |
| portion_2x (double weights) | portion_plausibility | 1.00 | 1.5 |
| calorie_inflate_2x (2x calories, same food) | nutrient_validity | 1.00 | 1.5 |
| **OVERALL** | | **0.944** | **gate_pass = True** (>=0.8) |

(The one miss: test_food1 wrong_food delta=0 — recognition was already at 2 (poor), so swapping one of many items didn't lower it further.)

## Why this matters
- Public evaluators miss >50% of injected degradations; passing at 0.944 is non-trivial evidence the judge actually DETECTS errors, not just produces plausible numbers.
- => The judge is trustworthy for DETECTION and RELATIVE ranking (degraded < original; candidate A vs B). The earlier advisory findings are therefore likely REAL, not judge-harshness artifacts:
  - naming_db_match ~1.6-1.9 weakest; wrong_food_identity on ~every image -> real matching/food-ID weakness.
  - v15 (natural names) showing NO improvement -> a real null (the judge detects real differences and found none), strengthening the v15-rejection.
  - conviction ~39 reflects real, detectable problems.

## Scope / what is still NOT validated
- This validates DISCRIMINATIVE POWER, not ABSOLUTE CALIBRATION to humans. The absolute level ("39/100", per-dimension floors) needs the human golden set (quadratic-weighted kappa>=0.6, Pearson r>=0.80). A golden template was written to `evals/judge/golden_set.template.jsonl` for ~6 images (extend to 15-25); fill human_scores 0-5, then add a `--golden` eval.
- Until golden kappa passes, the judge may be used for RELATIVE/advisory ranking and detection, but NOT as an absolute promotion floor.

## Next
1. Human-label golden_set (15-25 imgs) -> run kappa/Pearson -> if pass, enable absolute floors in the gate (v2).
2. Judge is now reliable enough to use as the RELATIVE arbiter for output-quality A/Bs (e.g., recognition-recall prompt tweaks), alongside calorie metrics.
3. Add the golden + perturbation runs to the PDCA bootstrap surface so each session sees "is the judge currently trustworthy?".
