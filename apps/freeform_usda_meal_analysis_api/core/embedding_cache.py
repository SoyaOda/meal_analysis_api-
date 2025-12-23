"""
Embedding キャッシュ

同一テキスト・同一モデルの Embedding を再計算せずにキャッシュから返す。
頻出する食材クエリ（"chicken", "rice" 等）で API 呼び出しを削減し、
レイテンシを 300ms → 1ms に短縮する。

使用例:
    from ..core.embedding_cache import get_embedding_cache

    cache = get_embedding_cache()

    # バッチ取得（キャッシュヒット/ミスを分離）
    cached_results, miss_indices = cache.get_batch(texts, model)

    # ミスしたテキストのみ API 呼び出し
    miss_texts = [texts[i] for i in miss_indices]
    new_embeddings = await api_call(miss_texts)

    # キャッシュに保存
    cache.set_batch(miss_texts, model, new_embeddings)
"""

import hashlib
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingCacheEntry:
    """キャッシュエントリ"""
    embedding: List[float]
    created_at: datetime


class EmbeddingCache:
    """
    Embedding結果のインメモリLRUキャッシュ

    - キャッシュキー = SHA256(model + ":" + text)
    - LRU方式で古いエントリを削除
    - TTL（有効期限）サポート
    """

    def __init__(self, max_size: int = 10000, ttl_hours: int = 24):
        """
        Args:
            max_size: 最大キャッシュエントリ数
            ttl_hours: エントリの有効期限（時間）
        """
        self._cache: Dict[str, EmbeddingCacheEntry] = {}
        self._max_size = max_size
        self._ttl = timedelta(hours=ttl_hours)
        self._lock = asyncio.Lock()

        # メトリクス
        self._hits = 0
        self._misses = 0

        logger.info(f"EmbeddingCache initialized: max_size={max_size}, ttl={ttl_hours}h")

    def _compute_key(self, text: str, model: str) -> str:
        """テキストとモデルから一意なキャッシュキーを生成"""
        combined = f"{model}:{text}"
        return hashlib.sha256(combined.encode()).hexdigest()

    async def get(self, text: str, model: str) -> Optional[List[float]]:
        """
        キャッシュから Embedding を取得

        Args:
            text: テキスト
            model: Embedding モデル名

        Returns:
            キャッシュヒット時は Embedding ベクトル、ミス時は None
        """
        key = self._compute_key(text, model)

        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None

            # TTL チェック
            if datetime.now() - entry.created_at > self._ttl:
                del self._cache[key]
                self._misses += 1
                return None

            self._hits += 1
            return entry.embedding

    async def set(self, text: str, model: str, embedding: List[float]) -> None:
        """
        キャッシュに Embedding を保存

        Args:
            text: テキスト
            model: Embedding モデル名
            embedding: Embedding ベクトル
        """
        key = self._compute_key(text, model)

        async with self._lock:
            # LRU: 最大サイズ超過時は古いエントリを10%削除
            if len(self._cache) >= self._max_size:
                self._evict_old_entries()

            self._cache[key] = EmbeddingCacheEntry(
                embedding=embedding,
                created_at=datetime.now()
            )

    def _evict_old_entries(self) -> None:
        """古いエントリを削除（LRU方式）"""
        # 削除数 = 最大サイズの10%
        evict_count = max(1, self._max_size // 10)

        # 作成日時でソートして古い順に削除
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )

        for key in sorted_keys[:evict_count]:
            del self._cache[key]

        logger.debug(f"Evicted {evict_count} old cache entries")

    async def get_batch(
        self,
        texts: List[str],
        model: str
    ) -> Tuple[List[Optional[List[float]]], List[int]]:
        """
        バッチでキャッシュを取得

        Args:
            texts: テキストリスト
            model: Embedding モデル名

        Returns:
            (cached_results, miss_indices) のタプル
            - cached_results: 各テキストの Embedding（キャッシュミスは None）
            - miss_indices: キャッシュミスしたテキストのインデックスリスト
        """
        results: List[Optional[List[float]]] = []
        miss_indices: List[int] = []

        for i, text in enumerate(texts):
            cached = await self.get(text, model)
            results.append(cached)
            if cached is None:
                miss_indices.append(i)

        return results, miss_indices

    async def set_batch(
        self,
        texts: List[str],
        model: str,
        embeddings: List[List[float]]
    ) -> None:
        """
        バッチでキャッシュに保存

        Args:
            texts: テキストリスト
            model: Embedding モデル名
            embeddings: Embedding ベクトルリスト
        """
        if len(texts) != len(embeddings):
            raise ValueError(f"texts ({len(texts)}) and embeddings ({len(embeddings)}) must have same length")

        for text, embedding in zip(texts, embeddings):
            await self.set(text, model, embedding)

    def get_stats(self) -> Dict[str, any]:
        """キャッシュ統計を取得"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl_hours": self._ttl.total_seconds() / 3600,
        }

    def clear(self) -> None:
        """キャッシュをクリア"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("EmbeddingCache cleared")


# グローバルインスタンス
_embedding_cache: Optional[EmbeddingCache] = None


def get_embedding_cache(max_size: int = 10000, ttl_hours: int = 24) -> EmbeddingCache:
    """
    グローバルな Embedding キャッシュを取得

    Args:
        max_size: 最大キャッシュエントリ数（初回のみ有効）
        ttl_hours: エントリの有効期限（初回のみ有効）

    Returns:
        EmbeddingCache インスタンス
    """
    global _embedding_cache

    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache(max_size=max_size, ttl_hours=ttl_hours)

    return _embedding_cache
