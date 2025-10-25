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

    Sentence-Transformerを使用してテキストをベクトル化します。
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        normalize_embeddings: bool = True
    ):
        """
        Args:
            model_name: Sentence-Transformerモデル名
            device: 使用デバイス ("cpu" or "cuda")
            normalize_embeddings: 埋め込みベクトルを正規化するか（コサイン類似度用）
        """
        # macOS compatibility - disable all parallelism to avoid segmentation fault
        # Only set once per process to avoid RuntimeError
        import os
        import torch
        
        # Set tokenizer parallelism (can be set multiple times)
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        
        # Set torch threads only if not already set
        # Note: These can only be set once per process
        try:
            current_threads = torch.get_num_threads()
            if current_threads > 1:
                torch.set_num_threads(1)
        except RuntimeError:
            pass  # Already set, ignore
        
        try:
            current_interop = torch.get_num_interop_threads()
            if current_interop > 1:
                torch.set_num_interop_threads(1)
        except RuntimeError:
            pass  # Already set, ignore
        
        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings

        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name, device=device)
        print(f"Model loaded successfully. Embedding dimension: {self.get_embedding_dim()}")

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
            batch_size: バッチサイズ
            show_progress_bar: プログレスバーを表示するか

        Returns:
            埋め込みベクトル（shape: [num_texts, embedding_dim]）
        """
        # 単一テキストの場合はリスト化
        if isinstance(texts, str):
            texts = [texts]

        # ベクトル化実行
        # Note: macOS compatibility settings are applied in __init__
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
            normalize_embeddings=self.normalize_embeddings,
            device=self.device
        )

        return embeddings

    def get_embedding_dim(self) -> int:
        """
        埋め込み次元数を取得

        Returns:
            埋め込み次元数
        """
        return self.model.get_sentence_embedding_dimension()

    def __repr__(self) -> str:
        return (
            f"EmbeddingModel(model_name={self.model_name}, "
            f"device={self.device}, "
            f"dim={self.get_embedding_dim()}, "
            f"normalize={self.normalize_embeddings})"
        )