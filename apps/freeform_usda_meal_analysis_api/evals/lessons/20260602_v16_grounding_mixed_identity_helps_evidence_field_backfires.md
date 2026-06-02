# Lesson: v16 anti-hallucination grounding is a WASH — the per-item evidence field BACKFIRES (hallucination up), but describe-shape identity helps wrong_food

- Date: 2026-06-02
- Context: VLM-recognition PDCA. Research+diagnosis (7 agents) localized the conviction ceiling to VLM recognition: hallucinated ~1.55/img (phantom fruit/apples on 11/40 imgs, phantom default sides, phantom condiments), missed ~2.1/img, wrong_food ~2.0/img (couscous->rice 5/5, caesar-default, mac&cheese->plain pasta, broccoli->cabbage).
- v16 (`...ver_v16_visibility_grounding_20260602.txt`, sha 96bcc969) bundled FOUR changes onto v13: (1) global visibility-grounding rule ("list only clearly visible; don't add typical accompaniments"), (2) a per-item `visible_evidence` JSON field (parser ignores it), (3) whole-plate scan, (4) describe-shape-before-naming (Pass 2 identity) + cooked-default.

## Result (dev40, v13 vs v16, both fresh VLM, judge sonnet-4.6 rubric v2, advisory)
| metric | v13 | v16 |
|---|---|---|
| conviction | 32.18 | 33.06 |
| recognition | 2.15 | 2.025 |
| naming_db_match | 1.70 | 1.70 |
| hallucinated_items/img | 1.90 | **2.02 (UP)** |
| per-dish hallucinated | 58 | **75 (UP)** |
| per-dish wrong_food | 76 | **61 (DOWN)** |
| missed_gt_items/img | 2.27 | 2.15 |
- cal_MAE 17.46 -> 21.71 (within the wide single-run CI; not significant).

## Findings
- **The anti-hallucination goal FAILED**: hallucination went UP, not down. The likely culprit is the `visible_evidence` field + whole-plate-scan — forcing a justification slot and "scan everything" ENCOURAGES enumeration, and the VLM happily fabricates a visual cue for phantom items (research warned: CoT/justification "amplifies overconfidence"). A single-prompt grounding rule does not suppress invention when paired with a list-everything pressure.
- **The describe-shape-before-naming (identity) component HELPED**: per-dish wrong_food 76 -> 61. Spot checks confirm it fixes shape/feature confusions (mac&cheese recognized via the orange sauce; broccoli not mislabeled). This is the salvageable lever.
- **Net conviction is flat (32.18 vs 33.06, within n=40 judge noise).** Consistent with the broader pattern: conviction sits at a ~32 ceiling for gemini-3-flash and no single prompt lever has moved it beyond noise.

## Action
- **Do NOT adopt v16.** 
- Isolate the helpful component -> **v17 = v13 + describe-shape identity discipline + cooked-default ONLY** (no evidence field, no whole-plate-scan, no grounding rule). Tests whether the wrong_food gain survives without the hallucination cost.
- If anti-hallucination is revisited, the evidence-field/grounding-rule approach is a dead end; use a SEPARATE self-verification pass (2nd call: confirm/drop each candidate) or a confidence threshold instead.

## Related
- [[20260602_reranker_instruction_was_inert_bug_fixed]] (localized conviction ceiling to VLM recognition)
- [[20260601_v14_scale_anchor_raises_slope_but_overcorrects]] / v15 (prior single-prompt levers also rejected)
