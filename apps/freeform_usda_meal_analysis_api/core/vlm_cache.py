"""
VLM 画像キャッシュ

同一画像・同一プロンプト・同一モデルの VLM 分析結果をキャッシュ。
モデル比較や再試行時にAPI呼び出しをスキップし、コストを削減する。

キャッシュキー設計:
- image_hash (SHA256): 画像の完全一致
- prompt_hash: プロンプトの一致
- model_id: モデルの一致

これにより、異なるモデルで同じ画像を分析した場合は別エントリとして扱われる。

使用例:
    from ..core.vlm_cache import get_vlm_cache

    cache = get_vlm_cache()

    # キャッシュチェック
    cached = await cache.get(image_bytes, prompt, model_id)
    if cached:
        response, usage = cached
        return response, usage

    # API呼び出し
    response, usage = await vlm_api_call(...)

    # キャッシュ保存
    await cache.set(image_bytes, prompt, model_id, response, usage)
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class VLMCacheEntry:
    """VLMキャッシュエントリ"""

    response: Dict[str, Any]
    usage: Dict[str, Any]
    model_id: str
    created_at: datetime


class VLMCache:
    """
    VLM結果の完全一致キャッシュ

    キャッシュキーは「画像ハッシュ + プロンプトハッシュ + モデルID」の複合キー。
    これにより、同じ画像でも異なるモデルで分析した場合は別エントリとして扱われる。

    ユースケース:
    - モデル比較: GPT-4V vs Gemini vs Claude で同じ画像を分析 → 各モデルの結果を個別にキャッシュ
    - 再試行: 同じモデル・同じ画像 → キャッシュヒットで即座に結果を返す
    - プロンプト変更: Admin Panelでプロンプト変更後 → キャッシュミスで新しいAPIコール
    - 誤タップ防止: 重複リクエストをキャッシュヒットで処理
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_hours: int = 24,
        cache_dir: Optional[str] = None,
    ):
        """
        Args:
            max_size: 最大キャッシュエントリ数
            ttl_hours: エントリの有効期限（時間）
            cache_dir: 任意。指定（または env VLM_CACHE_DIR）時はディスクにも永続化し、
                プロセス再起動を跨いで結果を共有する（embedding A/B のように同一 VLM 出力を
                サーバ再起動越しに凍結したい用途で使う。本番では未設定＝従来のメモリのみ）。
        """
        self._cache: Dict[str, VLMCacheEntry] = {}
        self._max_size = max_size
        self._ttl = timedelta(hours=ttl_hours)
        self._lock = asyncio.Lock()

        # メトリクス
        self._hits = 0
        self._misses = 0

        # ディスク永続層（opt-in）
        self._cache_dir = cache_dir or os.getenv("VLM_CACHE_DIR")
        if self._cache_dir:
            Path(self._cache_dir).mkdir(parents=True, exist_ok=True)

        logger.info(
            f"VLMCache initialized: max_size={max_size}, ttl={ttl_hours}h, "
            f"disk={'on:' + self._cache_dir if self._cache_dir else 'off'}"
        )

    def _disk_path(self, key: str) -> Path:
        """キーをファイル名に変換（':' は安全な '_' に置換）。"""
        return Path(self._cache_dir) / (key.replace(":", "_") + ".json")

    def _load_from_disk(self, key: str) -> Optional[VLMCacheEntry]:
        """ディスクからエントリを読む（無ければ None）。読み取り失敗はミス扱い。"""
        path = self._disk_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return VLMCacheEntry(
                response=data["response"],
                usage=data["usage"],
                model_id=data["model_id"],
                created_at=datetime.fromisoformat(data["created_at"]),
            )
        except Exception as e:
            logger.warning(f"VLM disk cache read failed for {path.name}: {e}")
            return None

    def _save_to_disk(self, key: str, entry: VLMCacheEntry) -> None:
        """ディスクへエントリを書く（atomic: tmp→rename）。書き込み失敗は警告のみ。"""
        path = self._disk_path(key)
        try:
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps(
                    {
                        "response": entry.response,
                        "usage": entry.usage,
                        "model_id": entry.model_id,
                        "created_at": entry.created_at.isoformat(),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            tmp.replace(path)
        except Exception as e:
            logger.warning(f"VLM disk cache write failed for {path.name}: {e}")

    @staticmethod
    def _normalize_cache_context(cache_context: Optional[Dict[str, Any]]) -> str:
        if not cache_context:
            return "noctx"
        normalized: Dict[str, Any] = {}
        for key in sorted(cache_context.keys()):
            value = cache_context[key]
            if isinstance(value, (str, int, float, bool)) or value is None:
                normalized[key] = value
            else:
                normalized[key] = str(value)
        encoded = json.dumps(
            normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]

    def _compute_cache_key(
        self,
        image_bytes: bytes,
        prompt: str,
        model_id: str,
        cache_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        画像 + プロンプト + モデルIDから一意なキャッシュキーを生成

        Args:
            image_bytes: 画像データ
            prompt: VLMプロンプト
            model_id: VLMモデルID (例: "openrouter:openai/gpt-4-vision", "deepinfra:gemma-3-27b")

        Returns:
            キャッシュキー文字列
        """
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        model_hash = hashlib.sha256(model_id.encode()).hexdigest()[:8]
        context_hash = self._normalize_cache_context(cache_context)
        return f"{image_hash}:{prompt_hash}:{model_hash}:{context_hash}"

    async def get(
        self,
        image_bytes: bytes,
        prompt: str,
        model_id: str,
        cache_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        キャッシュから結果を取得

        Args:
            image_bytes: 画像データ
            prompt: VLMプロンプト
            model_id: VLMモデルID

        Returns:
            キャッシュヒット時は (response, usage) タプル、ミス時は None
        """
        key = self._compute_cache_key(image_bytes, prompt, model_id, cache_context)

        async with self._lock:
            entry = self._cache.get(key)

            # メモリミス時はディスク永続層を確認（embedding A/B の再起動越し共有用）
            if entry is None and self._cache_dir:
                entry = self._load_from_disk(key)
                if entry is not None:
                    self._cache[key] = entry

            if entry is None:
                self._misses += 1
                logger.debug(f"VLM Cache MISS: {key[:32]}...")
                return None

            # TTLチェック
            if datetime.now() - entry.created_at > self._ttl:
                del self._cache[key]
                if self._cache_dir:
                    self._disk_path(key).unlink(missing_ok=True)
                self._misses += 1
                logger.debug(f"VLM Cache EXPIRED: {key[:32]}...")
                return None

            self._hits += 1
            logger.info(
                f"📦 VLM Cache HIT: model={model_id} (hits={self._hits}, misses={self._misses})"
            )
            return entry.response, entry.usage

    async def set(
        self,
        image_bytes: bytes,
        prompt: str,
        model_id: str,
        response: Dict[str, Any],
        usage: Dict[str, Any],
        cache_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        キャッシュに結果を保存

        Args:
            image_bytes: 画像データ
            prompt: VLMプロンプト
            model_id: VLMモデルID
            response: VLMの応答（パース済みJSON）
            usage: トークン使用量情報
        """
        key = self._compute_cache_key(image_bytes, prompt, model_id, cache_context)

        async with self._lock:
            # LRU: 最大サイズ超過時は古いエントリを削除
            if len(self._cache) >= self._max_size:
                self._evict_old_entries()

            entry = VLMCacheEntry(
                response=response,
                usage=usage,
                model_id=model_id,
                created_at=datetime.now(),
            )
            self._cache[key] = entry
            if self._cache_dir:
                self._save_to_disk(key, entry)
            logger.info(f"📦 VLM Cache SET: model={model_id} (size={len(self._cache)})")

    def _evict_old_entries(self) -> None:
        """古いエントリを削除（LRU方式）"""
        # 削除数 = 最大サイズの10%
        evict_count = max(1, self._max_size // 10)

        # 作成日時でソートして古い順に削除
        sorted_keys = sorted(
            self._cache.keys(), key=lambda k: self._cache[k].created_at
        )

        for key in sorted_keys[:evict_count]:
            del self._cache[key]

        logger.debug(f"Evicted {evict_count} old VLM cache entries")

    def get_stats(self) -> Dict[str, Any]:
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
        logger.info("VLMCache cleared")


# グローバルインスタンス
_vlm_cache: Optional[VLMCache] = None


def get_vlm_cache(max_size: int = 1000, ttl_hours: int = 24) -> VLMCache:
    """
    グローバルな VLM キャッシュを取得

    Args:
        max_size: 最大キャッシュエントリ数（初回のみ有効）
        ttl_hours: エントリの有効期限（初回のみ有効）

    Returns:
        VLMCache インスタンス
    """
    global _vlm_cache

    if _vlm_cache is None:
        _vlm_cache = VLMCache(max_size=max_size, ttl_hours=ttl_hours)

    return _vlm_cache
