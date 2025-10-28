#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simplified USDA Food Search Service (Full Index Only)

FAISSのfullインデックスのみを使用した軽量版の検索サービス。
全てDeepInfra APIを使用（ローカルモデル不要）。
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import faiss
import numpy as np

logger = logging.getLogger(__name__)


class SimplifiedUSDASearcher:
    """
    USDA食材検索（Fullインデックスのみ使用）

    weight_main/fullの概念を削除し、fullインデックスのみで検索する簡素化版。
    """

    def __init__(
        self,
        index_dir: str,
        stage1_top_k: int = 40,
        device: str = "cpu"
    ):
        """
        Args:
            index_dir: FAISSインデックスディレクトリのパス
            stage1_top_k: Stage1で取得する候補数
            device: 計算デバイス（'cpu' or 'cuda'）
        """
        self.index_dir = Path(index_dir)
        self.stage1_top_k = stage1_top_k
        self.device = device

        if not self.index_dir.exists():
            raise FileNotFoundError(f"Index directory not found: {index_dir}")

        logger.info(f"Initializing Simplified USDA Searcher...")
        logger.info(f"Index directory: {index_dir}")
        logger.info(f"Mode: Full index only (no main index)")

        # FAISSインデックスとメタデータをロード
        self._load_full_index()
        self._load_metadata()
        self._load_embedding_model()
        self._load_reranker()

        logger.info(f"✅ Simplified USDA Searcher initialized successfully")

    def _load_full_index(self):
        """Fullインデックスのみをロード"""
        full_path = self.index_dir / "usda_index_full.faiss"

        if not full_path.exists():
            raise FileNotFoundError(f"Full index not found: {full_path}")

        self.index_full = faiss.read_index(str(full_path))
        logger.info(f"✅ Loaded full index: {self.index_full.ntotal} vectors")

    def _load_metadata(self):
        """メタデータをロード"""
        metadata_path = self.index_dir / "usda_metadata.json"

        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.items = json.load(f)

        logger.info(f"✅ Loaded metadata: {len(self.items)} items")

    def _load_embedding_model(self):
        """埋め込みモデルをロード（DeepInfra API使用）"""
        from shared.services.deepinfra_service import DeepInfraService
        self.embedding_service = DeepInfraService(model_id="Qwen/Qwen3-Embedding-8B")
        logger.info(f"✅ Embedding model initialized (DeepInfra API)")

    def _load_reranker(self):
        """リランカーをロード（DeepInfra API使用）"""
        from shared.services.deepinfra_service import DeepInfraService
        self.reranker_service = DeepInfraService(model_id="Qwen/Qwen3-Reranker-8B")
        logger.info(f"✅ Reranker model initialized (DeepInfra API)")

    async def search_async(
        self,
        query_main: str,
        query_descriptors: str = "",
        return_top_k: int = 1
    ) -> Dict[str, Any]:
        """
        検索を実行（Fullインデックスのみ使用、DeepInfra API）

        Args:
            query_main: 主クエリ（例: "chicken"）
            query_descriptors: 説明クエリ（例: "grilled"）
            return_top_k: 返す候補数

        Returns:
            {
                "best_match": {...},
                "all_candidates": [...]
            }
        """
        # フルクエリを構築
        if query_descriptors:
            full_query = f"{query_main}, {query_descriptors}"
        else:
            full_query = query_main

        logger.info(f"🔍 Searching: '{full_query}'")

        # Stage 1: FAISS検索（Fullインデックスのみ）
        # DeepInfra APIでembeddingを生成
        embeddings = await self.embedding_service.generate_embeddings([full_query])
        query_vector = np.array(embeddings[0]).astype('float32').reshape(1, -1)

        # FAISS検索
        distances, indices = self.index_full.search(query_vector, self.stage1_top_k)

        # 候補を取得
        candidates = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.items):
                item = self.items[idx]
                candidates.append({
                    "fdc_id": item["fdc_id"],
                    "description": item["description"],
                    "main_name": item.get("main_name", ""),
                    "descriptors": item.get("descriptors", ""),
                    "source": item.get("source", "unknown"),
                    "stage1_score": float(dist),
                    "index": int(idx)
                })

        logger.info(f"📊 Stage 1: Retrieved {len(candidates)} candidates")

        # Stage 2: Reranking
        if not candidates:
            return {"best_match": None, "all_candidates": []}

        # リランキング用のドキュメントリスト
        documents = [c["description"] for c in candidates]

        # リランキング実行（DeepInfra API）
        best_idx, reranked_scores = await self.reranker_service.rerank(
            query=full_query,
            documents=documents
        )

        # スコアを候補に追加
        for i, score in enumerate(reranked_scores):
            candidates[i]["rerank_score"] = float(score)

        # スコア順にソート
        candidates_sorted = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)

        logger.info(f"✅ Best match: {candidates_sorted[0]['description']} (score: {candidates_sorted[0]['rerank_score']:.4f})")

        return {
            "best_match": candidates_sorted[0],
            "all_candidates": candidates_sorted[:return_top_k]
        }

    def search(
        self,
        query_main: str,
        query_descriptors: str = "",
        return_top_k: int = 1
    ) -> Dict[str, Any]:
        """
        検索を実行（同期ラッパー）

        asyncioイベントループで非同期検索を実行
        """
        return asyncio.run(self.search_async(query_main, query_descriptors, return_top_k))
