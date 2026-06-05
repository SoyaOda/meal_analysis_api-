# Lesson: E2 weight floor 80→20 — harmless overall (−0.68pt, NS) but the small-dish target (<300 kcal) is UNTESTABLE on the 50-set (no GT<300 images). Plus E12, this confirms the meta-finding: small data-independent levers cannot be validated on the 50-set; they need pooled N5k+NVReal.

- date: 2026-06-05
- scope: Phase 2.3 / E2 of the long-term plan.
- change: schema weight range lowered (main `80-400`→`20-400`, extras `5-120`→`1-120`) in the v13 prompt — a prompt-only edit (server has no weight floor; the prompt range was the only floor). v13 vs v13_floor20, flash, default light stack, cache=false, 50-set.

## Result (50-set, fail=0 both)
| candidate | overall MAE% | p90 | high30 | paired vs v13 |
|---|---|---|---|---|
| v13 | 19.50 | 35.3 | 14 | — |
| v13_floor20 | 18.82 | 35.0 | 16 | −0.68 [−5.1,+3.4] p=0.77 |
- **<300 kcal bucket: empty (n=0)** — the 50-set has no ground-truth-<300 images, so E2's actual hypothesis (small-dish over-estimation 1.27x, lesson 20260604_v14_*) CANNOT be measured here.

## Interpretation
- Overall: −0.68pt is within noise (NS) — lowering the floor is **harmless** (no regression, fail=0). The floor of 80g was an arbitrary constraint; permitting 20g is mechanistically reasonable. But there is **no measured benefit** on the 50-set.
- The targeted subgroup (<300 kcal small dishes) has **no test data** on the 50-set → the small-dish hypothesis is untestable here. N5k (median GT ~222 kcal, many <300) is the set that would test it.
- **Meta-finding confirmed (2nd time, after E12)**: at n=50 cache=false, VLM-draw variance (~±3pt) swamps small-lever deltas, AND the 50-set lacks small-dish coverage. **Data-independent small levers (E2/E7-density/E1) cannot be meaningfully validated on the 50-set.** Robust judgement requires pooled large-N (N5k 250 + NVReal 104) and, for subgroup levers, the set that actually contains the subgroup.

## Decision / next
- **Do NOT flip the production prompt yet** (deploy/prompt change needs explicit instruction). E2 is a safe permissive change to fold into the next prompt update IF an N5k run shows it helps the <300 subgroup.
- **Strategic**: stop validating small levers on the 50-set. For Phase 2 to be conclusive, each lever must run on **pooled N5k+NVReal** (bigger paid campaigns) — OR accept that the calorie wall needs real measured mozu data (E13, currently blocked) and that the banked wins (Phase 1: light stack latency/cost, F2 race-fix + parallel-SC code) are the realistic deliverables until that data exists.
- E7 (top-k density) remains the one Phase-2 lever that IS frozen-VLM isolatable (deterministic retrieval comparison) and worth doing properly — but it's a multi-point retrieval refactor.
- Artifact (gitignored): run `20260605_142205`. Config `pdca_e2_weight_floor20_full50_20260605.json`.
