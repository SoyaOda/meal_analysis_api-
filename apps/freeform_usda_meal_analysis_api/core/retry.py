"""
リトライロジック

tenacityを使用したExponential Backoff + Jitterによるリトライ戦略を提供。
VLM, Embedding, Reranker API呼び出しの耐障害性を向上させる。

使用例:
    from ..core.retry import llm_retry, embedding_retry

    @llm_retry
    async def call_vlm_api(...):
        ...

    @embedding_retry
    async def generate_embeddings(...):
        ...
"""

import logging
import httpx
from typing import Type, Tuple, Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
    RetryError,
)

# OpenAI SDK の例外をインポート
try:
    from openai import RateLimitError, APIConnectionError, APITimeoutError
except ImportError:
    # OpenAI SDKがない場合のフォールバック
    RateLimitError = Exception
    APIConnectionError = Exception
    APITimeoutError = Exception

logger = logging.getLogger(__name__)

# リトライ対象の例外タイプ
RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    ConnectionError,
    TimeoutError,
)


def _create_retry_decorator(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 60.0,
    jitter: float = 5.0,
    exceptions: Tuple[Type[Exception], ...] = RETRYABLE_EXCEPTIONS,
):
    """
    リトライデコレータを作成

    Args:
        max_attempts: 最大リトライ回数
        initial_wait: 初回待機時間（秒）
        max_wait: 最大待機時間（秒）
        jitter: ジッター（ランダム変動）の最大秒数
        exceptions: リトライ対象の例外タイプ

    Returns:
        tenacityリトライデコレータ
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(initial=initial_wait, max=max_wait, jitter=jitter),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.DEBUG),
        reraise=True,
    )


# VLM API用リトライデコレータ
# VLMは処理時間が長いため、待機時間を長めに設定
llm_retry = _create_retry_decorator(
    max_attempts=3,
    initial_wait=2.0,   # VLMは重いので初回待機を長く
    max_wait=60.0,
    jitter=5.0,
)

# Embedding API用リトライデコレータ
# 処理が比較的軽いため、待機時間を短めに設定
embedding_retry = _create_retry_decorator(
    max_attempts=3,
    initial_wait=0.5,
    max_wait=10.0,
    jitter=2.0,
)

# Reranker API用リトライデコレータ
# Embeddingと同様
reranker_retry = _create_retry_decorator(
    max_attempts=3,
    initial_wait=0.5,
    max_wait=10.0,
    jitter=2.0,
)

# 汎用リトライデコレータ（デフォルト設定）
default_retry = _create_retry_decorator()


def is_retryable_exception(exception: Exception) -> bool:
    """
    例外がリトライ可能かどうかを判定

    Args:
        exception: 判定する例外

    Returns:
        リトライ可能な場合True
    """
    return isinstance(exception, RETRYABLE_EXCEPTIONS)


class RetryConfig:
    """リトライ設定を管理するクラス"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_wait: float = 1.0,
        max_wait: float = 60.0,
        jitter: float = 5.0,
    ):
        self.max_attempts = max_attempts
        self.initial_wait = initial_wait
        self.max_wait = max_wait
        self.jitter = jitter

    def create_decorator(self):
        """この設定でリトライデコレータを作成"""
        return _create_retry_decorator(
            max_attempts=self.max_attempts,
            initial_wait=self.initial_wait,
            max_wait=self.max_wait,
            jitter=self.jitter,
        )


# プリセット設定
RETRY_CONFIGS = {
    "vlm": RetryConfig(max_attempts=3, initial_wait=2.0, max_wait=60.0, jitter=5.0),
    "embedding": RetryConfig(max_attempts=3, initial_wait=0.5, max_wait=10.0, jitter=2.0),
    "reranker": RetryConfig(max_attempts=3, initial_wait=0.5, max_wait=10.0, jitter=2.0),
    "default": RetryConfig(max_attempts=3, initial_wait=1.0, max_wait=60.0, jitter=5.0),
}
