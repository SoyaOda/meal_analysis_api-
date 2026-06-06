# Lesson: JFB (1,000 real eye-level mobile-user photos, CC-BY-4.0) integrated as the in-domain eval set — and it immediately surfaced what the curated sets hid: on real user photos v13 calorie MAE is ~54% with a systematic +44% OVER-prediction (vs ~16% on the curated dev set). E2 floor-20 is now triple-confirmed (significant on JFB small dishes too). The E13 quick-win.

- date: 2026-06-06
- scope: E13 quick-win (the free, do-now item of `docs/E13_DATA_COLLECTION_PLAN_20260606.md`).

## What was integrated
- **JFB = January Food Benchmark** (arXiv 2508.09966, [repo](https://github.com/January-ai/food-scan-benchmarks), CC-BY-4.0): 1,000 real-world **eye-level mobile-app user photos** with human-validated meal name + ingredients + macronutrients. The closest *public* proxy to mozu's actual deployment domain (eye-level smartphone photos of users' own diverse real meals).
- Pulled from the public unsigned S3 bucket `january-food-image-dataset-public`, converted to the harness format → `test_images_jfb/images/test_food{i}.jpg` + `images_label_with_nutrition/test_food{i:02d}.json` (nested dishes/extras; per-ingredient macros as extras serve both `load_label_nutrition` (sum == stated total, 0.00% discrepancy) and `load_label_items` (ingredient names for recognition)). Split `evals/splits/jfb_test_100.txt` (100 evenly-spread).
- **GT granularity**: total calories + P/F/C + per-ingredient names. **No weighed grams** → JFB supports calorie/macro/recognition eval, NOT the grams-vs-density decomposition (which needs measured mass per the E13 plan). GT is expert-ESTIMATED, not weighed.

## Baseline reality-check (JFB-100, v13 adopted: flash + light 0.6B + E7 top_n=5)
| candidate | calorie MAE | p90 | high30 | signed bias | macro MAE P/F/C |
|---|---|---|---|---|---|
| v13 | **53.8%** | 124 | 56% | **+43.9%** | 54 / 79 / 106 |
| v13_floor20 | 47.8% | 114 | 49% | +37.8% | 48 / 72 / 105 |

- **On real eye-level user photos, v13 calorie MAE is ~54% with a broad, systematic +44% OVER-prediction** (56% of images >30% error — not a few outliers). The curated eye-level dev set (frozen-50, mynetdiary-style) shows ~16% and near-zero bias. **The real-domain error and its over-prediction direction were INVISIBLE on the curated sets** — exactly the gap the E13 plan predicted; this is why an in-domain eval set matters.
- **Caveat (important):** JFB GT is **human/expert-ESTIMATED from photos, not weighed**. Research puts expert photo estimation at ~58% MAE, so this number is *mozu-vs-expert-reference agreement*, not error vs weighed truth — the absolute 54% conflates mozu error with JFB GT noise. What is robust is the **systematic over-prediction direction** (both arms read ~+38–44% high vs the human reference). A weighed in-domain set (E13 §3) is still required to quantify true error and to fit E14.

## E2 floor-20 confirmed on the real-domain proxy (3rd independent set)
| subgroup | n | MAE v13→f20 | paired CI | signed bias |
|---|---|---|---|---|
| lt_300 (small) | 22 | 86.1 → **63.4** (Δ−22.7) | **[−37.5, −7.8] SIG** | +71.3 → +52.3 |
| ≥300 | 78 | 44.7 → 43.4 (Δ−1.3) | [−8.6, +5.0] NS | +36.1 → +33.8 |
| ALL | 100 | 53.8 → 47.8 (Δ−6.0) | [−12.6, +0.3] borderline | +43.9 → +37.8 |

- **E2's small-dish fix is now confirmed on N5k + NVReal + JFB**, and on JFB (the most mozu-representative set) the lt_300 win is **significant** (CI excludes 0), via the same mechanism (small-dish weight 288→270g → less over-prediction). Non-regressive on ≥300.
- This **answers the open small-dish-frequency question**: real eye-level user photos are ~22% small dishes (JFB-100), and E2 significantly helps them. **E2 is adopt-worthy and now triple-validated** (see `20260606_e2_floor20_*`).

## Implications
- **Strongest case yet for E14 conditional calibration on real data**: the +44% real-domain over-prediction is a large, systematic, in-domain bias that prompt/schema cannot robustly fix (E1/E3/E7). JFB is now the in-domain eval to gate E14/E8 — but fitting needs the weighed E13 set (JFB GT is estimated).
- **Use JFB**: add `jfb_test_100` to the routine PDCA rotation alongside frozen-50/NVReal/N5k for an honest eye-level real-user signal. Keep `use_vlm_cache=false`; do not leak JFB labels into prompts.
- Over-prediction on real photos is the OPPOSITE of the curated sets' picture (frozen-50 near-zero, the aggregate lessons saw large-meal UNDER) → reinforces that the bias is distribution-specific and must be calibrated conditionally, never globally.
- Artifacts (gitignored): `test_images_jfb/` (1000 imgs+labels), run 20260606_102611. Tooling /tmp/jfb_convert.py. Source: JFB CC-BY-4.0.
