# Lesson: E2 weight floor 80→20 is a VALIDATED, SAFE, targeted fix for small-dish (<300 kcal) over-prediction — pooled lt_300 (n=87 across N5k+NVReal) calorie-MAE −20.75pt (CI[−40.8,−0.1], SIGNIFICANT), signed bias +84→+56, via the confirmed mechanism (the floor was forcing small portions up; lowering it drops their weight), with NO regression on ≥300 dishes. The first clean positive prompt-lever of the exploration phase. Closes the prior E2 lesson's open precondition.

- date: 2026-06-06
- scope: Phase 2.3 / E2 (roadmap "main_food floor 80→20, extras 5→1").
- change: schema weight ranges lowered (main `80-400`→`20-400`, extras `5-120`→`1-120`) in the v13 prompt — PROMPT-ONLY (the server enforces no weight floor; the prompt range WAS the only floor). v13 vs v13_floor20, flash, light 0.6B stack, E7 top_n=5, K=1, cache=false.
- why now: the prior E2 lesson (`20260605_e2_weight_floor20_inconclusive_50set_no_small_dish_data`) found it harmless on the 50-set but UNTESTABLE there (no GT<300 images), and set the precondition "adopt IF an N5k run shows it helps the <300 subgroup." This run tests exactly that on the two small-dish-rich sets.

## Result (per-set, paired)
| set | subgroup | n | MAE v13→f20 | signed bias v13→f20 | total pred weight |
|---|---|---|---|---|---|
| N5k | lt_300 | 66 | 96.7 → **74.2** (Δ−22.4) | +87.6 → +59.8 | 179 → 164 g |
| N5k | ≥300 | 34 | 30.5 → 31.0 (Δ+0.4) | −1.1 → −2.4 | 314 → 307 g |
| NVReal | lt_300 | 21 | 79.5 → **64.1** (Δ−15.4) | +72.6 → +43.7 | 166 → 150 g |
| NVReal | ≥300 | 83 | 34.6 → 31.1 (Δ−3.5) | −11.5 → −15.3 | 315 → 308 g |

**Pooled lt_300 (n=87): ΔMAE −20.75pt, CI[−40.79, −0.10] → SIGNIFICANT; signed bias +84.0 → +55.9 (−28.1pt over-prediction).**
**Pooled ≥300 (n=117): ΔMAE −2.34pt, CI[−5.27, +0.46] → NS, non-regressive (slightly better).**

## Verdict: ADOPT-worthy (safe, targeted small-dish win)
- **Mechanism confirmed & direction-consistent across two independent sets**: the 80g main floor was forcing genuinely small portions up; lowering to 20g drops the predicted weight on small dishes (179→164, 166→150g) → reduces the over-prediction (signed bias halved toward 0) → cuts lt_300 MAE ~15–22pt. Same direction on N5k AND NVReal.
- **No downside**: ≥300 dishes non-regress on both sets (the floor only binds when the VLM wants <80g, i.e. exactly the small-dish case). Prior 50-set run: harmless (−0.68 NS). So across 3 sets E2 is non-regressive on normal/large dishes.
- **Contrast with E1 v18** (`20260606_e1_v18_*`): v18's small-dish help was a global density-DEFLATION that sign-flipped across sets and WORSENED large meals (slope down). E2 is the opposite — a TARGETED grams fix that only touches small dishes, is direction-consistent, and leaves large dishes alone. E2 is the right lever for small-dish over-prediction; v18's deflation is not.
- Per-set lt_300 CIs are wide (small n, huge %-error variance on tiny portions) but POOLED is significant + mechanism-confirmed + permissive (can only help small dishes) → the asymmetric risk (near-zero downside, real upside) justifies adoption.
- **3rd-set confirmation (2026-06-06, the strongest)**: on **JFB** (1000 real eye-level mobile-user photos, the most mozu-representative set; see `20260606_jfb_*`), lt_300 (n=22) MAE 86.1→63.4 = **Δ−22.7 CI[−37.5,−7.8] SIGNIFICANT on its own**, ≥300 non-regressive. E2 now confirmed on N5k + NVReal + JFB. Real eye-level user photos are ~22% small dishes → the small-dish-frequency question is answered: E2 significantly helps the real domain.

## Adoption / caveat
- The 80g floor was an arbitrary constraint; 20g is mechanistically sound and strictly safer. **Recommend adopting** = update the production prompt weight ranges to `20-400` (main) / `1-120` (extras). It is a prod prompt change → needs explicit deploy instruction (Firestore prompt_text override).
- **Real-world value scales with mozu's small-portion frequency**: small (<300 kcal) dishes are common in overhead/snack/single-item photos (N5k 66%, NVReal 20%) but absent from the eye-level full-meal 50-set. For a calorie tracker (snacks, small portions, single items are real), the win is genuine when they occur and harmless otherwise.
- Can stack with E7 (adopted) and SC K=3 (adopted); orthogonal to both. The v18 density nugget for small dishes is SUPERSEDED by E2 here (E2 is the cleaner mechanism).
- Artifacts (gitignored): runs 20260606_093315 (N5k), 093336 (NVReal). Config pdca_e2_weight_floor20_full50_20260605.json (the `v13_floor20` candidate is the ready floor-20 prompt). Tooling /tmp/e2_analyze.py.
