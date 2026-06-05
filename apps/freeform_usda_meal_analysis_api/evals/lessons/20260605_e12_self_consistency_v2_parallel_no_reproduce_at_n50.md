# Lesson: E12 self-consistency v2 — parallelization SHIPPED (latency ~1.15× not 3×), but K=3 median did NOT reproduce the −2pt calorie win at n=50 (a lucky-good single baseline draw → median regresses to mean). K=3's value is variance reduction (needs pooled large-N to show), not a single-run guarantee. K=1 kept as default.

- date: 2026-06-05
- scope: Phase 1.3 / E12 of the approved long-term plan (`~/.claude/plans/flickering-swinging-ember.md`).
- model: flash, v13 prompt, DEFAULT light stack (Qwen3-Embedding-0.6B + Qwen3-Reranker-0.6B, adopted Phase 1.1), cache=false (each K sample fresh seed).

## Code delivered (committed 8557d94, behavior-preserving)
- `pipeline.analyze_meal_from_image`: the K self-consistency samples now run **concurrently via asyncio.gather** (was a sequential `for i in range(k): await`). Safe because F2 (Phase 1.2) made vlm_service stateless — each sample resolves its own request-local prompt/model/provider. K=1 default unchanged.
- `run_pdca_batch_eval`: pass `self_consistency_k` candidate→request (it was silently dropped by build_candidate_list's whitelist → server-side K could not be A/B'd before). Opt-in. Router already accepts the Form param.
- Verified live: K=3 fires 3 parallel samples (seeds 1..3) → median-total-calorie selection (e.g. [645,775,669] → 668.8). 73 tests pass.

## A/B result (50-set, cache=false real VLM)
| candidate | MAE% | p50 | p90 | high30% | latency | fail |
|---|---|---|---|---|---|---|
| sc_k1 (single) | 16.84 | 15.60 | 26.9 | 8.0 | 20.6s | 0 |
| sc_k3 (median-of-3, parallel) | 18.24 | 15.44 | 39.5 | 14.3 | 23.8s | 1 |

paired sc_k3 vs sc_k1: **+1.30pt CI[−1.68,+4.90] p=0.46** (WORSE, not significant).

## Interpretation (honest)
- **K=3 did NOT reproduce the prior −2pt win** on this run. Root cause = the session-wide VLM-draw variance: this sc_k1 single draw landed at 16.84% (unusually good; same-config draws this session ranged ~16.8–22.3%). Median-of-3 regresses toward the mean (~18%), so vs a lucky-good single baseline it looks WORSE. This is expected: **median-of-K is a variance-reduction tool, not a guaranteed single-run improvement** — it pays off in EXPECTATION over many draws / pooled large-N, which a single n=50 comparison cannot show (the prior −2pt was pooled across NVReal+N5k).
- **Latency: parallelization works** (20.6→23.8s ≈ 1.15×, far below the old ~3× sequential; not exactly 1× because OpenRouter throttles concurrent same-key calls). The latency-neutralization (the point of E12 v2) is achieved.
- **fail=1**: one of the 150 K3-sample VLM calls hit a transient error; asyncio.gather propagates it (no-fallback) → that image fails. Per non-negotiable (failure_count>0 → don't adopt), plus the +1.3pt, **K=3 is NOT adopted; K=1 stays default.**

## Decision / next
- **Adopt: the parallelization CODE** (latency-neutral self-consistency, ready for when K>1 is wanted). **Do NOT enable K=3 by default.**
- To actually validate the variance-reduction win, run K=1-vs-K=3 on the **pooled external sets (N5k 250 + NVReal 104)** where the prior −2pt was measured — a larger-N campaign (≈1400 VLM calls). Deferred (cost/time); the 50-set alone is too draw-noisy to conclude.
- Consider **selective self-consistency** (K>1 only on high-uncertainty/high-calorie images) as a cost-efficient variant — but only after the pooled validation shows K>1 helps at all on the current stack.
- Reinforces the session theme: at n=50 cache=false, VLM-draw variance (~±3pt) dominates single-lever deltas. Robust judgement needs pooled large-N or frozen-VLM isolation (not applicable when the VLM itself is what self-consistency varies).
- Artifact (gitignored): run `20260605_133911`.
