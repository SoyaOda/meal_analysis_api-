# Lesson: NutritionVerse-Real (Kaggle "manual" dist) — image filename `dish_N` does NOT equal metadata `dish_id N`; naive identity-join produced 40% WRONG calorie GT

- Date: 2026-06-03
- Codex (Computer Use) downloaded NutritionVerse-Real from Kaggle and built `test_images_nvreal/` (225 dishes) via a new `build_nutritionverse_evalset.py`. The converter joined image filename `dish_<N>` to metadata CSV `dish_id == N` (identity). All deterministic checks PASSED (225/225 loader-readable, label-sum == CSV total to 0.0000 kcal, naming/pairing matches the harness). **It would have shipped a corrupt eval if not visually inspected.**

## The trap (why deterministic checks were not enough)
- **Visual spot-check broke it**: `test_food1.jpg` (idx1 → metadata dish_id 2 = "half-bread-loaf"+"lobster", 187 kcal) is actually a single **apple**; `test_food2.jpg` (dish_id 21 = tofu+chicken+cucumber) is a single **asian-pear**. The image and its assigned GT are different foods.
- **Root cause**: the dataset ships 3 files only — `nutritionverse_dish_metadata3.csv` (nutrition, keyed by its own `dish_id`), `updated-manual-dataset-splits.csv` (Train/Val), and a Roboflow `_annotations.coco.json` (per-image ingredient categories + masks). **There is NO image→dish_id crosswalk.** COCO image entries carry only id/file_name/h/w/date. The image filename's `dish_N` and the CSV's `dish_id` are **independent numbering systems** that happen to share the 1..251 range.
- The label-sum == CSV-total check only proves the converter copied a CSV row faithfully — it says nothing about whether that row belongs to the image.

## How wrong, and what is salvageable (use COCO as the truth)
COCO categories ARE a reliable per-image food-content GT (apple image → category `red-yellow-apple`). Comparing each image's COCO ingredient set to its assigned metadata ingredient set:
- **Current 225 built dishes: 136 identity-correct, 89 (40%) GT-WRONG.** Mismatches are a mix of fully-different (apple vs bread+lobster, the shuffled low-N region), off-by-one ingredient (COCO over/under-segmentation or genuinely different dish), and false mismatches from name variants (`red-yellow-apple` vs `red-apple`).
- The correct join key is **CONTENT, not id**: match each image's COCO ingredient multiset to the metadata dish with the same multiset. Strict-multiset unique matches = **105 dishes**; set-based with name-normalization recovers more (~120-136). The remainder (ambiguous/no-match from segmentation count drift) must be dropped.
- Offset diagnostic: among unique content matches, `metadata_id - image_N == 0` for 117/121 — i.e. identity is actually correct for most `dish_N >= ~23`; only the low-N single-item shots are shuffled. So "drop the contaminated + rebuild content-verified" keeps the bulk.

## Realism characterization (separate from the GT bug)
- Composed dishes (e.g. dish_200 = rib + chicken-sandwich + fried-chicken + sushi) are **eye-level plated meals on a white plate** — genuinely complementary to Nutrition5k's overhead angle, decent phone-like realism.
- But many entries are **studio single grocery items** (apple, pear with price stickers, tripods in frame), and these are the contaminated low-N ones. NutritionVerse-Real "manual" is a **controlled lab capture**, NOT casual real-user phone photos — so like N5k it is a stress-test, not a true mozu-domain anchor.

## Actions / implications
- **Do NOT run calorie eval on the current `test_images_nvreal/` (40% wrong GT).** The Codex converter's identity-join is unsafe; it needs a **content-based (COCO-multiset) join** + drop-on-ambiguous, yielding ~105-136 verified dishes.
- **Always visually spot-check an externally-built eval set** before trusting it — deterministic schema/sum checks cannot catch an image↔label mapping error.
- **Bonus use**: COCO per-image categories are clean **recognition GT** (45-category vocab) → NutritionVerse-Real can serve the recognition-generalization axis even where calorie GT is unrecoverable.
- The Codex task doc `docs/CODEX_TASK_nutritionverse_real.md` assumed identity-join; it must be corrected to mandate the COCO-content join + visual spot-check.

## Related
- [[20260603_nutrition5k_external_eval_generalization_gap]] (the other external set; overhead angle)
- [[20260603_n5k_pro_advantage_test_retest_borderline]] (N5k stability)
- [[20260603_frozen50_gt_is_gpt5pro_estimate_two_gate_strategy]] (two-gate eval strategy this set was meant to strengthen)
