# Lesson: Rubric v2 tightening stabilizes nutrient_validity (kappa 0.22 -> 0.64); portion partially fixed

- Date: 2026-06-02
- Rubric: `evals/judge/judge_rubric_v2.txt` (now DEFAULT). v1 kept for reference.
- Re-validation: fast judge (sonnet-4.6) AND Opus draft BOTH re-run with v2 on the same 20 outputs; agreement = `run_judge_validation --golden judge_..._v2.json vs golden_set.draft_claude_v2.jsonl`. (Claude-vs-Claude self-agreement; human golden still pending.)

## What v2 changed
- **nutrient_validity**: made explicit and two-part: (a) self-consistency (calories ~= weight x per-100g AND plausible kcal/g 0.1-9) AND (b) macro plausibility vs GT. Stated outright that "item calories summing to the total is additive bookkeeping, NOT nutrient validity" — the exact leniency that made the v1 Opus draft score 4.0.
- **portion_plausibility**: explicit bands (within_10 -> 5, within_25 -> 4, 25-50% -> 3, >50% -> 2, systematic -> 1, gross -> 0) and "score only correctly-identified items' weights".

## Agreement: v1 -> v2 (judge vs Opus draft, n=20)
| dimension | v1 kappa | v2 kappa | v1 r | v2 r |
|---|---|---|---|---|
| nutrient_validity | 0.22 | **0.64** | 0.64 | **0.81** |
| total_plausibility | 0.41 | 0.56 | 0.58 | 0.78 |
| portion_plausibility | 0.17 | 0.19 | 0.39 | 0.63 |
| naming_db_match | 0.67 | 0.55 | 0.67 | 0.56 |
| recognition | 0.33 | 0.27 | 0.57 | 0.47 |
| user_conviction | 0.57 | 0.52 | 0.71 | 0.69 |
| composite Pearson r | 0.71 | **0.76** | | |
- Opus draft nutrient mean 4.00 (v1) -> 2.60 (v2), now near the fast judge (2.0).

## Findings
- **nutrient_validity is now gate-ready (kappa 0.64 >= 0.6, r 0.81)** — the tightening worked; the ambiguity was the whole problem.
- total_plausibility and composite r improved.
- **portion: correlation improved (r 0.39 -> 0.63) but weighted-kappa stayed low (0.19)** — the two judges now rank portions similarly but differ in absolute band placement (a systematic offset). v3 should pin exact band thresholds / examples or anchor to the deterministic portion_bands metric.
- naming dipped slightly (0.67 -> 0.55, n=20 noise); still moderate.
- Overall gate still not passed (portion is the floor), but this is self-agreement; the human golden remains the real arbiter.

## Action
- Adopt rubric v2 as default (run_judge_eval/validation `--rubric-version`, default v2; output files suffixed `_v2`).
- Next: v3 to pin portion band thresholds; then human-label golden (review the v2 draft) for the real kappa.
