# Embedding/Reranker landscape research (2026-06-04) — fix the ~30s embedding latency

> 背景: 現行 Qwen3-Embedding-8B(dim4096) + Qwen3-Reranker-4B（DeepInfra serverless）。USDA FNDDS 13,564件の小コーパスに短い食材名を検索。**embedding API 呼び出しが毎回 ~28-31s（8B の serverless スケール0→コールドスタート）= 全リクエスト ~44s の主因**。本 doc は web research（6エージェント・5観点）の統合結論。

Decision-oriented synthesis for your use case (short food-name queries, 13,564-doc FNDDS corpus, FAISS top-50 → cross-encoder rerank, hard <1s embedding budget). The five findings agree strongly; below is the decisive read.

---

## 1) Are Qwen3-Embedding-8B + Qwen3-Reranker-4B still the best choice in 2026 for THIS use case?

**No (partly on quality, no on fit).**

- **Embedder:** Qwen3-Embedding-8B is genuinely SOTA (still #1 MMTEB multilingual ~70.6, best open-weight). But it is the wrong tool here. Your first stage only needs **recall@50** on a tiny, semantically-clean 13.5k corpus; the cross-encoder recovers precision. In that role a 0.6B/308M model is within a few nDCG points, and the gap shrinks further on an easy small corpus. The 8B's quality is real but **non-actionable** here — and its 8B size is the literal cause of the ~28-31s serverless cold-start. You're paying (in latency) for quality the reranker makes redundant.
- **Reranker:** Qwen3-Reranker-4B is **no longer competitive** for short-query reranking. Independent short-query benchmarking (aimultiple, ~145k Amazon reviews) ranks it **4th at 77.67% Hit@1, ~1,100ms**, *behind* a 149M model (gte-reranker-modernbert-base, 83% Hit@1, ~150ms), a 0.6B (jina-reranker-v3, 81.3%, 188ms) and a 1.2B (nemotron-rerank-1b, 83%, 243ms). It is both slower and less accurate on exactly your regime.

**Root cause framing (do not lose this):** the ~28-31s is **serverless scale-to-zero cold-start of an idle 8B model** — textbook, not a bug. Bursty short-query traffic hits a cold start nearly every request. This is fundamentally incompatible with <1s on serverless scale-to-zero. Fix the embedding packaging first; the reranker is **not** your bottleneck.

---

## 2) Fastest path to fix the ~30s embedding latency: (A) keep-warm 8B vs (B) switch to a fast model

**(A) Keep Qwen3-8B, make it always-warm (DeepInfra dedicated, `min_instances=1`)**
- Pros: zero quality change, **no re-embedding** (model unchanged), kills cold-start (<100ms warm), keeps data on your infra.
- Cons: pays per GPU-hour regardless of traffic — **A100 80GB ~$0.89/hr ≈ $640/mo, H100 ~$1.79/hr ≈ $1,290/mo, 24×7**. The reranker needs its own warm GPU, **roughly doubling** that. For low/bursty traffic this is **poor value** — you lose the entire serverless cost benefit the moment you pin a replica.
- Effort: low (config change). **Choose only if a hard data-residency / no-third-party rule applies.**

**(B) Switch to a fast model — STRONGLY PREFERRED.** Two concrete shapes:

**B1 — Hosted always-warm API (lowest ops, fastest to ship):**
- **Top pick: Voyage `voyage-3.5-lite`** — vendor ~11ms single short query, **$0.02/1M tokens**, **1024-dim Matryoshka** (shrinks FAISS vs current 4096), quality reportedly above OpenAI 3-large. `voyage-3.5` (~62.5ms, $0.06/1M) is the higher-quality step-up if lite under-recalls.
- **Quality-first alternative: `gemini-embedding-001`** (GA) — MMTEB ~68.3, 3072-dim (MRL-truncatable to 768/1536), ~$0.15/M. Use if food-name recall is the real pain.
- Caveat from findings: vendor latencies aren't independently reproduced, and OpenAI 3-small showed **p99 ~5s** in independent benchmarking — so **wrap every call in a 300-500ms timeout** and lean on the reranker. (OpenAI 3-large/3-small: not recommended — no latency edge, beaten on quality.)

**B2 — Self-hosted small model on a warm box (no vendor, cheap to keep warm):**
- **Top pick: EmbeddingGemma-300M** — ~tens of ms/query, English MTEB v2 ~69.67, 768-dim Matryoshka-truncatable to 256 (~4-5% Recall@10 loss, recoverable by the reranker), runs <200MB (CPU/edge OK → most robust cold-start cure).
- **Lowest-friction alternative: Qwen3-Embedding-0.6B** — same Qwen family (identical prompt/instruction conventions, most familiar embedding geometry), ~13× smaller, sub-second, cheap to keep warm. Or **bge-m3** (already a DeepInfra hosted endpoint → change one model ID, no infra mgmt).

**Re-embed-13.5k-docs effort (B, any variant):** the whole corpus is **well under 1M tokens → one-time ~$0.0001-0.02, minutes**. Negligible. This is **not** the risk; the risk is re-validation (Section 5).

---

## 3) Reranker: keep Qwen3-Reranker-4B or switch?

**Switch.** Since you must re-embed anyway, retire the whole Qwen3 pair.

- **Top pick: `gte-reranker-modernbert-base` (149M, Alibaba)** — tied-best short-query accuracy (**83% Hit@1, ~150ms**, realistically **<100ms** on top-50 short pairs), free open weights, TEI-deployable, **co-locate on the same warm box as the embedder** → no per-call cold-start, no extra vendor, sub-200ms.
- **Alternatives:** `jina-reranker-v3` (0.6B, 81.3% Hit@1, BEIR-SOTA among rerankers, sub-200ms) — but **CC-BY-NC license is a blocker for a commercial calorie tracker**; self-host needs a commercial arrangement, or use its hosted API. `nemotron-rerank-1b` (83%, 243ms) as a fallback. Hosted-warm option if you don't want a GPU: **Voyage `rerank-2.5-lite`** (~0.6s, $0.02/1M, 200M free tokens → effectively free at your scale).

---

## 4) Recommended target stack + expected latency + migration steps

**Recommended target stack (decisive pick):**

| Component | Model | Dim | Why |
|---|---|---|---|
| Embedding | **Voyage `voyage-3.5-lite`** (hosted, warm) | 1024 (Matryoshka) | ~11ms, $0.02/1M, no cold-start, smaller FAISS index, quality ≥ OpenAI 3-large |
| Reranker | **`gte-reranker-modernbert-base`** (149M, self-host warm) | — | 83% Hit@1, <100-150ms, free, no vendor lock-in |

**Expected per-request latency:** embedding ~10-60ms + FAISS top-50 (trivial on 13.5k) + rerank <150ms ≈ **well under 1s end-to-end** (vs ~44s today). Embedding latency drops from ~28-31s to sub-100ms.

**If a no-third-party/data-residency rule applies**, swap embedding to self-hosted **EmbeddingGemma-300M** (768→256-dim) co-located with the reranker on one warm GPU — same sub-1s profile, zero external dependency. Worst-case all-self-host fallback that changes nothing else: **DeepInfra dedicated 8B `min_instances=1`** (keeps quality, ~$640-1,290/mo, no re-embed).

**Migration steps:**
1. Stand up the embedding choice (Voyage key + 300-500ms timeout wrapper, or warm self-host endpoint).
2. **Re-embed all 13,564 FNDDS docs once** with the new model (batch, minutes, ~cents). Build a **new FAISS index at the new dim (4096 → 1024 for Voyage, or 256-768 for Gemma)** — smaller index = faster search, less memory. Keep the old 4096 index alongside for A/B.
3. Deploy `gte-reranker-modernbert-base` via TEI on the **same warm box** as the (self-host) embedder, or alongside the API.
4. Add the **timeout + reranker** as the safety net for tail latency.
5. Run the eval harness (Section 5) on old vs new before cutover; flip behind a flag.

---

## 5) Risks / what to A/B test (retrieval quality must not regress)

**Primary risk is NOT embedder quality — it is the one-time re-embed + re-validation**, plus tail latency and licensing. Concretely:

- **Quality regression on YOUR domain.** All cited benchmarks are general/e-commerce/medical, **not USDA food names**, and reranker deltas are only a few points (could flip on your domain). **Gate strictly on your own eval harness** (NDCG/Hit@1 / gold FNDDS match on your 50-example PDCA set), end-to-end old-pair vs new-pair, before cutover.
- **A/B matrix:**
  - **Embedders:** `voyage-3.5-lite` vs `voyage-3.5` vs `gemini-embedding-001` (and self-host EmbeddingGemma-300M if residency matters) — judge **recall@50** on real food-name queries.
  - **Rerankers:** `gte-reranker-modernbert-base` vs `jina-reranker-v3` vs `nemotron-rerank-1b` — judge Hit@1 / NDCG on gold FNDDS match.
  - **Matryoshka dim sweep** (Voyage 1024; Gemma 768/256) — confirm the dim-truncation recall loss is recovered by the reranker.
- **Tail latency.** Vendor sub-100ms numbers are not independently reproduced; OpenAI showed p99 ~5s. **Hard 300-500ms timeout on every embedding call** + reranker as backstop. Measure p50/p90/p99, not just mean.
- **Licensing.** `jina-reranker-v3` is **CC-BY-NC** — resolve commercial licensing before self-hosting, or use its hosted API. `gte-reranker-modernbert-base` (open) avoids this.
- **Vendor / lock-in.** Hosted embeddings mean data leaves infra and future re-embeds depend on the vendor (Voyage/Google). EmbeddingGemma/bge-m3/Qwen-0.6B self-host avoids this if it matters.
- **Don't regress on the easy win:** keep the cutover behind a flag with the old index retained so you can roll back instantly if eval shows regression.

**Bottom line:** Stop paying ~30s for 8B quality the reranker makes redundant. Target stack = **Voyage `voyage-3.5-lite` (or self-host EmbeddingGemma-300M) + `gte-reranker-modernbert-base`**, expected **<1s** end-to-end, re-embed is trivial, and the only real work is A/B-gating retrieval quality on your own eval harness before flipping.