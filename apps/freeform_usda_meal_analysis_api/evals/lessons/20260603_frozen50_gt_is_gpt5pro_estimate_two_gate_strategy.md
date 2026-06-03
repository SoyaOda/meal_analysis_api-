# Lesson: the frozen-50 GT is GPT-5-pro ESTIMATES (not measured) — "~18% cal_MAE" is agreement-with-GPT-5-pro, NOT accuracy. Adopt a TWO-GATE eval strategy; do NOT switch wholesale to Nutrition5k.

- Date: 2026-06-03
- Trigger: user flagged that the frozen-50's labels are GPT-5-pro estimates. Verified in-repo: ALL 50 labels carry per-item `confidence` (0.78-0.90) and 100% of weight_g are 5g-rounded (264/265) — markers of model generation, not measurement (Nutrition5k weights are fractional: 58.0/25.7/4.6g). Reviewed via a 4-perspective adversarial workflow (invalid-GT / switch-to-N5k / skeptic / GT-best-practice research).

## Verdict: PARTIAL mistake, axis-dependent — NOT a wholesale switch to Nutrition5k
Literature is unambiguous: no reputable 2024-2026 food-calorie benchmark (Nutrition5k, NutritionVerse, MenuMatch, the 2026 six-app study) uses LLM-estimated values as GT — LLMs are always the system-under-test, graded vs weighed-mass + USDA. GPT-5-pro-class estimators carry ~14% (ingredient-informed) to ~30% (image-only) own error, ICC 0.31-0.67 vs dietitians.

### Q1 — was tuning to the GPT-5-pro 50 a mistake?
- **CALORIE LEVEL / BIAS-SIGN / CALIBRATION axis: YES, a methodological error.** The repo's own measured-GT data proves the proxy misled: the 50 says pro is -5.3% UNDER; measured N5k says +30.7% OVER. A stable model property cannot move 36pt and flip sign between datasets → the "-5.3% under" is a property of the LABELER (GPT-5-pro), not the model. So calorie-level/bias/calibration decisions made against the 50 optimized "agreement with GPT-5-pro's guess," not accuracy.
- **RANKING / RELATIVE A/B axis: NO, not categorically wrong.** GT noise only biases rankings when CORRELATED with the model under test; GPT-5-pro (a different family from gemini) inflates flash and pro ~equally and largely cancels in the paired delta. Empirically pro>flash did NOT scramble under independent N5k GT — it confirmed and sharpened (NS on 50 → significant on N5k). The 50's IMAGES are gold; only its LABELS are silver. The mistake was trusting the label and reading "~18%" as absolute accuracy — NOT using the 50 for ranking.

### Q2 — switch to Nutrition5k?
**NO.** Promote N5k to the PRIMARY independent CALORIE-TRUTH gate (totals-only axis) but NEVER as a tuning target or sole gate: (1) wrong distribution (overhead/top-down cafeteria vs eye-level phone — part of the 18%→58% gap is angle shift, so N5k is a PESSIMISTIC stress-test, true mozu number lies BETWEEN); (2) not "general Western" (single CA cafeteria menu); (3) only its total-calorie axis is usable (ingredient names don't token-match → recognition/portion F1 is noise, 0.329 vs 0.325; discount it). N5k is ALSO unfit for calibration: the affine fit EXPLODES on its own held-out (RAW 53.0% → CAL 132.6%, signed +116%) because the over-bias is ~multiplicative, not affine.

## What SURVIVES vs is COMPROMISED
SURVIVES: pro>flash ranking (strengthened; justify on N5k + recognition, NOT the 50 calorie number); recognition-axis A/Bs (deterministic F1, GT-independent; pro>flash 4/4); the frozen-50 IMAGES (on-distribution phone realism set); large-effect relative use of the 50; naming-regression finding (judge kappa 0.67); USDA-matching-is-the-bottleneck diagnosis.
COMPROMISED/VOID: the "~18% cal_MAE" as accuracy (relabel as agreement-with-GPT-5-pro; report a RANGE 50~18% floor / N5k~58% ceiling); the -5.3% bias sign + any correction derived from it; the 50-fit `calorie_calibration_pro_v13.json` (fits gemini→GPT-5-pro, treat as VOID not "pending"); calorie-axis prompt A/Bs v14/v15/v16/v17 (weakened — re-check vs measured GT); the N5k-fit calibration (fails); the claim that the 50 tests Western generalization (too small/narrow).

## TWO-GATE strategy (adopted)
- **GATE A (measured calorie):** Nutrition5k TOTAL-CALORIE axis — independent regression/direction check. Promote only if measured calories do NOT regress; a gain on N5k-only is suspect (overhead overfit), a gain on the 50-only is unproven (proxy noise).
- **GATE B (distribution realism + ranking):** frozen-50 IMAGES — eye-level phone Western plates; keep as dev/regression/large-effect-A/B set, but STOP treating its calorie labels as truth and STOP fitting calibration to it.
- **EVENTUAL TRUE GATE (the asset to build):** a small in-domain MEASURED anchor (~20-50 representative Western eye-level phone meals, weighed per-ingredient × USDA) — the only set that resolves the true mozu number and the only valid calibration-fitting distribution. This is the real cost the GPT-5-pro shortcut deferred.

## Immediate corrections (done in this commit)
- PAUSE MOZU_MODEL_DECISION follow-up #1 ("calorie under-bias correction, mandatory before prod"): it targets the wrong sign (-5.3% under is a labeler artifact; real is +30.7% over) — applying it would WORSEN real accuracy. Mark `calorie_calibration_pro_v13.json` VOID, not "pending external fit."
- Relabel "~18%" as agreement-with-GPT-5-pro; Exit Criteria → calorie RANGE + measured-anchor gate.
- pro stays adopted, justification rewritten on N5k significant delta + 4/4 recognition F1 (drop the 50 calorie number).
- Recalibration only on a real measured anchor, MULTIPLICATIVE/slope-only form; keep both calibration JSONs enabled=false.

## Follow-ups (need credits / data)
- Re-run N5k 250 calorie eval ONCE for stability (repo's >=2-repeat bar; ~$7).
- Build the measured in-domain anchor (weigh 20-50 Western phone meals).
- Recognition-only cross-Western generalization (ISIA Food-500 / FoodX-251, name GT) for hallucination/wrong-food.
- Re-evaluate calorie-axis prompt A/Bs vs the N5k gate.

## Related
- [[20260603_nutrition5k_external_eval_generalization_gap]] (the measured-GT result that exposed this)
- [[20260602_calorie_calibration_layer_implemented]] (the affine layer; now VOID on both 50 and N5k fits)
- `docs/MOZU_MODEL_DECISION_20260603.md` (being corrected)
