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
from typing import Dict, Any, Optional
import faiss
import numpy as np

logger = logging.getLogger(__name__)


class SimplifiedUSDASearcher:
    """
    USDA食材検索（Fullインデックスのみ使用）

    weight_main/fullの概念を削除し、fullインデックスのみで検索する簡素化版。
    """

    def __init__(self, index_dir: str, stage1_top_k: int = None, device: str = "cpu"):
        """
        Args:
            index_dir: FAISSインデックスディレクトリのパス
            stage1_top_k: Stage1で取得する候補数（Noneの場合はConfigManagerから取得）
            device: 計算デバイス（'cpu' or 'cuda'）
        """
        # 設定を取得 - ConfigManagerから動的設定
        from ..admin.config_manager import get_config_manager

        config_manager = get_config_manager()
        config = config_manager.get_config()

        # stage1_top_kが指定されていない場合はConfigManagerから取得
        if stage1_top_k is None:
            stage1_top_k = config.search.stage1_top_k

        self.index_dir = Path(index_dir)
        self.stage1_top_k = stage1_top_k
        self.device = device

        if not self.index_dir.exists():
            raise FileNotFoundError(f"Index directory not found: {index_dir}")

        logger.info("Initializing Simplified USDA Searcher...")
        logger.info(f"Index directory: {index_dir}")
        logger.info("Mode: Full index only (no main index)")
        logger.info(f"Stage1 top_k: {stage1_top_k}")

        # FAISSインデックスとメタデータをロード
        self._load_full_index()
        self._load_metadata()
        self._load_embedding_model()
        self._load_reranker()

        logger.info("✅ Simplified USDA Searcher initialized successfully")

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

        with open(metadata_path, "r", encoding="utf-8") as f:
            self.items = json.load(f)

        logger.info(f"✅ Loaded metadata: {len(self.items)} items")

    def _load_embedding_model(self):
        """埋め込みモデルをロード（DeepInfra API使用）。

        E5: モデルは settings.DEFAULT_EMBEDDING_MODEL（env EMBEDDING_MODEL）で差し替え
        可能。query 側と FAISS index 構築は同一モデルでなければならない。
        """
        from .deepinfra_service import DeepInfraService
        from ..config import get_settings

        model_id = get_settings().DEFAULT_EMBEDDING_MODEL
        self.embedding_service = DeepInfraService(model_id=model_id)
        logger.info(f"✅ Embedding model initialized (DeepInfra API): {model_id}")

    def _load_reranker(self):
        """リランカーをロード（DeepInfra API使用）

        NOTE: このサービスはReranker APIクライアントとして初期化される。
        実際に使用されるモデルは、API呼び出し時にConfigManager（Admin Panel）から
        取得され、rerank_batch()のmodelパラメータとして渡される。
        """
        from .deepinfra_service import DeepInfraService

        # Rerankerサービスをモデル非依存で初期化
        # 実際のモデルはAPI呼び出し時に指定される
        self.reranker_service = DeepInfraService(model_id="reranker-client")
        logger.info("✅ Reranker service initialized (DeepInfra API)")

    async def search_async(
        self,
        query_main: str,
        query_descriptors: str = "",
        return_top_k: int = 1,
        reranker_instruction: Optional[str] = None,
        reranker_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        検索を実行（Fullインデックスのみ使用、DeepInfra API）

        Args:
            query_main: 主クエリ（例: "chicken"）
            query_descriptors: 説明クエリ（例: "grilled"）
            return_top_k: 返す候補数
            reranker_instruction: Reranker用のinstruction（Noneの場合はsettingsから取得）
            reranker_model: Rerankerモデル（例: "Qwen/Qwen3-Reranker-0.6B"）

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
        query_vector = np.array(embeddings[0]).astype("float32").reshape(1, -1)

        # FAISS検索
        distances, indices = self.index_full.search(query_vector, self.stage1_top_k)

        # 候補を取得
        candidates = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.items):
                item = self.items[idx]
                candidates.append(
                    {
                        "fdc_id": item["fdc_id"],
                        "description": item["description"],
                        "main_name": item.get("main_name", ""),
                        "descriptors": item.get("descriptors", ""),
                        "source": item.get("source", "unknown"),
                        "stage1_score": float(dist),
                        "index": int(idx),
                    }
                )

        logger.info(f"📊 Stage 1: Retrieved {len(candidates)} candidates")

        # Stage 2: Reranking
        if not candidates:
            return {"best_match": None, "all_candidates": []}

        # リランキング用のドキュメントリスト
        documents = [c["description"] for c in candidates]

        # ConfigManager（Firestore）を単一の設定ソースとして使用
        from ..admin.config_manager import get_config_manager

        config_manager = get_config_manager()
        config = config_manager.get_config()

        # Reranker instructionを取得（指定がない場合はConfigManagerから）
        if reranker_instruction is None:
            reranker_instruction = config.reranker.instruction

        # Rerankerモデルを取得（指定がない場合はConfigManagerから）
        if reranker_model is None:
            reranker_model = config.reranker.model

        logger.info(f"  Reranker model: {reranker_model} (from ConfigManager)")
        logger.info(
            f"  Reranker instruction: {reranker_instruction[:100]}..."
            if len(reranker_instruction) > 100
            else f"  Reranker instruction: {reranker_instruction}"
        )

        # リランキング実行（DeepInfra API）
        best_idx, reranked_scores = await self.reranker_service.rerank(
            query=full_query,
            documents=documents,
            model=reranker_model,
            instruction=reranker_instruction,
        )

        # スコアを候補に追加
        for i, score in enumerate(reranked_scores):
            candidates[i]["rerank_score"] = float(score)

        # スコア順にソート
        candidates_sorted = sorted(
            candidates, key=lambda x: x["rerank_score"], reverse=True
        )

        logger.info(
            f"✅ Best match: {candidates_sorted[0]['description']} (score: {candidates_sorted[0]['rerank_score']:.4f})"
        )

        return {
            "best_match": candidates_sorted[0],
            "all_candidates": candidates_sorted[:return_top_k],
        }

    def search(
        self, query: str, search_mode: str = "full_index_only", stage1_top_k: int = 1
    ) -> Dict[str, Any]:
        """
        検索を実行（同期ラッパー）

        asyncioイベントループで非同期検索を実行
        """
        # 互換性のためsearch_modeとstage1_top_kは無視（SimplifiedUSDASearcherは独自のパラメータを使用）
        return asyncio.run(self.search_async(query, "", stage1_top_k))
