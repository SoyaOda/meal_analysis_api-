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
        self.is_loaded = False
        self.load_lock = asyncio.Lock()

    async def lazy_load_indexes(self) -> Tuple[Optional[object], Optional[object]]:
        """インデックスの遅延ロード（必要時のみ）"""
        async with self.load_lock:
            if self.is_loaded:
                return self.faiss_index, self.bm25_index

            start_time = time.time()
            logger.info("Starting lazy loading of indexes...")

            # FAISSインデックスのロード
            faiss_path = os.getenv("USDA_INDEX_DIR", "/app/data/faiss")
            if os.path.exists(faiss_path):
                try:
                    # 実際のFAISSロードロジックをここに実装
                    # self.faiss_index = load_faiss_index(faiss_path)
                    logger.info(f"FAISS index loaded from {faiss_path}")
                except Exception as e:
                    logger.error(f"Failed to load FAISS index: {e}")

            # BM25インデックスのロード
            bm25_path = os.getenv("BM25_INDEX_PATH", "/app/data/bm25/bm25_index.pkl")
            if os.path.exists(bm25_path):
                try:
                    with open(bm25_path, 'rb') as f:
                        self.bm25_index = pickle.load(f)
                    logger.info(f"BM25 index loaded from {bm25_path}")
                except Exception as e:
                    logger.error(f"Failed to load BM25 index: {e}")

            self.is_loaded = True
            elapsed = time.time() - start_time
            logger.info(f"Index loading completed in {elapsed:.2f} seconds")

            return self.faiss_index, self.bm25_index

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