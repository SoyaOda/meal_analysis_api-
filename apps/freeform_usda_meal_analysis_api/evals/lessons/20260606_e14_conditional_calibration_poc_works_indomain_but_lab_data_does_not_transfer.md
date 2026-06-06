# Lesson: E14 conditional-calibration PoC — the machinery WORKS in-domain (JFB held-out calorie MAE 56.6→38.1, −18.5pt; conditional beats global on real photos) BUT a calibration fit on the WEIGHED LAB sets (NVReal+N5k) does NOT transfer to real eye-level photos (applied to JFB it is WORSE than raw, 53.8→55.5). ⇒ E14 is viable, and a mozu-domain in-domain labeled set (E13) is REQUIRED to fit it — existing weighed lab data is insufficient.

- date: 2026-06-06
- scope: E14 (conditional/hierarchical calibration). Offline PoC on existing v13 predictions + GT — no new evals, no pipeline change yet.
- method: per predicted-calorie quantile bucket (5), `corrected = pred × factor[bucket(pred)]`, `factor = median(GT/pred)` on a FIT split, clamped [0.5,2.5]. Compared vs no-cal and vs GLOBAL (single factor). Data: v13 runs NVReal 20260606_093336, N5k 20260606_093315, JFB 20260606_102611. (Existing global calibration `calorie_calibration_pro_v13.json` is slope/intercept, enabled=false / VOID.)

## Results
**A. Within-set (fit even / blind-hold odd):**
| set (bias) | holdout raw | global | conditional |
|---|---|---|---|
| NVReal (signed +5.5, ~unbiased) | 36.8 | 36.7 | 38.2 |
| N5k (signed +57.5, over) | 69.0 | 52.9 | 52.1 |
| **JFB (signed +43.9, over)** | 56.6 | 41.3 | **38.1** |

- Calibration helps exactly where there is bias (N5k −16pt, JFB −18.5pt) and is a no-op/slight-overfit where there isn't (NVReal — already unbiased, small-split per-bucket noise made conditional 38.2 > raw 36.8). **On the real-photo domain (JFB), conditional BEATS global (38.1 vs 41.3)** — the per-bucket structure matters.

**B. Cross-set (weighed → weighed):** N5k→NVReal 43.6→42.0; NVReal→N5k 74.2→74.3. **Calibration does NOT transfer between weighed distributions** (the edges are set-specific: NVReal grams 0.88/density 1.14 vs N5k 1.01/1.03).

**C. KILLER TEST (weighed lab fit → real eye-level JFB):** fit NVReal+N5k (n=204) → apply JFB: raw 53.8 → global 46.1 → **conditional 55.5 (WORSE than raw)**. Reference: JFB self-calibrated (fit JFB-even→JFB-odd) → **38.1**.

## Verdict
- **E14 conditional calibration is VIABLE**: on in-domain held-out data it cuts calorie MAE substantially (JFB −18.5pt) and beats global calibration on real photos. The strategy redirect (E3: prompt can't fix systematic bias → calibrate it) is mechanically sound.
- **But it MUST be fit on in-domain data**: a calibration fit on weighed LAB sets and applied to real eye-level photos is *worse than no calibration* (conditional fit on weighed → JFB = 55.5 vs 53.8 raw) because the lab sets' bias-by-bucket structure does not match the real domain. Global-on-weighed gives a mild blanket nudge (46.1) only because both happen to over-predict, but that is luck, not transfer.
- **⇒ E13 (mozu-domain labeled set) is REQUIRED, not optional.** This PoC quantifies it: the in-domain calibration ceiling is large (JFB self-cal −18.5pt), but only reachable with in-domain labels. Existing NVReal/N5k cannot stand in.
- **Caveat**: JFB GT is expert-ESTIMATED (not weighed), so JFB-self-calibration calibrates toward expert estimates, not weighed truth — it shows the *structural* ceiling, not a production-ready coefficient. Production E14 needs a WEIGHED mozu-domain set (E13 §3). Also: condition on OBSERVABLE features (predicted-calorie bucket here); the small-split per-bucket overfit (NVReal) signals E14 needs shrinkage/hierarchical pooling + enough per-cell n (E13 §6).

## Implications / next
- **E14 is ready to fit the moment E13 in-domain labeled data exists.** Design: conditional (per predicted-bucket × food-group × angle × container) multiplicative correction with hierarchical shrinkage, fit on E13-fit, validated on E13-blind-holdout, corrected calorie in a SEPARATE field (displayed grams unchanged — per the F1-e VOID guard).
- Do NOT enable a global or lab-fit calibration in production (it is worse-than-raw on the real domain). Keep `calorie_calibration` disabled until an in-domain conditional fit passes the holdout gate.
- The +44% real-domain over-prediction (JFB) + the −18.5pt in-domain calibration ceiling together make E13 collection the single highest-value next investment.
- Tooling (gitignored, /tmp): `e14_calibration_poc.py`. Uses existing run artifacts.
