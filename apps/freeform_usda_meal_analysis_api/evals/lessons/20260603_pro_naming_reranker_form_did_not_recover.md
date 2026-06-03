# Lesson: form-tuned reranker instruction does NOT recover pro's naming regression (raw_vs_cooked got WORSE), though it improves deterministic calorie MAE (likely via full-fat default)

- Date: 2026-06-03
- Roadmap #1 (mozu): pro's naming_db_match dips -0.125 vs flash; diagnosed as mostly raw_vs_cooked form-matching (pro 28 vs flash 23). Hypothesis: a reranker instruction enforcing bidirectional form matching (raw-stays-raw + cooked-stays-cooked) + full-fat-default would recover it.
- A/B: pro + current default reranker vs pro + form-tuned reranker. SAME pro VLM output (cache shared) — only the reranker instruction differs (per-request override, Firestore untouched). dev40. Run `20260603_135055`. The reranker changed the selected record on 39/40 images (clean isolation confirmed).

## Result (dev40, judge sonnet-4.6 rubric v2 advisory)
| metric | pro+base reranker | pro+form reranker |
|---|---|---|
| naming_db_match | 1.725 | 1.75 (+0.025, noise) |
| raw_vs_cooked_mismatch (tag) | 20 | **25 (WORSE)** |
| per-dish correct% | 19.1 | 16.4 (down) |
| conviction | 33.07 | 31.85 (down) |
| recognition | 2.20 | 2.25 |
| **cal_MAE% (deterministic, same VLM)** | 24.55 | **19.67 (-4.9pt)** |

## Findings
- **The naming goal FAILED**: the form-tuned reranker did NOT reduce raw_vs_cooked (it INCREASED it 20->25), per-dish correct% dropped, conviction dropped. naming_db_match moved only +0.025 (noise). The bidirectional form instruction over-steered (same failure mode as the earlier rejected "hardened" reranker instruction).
- **Root cause of the non-fix**: the reranker only sees the VLM food-name QUERY, not the dish/visual context. pro's queries often do not carry an explicit raw/cooked form, so the reranker cannot reliably pick the right form — the form signal must come from the VLM PROMPT, not the reranker. naming is therefore NOT cheaply reranker-fixable.
- **Unexpected side-benefit**: the form reranker improved DETERMINISTIC cal_MAE 24.55->19.67 on the SAME VLM output. This almost certainly comes from the FULL-FAT-DEFAULT clause (picking regular over fat-free/light -> higher, more accurate calories), not the raw/cooked part. The full-fat-default is worth isolating as a calorie lever (separate from naming).

## Action
1. **Do NOT adopt the form-tuned reranker** for naming. pro's small naming regression (-0.125) is left as-is (it is minor vs the recognition gain).
2. If naming is revisited, the lever is the VLM PROMPT (have the generator state cooking form in the food name), NOT the reranker — but prompt changes risk the v17-style calorie regression, so weigh carefully.
3. **Follow-up worth doing**: isolate the FULL-FAT-DEFAULT-only reranker tweak (drop the bidirectional raw/cooked) to see if the -4.9pt cal_MAE win holds without the naming harm. Cheap (cache-shared reranker A/B).

## Related
- [[20260603_pro_stability_confirmed_and_calorie_bias_calibrated]] (the naming regression this tried to fix)
- [[20260602_reranker_instruction_was_inert_bug_fixed]] (reranker instruction now works; over-steering still a risk)
- [[20260602_v16_grounding_mixed_identity_helps_evidence_field_backfires]] (prior over-steering precedent)
