# E13 — Real Measured Data Collection Plan (mozu)

- date: 2026-06-06
- status: PLAN (design SSOT). No collection started. Decisions for the user are in §12.
- author: PDCA session `mozu-e13`. Grounded by a 3-agent research workflow (GT methods + public-dataset landscape + internal-findings implications); key sources cited inline.

## 1. Why E13 exists (the one remaining real lever)
The 2026-06 PDCA cycle proved that **prompt / schema / retrieval / model selection are at the ceiling** for photo calorie estimation:
- **E3**: no available uncertainty signal predicts calorie error (pooled N=253, AUC 0.51) → E9/E18 cheap versions dead. Error is *systematic portion/density bias*, invisible to sample variance ("confidently wrong").
- **E1 v18**: schema separation = a global calorie *deflation*; set-specific (helped overhead N5k, wash on eye-level, worsened large meals). Prompt cannot deliver a distribution-robust calorie win.
- **E7 / E2**: retrieval density-mixture and the small-dish floor only move set-specific sub-pathologies.

External evidence agrees the wall is intrinsic: on Nutrition5k (exact GT), a 2D RGB-only model — mozu's regime — reaches only **~70 kcal MAE / ~26% MAPE** ([Nutrition5k](https://arxiv.org/abs/2103.03375)). Dietitians estimating from photos run **~58% MAE / 25% within-20%**, no better than laypeople or modern VLMs ([JMIR crowdsourcing](https://pmc.ncbi.nlm.nih.gov/articles/PMC6246963/)).

**Conclusion**: the only lever left is **E14 conditional calibration** and **E8 user_context**, and both are blocked purely on *real measured, mozu-domain data*. E13 produces that data. This doc is the plan.

## 2. The core GT problem: eye-level photos cannot be grounded from pixels
mozu's input is **eye-level (oblique) smartphone photos of users' own meals**. That is the *hardest* case for portion ground truth: monocular **scale ambiguity** makes the pixel→grams mapping indeterminate without a known reference ([smartphone portion w/o fiducial](https://www.cambridge.org/core/journals/public-health-nutrition/article/imagebased-food-portion-size-estimation-using-a-smartphone-without-a-fiducial-marker/47ED461DDE607FE0C7E6D70168E80BFA)).

**Implication (load-bearing):** you cannot recover trustworthy GT grams *from the eye-level photo*. The mass must be **captured at the moment of the photo** (weighed, or a known reference / chain item), then the photo is *paired* to that GT. Every design choice below follows from this.

## 3. Collection protocol — "weigh-as-you-plate, photographed eye-level"
Adopt the Nutrition5k weigh-as-you-plate method, but **shoot eye-level** so the image distribution matches mozu (Nutrition5k itself is fixed top-down — its single biggest mismatch vs mozu).

Per meal:
1. **Plate incrementally on a 0.1–1 g scale**: add each ingredient one at a time, record incremental grams per item.
2. **Compute GT** per item and total: `(USDA/FNDDS per-gram nutrition) × measured grams` → trustworthy per-item kcal + P/F/C + grams (sub-5% — the reference standard, [WFR](https://inddex.nutrition.tufts.edu/data4diets/data-source/weighed-food-record-wfr)).
3. **Photograph 1–3 eye-level shots** at realistic phone angles/lighting immediately after plating, with a subtle known reference in frame (standard plate/utensil; optional fiducial) so the photo is honest for eval.
4. **Log stratification metadata** (see §4) per photo.
5. **Experts (dietitian) only for QA** — verify food identity / ingredient list, flag implausible logs. **Never** use expert photo estimates as portion GT (they carry the same ~50%+ error we are eliminating).

GT sourcing varies by stratum to keep cost down without losing per-item grams:
| stratum | GT method | per-item grams? | accuracy |
|---|---|---|---|
| home-cooked mixed | weigh each ingredient + recipe decomposition→USDA/FNDDS ([Recipe1M+ 94.5% match](https://arxiv.org/pdf/1810.06553)) | yes | high (if weighed) |
| single packaged | barcode/label, **weigh the as-eaten portion** | yes | ~5–10% ([snack calorimetry ~4.3%](https://pmc.ncbi.nlm.nih.gov/articles/PMC3605747/)) |
| chain restaurant | Nutritionix/MenuStat published (legally within 20%) | no (item total) | good at item level |
| "hard" plates (sauced/energy-dense/occluded) | full weigh-as-you-plate | yes | high |

## 4. Stratification — the bias is set-specific, so calibration must be conditional
The decomposition lessons show the systematic edges are **distribution/angle dependent and cancel in aggregate** — there is *no global edge to fix*. E13 must stratify so E14 can fit a correction *per cell*. Required axes (each with evidence):

1. **Camera angle (eye-level vs overhead)** — dominant. grams/density signature flips: NVReal eye-level realistic-range grams 0.88 / density 1.14 vs N5k overhead 1.01 / 1.03. v18 worsened eye-level, helped overhead. *Over-sample eye-level (mozu's real input).*
2. **Dish/portion size (small <300 vs large 700–1500+ kcal)** — **opposite-signed, cancelling**: small OVER ~1.27× (N5k lt_300 signed +87.6; E2 floor cut pooled lt_300 −20.75pt, n=87, sig), large UNDER (calibration slope ~0.47; v18 worsened gte_1500). A global nudge helps one and hurts the other.
3. **Food group / density class (lean vs dense/fried/full-fat)** — density-over 1.14× = matching prefers calorie-denser variants (pred 2.09 vs GT 1.76 kcal/g; GT spans 0.69–4.40). Need per-food-group density priors.
4. **Container (bowl vs plate) & composition (single-item/snack vs mixed full-meal)** — bowl depth/piling ambiguity; small single-item carries the over-prediction pathology absent from full-meal sets.
5. **Macro / hidden-fat dishes** — fat is the worst macro (38–41% MAE, hidden oils). Needs per-item macros to gate PFC separately from calorie.

Secondary tags: cuisine, eat-out vs home (for E8 context signals).

## 5. GT granularity (non-negotiable): PER-ITEM grams + per-item nutrition
The load-bearing diagnostic is `pred/GT = (pred_grams/GT_grams) × (pred_density/GT_density)`. To keep it computable (it localized error at *zero* API cost in 20260601/20260604), every photo's GT must carry:
- **per-item + total measured grams** (manifest field like NutritionVerse-Real's `total_food_weight_g` plus per-component weights) → isolates the grams ratio;
- **per-item nutrition (kcal + P/F/C grams)** → isolates density (kcal/g) per item, and enables **PFC absolute-gram MAE** + density error (kcal/100g) (use absolute grams — fat MAE% explodes on small denominators);
- **stratum metadata** (§4) baked into the manifest so calibration cells can be formed.

Manifest should match the existing harness loader (`test_food{i}.jpg` + `test_food{i:02d}.json` with calories/protein/fat/carbs, plus new `total_food_weight_g` and per-item arrays) so E13 data plugs straight into `run_pdca_batch_eval` and auto-emits `decomposed` + `dish_match_agg`.

## 6. Sample size & power — budget per STRATUM, not per total
n=50 single-draw is untrustworthy: VLM draw noise alone is **±3pt MAE** (dev40 v18 −1.63 flipped to +0.46 from 10 extra images; E12 "didn't reproduce at n=50"; E2 frozen-50 was −0.68 NS *and* structurally untestable — zero GT<300 images). Signals only became real and direction-consistent at **pooled N=253**; the small-dish win needed the rich sets specifically (N5k 66 + NVReal 21 = pooled n=87, CI still wide [−40.8,−0.1]).

Targets:
- **Total 200–500** (roadmap; 20–50 is *direction-confirmation only*, never an adoption gate).
- **Per edge-cell ~30–90+ images** (mirroring the n=66–87 that made small-dish significant), with the **large / small** and **bowl / plate** and **overhead / eye-level** edge cells **deliberately over-sampled** (highest %-error variance).
- **Fit / blind-holdout split** decided *before* any fitting; each cell must have enough in *both* splits for the holdout paired CI to exclude 0.

## 7. Sampling prioritization — NOT uncertainty (E3 killed it)
Do **not** prioritize by single-model uncertainty: E3 showed output proxies (Spearman ~0, AUC 0.43–0.55, sign-flipping) and seed-dispersion (CV-vs-error ρ +0.048, AUC 0.51) do not predict error. Instead prioritize by:
1. **Stratum coverage / balance** — fill the cells where bias is large and opposite-signed (small-over, large-under, bowl, overhead, fried/high-fat).
2. **Cross-MODEL disagreement** (flash-vs-pro / flash-vs-3.5) — E18's real mechanism, not within-model dispersion (caveat: pro makes flash-correlated errors, so it only partially escapes the confidently-wrong trap).
3. **High-leverage cells** — high predicted calorie and the distribution-edge size/density buckets where the 0.47 slope and 1.27× over-prediction bite hardest.

## 8. Existing public datasets — hybrid (eval-now, build-own for adoption)
No public set matches mozu on all of {eye-level, diverse restaurant+home, occlusion, accurate per-meal GT, commercial license}. Use them as **eval benchmarks + pretraining**, not as in-domain calorie GT:
| dataset | role for mozu | license | note |
|---|---|---|---|
| **JFB** (January Food Benchmark, 1k real mobile user photos, eye-level, expert macros) | **primary in-domain eval proxy** now | CC-BY-4.0 ✅ | closest public match; GT is expert-estimated, American-skewed |
| **Nutrition5k** (5k plates, measured) | measured-calorie regression check | CC-BY-4.0 ✅ | overhead, CA cafeterias |
| **NutritionVerse-Real** (889, measured, iPhone) | already in our eval rotation | research | small, staged |
| **SimpleFood45** (measured, eye-level, scale ref) | protocol template for §3 | research | tiny but the cleanest eye-level+measured example |
| Recipe1M+, FoodSeg103 | recognition / ingredient / occlusion pretraining ONLY | Apache-2.0 ✅ (FoodSeg) | no per-image calorie GT |
| MM-Food-100K, CGMacros | **analysis-only** | royalty / CC-BY-NC ❌ | NOT commercial-safe |

→ Add **JFB** as a benchmark to the PDCA rotation immediately (free, in-domain proxy); invest the real effort in the mozu-native measured eye-level set (§3) as the authoritative fine-tune + promotion-gate GT and mozu's data moat.

## 9. How E13 unblocks E14 and E8
- **E14 (conditional/hierarchical calibration: food-group × container × size × angle × confidence)**: E13's per-item grams + per-item nutrition + stratum metadata is exactly the population to **fit multiplicative per-cell corrections and validate on a blind holdout**. Must correct **grams-under and density-over jointly per cell** — fixing one breaks the 0.88×1.14=0.98 cancellation and worsens calorie. Corrected calorie → a **separate field**; displayed grams unchanged.
- **E8 (user_context → VLM + retrieval)**: needs real photos carrying real auxiliary signals (half-eaten / restaurant / menu / plate-diameter / large-portion) to run a leak-managed context-on vs context-off A/B. E13's eat-out/home + container + reference metadata is that substrate.
- **Both**: E13 is the first population where the F3/F4 promotion KPIs (PFC absolute-gram MAE, density error kcal/100g, interval coverage, subgroup guard, calorie-weighted recognition) can be computed on *real* GT — so E14/E8 promotion is gated on the AND-condition gate, not noisy n=50 totals.

## 10. Constraints (carry from prior lessons — do not relitigate)
- **Blind holdout / anti-overfit**: split fit vs blind holdout *before* fitting; judge E14 only on the holdout paired CI.
- **Global calibration is VOID**: E14 must be **conditional/hierarchical**, never a single global intercept/slope (edges cancel + are set-specific; a global nudge helped one set and hurt another — v18). Corrected calorie in a separate field; returned grams unmodified.
- **No eval-leak**: never embed eval-specific info (test ids, label values, GT, calibration constants) into the prompt/pipeline; E13 GT is for fit/validation only. Evals `use_vlm_cache=false`.
- **Coordinated grams+density only**: never correct one in isolation.
- **AND-conditioned promotion (F3)**: MAE ≥2pt AND paired CI upper<0 AND p90/bias/high30/recognition non-regress AND latency/cost budget AND subgroup guard. Never promote on total-calorie alone.
- **Targeted not global**: size-conditional small-dish lever (E2) is adopt-worthy only conditioned on size.

## 11. Phased rollout
1. **Now (free)**: add JFB (CC-BY-4.0) to the eval rotation as the in-domain proxy; keep NVReal+N5k+frozen-50. Adds eye-level real-user signal at zero collection cost.
2. **Pilot (20–50 meals, weigh-as-you-plate eye-level)**: validate the protocol + manifest + harness integration end-to-end. Direction-confirmation only.
3. **Full (200–500, stratified §4–6)**: the authoritative fit + blind-holdout set. Unblocks E14/E8.
4. **Ongoing**: cheaper barcode/chain-API logging for scale; periodic re-fit of conditional calibration as the set grows.

## 12. Decisions for the user (cannot be resolved from code)
- **Build vs partner**: run the weigh-as-you-plate collection in-house, or commission it? (it is labor-bound, not software-bound)
- **Who/where**: who plates+weighs+photographs; what cuisine/eat-context mix mirrors mozu's real users?
- **Budget & scale**: 200 (cheapest defensible) vs 500 (per-cell power at the edges)?
- **Privacy/consent** if any real user photos are used (vs operator-plated meals).
- **Quick win**: approve adding **JFB** to the eval rotation now (free, immediate in-domain coverage) while the measured set is built? **(DONE 2026-06-06: JFB integrated as `test_images_jfb/` + `jfb_test_100`; v13 baseline = 53.8% MAE / +43.9% over-prediction on real photos — see `evals/lessons/20260606_jfb_*`.)**

## 13. Turnkey ingestion (built 2026-06-06) — the physical weighing is the only human step left
`scripts/ingest_e13_collection.py` makes everything after the physical capture turnkey:
- The collector records, per meal: an **eye-level photo** + a small JSON manifest with per-ingredient **weighed grams** + **nutrition** (calories/protein_g/fat_g/carbs_g, looked up from USDA/FNDDS/barcode/menu) + stratum tags (angle / container / size / cuisine / eat_context / fat_level). `--template` prints the exact schema.
- The script validates ALL manifests (no partial/fallback ingest — hard-fails on a missing grams/nutrition/stratum field), converts to the harness format (`test_images_<name>/` with `test_food{i}.jpg` + nested label carrying per-item grams + nutrition + `total_food_weight_g` + `stratum`), writes a split, and **reports stratum coverage (angle × size_bucket) flagging thin cells (<30)** so §4/§6 balance is visible during collection. Verified end-to-end (loads via the eval harness; `test_images_e13*/` is gitignored).
- **E14 is ready to fit the moment this data exists** — the conditional-calibration PoC (`evals/lessons/20260606_e14_*`) showed in-domain conditional calibration cuts held-out calorie MAE ~18pt, but a lab-fit calibration is *worse than raw* on real photos → the in-domain weighed set is the binding prerequisite.

(Tooling: research workflow result in the session transcript. Ingestion: `scripts/ingest_e13_collection.py`. E14 PoC: `/tmp/e14_calibration_poc.py`.)
