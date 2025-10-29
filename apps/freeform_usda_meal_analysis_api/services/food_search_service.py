#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
USDA Food Search Service

FAISS vector searchを使用してUSDA食材を検索する。
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class USDAFoodSearchService:
    """
    USDA食材検索サービス（Fullインデックスのみ使用）

    FAISSのfullインデックスのみを使用して、クエリに最も適した食材を検索する。
    """

    def __init__(
        self,
        index_dir: str,
        stage1_top_k: int = 40,
        device: str = "cpu",
        hybrid_engine=None
    ):
        """
        Args:
            index_dir: FAISSインデックスディレクトリのパス
            stage1_top_k: Stage1で取得する候補数
            device: 計算デバイス('cpu' or 'cuda')
            hybrid_engine: HybridSearchEngineインスタンス（オプション）
        """
        self.index_dir = Path(index_dir)

        if not self.index_dir.exists():
            raise FileNotFoundError(f"Index directory not found: {index_dir}")

        # SimplifiedUSDASearcherを初期化
        logger.info(f"Initializing USDA Food Search Service...")
        logger.info(f"Index directory: {index_dir}")
        logger.info(f"Mode: Full index only")

        # Import SimplifiedUSDASearcher
        from .usda_search import SimplifiedUSDASearcher

        self.searcher = SimplifiedUSDASearcher(
            index_dir=str(self.index_dir),
            stage1_top_k=stage1_top_k,
            device=device
        )

        # HybridSearchEngineを保持
        self.hybrid_engine = hybrid_engine
        if hybrid_engine:
            logger.info(f"✅ Hybrid search engine attached")

        logger.info(f"✅ USDA Food Search Service initialized successfully")

    def search(
        self,
        search_name: str,
        description: str = "",
        top_k: int = 1,
        mode: str = "accurate"
    ) -> Optional[Dict[str, Any]]:
        """
        単一クエリで検索を実行

        Args:
            search_name: 食材の主名称(例: "chicken")
            description: 食材の説明(例: "grilled")
            top_k: 上位何件返すか(デフォルト: 1)
            mode: 検索モード - "accurate" (FAISS + Rerank), "hybrid" (BM25 + FAISS), "fast" (FAISSのみ)

        Returns:
            マッチ結果: {
                "fdc_id": int,
                "matched_name": str,
                "matched_description": str,
                "matched_full_description": str,
                "rerank_score": float,
                "stage1_score": float
            }
            マッチしなかった場合はNone
        """
        logger.info(f"🔍 Searching for: '{search_name}' | '{description}' (mode={mode})")

        try:
            # Hybridモードの処理
            if mode == "hybrid" and self.hybrid_engine:
                import asyncio
                # クエリの結合
                query = f"{search_name} {description}".strip()
                
                # Hybridサーチを実行
                candidates = asyncio.run(
                    self.hybrid_engine.search_hybrid(
                        query=query,
                        faiss_index=self.searcher.index_full,
                        embedding_service=self.searcher.embedding_service,
                        items=self.searcher.items,
                        top_k=top_k,
                        stage1_top_k=100
                    )
                )
                
                if not candidates:
                    logger.warning(f"No matches found for: {search_name} | {description}")
                    return None
                
                # 最上位の結果を取得
                best_match = candidates[0]
                matched_result = {
                    "fdc_id": best_match['fdc_id'],
                    "matched_name": best_match['main_name'],
                    "matched_description": best_match['descriptors'],
                    "matched_full_description": best_match['description'],
                    "rerank_score": best_match['hybrid_score'],  # Hybrid scoreを使用
                    "stage1_score": best_match['component_scores']['vector'],  # Vector scoreをstage1として使用
                    "source": best_match.get('source', 'unknown'),
                    "search_mode": "hybrid"
                }
                
                logger.info(f"✅ Hybrid match found: {matched_result['matched_full_description']} (FDC: {matched_result['fdc_id']}, Score: {matched_result['rerank_score']:.4f})")
                return matched_result
            
            # Accurate/Fastモードの処理（既存のSimplifiedUSDASearcherを使用）
            result = self.searcher.search(
                query_main=search_name,
                query_descriptors=description,
                return_top_k=top_k
            )

            # 最上位の結果を取得
            best_match = result.get('best_match')

            if not best_match:
                logger.warning(f"No matches found for: {search_name} | {description}")
                return None

            # 結果を変換（既存フォーマットに合わせる）
            matched_result = {
                "fdc_id": best_match['fdc_id'],
                "matched_name": best_match['main_name'],
                "matched_description": best_match['descriptors'],
                "matched_full_description": best_match['description'],
                "rerank_score": best_match['rerank_score'],
                "stage1_score": best_match['stage1_score'],
                "source": best_match.get('source', 'unknown'),
                "search_mode": mode
            }

            logger.info(f"✅ Match found: {matched_result['matched_full_description']} (FDC: {matched_result['fdc_id']}, Score: {matched_result['rerank_score']:.4f})")

            return matched_result

        except Exception as e:
            logger.error(f"❌ Search error for '{search_name}': {e}")
            return None

    def search_batch(
        self,
        queries: List[Dict[str, str]]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        複数クエリで一括検索

        Args:
            queries: [{"search_name": str, "description": str}, ...]

        Returns:
            マッチ結果リスト（各クエリに対応）
        """
        results = []

        for query in queries:
            search_name = query.get("search_name", "")
            description = query.get("description", "")

            result = self.search(
                search_name=search_name,
                description=description
            )

            results.append(result)

        return results
