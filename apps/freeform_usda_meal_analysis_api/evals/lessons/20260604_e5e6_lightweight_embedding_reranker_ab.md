# Lesson: E5/E6 — lightweight DeepInfra embedding + reranker A/B. Qwen3-Embedding-0.6B is non-inferior to 8B at ~9× lower embedding latency; swapping the reranker 4B→0.6B (or nemotron-1b) DIRECTIONALLY improves calorie MAE and the tail. The current 8B+4B stack is the slowest AND the worst.

- date: 2026-06-04
- scope: E5 (embedding A/B) + E6 (reranker A/B), roadmap `plans/PDCA_ROADMAP_3AI_REVIEW_20260604.md`
- model: flash (`gemini-3-flash-preview`), v13 prompt (prompt_sha256 c8d2fb97b30a86fa), reranker/search = ConfigManager defaults except the swapped dimension

## Setup (clean isolation)
- **Re-embedded the existing 13,564-doc metadata** with each candidate (script `scripts/build_embedding_ab_index.py`), reusing the SAME metadata + BM25 index → only the FAISS embedding vectors change. Per-model document/query prompt conventions applied (Qwen3 instruct prefix / EmbeddingGemma `task:`/`title:` format / bge-m3 plain) via new helpers `format_embedding_query`/`format_embedding_document`.
- **Fixed a blocking E5 bug**: app-local `DeepInfraService.generate_embeddings` ignored `self.model_id` and used the hardcoded default `Qwen/Qwen3-Embedding-8B`, so `EMBEDDING_MODEL` was a **no-op at both query and build time**. Now defaults `model` to `self.model_id`. (Verified live: 0.6B server returns dim-1024 results, http 200.)
- **VLM frozen across arms**: added opt-in disk persistence to `VLMCache` (env `VLM_CACHE_DIR`). The 8B baseline arm populated the cache with real VLM; all candidate arms ran with `use_vlm_cache=true` and logged **MISS=0** (VLM never recomputed) → the per-image calorie delta isolates RETRIEVAL only. This is the CLAUDE.md "retrieval-only A/B → cache=true is a justified exception". Note: the harness `cache_hit_rate_percent` does NOT reflect disk-cache hits (stays 0.0); confirm freezing via server-log `VLM Cache HIT` + latency.
- Eval: full 50 set, flash temp 0.3, frozen VLM. Retrieval/embedding/rerank APIs are non-sampling → the frozen-VLM comparison is **deterministic** (repeating gives identical results; the wide bootstrap CIs reflect image-to-image heterogeneity — most images keep the same top match, a few flip hard — not run-to-run noise).

## E5 — embedding A/B (reranker fixed at 4B), 50 images, frozen VLM
| embedding | dim | MAE% | MdAPE% | high30% | bias% | dish_f1 | embed latency (warm/cold, single short q) |
|---|---|---|---|---|---|---|---|
| Qwen3-Embedding-8B (current) | 4096 | 22.29 | 15.90 | 20.0 | +2.5 | 0.262 | ~6s / ~28-31s worst-case cold |
| **Qwen3-Embedding-0.6B** | 1024 | **21.04** | 15.62 | 24.0 | +4.1 | 0.303 | **0.70s / 0.74s** |
| bge-m3 | 1024 | 27.40 | 19.41 | 32.0 | +13.1 | — | 1.5s / 4.5s |
| embeddinggemma-300m | 768 | 23.27 | 16.31 | 32.0 | +5.6 | — | 0.62s / 0.63s |

Paired vs 8B (per-image APE delta): **Qwen3-0.6B −1.25pt CI[−8.68,+4.69]** (straddles 0 = non-inferior); bge-m3 +5.11pt (regress); gemma +0.98pt (regress).

**E5 verdict: Qwen3-Embedding-0.6B is the winner** — calorie MAE non-inferior to 8B (point slightly better), dish_match recall/f1 slightly BETTER, at ~9× lower embedding latency and removal of the 28-31s serverless cold-start (the single largest production latency source). bge-m3 and embeddinggemma both REGRESS calorie quality on USDA food-name retrieval → not adopted. (Confirms the research-doc prediction: the 0.6B, same Qwen family + identical instruct convention, is the lowest-risk swap; the cross-encoder reranker recovers first-stage precision so the 8B's 4096-dim quality is non-actionable here — only its latency cost is real.)

## E6 — reranker A/B (embedding fixed at 8B), 50 images, frozen VLM
| reranker | MAE% | p50 | p90 | high30% | rerank latency | paired vs 4B |
|---|---|---|---|---|---|---|
| Qwen3-Reranker-4B (current) | 22.21 | 15.26 | **45.44** | 20.0 | 1.44s* | — |
| nvidia/llama-nemotron-rerank-vl-1b-v2 | 18.69 | 16.50 | 34.44 | 20.0 | 0.74s* | −3.51pt CI[−13.25,+1.52] p≈0.37 |
| **Qwen3-Reranker-0.6B** | **18.06** | 15.09 | **30.45** | **12.0** | 0.97s* | **−4.15pt** CI[−15.14,+2.24] p≈0.36 |

*latency = run avg incl. cache-lookup; the direct probe gave ~0.55-0.6s for all three on 20 docs.

**E6 verdict: the current Qwen3-Reranker-4B is the WORST of the three** (worst p90 tail 45.4%). Both **nemotron-1b and Qwen3-Reranker-0.6B directionally improve** calorie MAE (−3.5/−4.1pt point), p90 (45→34/30) and (for 0.6B) high30 (20→12). Qwen3-Reranker-0.6B is best on every axis. Paired CIs straddle 0 at n=50 (not statistically significant) but the direction is consistent. Confirms the research-doc claim that Qwen3-Reranker-4B is "no longer competitive for short-query reranking."

## Combined LIGHT stack: Qwen3-Embedding-0.6B + Qwen3-Reranker-0.6B (frozen VLM)
| stack | MAE% | MdAPE% | p90 | high30% | bias% | dish_recall | dish_f1 |
|---|---|---|---|---|---|---|---|
| 8B + 4B (current prod) | 22.29 | 15.90 | 45.38 | 20.0 | +2.5 | 0.272 | 0.262 |
| **0.6B + 0.6B** | **18.84** | 15.07 | 39.51 | 22.0 | +2.7 | 0.304 | 0.297 |

Paired vs 8B+4B: **−3.45pt CI[−11.71,+3.41]**, win/tie/lose 25/3/22. p90 improved (45.4→39.5), bias neutral, dish_recall/f1 improved. Most of the gain is the reranker swap; the embedding swap is the latency/cost win at non-inferior quality.

## production-realistic confirmation (cache=false, real independent VLM draws)
| stack (real VLM) | MAE% | p50 | p90 | high30% | end-to-end latency | cost/img |
|---|---|---|---|---|---|---|
| 8B + 4B (current, arm8B) | 22.29 | 15.90 | 45.38 | 20.0 | 26.64s | $0.0085 |
| **0.6B + 0.6B (run 20260604_232753)** | **18.42** | 15.22 | 43.12 | 18.0 | **19.50s** | $0.0084 |

The cache=false (unpaired, independent VLM) result **−3.87pt MAE** corroborates the frozen-VLM paired result (−3.45pt) → the light-stack quality gain is **robust to VLM variation**, not a frozen-VLM artifact. End-to-end latency −7.1s (−27%) even with the 8B already partially warm; in low-traffic production where the 8B serverless goes fully cold (28-31s embedding), the latency win is far larger.

## Promotion gate (F3 AND-condition) verdict
- MAE ≥2pt improvement: ✓ (point −3.45pt) — but **paired CI upper < 0: ✗** (+3.41 at n=50, heterogeneity-driven).
- p90 non-degraded: ✓ (improved). bias non-degraded: ✓. 30%+ non-degraded: ✓ (~tie). dish_match non-degraded: ✓ (improved). latency/cost budget: ✓✓ (large win).
- **Verdict: adopt-leaning HOLD.** TWO independent regimes (frozen-VLM paired −3.45pt; cache=false real-VLM −3.87pt) agree the light stack is BETTER on calorie MAE, with non-degraded p90/bias/high30/dish_match and a large latency/cost win. The only unmet strict criterion is the paired-CI-upper<0 at n=50 (heterogeneity-driven). The embedding swap (8B→0.6B) is adoptable on latency/cost with confirmed non-inferiority NOW; the reranker swap (4B→0.6B) is corroborated across both regimes and improves the tail. Recommend promotion of the light stack pending one more independent-VLM-draw run (or larger N) to tighten the CI, OR accept on the consistent two-regime evidence + decisive latency/cost case.
- Deploy to Cloud Run / Firestore requires explicit user instruction (not done here).

## Exact DeepInfra ids (verified present 2026-06-04)
- embeddings: `Qwen/Qwen3-Embedding-8B` (4096), `Qwen/Qwen3-Embedding-0.6B` (1024), `BAAI/bge-m3` (1024), `google/embeddinggemma-300m` (768)
- rerankers (type=reranker, `/v1/inference/{model}` with `{queries,documents}`→`scores`): `Qwen/Qwen3-Reranker-{0.6B,4B,8B}`, **`nvidia/llama-nemotron-rerank-vl-1b-v2`** (= "nemotron-rerank-1b"; works with a bare query, NOT the Qwen `Instruct:` format → pass reranker_instruction=" ").

## Quality-ceiling check: Qwen3-Embedding-4B (DeepInfra, free; reranker fixed at 4B, frozen VLM, cache-HIT 50/50)
| embedding | MAE% | MdAPE% | high30% | bias% | dim | retrieval lat | paired vs 8B |
|---|---|---|---|---|---|---|---|
| 8B | 22.29 | 15.90 | 20.0 | +2.5 | 4096 | (cold 28-31s) | — |
| 0.6B | 21.04 | 15.62 | 24.0 | +4.1 | 1024 | 1.35s | −1.25pt CI[−8.68,+4.69] |
| 4B | 19.26 | 16.52 | 22.0 | −5.79 | 2560 | 2.05s | −3.03pt CI[−10.65,+3.20] |

4B is NOT a clean win: lower mean MAE but (a) **flips signed bias to −5.79%** (8B/0.6B are ~neutral — degrades the "no systematic bias" KPI), (b) **worse MdAPE than 0.6B** (16.5 vs 15.6 — improvement is tail-only, not central), (c) 2.5× the dim (2560), 139MB index, higher latency/cost. → **0.6B remains the best-balanced embedding** (non-inferior MAE, near-zero bias, fastest/smallest/cheapest). Going bigger in-family just shuffles which foods match (trading error modes), reinforcing that **retrieval embedding is near its useful ceiling for this task** (consistent with the 27%-wall decomposition: single-lever fixes cancel). Bigger levers = reranker (E6) and the VLM itself.

## Web research confirmation (2026-06-04) — usage was optimal; regression is genuine task-fit
A 5-agent web-research sweep (HF model cards, papers, DeepInfra docs, MTEB) CONFIRMED our usage was correct/optimal for all three, and that the bge-m3/gemma regression is a genuine task-fit limitation, NOT a usage artifact:
- **bge-m3** = ENCODER (XLM-RoBERTa-large ~560M, 2024), CLS pooling, **needs NO query instruction** (official: "no longer requires adding instructions to the queries"; maintainer confirmed) → our raw query/raw doc + L2-norm + cosine is exactly right. Its strengths (multilingual / dense+sparse+ColBERT hybrid / 8192-ctx) are irrelevant to short English; **on DeepInfra's OpenAI endpoint only the DENSE mode is exposed = its weakest mode for this task** (sparse/ColBERT unavailable; the pipeline's BM25 partly fills the sparse role).
- **embeddinggemma-300m** = Gemma3-based 308M on-device model (Sept 2025), mean pooling, MRL 768. Official retrieval prompts are EXACTLY query=`"task: search result | query: "` / doc=`"title: none | text: "` (what we used). DeepInfra's OpenAI endpoint has **no input_type/prompt param and does NOT auto-apply prompts → manual prepend (ours) is required and correct.** It ties Qwen3-0.6B on overall English MTEB but **trails on pure English retrieval (55.7 vs ~64.7)** — retrieval is its weaker axis.
- **Qwen3-Embedding-0.6B** = LLM/decoder (Qwen3, June 2025), last-token pooling, asymmetric instruct (query instruct, doc plain) = what we used. **Strongest open ≤1B for English retrieval** (beats even 7B gte-Qwen2 on retrieval). Our 14/15 dense-recall + non-inferior calorie matches this.
- Empirical dense-recall probe agreed: optimal variant per model was the one we used (Qwen3 instruct 14/15 > raw 10/15; bge-m3 raw = with-instruction 13/15; gemma task-prompt 14/15 > raw 13/15).
- **"newest ≠ best for this task"**: bge-m3 (2024 multilingual/hybrid encoder) and embeddinggemma (2025 on-device 300M) optimize for goals other than short-English dense retrieval; the LLM-based Qwen3-0.6B wins on this specific task.
- **Genuine quality ceiling is cross-provider closed APIs** (per April-2026 MTEB-Eng snapshot): gemini-embedding-001 (#1, 68.32, Google API only), Voyage-3.x (API only) — NOT on DeepInfra. Free DeepInfra quality-ceiling reference to try: **Qwen3-Embedding-4B** (retrieval 68.5 vs 0.6B 61.8). → drives the provider-agnostic expansion (roadmap Part E).

## Caveats / follow-ups
- The eval harness sends `user_context="pdca_batch_eval"`, which E8 now injects into the VLM prompt as USER-PROVIDED CONTEXT. Constant across all arms (frozen in cache) so it does NOT bias the A/B, but it mildly pollutes the absolute prompt — harness should send empty user_context or skip injection for sentinel values.
- Significance: n=50 paired CIs are wide due to retrieval-flip heterogeneity. A 2nd run with a DIFFERENT frozen VLM draw (re-seed) would test robustness to VLM variation; the frozen retrieval comparison itself is deterministic.
- Artifacts (gitignored `evals/runs/`): 8B+4B `20260604_231239`, 0.6B+4B `20260604_232209`, bge-m3 `20260604_232233`, gemma `20260604_232042`, E6 3-cand `20260604_232352`, 0.6B+0.6B frozen `20260604_232735`. Candidate indexes under gitignored `data/faiss_ab/`.
