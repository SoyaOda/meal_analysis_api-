# Lesson: Production reranker instruction was a NO-OP (DeepInfra ignores the 'instruction' field); fixed by baking it into the query. Mild naming win; reranker is NOT the conviction lever.

- Date: 2026-06-02
- Trigger: matching-quality PDCA (USDA matching is the top user-conviction bottleneck). Research+diagnosis workflow (7 agents) showed the production reranker is already Qwen3-Reranker (4B/8B) and is instruction-aware via `config.reranker.instruction`.

## The bug (root cause)
`deepinfra_service.rerank` / `rerank_batch` passed the reranker instruction as a top-level `instruction` field in the DeepInfra payload. **The DeepInfra rerank endpoint IGNORES that field.** Direct verification (query "sour cream", docs [regular, fat-free, reduced-fat]):
- instruction field "prefer fat-free" vs "prefer full-fat" -> BYTE-IDENTICAL scores [0.549, 0.473, 0.669].
- baking the instruction into the query (`Instruct: {instruction}\nQuery: {query}`, the Qwen3-Reranker format) -> scores FLIP correctly (full-fat: regular 0.963 > fat-free 0.955; fat-free: fat-free 0.994 >> regular 0.605).

So `config.reranker.instruction` (with its raw-vs-cooked / form-matching guidance) had been **completely inert in production** — a likely contributor to the diagnosed "leanest record wins" and "generic-over-specific" biases.

## The fix
`format_reranker_query(query, instruction)` bakes the instruction into the query (Qwen3 format); whitespace/empty -> bare query (explicit raw path). Applied in both `rerank` and `rerank_batch`; the dead `instruction` payload field removed. (Note: `reranker_providers.py` has the same latent pattern but is NOT wired into the production search path — left untouched.) Tests: `test_reranker_instruction.py` (4). Verified live: post-fix, the reranker responds to the instruction and e.g. matches mac-and-cheese correctly.

## A/B (dev40, 3 arms, SAME VLM via shared cache so the reranker is the only variable; per-request instruction override, production Firestore untouched)
| arm | conviction | naming_db_match | per-dish correct% | cal_MAE% | high30% |
|---|---|---|---|---|---|
| rerank_raw (current prod = instruction inert) | 33.2 | 1.675 | 14.5 | 20.97 | 27.5 |
| rerank_default (bug-fixed, default instruction applied) | 31.8 | **1.825** | **16.3** | 20.97 | **15.0** |
| rerank_hardened (default + anti-lean + complete-dish + cooked-default) | 30.2 | 1.80 | 13.1 | 17.28 | 20.0 |

(judge = sonnet-4.6 rubric v2, advisory; portion is the deterministic metric. Single run, n=40, no CI — calorie CIs overlap heavily, so calorie deltas are NOT significant.)

## Findings
- **Fixing the bug (applying the existing default instruction) is a mild, real win**: naming 1.675 -> 1.825, per-dish correct 14.5% -> 16.3%, and worst-tail calorie error halved (27.5% -> 15.0%), at zero added cost. It is also a pure CORRECTNESS fix (the feature was broken). **Keep it.**
- **The hardened instruction is REJECTED**: no naming gain, per-dish correct% DROPPED (13.1%), conviction lowest. The extra rules over-steer and cause collateral mis-matches (e.g. tomato -> "Apples, raw" seen in spot checks). Keep the default instruction.
- **The reranker is NOT the user-conviction lever.** Even with the fix, conviction is flat/slightly down within noise. Conviction is dominated by VLM RECOGNITION failures — wrong_food (78-84 dishes) + hallucinated (57-62) + missed — which record-selection cannot fix. The reranker-fixable bad_usda_match bucket (form/granularity, ~37-39) is real but a minority of what tanks conviction. This matches the earlier capability-bound finding ([[20260602_v15_natural_names_rejected_matching_is_capability_bound]]).

## Actions / next
1. **Ship the bug fix** (code). It activates the intended-but-broken `config.reranker.instruction`. This is a PRODUCTION-BEHAVIOR change (the reranker will start honoring the configured instruction) -> flag for the user's deploy decision; the current default instruction is a safe, mild-positive choice.
2. Do NOT adopt the hardened instruction.
3. **Pivot the next PDCA to VLM RECOGNITION** (reduce hallucinations + missed items + wrong-food identity), which is the actual conviction ceiling — not the reranker, not retrieval.

## Related
- [[20260602_judge_conviction_usda_matching_is_top_bottleneck]] (matching flagged as bottleneck — refined here: it's VLM recognition, not record selection)
- [[20260602_v15_natural_names_rejected_matching_is_capability_bound]] (matching is VLM-capability-bound)
- [[20260602_embedding_matcher_does_not_beat_token]] (eval-side matcher; bi-encoder dead end)
