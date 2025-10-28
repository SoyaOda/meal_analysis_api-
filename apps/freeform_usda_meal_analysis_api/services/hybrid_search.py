#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hybrid Search Engine (BM25 + Vector Search with RRF)

BM25キーワードサーチとVector意味検索を組み合わせた
ハイブリッドサーチエンジン（2025年ベストプラクティス準拠）
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import bm25s
import Stemmer

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """
    ハイブリッドサーチエンジン

    BM25（キーワードマッチング）とVector（セマンティック）を
    RRF（Reciprocal Rank Fusion）で融合
    """

    def __init__(
        self,
        index_dir: str,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6,
        rrf_k: int = 60
    ):
        """
        Args:
            index_dir: インデックスディレクトリ
            bm25_weight: BM25スコアの重み（デフォルト: 0.4）
            vector_weight: Vectorスコアの重み（デフォルト: 0.6）
            rrf_k: RRFのkパラメータ（デフォルト: 60）
        """
        self.index_dir = Path(index_dir)
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.rrf_k = rrf_k

        logger.info(f"Initializing Hybrid Search Engine...")
        logger.info(f"  BM25 weight: {bm25_weight}")
        logger.info(f"  Vector weight: {vector_weight}")
        logger.info(f"  RRF k: {rrf_k}")

        # BM25インデックスをロード
        self._load_bm25_index()

        # ステマーの初期化
        self.stemmer = Stemmer.Stemmer("english")

        logger.info(f"✅ Hybrid Search Engine initialized")

    def _load_bm25_index(self):
        """BM25インデックスをロード"""
        bm25_path = self.index_dir / "usda_bm25_index"

        if not bm25_path.exists():
            raise FileNotFoundError(f"BM25 index not found: {bm25_path}")

        self.bm25_model = bm25s.BM25.load(str(bm25_path), mmap=True)
        logger.info(f"✅ BM25 index loaded: {bm25_path}")

    def search_bm25(
        self,
        query: str,
        top_k: int = 100
    ) -> List[Tuple[int, float]]:
        """
        BM25検索を実行

        Args:
            query: 検索クエリ
            top_k: 取得する結果数

        Returns:
            [(doc_index, score), ...]
        """
        # クエリのトークナイズ
        query_tokens = bm25s.tokenize(
            [query],
            stopwords="en",
            stemmer=self.stemmer
        )

        # BM25検索
        results, scores = self.bm25_model.retrieve(
            query_tokens,
            k=top_k
        )

        # 結果を整形 (doc_index, score)
        doc_indices = results[0].tolist()
        doc_scores = scores[0].tolist()

        return list(zip(doc_indices, doc_scores))

    async def search_vector(
        self,
        query: str,
        faiss_index,
        embedding_service,
        top_k: int = 100
    ) -> List[Tuple[int, float]]:
        """
        Vectorセマンティック検索を実行

        Args:
            query: 検索クエリ
            faiss_index: FAISSインデックス
            embedding_service: 埋め込みサービス
            top_k: 取得する結果数

        Returns:
            [(doc_index, score), ...]
        """
        # Embedding生成
        embeddings = await embedding_service.generate_embeddings([query])
        query_vector = np.array(embeddings[0]).astype('float32').reshape(1, -1)

        # FAISS検索
        distances, indices = faiss_index.search(query_vector, top_k)

        # 結果を整形 (doc_index, score)
        doc_indices = indices[0].tolist()
        doc_scores = distances[0].tolist()

        return list(zip(doc_indices, doc_scores))

    def apply_rrf(
        self,
        bm25_results: List[Tuple[int, float]],
        vector_results: List[Tuple[int, float]]
    ) -> Dict[int, float]:
        """
        Reciprocal Rank Fusion（RRF）を適用

        Args:
            bm25_results: BM25検索結果 [(doc_idx, score), ...]
            vector_results: Vector検索結果 [(doc_idx, score), ...]

        Returns:
            {doc_idx: rrf_score, ...}
        """
        rrf_scores = {}

        # BM25結果のRRFスコア計算
        for rank, (doc_idx, _) in enumerate(bm25_results):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0) + 1 / (rank + self.rrf_k)

        # Vector結果のRRFスコア計算
        for rank, (doc_idx, _) in enumerate(vector_results):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0) + 1 / (rank + self.rrf_k)

        return rrf_scores

    def apply_weighted_fusion(
        self,
        bm25_results: List[Tuple[int, float]],
        vector_results: List[Tuple[int, float]],
        rrf_scores: Dict[int, float]
    ) -> List[Tuple[int, float, Dict[str, float]]]:
        """
        重み付け融合を適用

        Args:
            bm25_results: BM25検索結果
            vector_results: Vector検索結果
            rrf_scores: RRFスコア

        Returns:
            [(doc_idx, final_score, {'bm25': score, 'vector': score, 'rrf': score}), ...]
        """
        # スコアを正規化
        bm25_scores_dict = {idx: score for idx, score in bm25_results}
        vector_scores_dict = {idx: score for idx, score in vector_results}

        # BM25スコアの正規化（0-1の範囲に）
        bm25_max = max(bm25_scores_dict.values()) if bm25_scores_dict else 1.0
        bm25_normalized = {idx: score / bm25_max for idx, score in bm25_scores_dict.items()}

        # Vectorスコアの正規化（cosine similarityなので既に0-1の範囲）
        vector_normalized = vector_scores_dict

        # 全ドキュメントの収集
        all_doc_ids = set(rrf_scores.keys())

        # 重み付け最終スコア計算
        final_scores = []
        for doc_idx in all_doc_ids:
            bm25_score = bm25_normalized.get(doc_idx, 0)
            vector_score = vector_normalized.get(doc_idx, 0)
            rrf_score = rrf_scores[doc_idx]

            # 重み付けスコア
            final_score = (
                self.bm25_weight * bm25_score +
                self.vector_weight * vector_score +
                rrf_score  # RRFスコアも追加
            )

            final_scores.append((
                doc_idx,
                final_score,
                {
                    'bm25': bm25_score,
                    'vector': vector_score,
                    'rrf': rrf_score
                }
            ))

        # スコア順にソート
        final_scores.sort(key=lambda x: x[1], reverse=True)

        return final_scores

    async def search_hybrid(
        self,
        query: str,
        faiss_index,
        embedding_service,
        items: List[Dict],
        top_k: int = 40,
        stage1_top_k: int = 100
    ) -> List[Dict[str, Any]]:
        """
        ハイブリッドサーチを実行

        Args:
            query: 検索クエリ
            faiss_index: FAISSインデックス
            embedding_service: 埋め込みサービス
            items: アイテムメタデータ
            top_k: 返却する結果数
            stage1_top_k: Stage1で取得する候補数

        Returns:
            検索結果のリスト
        """
        logger.info(f"🔍 Hybrid search: '{query}'")

        try:
            # Stage 1: BM25 + Vector検索を並列実行
            bm25_task = asyncio.create_task(
                asyncio.to_thread(self.search_bm25, query, stage1_top_k)
            )
            vector_task = self.search_vector(query, faiss_index, embedding_service, stage1_top_k)

            # タイムアウト付きで実行（30秒）
            bm25_results, vector_results = await asyncio.wait_for(
                asyncio.gather(bm25_task, vector_task),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.error(f"❌ Hybrid search timeout after 30s")
            raise Exception("Hybrid search timeout")
        except Exception as e:
            logger.error(f"❌ Hybrid search error: {e}", exc_info=True)
            raise

        logger.info(f"  BM25 results: {len(bm25_results)}")
        logger.info(f"  Vector results: {len(vector_results)}")

        # Stage 2: RRF適用
        rrf_scores = self.apply_rrf(bm25_results, vector_results)
        logger.info(f"  RRF merged: {len(rrf_scores)} unique documents")

        # Stage 3: 重み付け融合
        final_scores = self.apply_weighted_fusion(bm25_results, vector_results, rrf_scores)

        # 結果を整形
        results = []
        for doc_idx, final_score, component_scores in final_scores[:top_k]:
            if doc_idx < len(items):
                item = items[doc_idx]
                results.append({
                    "fdc_id": item["fdc_id"],
                    "description": item["description"],
                    "main_name": item.get("main_name", ""),
                    "descriptors": item.get("descriptors", ""),
                    "source": item.get("source", "unknown"),
                    "hybrid_score": float(final_score),
                    "component_scores": {
                        "bm25": float(component_scores['bm25']),
                        "vector": float(component_scores['vector']),
                        "rrf": float(component_scores['rrf'])
                    }
                })

        logger.info(f"✅ Hybrid search completed: {len(results)} results")

        return results
