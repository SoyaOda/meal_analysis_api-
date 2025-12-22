"""
Embeddingプロバイダー抽象化レイヤー

環境変数 EMBEDDING_PROVIDER で切り替え可能:
- "siliconflow": SiliconFlow API + Qwen3-Embedding-8B
- "jina": Jina Embeddings v3 API
- "deepinfra" (デフォルト): DeepInfra API (後方互換)
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Embeddingプロバイダーの抽象基底クラス"""

    @abstractmethod
    async def generate_embeddings(
        self,
        texts: List[str],
        instruction: Optional[str] = None
    ) -> List[List[float]]:
        """
        テキストのEmbeddingを生成

        Args:
            texts: Embedding生成対象のテキストリスト
            instruction: タスク指示文（instruction-awareモデル用）

        Returns:
            List[List[float]]: 各テキストのEmbeddingベクトル
        """
        pass


class SiliconFlowEmbeddingProvider(EmbeddingProvider):
    """
    SiliconFlow API経由のQwen3-Embedding-8B

    特徴:
    - MTEB多言語 #1 (70.58)
    - 32Kトークンコンテキスト
    - instruction-aware対応
    """

    def __init__(self, model_id: str = "Qwen/Qwen3-Embedding-8B"):
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY environment variable is required")

        self.model_id = model_id
        self.base_url = "https://api.siliconflow.cn/v1"

        from ..core.http_client import get_async_client
        self.client = get_async_client()

        logger.info(f"SiliconFlowEmbeddingProvider initialized: {model_id}")

    async def generate_embeddings(
        self,
        texts: List[str],
        instruction: Optional[str] = None
    ) -> List[List[float]]:
        """SiliconFlow API経由でEmbedding生成"""
        url = f"{self.base_url}/embeddings"

        # instruction-aware形式
        if instruction:
            formatted_texts = [
                f"Instruct: {instruction}\nQuery: {text}"
                for text in texts
            ]
        else:
            formatted_texts = texts

        payload = {
            "model": self.model_id,
            "input": formatted_texts,
            "encoding_format": "float"
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            embeddings = [item["embedding"] for item in result.get("data", [])]
            logger.info(f"✅ Generated {len(embeddings)} embeddings via SiliconFlow")
            return embeddings

        except Exception as e:
            logger.error(f"SiliconFlow embedding failed: {e}")
            raise


class JinaEmbeddingProvider(EmbeddingProvider):
    """
    Jina Embeddings v3 API

    特徴:
    - 多言語対応
    - 8192トークンコンテキスト
    - タスク指定可能（retrieval.query, retrieval.passage等）
    """

    def __init__(self, model_id: str = "jina-embeddings-v3"):
        self.api_key = os.getenv("JINA_API_KEY")
        if not self.api_key:
            raise ValueError("JINA_API_KEY environment variable is required")

        self.model_id = model_id
        self.base_url = "https://api.jina.ai/v1"

        from ..core.http_client import get_async_client
        self.client = get_async_client()

        logger.info(f"JinaEmbeddingProvider initialized: {model_id}")

    async def generate_embeddings(
        self,
        texts: List[str],
        instruction: Optional[str] = None
    ) -> List[List[float]]:
        """Jina API経由でEmbedding生成"""
        url = f"{self.base_url}/embeddings"

        payload = {
            "model": self.model_id,
            "input": texts,
        }

        # Jinaはtaskパラメータでinstruction指定
        if instruction:
            # 検索クエリの場合
            payload["task"] = "retrieval.query"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            embeddings = [item["embedding"] for item in result.get("data", [])]
            logger.info(f"✅ Generated {len(embeddings)} embeddings via Jina")
            return embeddings

        except Exception as e:
            logger.error(f"Jina embedding failed: {e}")
            raise


class DeepInfraEmbeddingProvider(EmbeddingProvider):
    """DeepInfra API（後方互換用）"""

    def __init__(self, model_id: str = "Qwen/Qwen3-Embedding-8B"):
        self.api_key = os.getenv("DEEPINFRA_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPINFRA_API_KEY environment variable is required")

        self.model_id = model_id

        # OpenAI互換クライアント
        from openai import AsyncOpenAI
        import httpx
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepinfra.com/v1/openai",
            timeout=httpx.Timeout(
                connect=10.0,
                read=60.0,
                write=30.0,
                pool=10.0,
            ),
        )

        logger.info(f"DeepInfraEmbeddingProvider initialized: {model_id}")

    async def generate_embeddings(
        self,
        texts: List[str],
        instruction: Optional[str] = None
    ) -> List[List[float]]:
        """DeepInfra API経由でEmbedding生成"""
        if instruction:
            formatted_texts = [
                f"Instruct: {instruction}\nQuery: {text}"
                for text in texts
            ]
        else:
            formatted_texts = texts

        try:
            response = await self.client.embeddings.create(
                input=formatted_texts,
                model=self.model_id,
                encoding_format="float"
            )

            embeddings = [item.embedding for item in response.data]
            logger.info(f"✅ Generated {len(embeddings)} embeddings via DeepInfra")
            return embeddings

        except Exception as e:
            logger.error(f"DeepInfra embedding failed: {e}")
            raise


class NovitaEmbeddingProvider(EmbeddingProvider):
    """
    Novita AI API経由のQwen3-Embedding-8B

    特徴:
    - 国際アクセス可能（日本からも利用可）
    - OpenAI互換API
    - $0.056/1M tokens（DeepInfraの約90倍安い）
    - Qwen3-Embedding-8B: MTEB多言語 #1
    """

    def __init__(self, model_id: str = "qwen/qwen3-embedding-8b"):
        self.api_key = os.getenv("NOVITA_API_KEY")
        if not self.api_key:
            raise ValueError("NOVITA_API_KEY environment variable is required")

        self.model_id = model_id
        self.base_url = "https://api.novita.ai/openai/v1"

        # OpenAI互換クライアント
        from openai import AsyncOpenAI
        import httpx
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=10.0,
                read=60.0,
                write=30.0,
                pool=10.0,
            ),
        )

        logger.info(f"NovitaEmbeddingProvider initialized: {model_id}")

    async def generate_embeddings(
        self,
        texts: List[str],
        instruction: Optional[str] = None
    ) -> List[List[float]]:
        """Novita AI API経由でEmbedding生成"""
        if instruction:
            formatted_texts = [
                f"Instruct: {instruction}\nQuery: {text}"
                for text in texts
            ]
        else:
            formatted_texts = texts

        try:
            response = await self.client.embeddings.create(
                input=formatted_texts,
                model=self.model_id,
                encoding_format="float"
            )

            embeddings = [item.embedding for item in response.data]
            logger.info(f"✅ Generated {len(embeddings)} embeddings via Novita AI")
            return embeddings

        except Exception as e:
            logger.error(f"Novita AI embedding failed: {e}")
            raise


class EmbeddingProviderFactory:
    """Embeddingプロバイダーのファクトリークラス"""

    _providers = {
        "novita": NovitaEmbeddingProvider,
        "siliconflow": SiliconFlowEmbeddingProvider,
        "jina": JinaEmbeddingProvider,
        "deepinfra": DeepInfraEmbeddingProvider,
    }

    @classmethod
    def create(cls, provider_name: Optional[str] = None) -> EmbeddingProvider:
        """環境変数またはパラメータに基づいてプロバイダーを生成"""
        if provider_name is None:
            provider_name = os.getenv("EMBEDDING_PROVIDER", "deepinfra")

        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown embedding provider: {provider_name}. "
                f"Available: {list(cls._providers.keys())}"
            )

        logger.info(f"Creating embedding provider: {provider_name}")
        return cls._providers[provider_name]()
