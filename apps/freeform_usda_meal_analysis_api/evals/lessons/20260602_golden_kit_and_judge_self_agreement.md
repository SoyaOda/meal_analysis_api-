# Lesson: Golden labeling kit built; judge self-agreement shows naming/conviction robust, portion/nutrient unstable

- Date: 2026-06-02
- Built: `docs/GOLDEN_LABELING_GUIDE.md`, `run_judge_validation.py --golden` (quadratic-weighted kappa + Pearson, dep-free), `evals/judge/labeling/*.json` (20 per-image inputs), `evals/judge/golden_set.draft_claude.jsonl` (Opus 4.8 max-care draft, for HUMAN review).
- Preliminary check: fast judge (sonnet-4.6) vs careful Opus draft on 20 images. **NOT human validation** (Claude-vs-Claude is partly circular) — it is an interim self-agreement / rubric-stability signal. Human review of the draft -> golden_set.jsonl is the real gate.

## Judge vs Opus-draft agreement (20 imgs)
| dimension | weighted kappa | pearson r |
|---|---|---|
| naming_db_match | 0.67 | 0.67 |
| user_conviction | 0.57 | 0.71 |
| total_plausibility | 0.41 | 0.58 |
| recognition | 0.33 | 0.57 |
| nutrient_validity | 0.22 | 0.64 |
| portion_plausibility | 0.17 | 0.39 |
composite Pearson r = 0.71, min kappa = 0.17, gate_pass = False (needs all kappa>=0.6 AND composite r>=0.80).

## Findings
- **naming_db_match and user_conviction are robust across two independent Claude passes** (kappa 0.67 / 0.57). The headline conviction findings — USDA-matching quality is the weakest dimension (draft mean 1.75 ~ judge 1.6) and overall conviction is low (~1.9) — reproduce under a careful Opus pass. Trustworthy.
- **portion (kappa 0.17) and nutrient (kappa 0.22) are UNSTABLE between judges.** Notably the Opus draft scored nutrient_validity mean 4.0 (rewarding additive self-consistency) while the fast judge scored ~2.4 (stricter). => the rubric's nutrient_validity (and portion) definitions are AMBIGUOUS and must be tightened before gating on them.
- This is exactly the value of a stability check: it localizes WHICH dimensions are gate-ready (naming, conviction) vs which need rubric work (portion, nutrient) — before spending human labels.

## Action / next
1. **Human review** of `golden_set.draft_claude.jsonl` -> correct -> save as `evals/judge/golden_set.jsonl` (guide: docs/GOLDEN_LABELING_GUIDE.md). Then `run_judge_validation --golden` gives the REAL human-vs-judge kappa.
2. **Tighten rubric v2 for nutrient_validity and portion_plausibility** (make nutrient_validity explicitly = self-consistency AND vs-GT-density, with 0/5 anchors; make portion bands explicit) — the two dims that disagree. Re-run self-agreement; expect their kappa to rise.
3. Until kappa>=0.6 on a dimension (human golden), do NOT use that dimension as an absolute gate floor. naming_db_match + user_conviction are the closest to gate-ready; portion/nutrient are advisory only.
4. The discriminative-power gate (passed, 0.944) + naming/conviction self-agreement together already make the judge a trustworthy RELATIVE arbiter for output-quality A/Bs.
