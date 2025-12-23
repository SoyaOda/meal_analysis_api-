"""
Core modules for Cloud Run optimization and API resilience
"""
from .startup_optimizer import startup_optimizer, connection_pool
from .http_client import get_async_client, close_async_client, health_check_client
from .retry import (
    llm_retry,
    embedding_retry,
    reranker_retry,
    default_retry,
    is_retryable_exception,
    RetryConfig,
    RETRY_CONFIGS,
)
from .embedding_cache import (
    EmbeddingCache,
    get_embedding_cache,
)
from .vlm_cache import (
    VLMCache,
    get_vlm_cache,
)

__all__ = [
    # Startup optimization
    "startup_optimizer",
    "connection_pool",
    # HTTP client
    "get_async_client",
    "close_async_client",
    "health_check_client",
    # Retry decorators
    "llm_retry",
    "embedding_retry",
    "reranker_retry",
    "default_retry",
    "is_retryable_exception",
    "RetryConfig",
    "RETRY_CONFIGS",
    # Embedding cache
    "EmbeddingCache",
    "get_embedding_cache",
    # VLM cache
    "VLMCache",
    "get_vlm_cache",
]
