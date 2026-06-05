# Lesson: cross-provider "best regardless of provider" retrieval A/B — NO premium embedding or reranker cleanly beats the free open lightweight models for USDA calorie estimation. The retrieval slot is at its useful ceiling; the real levers are the VLM + input info (E8/E13/E14).

- date: 2026-06-05
- scope: roadmap Part E (provider-agnostic best-model premise). Built provider routing for Voyage/Google/Cohere/OpenAI and A/B'd them on the SAME frozen-VLM, retrieval-isolated harness as E5/E6.
- model: flash + v13 prompt, frozen VLM via shared VLM_CACHE_DIR (all arms cache-HIT 50/50 = retrieval-only difference), 50 images.

## F-PROV foundation implemented
- `services/extra_providers.py`: thin httpx clients for Voyage/Google/Cohere/OpenAI embeddings + Cohere/Voyage rerank, selected by a `"<provider>:<model>"` model-id prefix (e.g. `"google:gemini-embedding-001"`, `"cohere:rerank-v3.5"`). Per-provider query/document conventions baked in (Cohere input_type search_query/search_document; Google taskType RETRIEVAL_QUERY/DOCUMENT; OpenAI/Voyage none). 429/5xx retry+backoff; Google batch throttle. NO new Python deps (raw REST).
- Wired: app-local `DeepInfraService.generate_embeddings` and `rerank`/`rerank_batch` delegate to extra_providers when the model id is external; `build_embedding_ab_index.py` embeds docs via the provider's document convention. DeepInfra/no-prefix path unchanged (regression-safe). Keys in `.env` (gitignored): VOYAGE_API_KEY/GEMINI_API_KEY/COHERE_API_KEY/OPENAI_API_KEY.

## Provider verification (live API, 2026-06-05)
- ✅ Google `gemini-embedding-001` (3072d), Cohere `embed-v4.0` (1536d) + `rerank-v3.5`, OpenAI `text-embedding-3-large` (3072d) — all work.
- ❌ Voyage — HTTP 403 Forbidden on both embed + rerank (key `al-…` rejected; Voyage keys are usually `pa-…`). NOT tested; key needs rechecking.

## Embedding A/B (reranker fixed = Qwen3-Reranker-4B, frozen VLM, 50 imgs)
| embedding | dim | MAE% | MdAPE% | high30 | signed-bias% | paired vs 8B (CI95) |
|---|---|---|---|---|---|---|
| Qwen3-Embedding-8B (current) | 4096 | 22.29 | 15.90 | 20 | +2.5 | — |
| Qwen3-Embedding-0.6B (free) | 1024 | 21.04 | 15.62 | 24 | +4.1 | −1.25 [−8.7,+4.7] |
| Qwen3-Embedding-4B (free) | 2560 | 19.26 | 16.52 | 22 | −5.8 | −3.03 [−10.7,+3.2] |
| Cohere embed-v4.0 | 1536 | 19.68 | 15.05 | 20 | −4.0 | −2.61 [−12.3,+5.0] |
| OpenAI text-embedding-3-large | 3072 | 20.28 | 17.88 | 24 | −2.1 | −2.01 [−10.4,+4.9] |
| Gemini-embedding-001 (MTEB #1) | 3072 | 19.73 | 16.20 | 22 | −2.8 | −2.56 [−11.5,+4.2] |
| bge-m3 (E5) | 1024 | 27.40 | 19.41 | 32 | +13.1 | +5.11 (regress) |
| embeddinggemma-300m (E5) | 768 | 23.27 | 16.31 | 32 | +5.6 | +0.98 (regress) |

## Reranker A/B (embedding fixed = 8B, frozen VLM, 50 imgs)
| reranker | MAE% | p90 | high30 | latency | paired vs Qwen-4B |
|---|---|---|---|---|---|
| Qwen3-Reranker-4B (current) | 20.58 | 40.1 | 18 | (slow) | — |
| Qwen3-Reranker-0.6B (free) | 19.04 | 35.1 | 14 | 0.93s | −1.54 [−8.0,+3.9] |
| Cohere rerank-v3.5 | 18.09 | 36.8 | 18 | 1.85s | −2.49 [−12.2,+2.4] |
| nemotron-rerank-1b (E6, free) | 18.69 | 34.4 | 20 | 0.74s | −3.51 [−13.2,+1.5] |

## Decisive conclusion
1. **No premium retrieval model delivers a clean calorie-accuracy win.** Across 8 embeddings (incl. the MTEB-#1 Gemini and the best-MTEB Cohere/OpenAI) and 2 premium-vs-free rerankers, EVERY paired CI straddles 0 at n=50. The stronger embeddings (4B / Cohere-v4 / Gemini) lower MEAN MAE ~2-3pt but **systematically flip the signed bias negative (−2 to −6%)** — they match lower-density USDA entries, trading one error mode for another (consistent with the 27%-wall decomposition: grams↔density errors cancel, single-lever fixes don't durably help). On the robust central metric (MdAPE) the whole field is tightly clustered (15.0–17.9%).
2. **"newest/biggest/premium ≠ best for this task."** The cross-encoder reranker recovers first-stage precision, so the dense embedder only needs recall@50 — where a free 0.6B LLM-embedder already saturates. The 8B's 4096-dim quality is non-actionable here; only its ~28-31s serverless cold-start latency is real (removed by any lightweight model).
3. **Best premium pick IF one insists**: Cohere `embed-v4.0` (best MdAPE 15.05, MAE 19.68, high30 20) — but with −4% bias + per-call cost/latency, not a decisive win. Cohere `rerank-v3.5` ≈ free Qwen3-Reranker-0.6B.
4. **Pragmatic production pick (unchanged from E5/E6)**: free light stack **Qwen3-Embedding-0.6B + Qwen3-Reranker-0.6B** — near-zero bias preserved (with 0.6B embedding), fastest/cheapest, ~9× embedding latency win, non-inferior-to-better calorie MAE.
5. **The real accuracy levers are NOT retrieval models.** Per the 3-AI review + the 27%-wall decomposition, invest next in: VLM-native params (E17, Google AI Studio thinking_level/media_resolution — the one cross-provider slot not yet tested, and the VLM is the dominant calorie factor), user_context (E8), and real-measured calibration (E13/E14).

## E17' VLM-native A/B (Google AI Studio generateContent native params) — added 2026-06-05
Implemented `services/providers/google_provider.py` (GoogleVLMProvider, registered in VLMProviderFactory as `"google"`). Native params encoded in the model-id suffix so one server/run A/Bs all variants: `google:gemini-3-flash-preview[|media=low|medium|high][|think=low|high]`. JSON mode via `responseMimeType`. Verified live (probe + smoke): media_resolution + thinking_level accepted, valid dishes JSON.

A/B (8B+4B retrieval fixed, **cache=false real VLM**, 50 imgs, fail=0):
| candidate | MAE% | p50 | p90 | high30 | paired vs OR-baseline |
|---|---|---|---|---|---|
| openrouter_baseline (current) | 18.20 | 14.79 | 27.8 | 8 | — |
| google_native | 25.23 | 17.26 | 42.5 | 24 | +7.03 [+3.0,+13.0] p=0.004 |
| google_media=high | 23.01 | 19.21 | 45.6 | 26 | +4.81 [−0.04,+10.2] p=0.076 |
| google_think=high | 21.90 | 17.65 | 42.1 | 20 | +3.71 [−0.46,+9.3] p=0.148 |

**Finding: VLM-native gives NO calorie benefit.** Same model (gemini-3-flash) measured WORSE via Google AI Studio than via OpenRouter, and native params (media_resolution/thinking_level) did NOT help (all variants worse than the OpenRouter baseline; native significantly so). **Caveat**: cache=false n=50 VLM-draw variance is large — this OpenRouter baseline (18.2%) is itself ~4pt better than the same-config 8B+4B runs elsewhere (22.3%), so the +7pt magnitude is partly draw variance and the per-image "paired" CI does NOT remove VLM noise (candidates have independent draws). What is robust: **E17 failed to show any win** — there is no evidence Google-native or its native params beat the current OpenRouter path. Latency this run (~80-140s/img) was abnormal (provider-side throttling) → not interpretable. A frozen-prompt repeat or larger N would tighten the magnitude, but the "no win" conclusion stands.

## Overall cross-provider verdict (ALL slots tested)
Across **embedding** (8B/0.6B/4B/bge-m3/gemma + premium Gemini-#1/Cohere/OpenAI), **reranker** (Qwen-4B/0.6B/nemotron + premium Cohere rerank-v3.5), and **VLM-native** (Google AI Studio + media_resolution/thinking_level), **NO cross-provider "best" model delivers a clean calorie-accuracy win** over the current/free stack. The retrieval slot is at its ceiling (reranker absorbs first-stage; 27%-wall errors cancel) and the VLM-native params don't move calorie. → **The real levers are NOT model selection**: per the 3-AI review + the 27%-wall decomposition, invest in **E8 (user_context / input info), E13/E14 (real-measured stratified calibration), and uncertainty/clarification (E3/E9)**. Pragmatic production stack: current OpenRouter gemini-3-flash VLM + free light retrieval (Qwen3-Embedding-0.6B + Qwen3-Reranker-0.6B) for the ~9× embedding-latency win at non-inferior calorie.

## Caveats
- n=50 paired CIs are wide (retrieval-flip heterogeneity; most images keep the same top match). Frozen-VLM retrieval comparison is deterministic, so point estimates are the stable retrieval-isolated effect; the wide CI is heterogeneity, not run noise. A larger N or the retrieval gold set (F4) would tighten significance — but the across-the-board CI-straddles-0 + bias-flip pattern is itself the conclusion.
- Voyage untested (403). Self-host gte-reranker-modernbert-base (research-doc top reranker) not tested (needs a self-host endpoint).
- Artifacts (gitignored evals/runs/): cohere_emb 20260605_002036, openai 20260605_002102, gemini 20260605_002821, qwen4b 20260605_000443, E6' reranker 20260605_001358. Indexes under gitignored data/faiss_ab/{cohere_emb,openai_emb,gemini_emb,qwen3_4b,...}.
