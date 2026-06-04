# Lesson: recognition on CLEAN independent GT (NVReal COCO) — pro has NO edge over flash (tie/slightly worse). The last pillar of the pro case collapses → flash is cost-rational.

- Date: 2026-06-04
- The pro adoption case, after calorie collapsed, rested entirely on the frozen-50 recognition gain (F1 4/4 vs flash). That gain was measured against GPT-5-pro-ESTIMATED food names. This lesson re-measures recognition against a CLEAN INDEPENDENT GT: NutritionVerse-Real's COCO segmentation categories (the real foods physically present). Method: reuse the EXISTING flash_v13 + pro_v13 predictions from run `20260603_232505` (no new VLM cost), score semantically with an 8-way parallel Claude judge (workflow `nvreal-recognition-judge`), lenient on USDA-verbose vs slug naming, brand, and dish granularity; strict on substitutions. 104 images, 309 distinct GT foods.

## Result
| model | recall | wrong-food (substitution) | per-image wins |
|---|---:|---:|---:|
| flash_v13 | **82.5%** (255/309) | 32 | 16 |
| pro_v13 | **80.6%** (249/309) | 36 | 13 |
| pro − flash | **−1.9pt (pro slightly worse)** | +4 (pro more) | tie 75 |

## Findings
1. **pro has NO recognition advantage on clean independent GT.** It is a tie-to-slightly-worse (−1.9pt recall, more wrong-food, 75/104 images tied). This DIRECTLY CONTRADICTS the frozen-50 "pro recognition 4/4 better" claim → that claim measured agreement with GPT-5-pro's NAMING, not real food-identification skill. pro names foods more like GPT-5-pro, not more correctly.
2. **Recognition itself is GOOD (~82% recall).** The harness token-F1 of ~0.12 on N5k/NVReal was a NAME-FORMAT MATCHING ARTIFACT ("Pears, asian, raw" vs "asian-pear"), not a recognition failure. Both models correctly identify ~4/5 of the true foods.
3. **Concrete, narrow failure modes** (improvable, model-independent): lobster systematically missed on crowded plates (#19/20/24/25); strawberry-jam-toast misidentified as the wrong fruit (#14/26/27); cucumber missed/substituted; pro hallucinates slightly more (adds cheeseburger/apple/rice not present).

## Implications — the pro vs flash verdict
- **pro has no robust edge over flash on EITHER axis** (calorie: non-robust/sign-flipping across 3 sets; recognition: tie on clean GT). The entire pro case came from frozen-50 signals that are agreement-with-GPT-5-pro, not real-world performance.
- **→ flash is the cost-rational choice: equal accuracy at ~1/3 the cost (pro is 3.2x).** Recommend reverting the default from pro to flash for mozu unless a future REAL-mozu-data eval shows a pro edge. (This reverses the 2026-06-03 pro adoption; settings.py/config default currently pro — flagged for change, not yet changed; deploy/config edits need explicit user instruction.)
- Recognition is already decent (~82%); further gains should target the specific gaps (lobster, jam, cucumber) rather than swapping models.

## Caveats
- Single judge run (Claude). The −1.9pt could be judge noise, but the qualitative call ("no MEANINGFUL pro advantage") is robust to it — even a +1.9pt swing would not justify 3.2x cost. A 2nd judge run could confirm stability.
- NVReal is one distribution (eye-level lab). But it is INDEPENDENT and clean — strictly better evidence than the frozen-50 GPT-5-pro labels the pro case was built on.

## Related
- [[20260604_nutritionverse_real_eyelevel_eval_pro_calorie_edge_not_robust]] (calorie: same no-edge conclusion)
- [[20260604_realistic_range_error_decomposition_grams_vs_density]] (calorie error is variance, near-zero bias)
- [[20260603_frozen50_gt_is_gpt5pro_estimate_two_gate_strategy]] (why frozen-50 signals overstate pro)
- `docs/MOZU_MODEL_DECISION_20260603.md` (SSOT — to be updated to flash-recommended)
