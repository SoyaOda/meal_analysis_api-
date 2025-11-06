"""
Startup optimization for Cloud Run deployment.
インデックスの遅延ロードとキャッシュ管理を実装
"""

import os
import time
import logging
from typing import Optional, Tuple
from functools import lru_cache
import asyncio
import pickle

logger = logging.getLogger(__name__)


class StartupOptimizer:
    """Cloud Runのコールドスタート最適化"""

    def __init__(self):
        self.faiss_index = None
        self.bm25_index = None
        self.metadata = None
        self.embedding_model = None
        self.reranker = None
        self.is_loaded = False
        self.is_loading = False
        self.load_lock = asyncio.Lock()
        self.searcher = None  # SimplifiedUSDASearcherインスタンスを保持

    async def get_indexes(self):
        """初回アクセス時にインデックスをロード"""
        # ロードされていない場合は待機
        if not self.is_loaded:
            if not self.is_loading:
                # まだロードが開始されていない場合は、このスレッドがロードを開始
                await self.lazy_load_indexes()
            else:
                # 他のスレッドがロード中の場合は、完了まで待機
                while self.is_loading:
                    await asyncio.sleep(0.1)
        return self.searcher

    async def lazy_load_indexes(self) -> None:
        """インデックスの遅延ロード（必要時のみ）"""
        async with self.load_lock:
            if self.is_loaded:
                return

            self.is_loading = True
            start_time = time.time()
            logger.info("Starting lazy loading of indexes...")

            try:
                # 設定を取得
                from ..config import get_settings
                settings = get_settings()
                
                index_dir = settings.USDA_INDEX_DIR
                stage1_top_k = settings.DEFAULT_STAGE1_TOP_K
                
                # SimplifiedUSDASearcherを非同期でインスタンス化
                # （実際のインデックスロードは別スレッドで実行）
                loop = asyncio.get_event_loop()
                self.searcher = await loop.run_in_executor(
                    None,
                    self._create_searcher,
                    index_dir,
                    stage1_top_k
                )
                
                self.is_loaded = True
                elapsed = time.time() - start_time
                logger.info(f"✅ Index loading completed in {elapsed:.2f} seconds")
                
            except Exception as e:
                logger.error(f"Failed to load indexes: {e}")
                self.is_loading = False
                raise
            finally:
                self.is_loading = False
    
    def _create_searcher(self, index_dir: str, stage1_top_k: int):
        """SimplifiedUSDASearcherのインスタンスを作成（ブロッキング処理）"""
        from ..services.usda_search import SimplifiedUSDASearcher
        return SimplifiedUSDASearcher(
            index_dir=index_dir,
            stage1_top_k=stage1_top_k,
            device="cpu"
        )

    def preload_critical_resources(self):
        """クリティカルなリソースの事前ロード"""
        # Cloud Run起動時に最小限必要なリソースのみロード
        logger.info("Preloading critical resources...")

        # 必要最小限のインポート
        import numpy as np
        import faiss

        # ヘルスチェック用の軽量データのみ準備
        self._health_check_ready = True

    @lru_cache(maxsize=128)
    def cached_search(self, query: str, top_k: int = 10):
        """検索結果のキャッシング"""
        # 頻繁に検索されるクエリをメモリにキャッシュ
        pass


class ConnectionPoolManager:
    """外部APIコネクションプール管理"""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.semaphore = asyncio.Semaphore(max_connections)

    async def acquire_connection(self):
        """コネクションの取得"""
        async with self.semaphore:
            yield

    def get_optimal_timeout(self, model_id: str) -> int:
        """モデル別の最適タイムアウト設定"""
        timeout_map = {
            "qwen/qwen3-vl-235b-a22b-thinking": 300,
            "openai/gpt-4o": 120,
            "openai/gpt-4o-mini": 60,
            "zhipuai/glm-4v-plus": 180,
            "default": 180
        }

        model_key = model_id.split(":")[-1] if ":" in model_id else model_id
        return timeout_map.get(model_key, timeout_map["default"])


# グローバルインスタンス（Cloud Runで再利用）
startup_optimizer = StartupOptimizer()
connection_pool = ConnectionPoolManager()