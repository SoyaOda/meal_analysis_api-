# Lesson: v14 portion-scaling raises the calorie slope but does NOT improve the realistic meal range — range-compression lives only in the unrealistic giant-plate tail

- Date: 2026-06-04
- PDCA on the "portion under-estimation / large-plate compression" lever (the model-independent candidate from the mozu PDCA summary). Prompt `v14_portion_scaling_20260604` (sha `efc1850658`) vs v13, flash, NutritionVerse-Real 104, cache off. Config `pdca_flash_v13_vs_v14_portion_20260604.json`, run `20260604_090008`.

## Plan (diagnosis that motivated v14)
On BOTH measured sets (N5k, NVReal) the pred/GT ratio compresses identically with meal size: small <300 kcal OVER (~1.3x), large 700-1500 UNDER (~0.6-0.8x), huge >1500 severely UNDER (~0.2x). The hard weight cap (main 400g) was NOT binding (max predicted item ~340g) — the cause is the PORTION ANCHORS being single-serving sizes that the model snaps to regardless of visual size. v14 = reframe anchors as "one serving, SCALE to visible amount (up 1.5-3x for oversized/sharing plates, down 0.3-0.6x for a few bites)", raise weight caps (main 400->700, extras 120->300), and "count every substantial component on full plates". No eval-specific info (overfitting policy respected).

## Result (NVReal 104, flash v13 vs v14)
| metric | v13 | v14 |
|---|---:|---:|
| total-calorie MAE (all 104) | 39.1% | 37.2% (Δ−2.0pt, paired CI [-8.3,+3.4] **NS**) |
| **MAE realistic 200-1500 kcal (n=73)** | **27.1%** | **27.0% (Δ−0.0pt, NS)** |
| MAE <1500 excl. giant tail (n=86) | 31.5% | 30.3% (Δ−1.2pt, NS) |
| calib_slope (OLS pred~GT) | 0.118 | **0.170** (compression eased) |
| pred/GT large 700-1500 | 0.82 | 0.87 |
| pred/GT huge >1500 | 0.23 | 0.28 |
| pred/GT small <300 | 1.27 | 1.28 (unchanged) |

## Findings
1. **The mechanism works but the win is confined to the unrealistic tail.** v14 raises the slope (0.118→0.170) and eases large/huge plates, but **the entire MAE gain comes from the giant >1500 kcal plates** (NVReal's oversized lab buffet plates, median GT 2975 kcal — not representative of normal mozu meals). **In the realistic 200-1500 kcal range the MAE is unchanged (27.1→27.0).**
2. **Range-compression is NOT the realistic-range problem.** In 200-1500 kcal, v13's pred/GT was already ~1.0 (not compressed); the ~27% MAE there comes from per-item error (gram noise and/or food-identity → wrong kcal/g), which a portion-scaling prompt does not touch.
3. **Small-dish over-estimation (1.27x) was not fixed** by the "scale down 0.3-0.6x" guidance — likely a different cause (the 80 g main_food floor and/or matching small items to calorie-dense USDA entries), not portion compression.
4. Everything is NS (flash is fairly reproducible, so −2pt is a real but tiny effect dominated by a few giant plates).

## Decision / Act
- **Do NOT adopt v14** (no realistic-range improvement; all NS). Keep v13 as baseline. v14 prompt + config retained as artifacts (marginally better only if mozu ever sees giant sharing-plate meals).
- **Redirect**: prompt-level portion-scaling is the WRONG lever for realistic-range accuracy. The ~27% realistic-range MAE needs a different diagnosis — decompose it into (a) total-gram error vs (b) matched-food kcal/g error. That decomposition needs a set with reliable per-item GT (N5k has lab-weighed per-ingredient masses, but pred↔GT item matching is blocked by vocab mismatch) → reinforces that a **real mozu-domain measured set with per-item truth is the actual bottleneck**.
- Open sub-lever worth a cheap test later: lower the main_food weight floor (80→~20 g) to fix small-dish over-estimation (the other end of the slope), independent of the large-plate scaling.

## Related
- [[20260604_nutritionverse_real_eyelevel_eval_pro_calorie_edge_not_robust]] (the eval that surfaced the compression; same set)
- [[20260603_nutritionverse_real_broken_id_mapping]] (how the 104-dish set was built)
- `docs/MOZU_PDCA_SUMMARY_20260604.md` (item 2 = this portion lever)
