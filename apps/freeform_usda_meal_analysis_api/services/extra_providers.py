# -*- coding: utf-8 -*-
"""Cross-provider embedding/reranker clients (Voyage / Google / Cohere / OpenAI).

F-PROV: provider 横断で「最良モデル」を A/B するための薄いクライアント層。
モデル id を `"<provider>:<model>"` 形式で受け取り（例 `"cohere:rerank-v3.5"`,
`"google:gemini-embedding-001"`）、provider 別の API・query/document 規約・input_type を
内包する。`"deepinfra:"` 接頭辞または接頭辞なしは既存の DeepInfra 経路に委譲する
（このモジュールでは扱わない）。新規 Python 依存は追加せず httpx で直叩きする。

各 provider のキーは env（`VOYAGE_API_KEY`/`GEMINI_API_KEY`(or `GOOGLE_API_KEY`)/
`COHERE_API_KEY`/`OPENAI_API_KEY`）から読む。ハードコード禁止。
"""

import os
import time
import logging
from typing import List, Tuple

import httpx

logger = logging.getLogger(__name__)

# このモジュールが扱う非 DeepInfra provider
EXTERNAL_PROVIDERS = ("voyage", "google", "cohere", "openai")

_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)


def parse_provider(model_id: str) -> Tuple[str, str]:
    """`"provider:model"` を (provider, bare_model) に分解。接頭辞が無ければ provider=''。"""
    if ":" in model_id:
        prefix, bare = model_id.split(":", 1)
        if prefix.lower() in EXTERNAL_PROVIDERS or prefix.lower() == "deepinfra":
            return prefix.lower(), bare
    return "", model_id


def is_external(model_id: str) -> bool:
    return parse_provider(model_id)[0] in EXTERNAL_PROVIDERS


def _require_key(*names: str) -> str:
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    raise ValueError(f"missing API key env (any of: {', '.join(names)})")


# ---------------- Embeddings ----------------


def embed_texts(model_id: str, texts: List[str], is_query: bool) -> List[List[float]]:
    """provider 別に texts を埋め込む。is_query で query/document 規約を切り替える。"""
    provider, model = parse_provider(model_id)
    if provider == "openai":
        return _openai_embed(model, texts)
    if provider == "cohere":
        return _cohere_embed(model, texts, is_query)
    if provider == "google":
        return _google_embed(model, texts, is_query)
    if provider == "voyage":
        return _voyage_embed(model, texts, is_query)
    raise ValueError(f"embed_texts: unsupported provider in '{model_id}'")


def _post(url: str, payload: dict, headers: dict, timeout: float = 60.0) -> dict:
    """POST with retry+backoff on 429 / 5xx (free-tier RPM limits, esp. Google)."""
    import time

    max_attempts = 8
    with httpx.Client(timeout=_TIMEOUT) as client:
        for attempt in range(max_attempts):
            r = client.post(
                url,
                json=payload,
                headers={**headers, "Content-Type": "application/json"},
            )
            if (
                r.status_code in (429, 500, 502, 503, 504)
                and attempt < max_attempts - 1
            ):
                retry_after = r.headers.get("Retry-After")
                wait = (
                    float(retry_after)
                    if retry_after and retry_after.isdigit()
                    else min(2**attempt, 30)
                )
                logger.warning(
                    f"{r.status_code} from {url.split('/')[-1]}; retry {attempt + 1}/{max_attempts} in {wait}s"
                )
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
    raise RuntimeError(f"_post exhausted retries for {url}")


def _openai_embed(model: str, texts: List[str]) -> List[List[float]]:
    key = _require_key("OPENAI_API_KEY")
    out: List[List[float]] = []
    for i in range(0, len(texts), 256):
        chunk = texts[i : i + 256]
        r = _post(
            "https://api.openai.com/v1/embeddings",
            {"input": chunk, "model": model},
            {"Authorization": f"Bearer {key}"},
        )
        out.extend(d["embedding"] for d in r["data"])
    return out


def _cohere_embed(model: str, texts: List[str], is_query: bool) -> List[List[float]]:
    key = _require_key("COHERE_API_KEY")
    input_type = "search_query" if is_query else "search_document"
    out: List[List[float]] = []
    for i in range(0, len(texts), 96):
        chunk = texts[i : i + 96]
        r = _post(
            "https://api.cohere.com/v2/embed",
            {
                "model": model,
                "texts": chunk,
                "input_type": input_type,
                "embedding_types": ["float"],
            },
            {"Authorization": f"Bearer {key}"},
        )
        out.extend(r["embeddings"]["float"])
    return out


def _google_embed(model: str, texts: List[str], is_query: bool) -> List[List[float]]:
    key = _require_key("GEMINI_API_KEY", "GOOGLE_API_KEY")
    task_type = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
    model_path = model if model.startswith("models/") else f"models/{model}"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:batchEmbedContents"
    out: List[List[float]] = []
    for i in range(0, len(texts), 100):
        chunk = texts[i : i + 100]
        requests = [
            {
                "model": model_path,
                "content": {"parts": [{"text": t}]},
                "taskType": task_type,
            }
            for t in chunk
        ]
        r = _post(url, {"requests": requests}, {"x-goog-api-key": key})
        out.extend(e["values"] for e in r["embeddings"])
        # free-tier RPM を緩和するため batch 間を軽く throttle（429 retry の無駄打ち削減）
        if i + 100 < len(texts):
            time.sleep(1.0)
    return out


def _voyage_embed(model: str, texts: List[str], is_query: bool) -> List[List[float]]:
    key = _require_key("VOYAGE_API_KEY")
    input_type = "query" if is_query else "document"
    out: List[List[float]] = []
    for i in range(0, len(texts), 128):
        chunk = texts[i : i + 128]
        r = _post(
            "https://api.voyageai.com/v1/embeddings",
            {"input": chunk, "model": model, "input_type": input_type},
            {"Authorization": f"Bearer {key}"},
        )
        out.extend(d["embedding"] for d in sorted(r["data"], key=lambda x: x["index"]))
    return out


# ---------------- Rerankers ----------------


def rerank(model_id: str, query: str, documents: List[str]) -> List[float]:
    """provider 別に rerank し、documents の元順に揃えた score リストを返す。"""
    provider, model = parse_provider(model_id)
    if not documents:
        return []
    if provider == "cohere":
        return _cohere_rerank(model, query, documents)
    if provider == "voyage":
        return _voyage_rerank(model, query, documents)
    raise ValueError(f"rerank: unsupported provider in '{model_id}'")


def _cohere_rerank(model: str, query: str, documents: List[str]) -> List[float]:
    key = _require_key("COHERE_API_KEY")
    r = _post(
        "https://api.cohere.com/v2/rerank",
        {
            "model": model,
            "query": query,
            "documents": documents,
            "top_n": len(documents),
        },
        {"Authorization": f"Bearer {key}"},
    )
    scores = [0.0] * len(documents)
    for item in r["results"]:
        scores[item["index"]] = float(item["relevance_score"])
    return scores


def _voyage_rerank(model: str, query: str, documents: List[str]) -> List[float]:
    key = _require_key("VOYAGE_API_KEY")
    r = _post(
        "https://api.voyageai.com/v1/rerank",
        {
            "query": query,
            "documents": documents,
            "model": model,
            "top_k": len(documents),
        },
        {"Authorization": f"Bearer {key}"},
    )
    rows = r.get("data") or r.get("results") or []
    scores = [0.0] * len(documents)
    for item in rows:
        scores[item["index"]] = float(
            item.get("relevance_score", item.get("score", 0.0))
        )
    return scores
