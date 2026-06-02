# Lesson: Embedding matcher does NOT beat the token/char matcher for pred↔GT dish matching (token stays default)

- Date: 2026-06-02
- Built (opt-in, no new dependency): `EmbeddingSimilarity` + `build_embedding_fn` in `run_pdca_batch_eval.py` (reuses the app's `EmbeddingProviderFactory` / Qwen3-Embedding-8B via DeepInfra), wired into `run_judge_eval --match-embeddings` for the deterministic portion matcher. Default remains the dependency-free token/char matcher.
- Motivation: the deterministic portion (lesson [[20260602_rubric_v3_portion_should_be_deterministic]]) loses a few items to the token/char matcher's 0.75 threshold (test_food4/11/13 -> det=0). Embeddings were expected to recover those semantic matches and raise portion agreement vs the careful Opus draft.

## Result: embeddings raise recall but TANK agreement — no operating point beats token
Deterministic portion vs the Opus-draft-v3 golden (n=20, weighted kappa):

| matcher | kappa vs Opus draft | matched/GT |
|---|---|---|
| **token/char, T=0.75 (default)** | **0.503** | 0.31 |
| embedding (no instruction), T=0.75 | 0.115 | 0.44 |
| embedding (no instruction), T=0.80 | 0.164 | 0.23 |
| embedding (no instruction), T>=0.84 | <=0.06 | <=0.06 |
| embedding (+retrieval instruction), best (T=0.80) | 0.152 | 0.28 |
| embedding (+instruction), T>=0.85 | <=0.13 | collapses |

- Embeddings DID fix the token misses (test_food4/11/13: det 0 -> matched) and raised average recall (0.31 -> 0.44 at T=0.75), BUT simultaneously LOST correct matches the token matcher caught (test_food6 5->0, test_food7 5->0, test_food12 3->1) and added wrong matches. Portion scores swung wildly (test_food7 5->0). Net agreement collapsed (0.503 -> 0.12-0.16).
- Threshold sweep (0.75 -> 0.94) never recovers: low T over-matches (every food is somewhat similar in embedding space), high T finds nothing (matched/GT -> 0.01). The retrieval `embedding_instruction` did not change the picture (best kappa 0.152).

## Why
Phrase-level food-name cosine similarity is not discriminative enough for the one-to-one Hungarian assignment used here: distinct foods cluster (chicken/beef/pork, the many "salad …" items) at cosine ~0.6-0.85, so the assignment + single global threshold mis-pairs. The token/char overlap keys on shared head words ("chicken", "broccoli", "macaroni") and is actually better suited to matching a short GT name against a predicted name / verbose USDA `matched_desc`.

## Actions
1. **Token/char matcher stays the DEFAULT.** `--match-embeddings` is kept as an opt-in EXPERIMENTAL capability (tested, default OFF) but is **currently worse — do NOT enable it.** The `similarity_fn` arg of `dish_match_metrics` remains the extension point.
2. If matching quality is revisited (it is the conviction bottleneck, see [[20260602_judge_conviction_usda_matching_is_top_bottleneck]]), the next lever is NOT a bigger general embedding — try a **cross-encoder / reranker** (the app already has Qwen3-Reranker infra) scoring pred-vs-GT pairs, or threshold calibration on a real held-out split (NOT the 20 used here — that would overfit). General bi-encoder embeddings are a dead end for this assignment.
3. Negative result preserved so this is not re-attempted blind.

## Related
- [[20260602_rubric_v3_portion_should_be_deterministic]] (portion is deterministic; matcher is the residual lever)
- [[20260602_judge_conviction_usda_matching_is_top_bottleneck]] (matching = top conviction bottleneck)
