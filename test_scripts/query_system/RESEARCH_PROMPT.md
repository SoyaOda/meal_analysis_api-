# Research Query: CrossEncoder Reranking Alternatives for Text-based Semantic Search

## Context & Problem

We are building a **food name semantic matching system** that matches VLM-generated food queries (e.g., "grilled chicken breast") against a USDA food database (~1,400 items).

**Current Issue:**
- **CrossEncoder** (`cross-encoder/ms-marco-MiniLM-L-6-v2`) returns **NaN scores** on macOS with PyTorch 2.7.1
- Root cause: SDPA (Scaled Dot-Product Attention) incompatibility on macOS
- Issue persists even with `attn_implementation="eager"` workaround
- Affects both CPU and MPS backends

**Current Architecture (2-stage):**
1. **Stage 1**: Bi-encoder (SentenceTransformer) + FAISS → Top-K candidates (K=5)
2. **Stage 2**: **Reranker** → Select best match from K candidates

**Current Temporary Solution:**
- Fallback to bi-encoder cosine similarity for reranking
- Works but not optimal (same model for both stages)

---

## Research Objectives

Compare **text-based reranking alternatives** to CrossEncoder that:

### 1. **Technical Requirements**
- ✅ Works on **macOS** (Apple Silicon M1/M2)
- ✅ Compatible with **PyTorch 2.7.1** or can use alternative frameworks
- ✅ **No NaN score issues**
- ✅ **Open-source** and locally runnable (no external APIs)
- ✅ **Real-time inference**: <100ms for 5-10 candidate pairs

### 2. **Performance Requirements**
- 📈 **Better than bi-encoder cosine similarity** for reranking
- 📈 Handles **semantic similarity** (e.g., "fried potato" ≈ "french fries")
- 📈 Works well with **short text** (5-15 words per item)
- 📈 Domain: **Food names and descriptions**

### 3. **Use Case Specifics**
- **Query example**: `"grilled chicken breast"` (from VLM image analysis)
- **Candidates**: 5-10 USDA food items like:
  - `"Chicken, broilers or fryers, breast, meat only, cooked, grilled"`
  - `"Chicken, broilers or fryers, breast, meat and skin, cooked, roasted"`
  - `"Turkey, breast, meat only, cooked"`
- **Goal**: Pick the **most semantically similar** match

---

## Research Questions

### A. **Alternative Reranking Approaches**

**Q1:** What are the **top alternatives to CrossEncoder** for text reranking in 2024-2025?

Consider:
- **MonoT5 / DuoT5** (T5-based reranking)
- **ColBERT** (late interaction)
- **SPLADE** (sparse retrieval + reranking)
- **BGE-reranker** (BAAI general embedding reranker)
- **Cohere rerank** (if open-source version exists)
- **Custom fine-tuned bi-encoders**
- **LLM-based reranking** (small models like FLAN-T5, Phi-2)
- Other modern approaches

**For each approach, please provide:**
1. **Model name** and Hugging Face link (if applicable)
2. **Architecture** (CrossEncoder, T5, ColBERT, etc.)
3. **Inference speed** benchmark (for 10 pairs)
4. **macOS compatibility** status
5. **Pros/cons** compared to CrossEncoder
6. **Code example** (inference only, 3-5 lines)

---

### B. **ColBERT as Alternative**

**Q2:** Can **ColBERT** be used for reranking instead of retrieval?

- How does ColBERT's **late interaction** compare to CrossEncoder for small candidate sets?
- Is there a **macOS-compatible ColBERT implementation**?
- What's the **inference latency** for scoring 5-10 pairs?
- Code example for ColBERT reranking

---

### C. **BGE-reranker Models**

**Q3:** How do **BAAI/bge-reranker** models perform?

Specific models to investigate:
- `BAAI/bge-reranker-base`
- `BAAI/bge-reranker-large`
- `BAAI/bge-reranker-v2-m3`

Questions:
- Are they **CrossEncoder-based** or different architecture?
- **macOS compatibility** with PyTorch 2.7.1?
- **Performance** vs ms-marco-MiniLM?
- **Code example**

---

### D. **LLM-based Reranking**

**Q4:** Can **small LLMs** (FLAN-T5, Phi-2, etc.) be used for efficient reranking?

Approach:
- Prompt: `"Which text is more relevant to '{query}': (A) {candidate1} or (B) {candidate2}?"`
- Model outputs: `A` or `B`

Questions:
- **Best small LLMs** for this task (<3B parameters)?
- **Inference speed** on CPU (macOS)?
- **Quantization** options (4-bit, 8-bit)?
- How to score **5 candidates** (pairwise comparison or listwise)?
- **Code example** with prompt template

---

### E. **Bi-encoder Improvements**

**Q5:** If sticking with **bi-encoder fallback**, how to improve it?

Options:
- Use **different bi-encoder** for stage 2 (specialized model)?
- **Ensemble** multiple bi-encoders?
- **Fine-tune** a bi-encoder on food domain data?
- **Hybrid scoring** (combine cosine + lexical features)?

---

### F. **Sparse Retrieval Methods**

**Q6:** Can **SPLADE** or **BM25-based reranking** help?

- SPLADE for semantic + lexical matching
- BM25 + neural reranker combination
- **Rank-BM25** with neural features

---

## Expected Output Format

For each alternative approach, provide:

### 1. **Summary Table**

| Approach | Model Example | Speed (10 pairs) | macOS Compatible | Accuracy vs CrossEncoder | Complexity |
|----------|---------------|------------------|------------------|------------------------|------------|
| CrossEncoder | ms-marco-MiniLM | ~60ms | ❌ (NaN issue) | Baseline | Low |
| MonoT5 | castorini/monot5-base | ? | ? | ? | Medium |
| ColBERT | colbert-ir/colbertv2.0 | ? | ? | ? | High |
| BGE-reranker | BAAI/bge-reranker-base | ? | ? | ? | Low |
| LLM (FLAN-T5) | google/flan-t5-small | ? | ? | ? | Medium |
| Bi-encoder+ | all-mpnet-base-v2 | ~30ms | ✅ | Lower | Low |

### 2. **Recommended Solution**

Based on:
- **macOS compatibility**
- **Inference speed** (<100ms)
- **Accuracy** (better than bi-encoder)
- **Ease of implementation**

Provide:
1. **Top 3 recommendations** with rationale
2. **Code example** for best option
3. **Fallback strategy** if top choice fails

### 3. **Implementation Checklist**

For the recommended approach:
- [ ] Install dependencies
- [ ] Load model
- [ ] Test inference
- [ ] Benchmark speed
- [ ] Compare accuracy with existing baseline

---

## Additional Context

### Current Environment
- **OS**: macOS Sequoia 15.6.1 (Apple Silicon M2)
- **Python**: 3.10.12
- **PyTorch**: 2.7.1
- **sentence-transformers**: 5.1.0
- **transformers**: 4.57.1
- **NumPy**: 2.2.6

### Current Working Models
- ✅ **Bi-encoder**: `sentence-transformers/all-MiniLM-L6-v2` (384dim, ~6ms encoding)
- ❌ **CrossEncoder**: `cross-encoder/ms-marco-MiniLM-L-6-v2` (NaN scores)

### Test Data
- **Queries**: 300 food items from VLM analysis
- **Database**: 1,398 USDA food items
- **Sample query**: `"beef steak grilled sliced"`
- **Sample candidates**: 5-10 beef-related USDA items

---

## Bonus: Edge Cases to Consider

1. **Very similar candidates**: How to distinguish `"Chicken, grilled"` vs `"Chicken, broiled"`?
2. **Synonym handling**: `"french fries"` vs `"fried potato"` vs `"pommes frites"`
3. **Partial matches**: `"chicken breast"` should match `"Chicken, broilers, breast, meat only"`

---

## Timeline

- **Research phase**: ASAP (urgent, blocking development)
- **Implementation**: Once best alternative is identified
- **Testing**: Compare against bi-encoder fallback baseline

---

**Please provide comprehensive research with code examples, benchmarks, and actionable recommendations.**
