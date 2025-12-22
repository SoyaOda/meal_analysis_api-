"""
Rerankerプロバイダー抽象化レイヤー

環境変数 RERANKER_PROVIDER で切り替え可能:
- "siliconflow" (デフォルト): SiliconFlow API + Qwen3-Reranker-8B
- "jina": Jina Reranker v2 API
- "deepinfra": DeepInfra API (後方互換)
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class RerankerProvider(ABC):
    """Rerankerプロバイダーの抽象基底クラス"""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        instruction: Optional[str] = None
    ) -> Tuple[int, List[float]]:
        """
        ドキュメントをリランキング

        Args:
            query: 検索クエリ
            documents: リランキング対象ドキュメントリスト
            top_n: 返す上位件数（Noneで全件）
            instruction: タスク指示文

        Returns:
            (best_index, scores): 最高スコアのインデックスと全スコアリスト
        """
        pass


class SiliconFlowRerankerProvider(RerankerProvider):
    """
    SiliconFlow API経由のQwen3-Reranker-8B

    特徴:
    - DeepInfraと同じQwen3モデルで精度維持
    - 2.3x高速な推論
    - 真の並列処理サポート
    """

    def __init__(self, model_id: str = "Qwen/Qwen3-Reranker-8B"):
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY environment variable is required")

        self.model_id = model_id
        self.base_url = "https://api.siliconflow.cn/v1"

        # 共有HTTPクライアント
        from ..core.http_client import get_async_client
        self.client = get_async_client()

        logger.info(f"SiliconFlowRerankerProvider initialized: {model_id}")

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        instruction: Optional[str] = None
    ) -> Tuple[int, List[float]]:
        """SiliconFlow API経由でリランキング"""
        url = f"{self.base_url}/rerank"

        payload = {
            "model": self.model_id,
            "query": query,
            "documents": documents,
        }
        if top_n is not None:
            payload["top_n"] = top_n

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            # レスポンス形式: {"results": [{"index": 0, "relevance_score": 0.95}, ...]}
            results = result.get("results", [])

            # スコアリストを元のインデックス順に再構築
            scores = [0.0] * len(documents)
            for item in results:
                idx = item.get("index", 0)
                score = item.get("relevance_score", 0.0)
                if idx < len(scores):
                    scores[idx] = score

            best_idx = scores.index(max(scores)) if scores else 0
            return best_idx, scores

        except Exception as e:
            logger.error(f"SiliconFlow rerank failed: {e}")
            raise


class JinaRerankerProvider(RerankerProvider):
    """
    Jina Reranker v2 API

    特徴:
    - ~150msレイテンシ（超高速）
    - 1リクエストで最大2048ドキュメント
    - 100+言語対応
    - オープンソースベース
    """

    def __init__(self, model_id: str = "jina-reranker-v2-base-multilingual"):
        self.api_key = os.getenv("JINA_API_KEY")
        if not self.api_key:
            raise ValueError("JINA_API_KEY environment variable is required")

        self.model_id = model_id
        self.base_url = "https://api.jina.ai/v1"

        from ..core.http_client import get_async_client
        self.client = get_async_client()

        logger.info(f"JinaRerankerProvider initialized: {model_id}")

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        instruction: Optional[str] = None
    ) -> Tuple[int, List[float]]:
        """Jina API経由でリランキング"""
        url = f"{self.base_url}/rerank"

        payload = {
            "model": self.model_id,
            "query": query,
            "documents": documents,
        }
        if top_n is not None:
            payload["top_n"] = top_n

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            # Jinaレスポンス形式: {"results": [{"index": 0, "relevance_score": 0.95}, ...]}
            results = result.get("results", [])

            scores = [0.0] * len(documents)
            for item in results:
                idx = item.get("index", 0)
                score = item.get("relevance_score", 0.0)
                if idx < len(scores):
                    scores[idx] = score

            best_idx = scores.index(max(scores)) if scores else 0
            return best_idx, scores

        except Exception as e:
            logger.error(f"Jina rerank failed: {e}")
            raise


class DeepInfraRerankerProvider(RerankerProvider):
    """
    DeepInfra API（後方互換用）

    注意: 逐次処理の問題があるため、本番使用は非推奨
    """

    def __init__(self, model_id: str = "Qwen/Qwen3-Reranker-8B"):
        self.api_key = os.getenv("DEEPINFRA_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPINFRA_API_KEY environment variable is required")

        self.model_id = model_id

        from ..core.http_client import get_async_client
        self.client = get_async_client()

        logger.info(f"DeepInfraRerankerProvider initialized: {model_id}")

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        instruction: Optional[str] = None
    ) -> Tuple[int, List[float]]:
        """DeepInfra API経由でリランキング"""
        url = f"https://api.deepinfra.com/v1/inference/{self.model_id}"

        payload = {
            "queries": [query],
            "documents": documents
        }
        if top_n is not None:
            payload["top_n"] = top_n
        if instruction is not None:
            payload["instruction"] = instruction

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            scores = result.get("scores", [])
            best_idx = scores.index(max(scores)) if scores else 0
            return best_idx, scores

        except Exception as e:
            logger.error(f"DeepInfra rerank failed: {e}")
            raise


class NovitaRerankerProvider(RerankerProvider):
    """
    Novita AI API経由のQwen3-Reranker-8B

    特徴:
    - 国際アクセス可能（日本からも利用可）
    - OpenAI互換API
    - $0.04/1M tokens（DeepInfraより大幅に安い）
    - Qwen3-Reranker-8B: MTEB-R 69.02
    """

    def __init__(self, model_id: str = "qwen/qwen3-reranker-8b"):
        self.api_key = os.getenv("NOVITA_API_KEY")
        if not self.api_key:
            raise ValueError("NOVITA_API_KEY environment variable is required")

        self.model_id = model_id
        self.base_url = "https://api.novita.ai/openai/v1"

        from ..core.http_client import get_async_client
        self.client = get_async_client()

        logger.info(f"NovitaRerankerProvider initialized: {model_id}")

    def _format_query_with_instruction(
        self,
        query: str,
        instruction: Optional[str] = None
    ) -> str:
        """
        Novita AI APIで最も効果的なフォーマットでinstructionを埋め込む

        検証結果:
        - Qwen3公式タグ (<Instruct>/<Query>) は Novita AI APIで効果なし
        - Inline [Task:] フォーマットが最も効果的 (精度2倍)

        フォーマット: [Task: {instruction}] {query}
        """
        if instruction:
            # 長いinstructionは最初の100文字に短縮
            short_instruction = instruction[:100] if len(instruction) > 100 else instruction
            return f"[Task: {short_instruction}] {query}"
        return query

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        instruction: Optional[str] = None
    ) -> Tuple[int, List[float]]:
        """Novita AI API経由でリランキング（instruction埋め込み対応）"""
        url = f"{self.base_url}/rerank"

        # Qwen3フォーマットでinstructionをqueryに埋め込む
        formatted_query = self._format_query_with_instruction(query, instruction)

        payload = {
            "model": self.model_id,
            "query": formatted_query,
            "documents": documents,
        }
        if top_n is not None:
            payload["top_n"] = top_n

        if instruction:
            logger.debug(f"Reranker query with instruction: {formatted_query[:100]}...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            # OpenAI互換レスポンス形式: {"results": [{"index": 0, "relevance_score": 0.95}, ...]}
            results = result.get("results", [])

            # スコアリストを元のインデックス順に再構築
            scores = [0.0] * len(documents)
            for item in results:
                idx = item.get("index", 0)
                score = item.get("relevance_score", 0.0)
                if idx < len(scores):
                    scores[idx] = score

            best_idx = scores.index(max(scores)) if scores else 0
            logger.info(f"✅ Reranked {len(documents)} documents via Novita AI")
            return best_idx, scores

        except Exception as e:
            logger.error(f"Novita AI rerank failed: {e}")
            raise


class RerankerProviderFactory:
    """Rerankerプロバイダーのファクトリークラス"""

    _providers = {
        "novita": NovitaRerankerProvider,
        "siliconflow": SiliconFlowRerankerProvider,
        "jina": JinaRerankerProvider,
        "deepinfra": DeepInfraRerankerProvider,
    }

    @classmethod
    def create(cls, provider_name: Optional[str] = None) -> RerankerProvider:
        """
        環境変数またはパラメータに基づいてプロバイダーを生成

        Args:
            provider_name: プロバイダー名（None時は環境変数から取得）

        Returns:
            RerankerProvider インスタンス
        """
        if provider_name is None:
            provider_name = os.getenv("RERANKER_PROVIDER", "deepinfra")

        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown reranker provider: {provider_name}. "
                f"Available: {list(cls._providers.keys())}"
            )

        logger.info(f"Creating reranker provider: {provider_name}")
        return cls._providers[provider_name]()
