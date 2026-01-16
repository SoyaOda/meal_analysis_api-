#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
USDA Food Search Service

FAISS vector searchを使用してUSDA食材を検索する。
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


class USDAFoodSearchService:
    """USDA食品データベースの検索サービス (Full indexのみ使用)"""

    def __init__(
        self,
        index_dir: str = None,
        stage1_top_k: int = None,
        device: str = "cpu",
        hybrid_engine=None,
        use_lazy_loading: bool = True
    ):
        """
        Args:
            index_dir: FAISSインデックスディレクトリのパス (Lazy Loadingの場合は不要)
            stage1_top_k: Stage1で取得する候補数（Noneの場合はConfigManagerから取得）
            device: 計算デバイス('cpu' or 'cuda')
            hybrid_engine: HybridSearchEngineインスタンス（オプション）
            use_lazy_loading: Lazy Loadingを使用するか（デフォルトTrue）
        """
        # 設定を取得 - ConfigManagerから動的設定、settingsから静的パス情報
        from ..config.settings import get_settings
        from ..admin.config_manager import get_config_manager
        settings = get_settings()
        config_manager = get_config_manager()
        config = config_manager.get_config()

        # stage1_top_kが指定されていない場合はConfigManagerから取得
        if stage1_top_k is None:
            stage1_top_k = config.search.stage1_top_k
        
        self.use_lazy_loading = use_lazy_loading
        self.stage1_top_k = stage1_top_k
        self.device = device
        self.searcher = None  # Lazy Loading時はNone
        
        if use_lazy_loading:
            # Lazy Loadingを使用する場合
            from ..core import startup_optimizer
            self.startup_optimizer = startup_optimizer
            self.index_dir = Path(settings.USDA_INDEX_DIR)
            logger.info("Using Lazy Loading for USDA Food Search Service")
        else:
            # 従来の同期ロード（テスト用など）
            if index_dir is None:
                index_dir = settings.USDA_INDEX_DIR
            self.index_dir = Path(index_dir)
            
            if not self.index_dir.exists():
                raise FileNotFoundError(f"Index directory not found: {index_dir}")

            # SimplifiedUSDASearcherを初期化
            logger.info("Initializing USDA Food Search Service...")
            logger.info(f"Index directory: {index_dir}")
            logger.info("Mode: Full index only")
            logger.info(f"Stage1 top_k: {stage1_top_k}")

            # Import SimplifiedUSDASearcher
            from .usda_search import SimplifiedUSDASearcher

            self.searcher = SimplifiedUSDASearcher(
                index_dir=str(self.index_dir),
                stage1_top_k=stage1_top_k,
                device=device
            )

            logger.info("✅ USDA Food Search Service initialized successfully")

        # HybridSearchEngineを保持
        self.hybrid_engine = hybrid_engine
        if hybrid_engine:
            logger.info("✅ Hybrid search engine attached")
    
    async def _ensure_searcher_loaded(self):
        """Lazy Loadingでsearcherを取得"""
        if self.use_lazy_loading and self.searcher is None:
            # 初回アクセス時にインデックスをロード
            self.searcher = await self.startup_optimizer.get_indexes()

    async def search(
        self,
        query: Union[str, List[Dict[str, str]]],
        search_mode: str = "full_index_only",
        stage1_top_k: Optional[int] = None,
        use_hybrid: bool = True,
        hybrid_top_k: int = 100,
        # Hybrid searchパラメータ
        bm25_weight: float = 0.6,
        vector_weight: float = 0.4,
        rrf_k: int = 60,
        rrf_weight: float = None,
        # Rerankerパラメータ
        reranker_model: Optional[str] = None,
        reranker_instruction: Optional[str] = None,
        reranker_top_n: Optional[int] = None,
        # デバッグオプション
        include_debug_info: bool = False
    ) -> Dict[str, Any]:
        """
        食品検索の実行
        
        Args:
            query: 検索クエリ（文字列または辞書のリスト）
            search_mode: 検索モード（デフォルト: FULL_INDEX_ONLY）
            stage1_top_k: Stage1で取得する候補数（未指定の場合はインスタンス初期化時の値を使用）
            use_hybrid: ハイブリッドサーチを使用するか
            hybrid_top_k: ハイブリッドサーチで取得する候補数
            bm25_weight: BM25スコアの重み（0-1）
            vector_weight: ベクトル検索スコアの重み（0-1）
            rrf_k: RRFのパラメータ（順位の影響を調整）
        
        Returns:
            List[SearchResult]: 検索結果のリスト
        """
        # Lazy Loading対応：非同期メソッドなので直接awaitできる
        if self.use_lazy_loading and self.searcher is None:
            await self._ensure_searcher_loaded()
        
        # stage1_top_kが未指定の場合はインスタンス初期化時の値を使用
        if stage1_top_k is None:
            stage1_top_k = self.stage1_top_k
            
        # search_modeをログ出力
        logger.info(f"Searching with mode: {search_mode}")
        
        # 複数クエリの場合は各クエリを処理してマージ
        if isinstance(query, list) and len(query) > 0 and isinstance(query[0], dict):
            all_results = []
            seen_fdc_ids = set()
            
            for q_dict in query:
                q_text = q_dict.get("query", "")
                q_weight = q_dict.get("weight", 1.0)
                
                # ハイブリッドサーチが有効で、エンジンが利用可能な場合
                if use_hybrid and self.hybrid_engine:
                    try:
                        # Hybrid search + Reranker実行
                        hybrid_results = await self.hybrid_engine.search_hybrid_with_reranker(
                            query=q_text,
                            faiss_index=self.searcher.index_full,
                            embedding_service=self.searcher.embedding_service,
                            reranker_service=self.searcher.reranker_service,
                            items=self.searcher.items,
                            top_k=hybrid_top_k,
                            stage1_top_k=stage1_top_k,
                            bm25_weight=bm25_weight,
                            vector_weight=vector_weight,
                            rrf_k=rrf_k,
                            rrf_weight=rrf_weight,
                            reranker_model=reranker_model,
                            reranker_instruction=reranker_instruction
                        )

                        # Hybrid search結果を追加（既に辞書形式で返される）
                        for h_result in hybrid_results:
                            if h_result["fdc_id"] not in seen_fdc_ids:
                                # 重み付けスコアを適用
                                h_result["score"] = h_result.get("hybrid_score", 0) * q_weight
                                all_results.append(h_result)
                                seen_fdc_ids.add(h_result["fdc_id"])
                        
                        logger.info(f"✅ Hybrid search returned {len(hybrid_results)} results for '{q_text}'")
                        
                    except Exception as e:
                        logger.warning(f"Hybrid search failed, falling back to FAISS: {e}")
                        # Hybrid searchが失敗した場合は通常のFAISSサーチにフォールバック
                        results = self.searcher.search(
                            query=q_text,
                            search_mode=search_mode,
                            stage1_top_k=stage1_top_k
                        )
                        for r in results:
                            if r.fdc_id not in seen_fdc_ids:
                                # 重み付けを適用
                                r.score = r.score * q_weight if r.score else q_weight
                                all_results.append(r)
                                seen_fdc_ids.add(r.fdc_id)
                else:
                    # 通常のFAISSサーチ
                    results = self.searcher.search(
                        query=q_text,
                        search_mode=search_mode,
                        stage1_top_k=stage1_top_k
                    )
                    for r in results:
                        if r.fdc_id not in seen_fdc_ids:
                            # 重み付けを適用
                            r.score = r.score * q_weight if r.score else q_weight
                            all_results.append(r)
                            seen_fdc_ids.add(r.fdc_id)
            
            # スコアでソート（降順）
            all_results.sort(key=lambda x: x.score if x.score else 0, reverse=True)
            
            # 上位結果のみ返す
            return all_results[:stage1_top_k]
        
        # 単一クエリの場合
        # ハイブリッドサーチが有効で、エンジンが利用可能な場合
        debug_info = None
        if use_hybrid and self.hybrid_engine:
            try:
                # Hybrid search + Reranker実行
                hybrid_response = await self.hybrid_engine.search_hybrid_with_reranker(
                    query=query,
                    faiss_index=self.searcher.index_full,
                    embedding_service=self.searcher.embedding_service,
                    reranker_service=self.searcher.reranker_service,
                    items=self.searcher.items,
                    top_k=hybrid_top_k,
                    stage1_top_k=stage1_top_k,
                    bm25_weight=bm25_weight,
                    vector_weight=vector_weight,
                    rrf_k=rrf_k,
                    rrf_weight=rrf_weight,
                    reranker_instruction=reranker_instruction,
                    include_debug_info=include_debug_info
                )

                # 新しいレスポンス形式に対応
                hybrid_results = hybrid_response.get("results", [])
                debug_info = hybrid_response.get("debug_info")

                # Hybrid search結果を返す（既に辞書形式）
                logger.info(f"✅ Hybrid search returned {len(hybrid_results)} results")
                # hybrid_scoreをscoreとしてコピー（既存システムとの互換性のため）
                for h_result in hybrid_results[:stage1_top_k]:
                    h_result["score"] = h_result.get("hybrid_score", 0)

                # stage1_top_k=1の場合は単一のアイテムを返す（pipeline.pyとの互換性）
                if stage1_top_k == 1:
                    result = hybrid_results[0] if hybrid_results else None
                    return {"result": result, "debug_info": debug_info}
                else:
                    return {"results": hybrid_results[:stage1_top_k], "debug_info": debug_info}

            except Exception as e:
                logger.warning(f"Hybrid search failed, falling back to FAISS: {e}")
                # Hybrid searchが失敗した場合は通常のFAISSサーチにフォールバック

        # 通常のFAISSサーチ（非同期）
        result = await self.searcher.search_async(
            query_main=query,
            query_descriptors="",
            return_top_k=stage1_top_k,
            reranker_instruction=reranker_instruction
        )
        # SimplifiedUSDASearcherのレスポンスフォーマットを変換
        # best_matchを返す（pipeline.pyがfdc_idに直接アクセスするため）
        best_match = result["best_match"] if result and result.get("best_match") else None
        return {"result": best_match, "debug_info": None}

    async def search_batch(
        self,
        queries: List[str],
        search_mode: str = "full_index_only",
        stage1_top_k: Optional[int] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        複数のクエリをバッチで検索

        Args:
            queries: 検索クエリのリスト
            search_mode: 検索モード（デフォルト: FULL_INDEX_ONLY）
            stage1_top_k: Stage1で取得する候補数（未指定の場合はインスタンス初期化時の値を使用）

        Returns:
            List[List[SearchResult]]: 各クエリに対する検索結果のリスト
        """
        # Lazy Loading対応：非同期メソッドなので直接awaitできる
        if self.use_lazy_loading and self.searcher is None:
            await self._ensure_searcher_loaded()

        # stage1_top_kが未指定の場合はインスタンス初期化時の値を使用
        if stage1_top_k is None:
            stage1_top_k = self.stage1_top_k

        return self.searcher.search_batch(
            queries=queries,
            search_mode=search_mode,
            stage1_top_k=stage1_top_k
        )

    async def search_with_precomputed_embedding(
        self,
        query: str,
        query_embedding: List[float],
        stage1_top_k: Optional[int] = None,
        # Hybrid searchパラメータ
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6,
        rrf_k: int = 60,
        rrf_weight: float = None,
        # Rerankerパラメータ
        reranker_instruction: Optional[str] = None,
        # デバッグオプション
        include_debug_info: bool = False
    ) -> Dict[str, Any]:
        """
        事前計算済みembeddingを使用した検索（バッチ最適化用）

        Embedding API呼び出しをスキップして高速化。
        パイプラインで複数クエリのembeddingを一括生成後、
        このメソッドで個別に検索を実行する。

        Args:
            query: 検索クエリ
            query_embedding: 事前計算済みのクエリembedding
            stage1_top_k: Stage1で取得する候補数
            bm25_weight: BM25スコアの重み
            vector_weight: ベクトル検索スコアの重み
            rrf_k: RRFのパラメータ
            rrf_weight: RRF融合スコアの重み
            reranker_instruction: Reranker用のinstruction
            include_debug_info: デバッグ情報を含めるか

        Returns:
            Dict[str, Any]: 検索結果（result, debug_info）
        """
        # Lazy Loading対応
        if self.use_lazy_loading and self.searcher is None:
            await self._ensure_searcher_loaded()

        if stage1_top_k is None:
            stage1_top_k = self.stage1_top_k

        # Hybrid engineが必須
        if not self.hybrid_engine:
            raise ValueError("Hybrid engine is required for search_with_precomputed_embedding")

        try:
            # Hybrid search + Reranker実行（事前計算済みembedding使用）
            response = await self.hybrid_engine.search_hybrid_with_reranker_precomputed(
                query=query,
                query_embedding=query_embedding,
                faiss_index=self.searcher.index_full,
                reranker_service=self.searcher.reranker_service,
                items=self.searcher.items,
                stage1_top_k=stage1_top_k,
                bm25_weight=bm25_weight,
                vector_weight=vector_weight,
                rrf_k=rrf_k,
                rrf_weight=rrf_weight,
                reranker_instruction=reranker_instruction,
                include_debug_info=include_debug_info
            )

            hybrid_results = response.get("results", [])
            debug_info = response.get("debug_info")

            # Hybrid search結果を返す
            logger.debug(f"✅ Hybrid search (precomputed) returned {len(hybrid_results)} results")

            for h_result in hybrid_results[:stage1_top_k]:
                h_result["score"] = h_result.get("hybrid_score", 0)

            if stage1_top_k == 1:
                result = hybrid_results[0] if hybrid_results else None
                return {"result": result, "debug_info": debug_info}
            else:
                return {"results": hybrid_results[:stage1_top_k], "debug_info": debug_info}

        except Exception as e:
            logger.error(f"Search with precomputed embedding failed: {e}")
            raise

    async def batch_generate_embeddings(
        self,
        queries: List[str]
    ) -> List[List[float]]:
        """
        複数クエリのembeddingを一括生成

        Args:
            queries: 検索クエリのリスト

        Returns:
            List[List[float]]: 各クエリのembeddingベクトル
        """
        # Lazy Loading対応
        if self.use_lazy_loading and self.searcher is None:
            await self._ensure_searcher_loaded()

        # 設定を取得 - ConfigManagerから動的設定
        from ..admin.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_config()
        embedding_instruction = config.search.embedding_instruction

        # バッチでembedding生成
        embeddings = await self.searcher.embedding_service.generate_embeddings(
            queries,
            instruction=embedding_instruction
        )

        logger.info(f"✅ Batch embedding generated for {len(queries)} queries")
        return embeddings

    def get_candidates_only_sync(
        self,
        query: str,
        query_embedding: List[float],
        stage1_top_k: Optional[int] = None,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6,
        rrf_k: int = 60,
        rrf_weight: float = None,
    ) -> List[Dict[str, Any]]:
        """
        候補取得のみ（Rerankerなし、同期版）

        BM25 + FAISS + RRF融合まで実行し、候補リストを返す。
        Rerankerは後から一括並列実行するため、このメソッドでは実行しない。

        Args:
            query: 検索クエリ
            query_embedding: 事前計算済みembedding
            stage1_top_k: 取得する候補数

        Returns:
            List[Dict]: 候補リスト（rerank_scoreなし）
        """
        if not self.hybrid_engine:
            raise ValueError("Hybrid engine is required for get_candidates_only_sync")

        if stage1_top_k is None:
            stage1_top_k = self.stage1_top_k

        # HybridSearchEngineの同期メソッドを呼び出し
        candidates = self.hybrid_engine.get_hybrid_candidates_sync(
            query=query,
            query_embedding=query_embedding,
            faiss_index=self.searcher.index_full,
            items=self.searcher.items,
            stage1_top_k=stage1_top_k,
            bm25_weight=bm25_weight,
            vector_weight=vector_weight,
            rrf_k=rrf_k,
            rrf_weight=rrf_weight,
        )

        return candidates

    async def batch_rerank_candidates(
        self,
        queries_and_candidates: List[Dict[str, Any]],
        reranker_model: Optional[str] = None,
        reranker_instruction: Optional[str] = None,
        top_k: int = 1
    ) -> List[Optional[Dict[str, Any]]]:
        """
        複数クエリの候補をRerankerで一括並列処理

        Args:
            queries_and_candidates: [{"query": str, "candidates": List[Dict]}, ...]
            reranker_model: Rerankerモデル（例: "Qwen/Qwen3-Reranker-0.6B"）
            reranker_instruction: Reranker用instruction
            top_k: 各クエリから返す結果数

        Returns:
            List[Dict]: 各クエリのベストマッチ結果
        """
        # Lazy Loading対応
        if self.use_lazy_loading and self.searcher is None:
            await self._ensure_searcher_loaded()

        if not self.hybrid_engine:
            raise ValueError("Hybrid engine is required for batch_rerank_candidates")

        # HybridSearchEngineの並列Rerankerメソッドを呼び出し
        results = await self.hybrid_engine.apply_reranker_batch(
            queries_and_candidates=queries_and_candidates,
            reranker_service=self.searcher.reranker_service,
            reranker_model=reranker_model,
            reranker_instruction=reranker_instruction,
            top_k=top_k
        )

        return results
