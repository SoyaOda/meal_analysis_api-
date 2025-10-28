🚀 New models by Bria.ai, generate and edit images at scale 🚀

Search That Actually Works: A Guide to LLM Rerankers
Published on 2025.09.10 by DeepInfra
Search That Actually Works: A Guide to LLM Rerankers

Search relevance isn’t a nice-to-have feature for your site or app. It can make or break the entire user experience.

When a customer searches "best laptop for video editing" and gets results for gaming laptops or budget models, they leave empty-handed.

Embeddings help you find similar content, but they often miss the mark when it comes to true relevance. Rerankers solve this problem by taking your initial search results and reordering them based on what actually matches your query.

DeepInfra provides state-of-the-art reranking models that make implementing this technology straightforward and cost-effective.
What are Rerankers?

Rerankers evaluate and reorder search results based on their relevance to a specific query. Unlike embeddings that work by measuring similarity in vector space, rerankers examine the actual relationship between a query and each candidate document, providing much more nuanced relevance scoring.

Think of rerankers as expert librarians who not only know where books are located but can also determine which book best answers your specific question. They understand context, intent, and subtle semantic relationships that traditional similarity matching might miss.

The key advantage of rerankers lies in their ability to consider the full context of both query and document simultaneously. While embeddings compare pre-computed vectors, rerankers dynamically analyze the query-document relationship, leading to significantly more accurate relevance scoring.
Traditional vs. LLM-Based Rerankers

Before LLMs, rerankers relied on classical machine learning approaches like learning-to-rank algorithms (RankNet, LambdaMART), feature-based models using BM25 scores, click-through data, and document metadata, or simple rule-based systems that weighted factors like keyword matching and document freshness.

These traditional approaches had significant limitations. They required extensive feature engineering, couldn't understand semantic meaning beyond keyword matching, and struggled with complex queries or domain-specific language. A search for "best budget phone for photography" might rank results based on keyword frequency rather than understanding that the user wants affordable devices with good cameras.

LLM-based rerankers like Qwen3 represent a fundamental shift. They understand natural language intent, can process context across entire documents, handle multilingual queries seamlessly, and adapt to domain-specific terminology without manual tuning. They don't just count keywords—they comprehend meaning.

As user expectations rise and queries become more conversational, your applications need to be able to understand the user’s intent behind every context. While traditional methods might still work for simple keyword matching, they can't compete with LLMs when users search with phrases and prompts like "show me laptops that won't break when my kids use them" or "find research papers that contradict the main findings in this study."
Two-stage retrieval architecture (embeddings + rerankers)

Modern search systems employ a two-stage architecture that leverages the strengths of both embeddings and rerankers:

Stage 1: Fast Candidate Retrieval (Embeddings)

    Process: Convert query to embedding vector
    Search: Find top 50-500 similar documents using vector similarity
    Speed: Extremely fast, can search millions of documents in milliseconds
    Purpose: Cast a wide net to capture potentially relevant content

Stage 2: Precise Relevance Ranking (Rerankers)

    Process: Evaluate query-document pairs individually
    Analyze: Deep semantic understanding of relevance
    Reorder: Rank candidates by true relevance to the query
    Purpose: Surface the most relevant results from the candidate pool

This architecture balances efficiency with accuracy. Embeddings handle the heavy lifting of searching large collections, while rerankers focus their computational power on making the final relevance determinations that matter most to users.
When to use rerankers vs. embeddings alone

Use embeddings alone when:

    You need extremely fast response times, < 100ms (real-time chat suggestions, autocomplete)
    Working with simple similarity matching tasks (finding duplicate content, basic recommendations)
    Budget constraints are primary concern (startup MVPs, prototype systems)
    Query and document types are very similar (searching within product catalogs, FAQ matching)

Add rerankers when:

    Search relevance quality is critical to user experience (e-commerce product search, customer support)
    Dealing with complex queries that require understanding intent (natural language questions, multi-part requests)
    Working with heterogeneous content (different document types, lengths, formats) (enterprise knowledge bases, legal databases)
    False positives from embedding-only search are problematic (medical information retrieval, technical documentation)
    User satisfaction scores indicate poor result relevance (high bounce and exit rates, low click-through rates)

The performance improvement from adding rerankers is typically most dramatic in scenarios involving complex queries, domain-specific content, or when precision is more important than recall.
Available Qwen3 Embedding & Reranker Models on DeepInfra

Embedding Models:

    Qwen3-Embedding-0.6B (0.6B parameters)
    Qwen3-Embedding-4B (4B parameters)
    Qwen3-Embedding-8B (8B parameters)

Reranker Models:

    Qwen3-Reranker-0.6B (0.6B parameters)
    Qwen3-Reranker-4B (4B parameters)
    Qwen3-Reranker-8B (8B parameters)

Real-World Applications for LLM Rerankers
Application	Use Case	Business Impact
RAG Systems	Improve context selection for LLM responses	Higher answer accuracy, reduced hallucination
E-commerce Search	Rank products by purchase intent vs. keyword match	Increased conversion rates, better user experience
Enterprise Knowledge Management	Surface most relevant internal documents	Faster employee onboarding, improved productivity
Customer Support	Match support tickets with best resolution articles	Reduced resolution time, higher satisfaction
Legal Research	Rank case law and precedents by relevance	More thorough research, better case preparation
Academic Search	Prioritize papers by research relevance	Accelerated literature reviews, better citations
Code Search	Rank code snippets by functional similarity	Faster development, improved code reuse
Content Recommendation	Personalize content ranking beyond topic similarity	Higher engagement, increased time-on-site
Recruitment	Match candidates to job requirements more precisely	Better hiring decisions, reduced screening time
Medical Information Retrieval	Rank diagnostic information by symptom relevance	Improved diagnostic accuracy, better patient outcomes
Technical Implementation - DeepInfra Reranker Model Inference Options
How to integrate reranker APIs into existing search systems

Integrating rerankers into your existing search pipeline is straightforward with DeepInfra's API. The typical integration pattern follows these steps:

    Initial Retrieval: Use your existing search system (embeddings, keyword search, etc.) to get candidate documents
    Reranking: Send query and candidates to the reranker API
    Result Processing: Reorder your original results based on the reranker scores

Here's the basic integration pattern:

import os
import requests

DEEPINFRA_TOKEN = os.getenv("DEEPINFRA_TOKEN")

def rerank_results(query, documents, model="Qwen/Qwen3-Reranker-4B"):
    url = f"https://api.deepinfra.com/v1/inference/{model}"
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "queries": [query],
        "documents": documents
    }

    response = requests.post(url, headers=headers, json=payload)
    scores = response.json()["scores"]

    # Sort documents by reranker scores
    ranked_results = sorted(zip(documents, scores),
                            key=lambda x: x[1], reverse=True)
    return ranked_results

# Example usage
query = "How to optimize database performance?"
candidate_docs = [
    "Database indexing improves query performance significantly...",
    "Regular maintenance schedules are important for servers...",
    "Query optimization techniques include proper indexing..."
]

ranked_results = rerank_results(query, candidate_docs)
copy

Code examples with DeepInfra's Qwen reranker models from Qwen3

DeepInfra offers three Qwen3 reranker models with different performance characteristics:

Qwen3-Reranker-0.6B - Optimized for speed and cost efficiency:

def fast_rerank(query, documents):
    url = "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-0.6B"
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "queries": [query],
        "documents": documents,
        "instruction": "Rank documents by relevance for quick customer support queries"
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()["scores"]
copy

Qwen3-Reranker-4B - Balanced performance for production use:

def balanced_rerank(query, documents):
    url = "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-4B"
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "queries": [query],
        "documents": documents,
        "instruction": "Given a technical query, rank documentation by practical relevance"
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()["scores"]
copy

Qwen3-Reranker-8B - Maximum accuracy for critical applications:

def precision_rerank(query, documents):
    url = "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-8B"
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "queries": [query],
        "documents": documents,
        "instruction": "For legal research queries, prioritize documents with direct precedential value"
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()["scores"]
copy

Pairing Reranker models with embeddings models

The most effective approach combines embeddings for initial retrieval with rerankers for final ranking. Here's a complete implementation using both Qwen3 embeddings and rerankers:

import os
import numpy as np
import requests

DEEPINFRA_TOKEN = os.getenv("DEEPINFRA_TOKEN")

class TwoStageRetrieval:
    def __init__(self, embedding_model="Qwen/Qwen3-Embedding-4B",
                 reranker_model="Qwen/Qwen3-Reranker-4B"):
        self.embedding_model_name = embedding_model
        self.reranker_model_name = reranker_model
        self.embeddings_cache = {}

    def get_embeddings(self, texts):
        """Get embeddings using DeepInfra API"""
        url = "https://api.deepinfra.com/v1/openai/embeddings"
        headers = {
            "Authorization": f"Bearer {DEEPINFRA_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "input": texts,
            "model": self.embedding_model_name
        }

        response = requests.post(url, headers=headers, json=payload)
        embeddings = [item["embedding"] for item in response.json()["data"]]
        return np.array(embeddings)

    def similarity_search(self, query, documents, top_k=50):
        """Stage 1: Fast similarity search using embeddings"""
        # Get query embedding
        query_embedding = self.get_embeddings([query])[0]

        # Get document embeddings (cache for efficiency)
        doc_embeddings = self.get_embeddings(documents)

        # Calculate similarities
        similarities = np.dot(doc_embeddings, query_embedding)

        # Get top-k candidates
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        candidates = [documents[i] for i in top_indices]

        return candidates

    def rerank(self, query, documents):
        """Stage 2: Precise reranking"""
        url = f"https://api.deepinfra.com/v1/inference/{self.reranker_model_name}"
        headers = {
            "Authorization": f"Bearer {DEEPINFRA_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "queries": [query],
            "documents": documents
        }

        response = requests.post(url, headers=headers, json=payload)
        scores = response.json()["scores"]

        # Sort by reranker scores
        ranked_results = sorted(zip(documents, scores),
                                key=lambda x: x[1], reverse=True)
        return ranked_results

    def search(self, query, document_corpus, final_k=10):
        """Complete two-stage search pipeline"""
        # Stage 1: Get candidates using embeddings
        candidates = self.similarity_search(query, document_corpus, top_k=50)

        # Stage 2: Rerank candidates
        ranked_results = self.rerank(query, candidates)

        # Return top final_k results
        return ranked_results[:final_k]

# Example usage with different model combinations
# Fast & cost-effective combination
fast_retriever = TwoStageRetrieval(
    embedding_model="Qwen/Qwen3-Embedding-0.6B",
    reranker_model="Qwen/Qwen3-Reranker-0.6B"
)
# Use: fast_retriever.search(query, document_corpus)

# Balanced performance combination
balanced_retriever = TwoStageRetrieval(
    embedding_model="Qwen/Qwen3-Embedding-4B",
    reranker_model="Qwen/Qwen3-Reranker-4B"
)
# Use: balanced_retriever.search(query, document_corpus)

# Maximum accuracy combination
precision_retriever = TwoStageRetrieval(
    embedding_model="Qwen/Qwen3-Embedding-8B",
    reranker_model="Qwen/Qwen3-Reranker-8B"
)
# Use: precision_retriever.search(query, document_corpus)
copy

Practical Guidance
Choosing the right reranker model size - Cost-performance trade-offs

Selecting the appropriate reranker model requires balancing accuracy, latency, and cost considerations:
Model	Best For	Performance	Cost	Use Cases
Qwen3-Reranker-0.6B	High-volume applications, real-time requirements	Good accuracy with 2-3x faster inference	Most economical option	Customer support, content moderation, real-time recommendations
Qwen3-Reranker-4B	Production systems requiring balanced performance	Strong accuracy with reasonable latency	Moderate pricing, good value proposition	Enterprise search, RAG systems, e-commerce
Qwen3-Reranker-8B	Applications where accuracy is paramount	Highest accuracy, slower inference	Premium pricing for premium performance	Legal research, medical information retrieval, high-stakes decision support

Decision Matrix:
Priority	Recommended Model	Reasoning
Speed & Cost	0.6B	Minimize latency and operational costs
Balanced Performance	4B	Optimal accuracy-to-cost ratio
Maximum Accuracy	8B	Best possible relevance scoring
High Volume (>1000 QPS)	0.6B	Cost-effective at scale
Critical Applications	8B	Accuracy justifies additional cost
Instruction prompting for domain-specific tasks

Qwen3 rerankers support instruction prompting to improve performance for specific domains:

Technical Documentation:

instruction = "Given a technical question, prioritize documentation that provides working code examples and step-by-step implementation guidance."
copy

Customer Support:

instruction = "For customer inquiries, rank solutions by their directness and ease of implementation for non-technical users."
copy

Academic Research:

instruction = "Prioritize peer-reviewed sources and recent publications that directly address the research question with empirical evidence."
copy

E-commerce:

instruction = "Rank products based on customer purchase intent, considering price, reviews, and feature match with the search query."
copy

Legal Research:

instruction = "For legal queries, prioritize binding precedents and statutory authority over secondary sources, with preference for recent decisions."
copy

The instruction prompting feature typically improves relevance scores, with larger improvements seen in specialized domains where context and expertise matter most.
Getting Started

Ready to implement rerankers in your search system? Start with DeepInfra's Qwen3-Reranker-4B for the best balance of performance and cost, then optimize based on your specific requirements. The combination of embeddings for speed and rerankers for precision represents the current state-of-the-art in search relevance.

Remember: the best search system is one that consistently delivers the right information to your users. Rerankers excel at turning good search results into great user experiences.
Related articles
Juggernaut FLUX is live on DeepInfra!
Juggernaut FLUX is live on DeepInfra!
Juggernaut FLUX is live on DeepInfra! At DeepInfra, we care about one thing above all: making cutting-edge AI models accessible. Today, we're excited to release the most downloaded model to our platform. Whether you're a visual artist, developer, or building an app that relies on high-fidelity ...
A Milestone on Our Journey Building Deep Infra and Scaling Open Source AI Infrastructure
A Milestone on Our Journey Building Deep Infra and Scaling Open Source AI Infrastructure
Today we're excited to share that Deep Infra has raised $18 million in Series A funding, led by Felicis and our earliest believer and advisor Georges Harik.
Enhancing Open-Source LLMs with Function Calling Feature
Enhancing Open-Source LLMs with Function Calling Feature
We're excited to announce that the Function Calling feature is now available on DeepInfra. We're offering Mistral-7B and Mixtral-8x7B models with this feature. Other models will be available soon. LLM models are powerful tools for various tasks. However, they're limited in their ability to per...
Footer Logo
SOC 2 CertifiedISO 27001 Certified

Have questions or need a custom solution?

Company
Pricing
Docs
Compare
DeepStart
About
Careers
Contact us
Trust Center
DeepGPT

Latest Models
zai-org/GLM-4.6
moonshotai/Kimi-K2-Instruct-0905
anthropic/claude-3-7-sonnet-latest
deepseek-ai/DeepSeek-V3.1
deepseek-ai/DeepSeek-V3.2-Exp

Featured Models
google/gemini-2.5-flash
Qwen/Qwen3-235B-A22B-Instruct-2507
Qwen/Qwen3-14B
hexgrad/Kokoro-82M
PaddlePaddle/PaddleOCR-VL-0.9B
Built With Love in Palo Alto

© 2025 Deep Infra. All rights reserved.
Privacy Policy
Terms of Service

