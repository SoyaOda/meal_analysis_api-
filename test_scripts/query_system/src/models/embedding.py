"""
埋め込みモデルモジュール

Sentence-BERTを使用したテキスト埋め込みを提供します。
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    テキスト埋め込みモデル

    DeepInfra API経由でQwen3-Embedding-8Bを使用してテキストをベクトル化します。
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Embedding-8B",
        device: str = "cpu",  # Unused for API, kept for compatibility
        normalize_embeddings: bool = True
    ):
        """
        Args:
            model_name: DeepInfra埋め込みモデル名 (default: Qwen/Qwen3-Embedding-8B)
            device: 使用デバイス（APIでは未使用、互換性のために保持）
            normalize_embeddings: 埋め込みベクトルを正規化するか（コサイン類似度用）
        """
        import os
        import requests

        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        self.api_url = "https://api.deepinfra.com/v1/openai/embeddings"

        # API usage tracking
        self.total_tokens = 0
        self.api_calls = 0

        # Get API token from environment
        self.api_token = os.getenv("DEEPINFRA_TOKEN") or os.getenv("DEEPINFRA_API_KEY")
        if not self.api_token:
            raise ValueError(
                "DEEPINFRA_TOKEN or DEEPINFRA_API_KEY environment variable not set. "
                "Please set it with your DeepInfra API token."
            )

        # Get embedding dimension by testing with a single text
        print(f"Initializing DeepInfra embedding model: {model_name}...")
        test_embedding = self._encode_via_api(["test"])
        self._embedding_dim = test_embedding.shape[1]
        print(f"Model initialized successfully. Embedding dimension: {self._embedding_dim}")

    def _encode_via_api(self, texts: List[str]) -> np.ndarray:
        """
        DeepInfra API経由でテキストをエンコード

        Args:
            texts: エンコードするテキストのリスト

        Returns:
            埋め込みベクトル (shape: [num_texts, embedding_dim])
        """
        import requests
        import numpy as np

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "input": texts,
            "model": self.model_name,
            "encoding_format": "float"
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=120  # 2 minute timeout
            )
            response.raise_for_status()

            result = response.json()

            # Track API usage
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            self.total_tokens += tokens_used
            self.api_calls += 1

            # Extract embeddings from response
            # Response format: {"data": [{"embedding": [...]}, ...]}
            embeddings = [item["embedding"] for item in result["data"]]
            embeddings = np.array(embeddings, dtype=np.float32)

            # Normalize if requested
            if self.normalize_embeddings:
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                embeddings = embeddings / (norms + 1e-8)

            return embeddings

        except requests.exceptions.RequestException as e:
            print(f"⚠️ DeepInfra API error: {e}")
            # Return zero vectors as fallback
            return np.zeros((len(texts), self._embedding_dim if hasattr(self, '_embedding_dim') else 4096), dtype=np.float32)

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress_bar: bool = False
    ) -> np.ndarray:
        """
        テキストをベクトル化

        Args:
            texts: エンコードするテキスト（文字列またはリスト）
            batch_size: バッチサイズ（API呼び出しのバッチ処理用）
            show_progress_bar: プログレスバーを表示するか

        Returns:
            埋め込みベクトル（shape: [num_texts, embedding_dim]）
        """
        # 単一テキストの場合はリスト化
        if isinstance(texts, str):
            texts = [texts]

        # バッチ処理でAPI呼び出し
        all_embeddings = []
        
        if show_progress_bar:
            from tqdm import tqdm
            iterator = tqdm(range(0, len(texts), batch_size), desc="Encoding")
        else:
            iterator = range(0, len(texts), batch_size)
        
        for i in iterator:
            batch = texts[i:i+batch_size]
            batch_embeddings = self._encode_via_api(batch)
            all_embeddings.append(batch_embeddings)
        
        # Concatenate all batches
        embeddings = np.vstack(all_embeddings)
        
        return embeddings

    def get_embedding_dim(self) -> int:
        """
        埋め込み次元数を取得

        Returns:
            埋め込み次元数
        """
        return self._embedding_dim

    def get_usage_stats(self) -> dict:
        """
        API使用統計を取得

        Returns:
            使用統計辞書 {
                "total_tokens": int,
                "api_calls": int,
                "cost_usd": float,
                "cost_per_1m_tokens": float
            }
        """
        cost_per_1m = 0.025  # $0.025 / 1M tokens for Qwen3-Embedding-8B
        cost_usd = (self.total_tokens / 1_000_000) * cost_per_1m

        return {
            "total_tokens": self.total_tokens,
            "api_calls": self.api_calls,
            "cost_usd": cost_usd,
            "cost_per_1m_tokens": cost_per_1m
        }

    def reset_usage_stats(self):
        """API使用統計をリセット"""
        self.total_tokens = 0
        self.api_calls = 0

    def __repr__(self) -> str:
        return (
            f"EmbeddingModel(model_name={self.model_name}, "
            f"device={self.device}, "
            f"dim={self._embedding_dim}, "
            f"normalize={self.normalize_embeddings})"
        )