#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hybrid Search Engine (BM25 + Vector Search with RRF)

BM25キーワードサーチとVector意味検索を組み合わせた
ハイブリッドサーチエンジン（2025年ベストプラクティス準拠）
"""

import logging
import asyncio
import json
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
        bm25_weight: float = None,
        vector_weight: float = None,
        rrf_k: int = None,
        rrf_weight: float = None
    ):
        """
        Args:
            index_dir: インデックスディレクトリ
            bm25_weight: BM25スコアの重み（Noneの場合はsettingsから取得）
            vector_weight: Vectorスコアの重み（Noneの場合はsettingsから取得）
            rrf_k: RRFのkパラメータ（Noneの場合はsettingsから取得）
            rrf_weight: RRF融合スコアの重み（Noneの場合はsettingsから取得）
        """
        # ConfigManager（Firestore）を単一の設定ソースとして使用
        from ..admin.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_config()

        # パラメータが指定されていない場合はConfigManagerから取得
        if bm25_weight is None:
            bm25_weight = config.search.bm25_weight
        if vector_weight is None:
            vector_weight = config.search.vector_weight
        if rrf_k is None:
            rrf_k = config.search.rrf_k
        if rrf_weight is None:
            rrf_weight = config.search.rrf_weight

        self.index_dir = Path(index_dir)
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.rrf_k = rrf_k
        self.rrf_weight = rrf_weight

        logger.info("Initializing Hybrid Search Engine...")
        logger.info(f"  BM25 weight: {bm25_weight}")
        logger.info(f"  Vector weight: {vector_weight}")
        logger.info(f"  RRF k: {rrf_k}")

        # BM25インデックスをロード
        self._load_bm25_index()

        # ステマーの初期化
        self.stemmer = Stemmer.Stemmer("english")

        logger.info("✅ Hybrid Search Engine initialized")

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
        top_k: int = None
    ) -> List[Tuple[int, float]]:
        """
        BM25検索を実行

        Args:
            query: 検索クエリ
            top_k: 取得する結果数（Noneの場合はsettingsから取得）

        Returns:
            [(doc_index, score), ...]
        """
        # ConfigManagerから設定を取得
        if top_k is None:
            from ..admin.config_manager import get_config_manager
            config = get_config_manager().get_config()
            top_k = config.search.stage1_top_k

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
        top_k: int = 100,
        embedding_instruction: str = None
    ) -> List[Tuple[int, float]]:
        """
        Vectorセマンティック検索を実行

        Args:
            query: 検索クエリ
            faiss_index: FAISSインデックス
            embedding_service: 埋め込みサービス
            top_k: 取得する結果数
            embedding_instruction: Qwen3-Embedding用のinstruction（設定から取得）

        Returns:
            [(doc_index, score), ...]
        """
        # Embedding Instruction取得 - ConfigManagerから
        if embedding_instruction is None:
            from ..admin.config_manager import get_config_manager
            config_manager = get_config_manager()
            config = config_manager.get_config()
            embedding_instruction = config.search.embedding_instruction

        # Embedding生成（Instruction形式を適用）
        embeddings = await embedding_service.generate_embeddings(
            [query],
            instruction=embedding_instruction
        )
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
        vector_results: List[Tuple[int, float]],
        k: int = None
    ) -> Dict[int, float]:
        """
        Reciprocal Rank Fusion（RRF）を適用

        Args:
            bm25_results: BM25検索結果 [(doc_idx, score), ...]
            vector_results: Vector検索結果 [(doc_idx, score), ...]
            k: RRFのkパラメータ（Noneの場合はインスタンス変数を使用）

        Returns:
            {doc_idx: rrf_score, ...}
        """
        # kパラメータが指定されていない場合はインスタンス変数を使用
        rrf_k = k if k is not None else self.rrf_k

        rrf_scores = {}

        # BM25結果のRRFスコア計算
        for rank, (doc_idx, _) in enumerate(bm25_results):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0) + 1 / (rank + rrf_k)

        # Vector結果のRRFスコア計算
        for rank, (doc_idx, _) in enumerate(vector_results):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0) + 1 / (rank + rrf_k)

        return rrf_scores

    def apply_weighted_fusion(
        self,
        bm25_results: List[Tuple[int, float]],
        vector_results: List[Tuple[int, float]],
        rrf_scores: Dict[int, float],
        bm25_weight: float = None,
        vector_weight: float = None,
        rrf_weight: float = None
    ) -> List[Tuple[int, float, Dict[str, float]]]:
        """
        重み付け融合を適用

        Args:
            bm25_results: BM25検索結果
            vector_results: Vector検索結果
            rrf_scores: RRFスコア
            bm25_weight: BM25スコアの重み（Noneの場合はインスタンス変数を使用）
            vector_weight: Vectorスコアの重み（Noneの場合はインスタンス変数を使用）
            rrf_weight: RRF融合スコアの重み（Noneの場合はインスタンス変数を使用）

        Returns:
            [(doc_idx, final_score, {'bm25': score, 'vector': score, 'rrf': score}), ...]
        """
        # 重みパラメータが指定されていない場合はインスタンス変数を使用
        bm25_w = bm25_weight if bm25_weight is not None else self.bm25_weight
        vector_w = vector_weight if vector_weight is not None else self.vector_weight
        rrf_w = rrf_weight if rrf_weight is not None else self.rrf_weight

        # スコアを正規化
        bm25_scores_dict = {idx: score for idx, score in bm25_results}
        vector_scores_dict = {idx: score for idx, score in vector_results}

        # BM25スコアの正規化（0-1の範囲に）
        # 注意: 短いクエリではBM25スコアが全て0になることがあるため、0除算を防止
        bm25_max = max(bm25_scores_dict.values()) if bm25_scores_dict else 1.0
        if bm25_max == 0:
            bm25_max = 1.0  # ゼロ除算防止
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
                bm25_w * bm25_score +
                vector_w * vector_score +
                rrf_w * rrf_score  # RRFスコアに重みを適用
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
        top_k: int = None,
        stage1_top_k: int = None,
        bm25_weight: float = None,
        vector_weight: float = None,
        rrf_k: int = None,
        rrf_weight: float = None
    ) -> List[Dict[str, Any]]:
        """
        ハイブリッドサーチを実行

        Args:
            query: 検索クエリ
            faiss_index: FAISSインデックス
            embedding_service: 埋め込みサービス
            items: アイテムメタデータ
            top_k: 返却する結果数（Noneの場合はsettingsから取得）
            stage1_top_k: Stage1で取得する候補数（Noneの場合はsettingsから取得）

        Returns:
            検索結果のリスト
        """
        # ConfigManager（Firestore）を単一の設定ソースとして使用
        if any(param is None for param in [top_k, stage1_top_k, bm25_weight, vector_weight, rrf_k, rrf_weight]):
            from ..admin.config_manager import get_config_manager
            config = get_config_manager().get_config()
            if top_k is None:
                top_k = config.search.stage1_top_k
            if stage1_top_k is None:
                stage1_top_k = config.search.stage1_top_k
            if bm25_weight is None:
                bm25_weight = config.search.bm25_weight
            if vector_weight is None:
                vector_weight = config.search.vector_weight
            if rrf_k is None:
                rrf_k = config.search.rrf_k
            if rrf_weight is None:
                rrf_weight = config.search.rrf_weight

        logger.info(f"🔍 Hybrid search: '{query}'")
        logger.info(f"  Parameters: bm25_weight={bm25_weight}, vector_weight={vector_weight}, rrf_k={rrf_k}, rrf_weight={rrf_weight}, stage1_top_k={stage1_top_k}")

        # 短いクエリ（3文字未満）の場合はBM25をスキップしてVectorのみで高速化
        short_query_threshold = 3
        skip_bm25 = len(query.strip()) < short_query_threshold

        try:
            if skip_bm25:
                logger.info(f"  Short query (<{short_query_threshold} chars): Using Vector-only search for faster response")
                # Vectorのみ実行
                vector_results = await self.search_vector(query, faiss_index, embedding_service, stage1_top_k)
                bm25_results = []  # BM25スキップ
            else:
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
            logger.error("❌ Hybrid search timeout after 30s")
            raise Exception("Hybrid search timeout")
        except Exception as e:
            logger.error(f"❌ Hybrid search error: {e}", exc_info=True)
            raise

        logger.info(f"  BM25 results: {len(bm25_results)}")
        logger.info(f"  Vector results: {len(vector_results)}")

        # デバッグ: BM25とVector検索のTop 5結果を表示
        logger.info(f"  BM25 Top 5: {[(items[idx]['description'], f'{score:.4f}') for idx, score in bm25_results[:5] if idx < len(items)]}")
        logger.info(f"  Vector Top 5: {[(items[idx]['description'], f'{score:.4f}') for idx, score in vector_results[:5] if idx < len(items)]}")

        # 「Soft drink, cola」が含まれているかチェック
        bm25_indices = [idx for idx, _ in bm25_results]
        vector_indices = [idx for idx, _ in vector_results]

        # "Soft drink, cola"を探す
        soft_drink_found_bm25 = False
        soft_drink_found_vector = False
        for idx, score in bm25_results:
            if idx < len(items) and items[idx]['description'] == 'Soft drink, cola':
                pos = bm25_indices.index(idx)
                logger.info(f"  'Soft drink, cola' in BM25: position {pos+1}, score={score:.4f}")
                soft_drink_found_bm25 = True
                break
        if not soft_drink_found_bm25:
            logger.info(f"  'Soft drink, cola' NOT in BM25 top {len(bm25_results)}")

        for idx, score in vector_results:
            if idx < len(items) and items[idx]['description'] == 'Soft drink, cola':
                pos = vector_indices.index(idx)
                logger.info(f"  'Soft drink, cola' in Vector: position {pos+1}, score={score:.4f}")
                soft_drink_found_vector = True
                break
        if not soft_drink_found_vector:
            logger.info(f"  'Soft drink, cola' NOT in Vector top {len(vector_results)}")

        # Stage 2: RRF適用
        rrf_scores = self.apply_rrf(bm25_results, vector_results, k=rrf_k)
        logger.info(f"  RRF merged: {len(rrf_scores)} unique documents")

        # Stage 3: 重み付け融合
        final_scores = self.apply_weighted_fusion(
            bm25_results, vector_results, rrf_scores,
            bm25_weight=bm25_weight, vector_weight=vector_weight, rrf_weight=rrf_weight
        )

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


    async def search_hybrid_with_reranker(
        self,
        query: str,
        faiss_index,
        embedding_service,
        reranker_service,
        items: List[Dict],
        top_k: int = None,
        stage1_top_k: int = None,
        bm25_weight: float = None,
        vector_weight: float = None,
        rrf_k: int = None,
        rrf_weight: float = None,
        reranker_model: str = None,
        reranker_instruction: str = None,
        include_debug_info: bool = False
    ) -> Dict[str, Any]:
        """
        Hybrid search + Reranker の統合版（5段階パイプライン）

        Args:
            query: 検索クエリ
            faiss_index: FAISSインデックス
            embedding_service: 埋め込みサービス
            reranker_service: リランカーサービス
            items: アイテムメタデータ
            top_k: 返却する結果数（Noneの場合settingsから取得）
            stage1_top_k: Stage1で取得する候補数（Noneの場合settingsから取得）
            reranker_instruction: Reranker用のinstruction（Noneの場合settingsから取得）
            include_debug_info: デバッグ情報を含めるか

        Returns:
            Dict with 'results' (and optionally 'debug_info')
        """
        # 設定を取得（embedding_instructionで常に必要なため条件外で取得）
        # ConfigManager（Firestore）を単一の設定ソースとして使用
        from ..admin.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_config()

        # 検索パラメータのデフォルト値をConfigManagerから取得
        if top_k is None:
            top_k = config.search.stage1_top_k
        if stage1_top_k is None:
            stage1_top_k = config.search.stage1_top_k
        if bm25_weight is None:
            bm25_weight = config.search.bm25_weight
        if vector_weight is None:
            vector_weight = config.search.vector_weight
        if rrf_k is None:
            rrf_k = config.search.rrf_k
        if rrf_weight is None:
            rrf_weight = config.search.rrf_weight
        if reranker_model is None:
            reranker_model = config.reranker.model
        if reranker_instruction is None:
            reranker_instruction = config.reranker.instruction

        logger.info(f"🔍 Hybrid search with reranker: '{query}'")
        logger.info(f"  Parameters: bm25_weight={bm25_weight}, vector_weight={vector_weight}, rrf_k={rrf_k}, rrf_weight={rrf_weight}, stage1_top_k={stage1_top_k}")

        # 短いクエリ（3文字未満）の場合はBM25をスキップしてVectorのみで高速化
        short_query_threshold = 3
        skip_bm25 = len(query.strip()) < short_query_threshold

        # ===== Stage 1: BM25 キーワード検索 =====
        start_time_bm25 = asyncio.get_event_loop().time()

        if skip_bm25:
            logger.info(f"  Short query (<{short_query_threshold} chars): Skipping BM25 search for faster response")
            bm25_indices = []
            bm25_scores = []
            bm25_time = 0.0
        else:
            # クエリのトークナイズ
            query_tokens = bm25s.tokenize(
                [query],
                stopwords="en",
                stemmer=self.stemmer
            )

            # BM25検索
            bm25_results_raw, bm25_scores_raw = self.bm25_model.retrieve(
                query_tokens,
                k=stage1_top_k
            )
            bm25_time = asyncio.get_event_loop().time() - start_time_bm25

            # BM25の結果をインデックスに変換（numpy配列をリストに）
            bm25_indices = bm25_results_raw[0].tolist()
            bm25_scores = bm25_scores_raw[0].tolist()

        # ===== Stage 2: FAISS Vector 検索 =====
        start_time_vector = asyncio.get_event_loop().time()
        # Embedding Instruction取得（Qwen3-Embedding-8B対応）- ConfigManagerから
        embedding_instruction = config.search.embedding_instruction
        # クエリのベクトル化（Instruction形式を適用）
        query_vectors = await embedding_service.generate_embeddings(
            [query],
            instruction=embedding_instruction
        )
        query_vector_np = np.array([query_vectors[0]], dtype='float32')

        # FAISS検索
        distances, indices = faiss_index.search(query_vector_np, stage1_top_k)
        vector_indices = indices[0].tolist()
        # FAISSの距離をスコアに変換（距離が小さいほど良い → スコアは大きいほど良い）
        vector_scores = (1.0 / (1.0 + distances[0])).tolist()
        vector_time = asyncio.get_event_loop().time() - start_time_vector

        logger.info(f"  BM25 results: {len(bm25_indices)}")
        logger.info(f"  Vector results: {len(vector_indices)}")

        # ===== Stage 3: RRF (Reciprocal Rank Fusion) =====
        start_time_rrf = asyncio.get_event_loop().time()

        # 各候補の rank を計算（0-indexed → 1-indexed）
        bm25_ranks = {idx: rank + 1 for rank, idx in enumerate(bm25_indices)}
        vector_ranks = {idx: rank + 1 for rank, idx in enumerate(vector_indices)}

        # RRF スコア計算
        rrf_scores = {}
        all_indices = set(bm25_indices) | set(vector_indices)

        for idx in all_indices:
            bm25_rank = bm25_ranks.get(idx, float('inf'))
            vector_rank = vector_ranks.get(idx, float('inf'))

            # RRF スコア: 1 / (k + rank)
            bm25_rrf = 1.0 / (rrf_k + bm25_rank) if bm25_rank != float('inf') else 0.0
            vector_rrf = 1.0 / (rrf_k + vector_rank) if vector_rank != float('inf') else 0.0

            rrf_scores[idx] = bm25_rrf + vector_rrf

        rrf_time = asyncio.get_event_loop().time() - start_time_rrf
        logger.info(f"  RRF merged: {len(rrf_scores)} unique documents")

        # ===== Stage 4: Weighted Fusion (BM25 + Vector) =====
        start_time_fusion = asyncio.get_event_loop().time()

        # BM25 と Vector のスコアを正規化
        bm25_score_dict = {idx: score for idx, score in zip(bm25_indices, bm25_scores)}
        vector_score_dict = {idx: score for idx, score in zip(vector_indices, vector_scores)}

        # 注意: 短いクエリではBM25スコアが全て0になることがあるため、0除算を防止
        max_bm25 = max(bm25_scores) if bm25_scores else 1.0
        if max_bm25 == 0:
            max_bm25 = 1.0  # ゼロ除算防止
        max_vector = max(vector_scores) if vector_scores else 1.0
        if max_vector == 0:
            max_vector = 1.0  # ゼロ除算防止

        # Weighted Fusion
        hybrid_scores = {}
        for idx in all_indices:
            bm25_normalized = bm25_score_dict.get(idx, 0) / max_bm25
            vector_normalized = vector_score_dict.get(idx, 0) / max_vector

            # RRF スコアと weighted スコアを組み合わせ
            rrf_score = rrf_scores[idx]
            weighted_score = (bm25_weight * bm25_normalized) + (vector_weight * vector_normalized)

            # 最終スコア = RRF(重み付き) + Weighted（両方の強みを活かす）
            hybrid_scores[idx] = (rrf_weight * rrf_score) + weighted_score

        # スコアでソート
        sorted_candidates = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        hybrid_candidates = [
            {
                "fdc_id": items[idx]["fdc_id"],
                "description": items[idx]["description"],
                "hybrid_score": score,
                "bm25_score": bm25_score_dict.get(idx, 0),
                "vector_score": vector_score_dict.get(idx, 0),
                "rrf_score": rrf_scores[idx]
            }
            for idx, score in sorted_candidates[:stage1_top_k]
        ]

        fusion_time = asyncio.get_event_loop().time() - start_time_fusion
        logger.info(f"  Hybrid fusion: {len(hybrid_candidates)} candidates for reranking")

        # ===== Stage 5: Reranker =====
        # リランキング用のドキュメントリスト
        documents = [c["description"] for c in hybrid_candidates]

        logger.info(f"  Reranker model: {reranker_model}")
        logger.info(f"  Reranker instruction: {reranker_instruction[:100]}..." if reranker_instruction and len(reranker_instruction) > 100 else f"  Reranker instruction: {reranker_instruction}")

        # リランキング実行（DeepInfra API）
        best_idx, reranked_scores = await reranker_service.rerank(
            query=query,
            documents=documents,
            model=reranker_model,
            instruction=reranker_instruction
        )

        # リランキング結果を反映
        for i, candidate in enumerate(hybrid_candidates):
            candidate["rerank_score"] = reranked_scores[i]
            candidate["original_rank"] = i + 1

        # Rerankerスコアでソート
        reranked_results = sorted(hybrid_candidates, key=lambda x: x["rerank_score"], reverse=True)

        logger.info(f"✅ Hybrid+Reranker search completed: {len(reranked_results)} results")
        if reranked_results:
            logger.info(f"  Best match: {reranked_results[0]['description']} (rerank_score: {reranked_results[0]['rerank_score']:.4f})")

        # 結果を返す
        final_results = reranked_results[:top_k]

        # ===== Cloud Logging用デバッグ出力（常に出力） =====
        # Cloud Run上ではJSON形式でログ出力するとCloud Loggingで構造化ログとして扱われる
        # Top 10を出力してデバッグ・分析に活用
        cloud_log_data = {
            "message": "HYBRID_SEARCH_DEBUG",
            "severity": "INFO",
            "query": query,
            "best_match": {
                "fdc_id": reranked_results[0]["fdc_id"] if reranked_results else None,
                "description": reranked_results[0]["description"] if reranked_results else None,
                "rerank_score": reranked_results[0]["rerank_score"] if reranked_results else None,
            },
            "bm25_top10": [
                {"rank": i + 1, "fdc_id": items[idx]["fdc_id"], "desc": items[idx]["description"][:50], "score": round(bm25_scores[i], 4) if i < len(bm25_scores) else 0}
                for i, idx in enumerate(bm25_indices[:10])
            ],
            "vector_top10": [
                {"rank": i + 1, "fdc_id": items[idx]["fdc_id"], "desc": items[idx]["description"][:50], "score": round(vector_scores[i], 4) if i < len(vector_scores) else 0}
                for i, idx in enumerate(vector_indices[:10])
            ],
            "hybrid_top10": [
                {"rank": i + 1, "fdc_id": c["fdc_id"], "desc": c["description"][:50], "score": round(c["hybrid_score"], 4)}
                for i, c in enumerate(hybrid_candidates[:10])
            ],
            "reranked_top10": [
                {"rank": i + 1, "fdc_id": r["fdc_id"], "desc": r["description"][:50], "score": round(r["rerank_score"], 4), "original_rank": r["original_rank"]}
                for i, r in enumerate(reranked_results[:10])
            ],
            "timing_ms": {
                "bm25": int(bm25_time * 1000),
                "vector": int(vector_time * 1000),
                "rrf": int(rrf_time * 1000),
                "fusion": int(fusion_time * 1000),
            },
            "params": {
                "bm25_weight": bm25_weight,
                "vector_weight": vector_weight,
                "rrf_k": rrf_k,
                "stage1_top_k": stage1_top_k,
            }
        }
        # Cloud Loggingで検索可能な構造化ログを出力
        print(json.dumps(cloud_log_data, ensure_ascii=False))

        # デバッグ情報を構築（レスポンスに含める場合）
        if include_debug_info:
            # BM25 Top 10
            bm25_top10 = [
                {
                    "fdc_id": items[idx]["fdc_id"],
                    "description": items[idx]["description"],
                    "bm25_score": bm25_scores[i] if i < len(bm25_scores) else 0,
                    "rank": i + 1
                }
                for i, idx in enumerate(bm25_indices[:10])
            ]

            # Vector Top 10
            vector_top10 = [
                {
                    "fdc_id": items[idx]["fdc_id"],
                    "description": items[idx]["description"],
                    "vector_score": vector_scores[i] if i < len(vector_scores) else 0,
                    "rank": i + 1
                }
                for i, idx in enumerate(vector_indices[:10])
            ]

            # Hybrid (pre-reranker) Top 10 - 明示的にコピーして循環参照を防止
            hybrid_top10 = [
                {
                    "fdc_id": c["fdc_id"],
                    "description": c["description"],
                    "hybrid_score": c["hybrid_score"],
                    "bm25_score": c.get("bm25_score", 0),
                    "vector_score": c.get("vector_score", 0),
                    "rank": i + 1
                }
                for i, c in enumerate(hybrid_candidates[:10])
            ]

            # Reranked Top 10
            reranked_top10 = [
                {
                    "fdc_id": r["fdc_id"],
                    "description": r["description"],
                    "rerank_score": r["rerank_score"],
                    "original_rank": r["original_rank"],
                    "final_rank": i + 1
                }
                for i, r in enumerate(reranked_results[:10])
            ]

            debug_info = {
                "query": query,
                "bm25_top10": bm25_top10,
                "vector_top10": vector_top10,
                "hybrid_top10": hybrid_top10,
                "reranked_top10": reranked_top10,
                "timing": {
                    "bm25_time_ms": int(bm25_time * 1000),
                    "vector_time_ms": int(vector_time * 1000),
                    "rrf_time_ms": int(rrf_time * 1000),
                    "fusion_time_ms": int(fusion_time * 1000),
                },
                "parameters": {
                    "bm25_weight": bm25_weight,
                    "vector_weight": vector_weight,
                    "rrf_k": rrf_k,
                    "stage1_top_k": stage1_top_k,
                }
            }

            return {
                "results": final_results,
                "debug_info": debug_info
            }

        return {
            "results": final_results,
            "debug_info": None
        }

    async def search_hybrid_with_reranker_precomputed(
        self,
        query: str,
        query_embedding: List[float],
        faiss_index,
        reranker_service,
        items: List[Dict],
        top_k: int = None,
        stage1_top_k: int = None,
        bm25_weight: float = None,
        vector_weight: float = None,
        rrf_k: int = None,
        rrf_weight: float = None,
        reranker_instruction: str = None,
        include_debug_info: bool = False
    ) -> Dict[str, Any]:
        """
        Hybrid search + Reranker（事前計算済みembeddingを使用）

        embedding生成をスキップして高速化。
        バッチ検索時に事前にembeddingを一括生成しておき、
        このメソッドに渡すことでAPI呼び出し回数を削減する。

        Args:
            query: 検索クエリ
            query_embedding: 事前計算済みのクエリembedding
            faiss_index: FAISSインデックス
            reranker_service: リランカーサービス
            items: アイテムメタデータ
            top_k: 返却する結果数
            stage1_top_k: Stage1で取得する候補数
            reranker_instruction: Reranker用のinstruction

        Returns:
            Dict with 'results' (and optionally 'debug_info')
        """
        # ConfigManager（Firestore）を単一の設定ソースとして使用
        from ..admin.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_config()

        # 検索パラメータのデフォルト値をConfigManagerから取得
        if top_k is None:
            top_k = config.search.stage1_top_k
        if stage1_top_k is None:
            stage1_top_k = config.search.stage1_top_k
        if bm25_weight is None:
            bm25_weight = config.search.bm25_weight
        if vector_weight is None:
            vector_weight = config.search.vector_weight
        if rrf_k is None:
            rrf_k = config.search.rrf_k
        if rrf_weight is None:
            rrf_weight = config.search.rrf_weight
        if reranker_instruction is None:
            reranker_instruction = config.reranker.instruction

        logger.debug(f"🔍 Hybrid search (precomputed embedding): '{query}'")

        # 短いクエリ（3文字未満）の場合はBM25をスキップ
        short_query_threshold = 3
        skip_bm25 = len(query.strip()) < short_query_threshold

        # ===== Stage 1: BM25 キーワード検索 =====
        start_time_bm25 = asyncio.get_event_loop().time()

        if skip_bm25:
            bm25_indices = []
            bm25_scores = []
            bm25_time = 0.0
        else:
            query_tokens = bm25s.tokenize(
                [query],
                stopwords="en",
                stemmer=self.stemmer
            )
            bm25_results_raw, bm25_scores_raw = self.bm25_model.retrieve(
                query_tokens,
                k=stage1_top_k
            )
            bm25_time = asyncio.get_event_loop().time() - start_time_bm25
            bm25_indices = bm25_results_raw[0].tolist()
            bm25_scores = bm25_scores_raw[0].tolist()

        # ===== Stage 2: FAISS Vector 検索（事前計算済みembedding使用） =====
        start_time_vector = asyncio.get_event_loop().time()
        query_vector_np = np.array([query_embedding], dtype='float32')
        distances, indices = faiss_index.search(query_vector_np, stage1_top_k)
        vector_indices = indices[0].tolist()
        vector_scores = (1.0 / (1.0 + distances[0])).tolist()
        vector_time = asyncio.get_event_loop().time() - start_time_vector

        # ===== Stage 3: RRF (Reciprocal Rank Fusion) =====
        start_time_rrf = asyncio.get_event_loop().time()
        bm25_ranks = {idx: rank + 1 for rank, idx in enumerate(bm25_indices)}
        vector_ranks = {idx: rank + 1 for rank, idx in enumerate(vector_indices)}
        rrf_scores = {}
        all_indices = set(bm25_indices) | set(vector_indices)

        for idx in all_indices:
            bm25_rank = bm25_ranks.get(idx, float('inf'))
            vector_rank = vector_ranks.get(idx, float('inf'))
            bm25_rrf = 1.0 / (rrf_k + bm25_rank) if bm25_rank != float('inf') else 0.0
            vector_rrf = 1.0 / (rrf_k + vector_rank) if vector_rank != float('inf') else 0.0
            rrf_scores[idx] = bm25_rrf + vector_rrf

        rrf_time = asyncio.get_event_loop().time() - start_time_rrf

        # ===== Stage 4: Weighted Fusion =====
        start_time_fusion = asyncio.get_event_loop().time()
        bm25_score_dict = {idx: score for idx, score in zip(bm25_indices, bm25_scores)}
        vector_score_dict = {idx: score for idx, score in zip(vector_indices, vector_scores)}

        max_bm25 = max(bm25_scores) if bm25_scores else 1.0
        if max_bm25 == 0:
            max_bm25 = 1.0
        max_vector = max(vector_scores) if vector_scores else 1.0
        if max_vector == 0:
            max_vector = 1.0

        hybrid_scores = {}
        for idx in all_indices:
            bm25_normalized = bm25_score_dict.get(idx, 0) / max_bm25
            vector_normalized = vector_score_dict.get(idx, 0) / max_vector
            rrf_score = rrf_scores[idx]
            weighted_score = (bm25_weight * bm25_normalized) + (vector_weight * vector_normalized)
            hybrid_scores[idx] = (rrf_weight * rrf_score) + weighted_score

        sorted_candidates = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        hybrid_candidates = [
            {
                "fdc_id": items[idx]["fdc_id"],
                "description": items[idx]["description"],
                "hybrid_score": score,
                "bm25_score": bm25_score_dict.get(idx, 0),
                "vector_score": vector_score_dict.get(idx, 0),
                "rrf_score": rrf_scores[idx]
            }
            for idx, score in sorted_candidates[:stage1_top_k]
        ]
        fusion_time = asyncio.get_event_loop().time() - start_time_fusion

        # ===== Stage 5: Reranker =====
        documents = [c["description"] for c in hybrid_candidates]
        best_idx, reranked_scores = await reranker_service.rerank(
            query=query,
            documents=documents,
            instruction=reranker_instruction
        )

        for i, candidate in enumerate(hybrid_candidates):
            candidate["rerank_score"] = reranked_scores[i]
            candidate["original_rank"] = i + 1

        reranked_results = sorted(hybrid_candidates, key=lambda x: x["rerank_score"], reverse=True)
        final_results = reranked_results[:top_k]

        # デバッグ情報
        if include_debug_info:
            debug_info = {
                "query": query,
                "timing": {
                    "bm25_time_ms": int(bm25_time * 1000),
                    "vector_time_ms": int(vector_time * 1000),
                    "rrf_time_ms": int(rrf_time * 1000),
                    "fusion_time_ms": int(fusion_time * 1000),
                },
                "parameters": {
                    "bm25_weight": bm25_weight,
                    "vector_weight": vector_weight,
                    "rrf_k": rrf_k,
                    "stage1_top_k": stage1_top_k,
                },
                "precomputed_embedding": True
            }
            return {"results": final_results, "debug_info": debug_info}

        return {"results": final_results, "debug_info": None}

    def get_hybrid_candidates_sync(
        self,
        query: str,
        query_embedding: List[float],
        faiss_index,
        items: List[Dict],
        stage1_top_k: int = None,
        bm25_weight: float = None,
        vector_weight: float = None,
        rrf_k: int = None,
        rrf_weight: float = None,
    ) -> List[Dict[str, Any]]:
        """
        BM25 + FAISS + RRF融合のみ実行（Rerankerなし、同期版）

        Rerankerを後から一括並列実行するために、
        候補リストのみを返す軽量メソッド。

        Returns:
            List of hybrid candidates (without reranker scores)
        """

        # ConfigManager（Firestore）を単一の設定ソースとして使用
        from ..admin.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_config()

        if stage1_top_k is None:
            stage1_top_k = config.search.stage1_top_k
        if bm25_weight is None:
            bm25_weight = config.search.bm25_weight
        if vector_weight is None:
            vector_weight = config.search.vector_weight
        if rrf_k is None:
            rrf_k = config.search.rrf_k
        if rrf_weight is None:
            rrf_weight = config.search.rrf_weight

        # 短いクエリ（3文字未満）の場合はBM25をスキップ
        short_query_threshold = 3
        skip_bm25 = len(query.strip()) < short_query_threshold

        # ===== Stage 1: BM25 キーワード検索 =====
        if skip_bm25:
            bm25_indices = []
            bm25_scores = []
        else:
            query_tokens = bm25s.tokenize(
                [query],
                stopwords="en",
                stemmer=self.stemmer
            )
            bm25_results_raw, bm25_scores_raw = self.bm25_model.retrieve(
                query_tokens,
                k=stage1_top_k
            )
            bm25_indices = bm25_results_raw[0].tolist()
            bm25_scores = bm25_scores_raw[0].tolist()

        # ===== Stage 2: FAISS Vector 検索 =====
        query_vector_np = np.array([query_embedding], dtype='float32')
        distances, indices = faiss_index.search(query_vector_np, stage1_top_k)
        vector_indices = indices[0].tolist()
        vector_scores = (1.0 / (1.0 + distances[0])).tolist()

        # ===== Stage 3: RRF (Reciprocal Rank Fusion) =====
        bm25_ranks = {idx: rank + 1 for rank, idx in enumerate(bm25_indices)}
        vector_ranks = {idx: rank + 1 for rank, idx in enumerate(vector_indices)}
        rrf_scores = {}
        all_indices = set(bm25_indices) | set(vector_indices)

        for idx in all_indices:
            bm25_rank = bm25_ranks.get(idx, float('inf'))
            vector_rank = vector_ranks.get(idx, float('inf'))
            bm25_rrf = 1.0 / (rrf_k + bm25_rank) if bm25_rank != float('inf') else 0.0
            vector_rrf = 1.0 / (rrf_k + vector_rank) if vector_rank != float('inf') else 0.0
            rrf_scores[idx] = bm25_rrf + vector_rrf

        # ===== Stage 4: Weighted Fusion =====
        bm25_score_dict = {idx: score for idx, score in zip(bm25_indices, bm25_scores)}
        vector_score_dict = {idx: score for idx, score in zip(vector_indices, vector_scores)}

        max_bm25 = max(bm25_scores) if bm25_scores else 1.0
        if max_bm25 == 0:
            max_bm25 = 1.0
        max_vector = max(vector_scores) if vector_scores else 1.0
        if max_vector == 0:
            max_vector = 1.0

        hybrid_scores = {}
        for idx in all_indices:
            bm25_normalized = bm25_score_dict.get(idx, 0) / max_bm25
            vector_normalized = vector_score_dict.get(idx, 0) / max_vector
            rrf_score = rrf_scores[idx]
            weighted_score = (bm25_weight * bm25_normalized) + (vector_weight * vector_normalized)
            hybrid_scores[idx] = (rrf_weight * rrf_score) + weighted_score

        sorted_candidates = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        hybrid_candidates = [
            {
                "fdc_id": items[idx]["fdc_id"],
                "description": items[idx]["description"],
                "hybrid_score": score,
                "bm25_score": bm25_score_dict.get(idx, 0),
                "vector_score": vector_score_dict.get(idx, 0),
                "rrf_score": rrf_scores[idx]
            }
            for idx, score in sorted_candidates[:stage1_top_k]
        ]

        return hybrid_candidates

    async def apply_reranker_batch(
        self,
        queries_and_candidates: List[Dict[str, Any]],
        reranker_service,
        reranker_model: str = None,
        reranker_instruction: str = None,
        top_k: int = 1
    ) -> List[Dict[str, Any]]:
        """
        複数クエリのRerankerを一括バッチ処理（単一APIコール最適化版）

        従来の並列実行（asyncio.gather）では、DeepInfraサーバー側の順次処理により
        クエリ数に比例した遅延が発生していた。
        本実装では全クエリ・ドキュメントペアを1回のAPIコールにフラット化することで、
        真のバッチ処理を実現し、大幅な高速化を達成。

        Args:
            queries_and_candidates: [{"query": str, "candidates": List[Dict]}, ...]
            reranker_service: Rerankerサービス（rerank_batchメソッドを持つ）
            reranker_model: Rerankerモデル（例: "Qwen/Qwen3-Reranker-0.6B"）
            reranker_instruction: Reranker用instruction
            top_k: 返却する結果数

        Returns:
            List of best results for each query
        """
        import time as time_module

        # ConfigManager（Firestore）を単一の設定ソースとして使用
        # フォールバックはConfigManagerが内部で処理（settings.pyのデフォルト値を使用）
        from ..admin.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_config()

        if reranker_model is None:
            reranker_model = config.reranker.model
        if reranker_instruction is None:
            reranker_instruction = config.reranker.instruction

        logger.info(f"  Reranker model: {reranker_model} (from ConfigManager)")

        batch_start_time = time_module.time()

        # 空のcandidatesを持つクエリをフィルタリング
        valid_items = []
        valid_indices = []
        for i, item in enumerate(queries_and_candidates):
            if item["candidates"]:
                valid_items.append(item)
                valid_indices.append(i)

        if not valid_items:
            logger.info("No valid candidates for reranking")
            return [None] * len(queries_and_candidates)

        # バッチAPI用のデータ準備
        queries_and_documents = []
        for item in valid_items:
            queries_and_documents.append({
                "query": item["query"],
                "documents": [c["description"] for c in item["candidates"]]
            })

        logger.info(f"🔄 Batch reranker execution for {len(queries_and_documents)} queries...")

        # rerank_batchメソッドが存在するか確認し、なければフォールバック
        if hasattr(reranker_service, 'rerank_batch'):
            # 新しいバッチAPIを使用（1回のAPIコール）
            batch_results = await reranker_service.rerank_batch(
                queries_and_documents=queries_and_documents,
                model=reranker_model,
                instruction=reranker_instruction
            )
        else:
            # フォールバック: 従来の並列実行
            logger.warning("⚠️ rerank_batch not available, falling back to parallel individual calls")

            async def rerank_single(query: str, documents: List[str]) -> Tuple[int, List[float]]:
                best_idx, scores = await reranker_service.rerank(
                    query=query,
                    documents=documents,
                    model=reranker_model,
                    instruction=reranker_instruction
                )
                return (best_idx, scores)

            tasks = [
                rerank_single(item["query"], item["documents"])
                for item in queries_and_documents
            ]
            batch_results = await asyncio.gather(*tasks)

        # 結果をマッピング
        final_results = [None] * len(queries_and_candidates)
        for idx, (valid_idx, (best_idx, scores)) in enumerate(zip(valid_indices, batch_results)):
            candidates = valid_items[idx]["candidates"]

            # スコアをcandidatesに付与
            for i, candidate in enumerate(candidates):
                candidate["rerank_score"] = scores[i] if i < len(scores) else 0.0
                candidate["original_rank"] = i + 1

            # スコアでソート
            reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
            final_results[valid_idx] = reranked[0] if reranked else None

        total_elapsed = time_module.time() - batch_start_time
        logger.info(f"✅ Batch reranker completed in {total_elapsed:.2f}s for {len(valid_items)} queries")

        return final_results
