# Lesson: recognition self-consistency (union of K samples) trades recall for wrong-food — NOT a clean win; recognition misses are mostly SYSTEMATIC, not variance

- Date: 2026-06-04
- User asked to improve the specific recognition failures (lobster/jam/cucumber misses). Naming specific foods in the prompt = overfitting (forbidden by prompts/CLAUDE.md), so tested the GENERAL lever: union-of-K-samples self-consistency for recall, reusing the existing K=5 flash samples (NVReal run `20260604_105446`, no new VLM cost). Compared single (s1) vs union-of-5 food sets, scored semantically by an 8-way parallel Claude judge (workflow `nvreal-union-recall-judge`).

## Diagnostic first: misses are bimodal (systematic), not variance
Crude per-food coverage across the 5 samples (how many of 5 identified each GT food): **0/5 = 65, 5/5 = 53, partial (1-4/5) = only ~23**. The distribution is BIMODAL — a food is usually EITHER caught by all samples OR missed by all. lobster on idx 19/20/24 = 0/5 (every sample misses it). → the misses are SYSTEMATIC (samples agree), not sampling variance, so self-consistency has little headroom (only the ~23 partial cases are recoverable).

## Result (single vs union, n=40 imgs judged, 92 GT foods)
| | recall | wrong-food |
|---|---:|---:|
| single sample | 85.9% | 13 |
| union of 5 | 91.3% (+5.4pt) | 37 (+24, ~3x) |

## Findings
1. **Union improves recall +5.4pt but ~TRIPLES wrong-food** (13→37). It recovers some partial-miss foods but adds many phantom foods (the union has ~2.3x more items: median 3→7).
2. **Net-negative for the calorie pipeline**: the VLM food list feeds USDA retrieval + calorie summation, so the +24 phantom foods would ADD calories and worsen calorie MAE. Union helps the "did we name the foods" metric but hurts the headline (calorie). Not adoptable for a calorie tracker.
3. **Majority-vote (food in >=3/5 samples) would not help**: consistently-seen foods are already 5/5 (kept), partial foods (<3) get dropped — so majority ≈ single recall, no gain, with the benefit of not adding phantoms. I.e. no general self-consistency setting recovers the systematic misses without a precision cost.
4. The systematic misses are either genuine recognition gaps (lobster not recognized on crowded plates) or naming-format mismatches the semantic judge already credits (single recall is already 86%). Neither is fixable by a GENERAL prompt change without naming specific foods (overfit).

## Implications
- **Recognition is near its floor for general (non-overfit) levers**: single-sample recall ~82-86% (clean GT), and the remaining misses are systematic, not recoverable by self-consistency without inflating wrong-food / hurting calorie.
- Consistent with the session theme: the pipeline is near its practical floor with prompt/inference tuning; **real mozu measured data (and possibly product-level richer input) is the bottleneck** for further gains on both calorie and recognition.
- If recognition recall specifically matters (independent of calorie), union-of-K is a usable recall booster — but only where the downstream does NOT sum calories over the (inflated, phantom-containing) food list.

## Related
- [[20260604_recognition_clean_gt_pro_no_edge_flash_cost_rational]] (single-sample recognition ~82%, pro no edge)
- [[20260604_self_consistency_median_ensemble_significant_calorie_win]] (calorie self-consistency: median works ~2pt because calorie error IS partly variance; recognition misses are NOT, hence union fails)
