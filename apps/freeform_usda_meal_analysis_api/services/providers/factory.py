# apps/freeform_usda_meal_analysis_api/services/providers/factory.py

import logging
from typing import Optional

from .base_provider import BaseVLMProvider
from .deepinfra_provider import DeepInfraProvider
from .alibaba_provider import AlibabaProvider
from .openrouter_provider import OpenRouterProvider

logger = logging.getLogger(__name__)


class VLMProviderFactory:
    """
    VLMプロバイダーのファクトリークラス

    model_id文字列から適切なプロバイダーインスタンスを生成します。

    サポートされるフォーマット:
    1. "provider:model_id" 形式（例: "openrouter:qwen/qwen3-vl-235b-a22b-thinking", "alibaba:qwen-vl-plus", "deepinfra:google/gemini-2.5-flash"）
    2. "model_id" のみ（例: "Qwen/Qwen3-VL-30B-A3B-Thinking"）→ デフォルトでDeepInfraを使用
    """

    # サポートされるプロバイダー
    SUPPORTED_PROVIDERS = {
        "deepinfra": DeepInfraProvider,
        "alibaba": AlibabaProvider,
        "openrouter": OpenRouterProvider,
    }

    # デフォルトプロバイダー
    DEFAULT_PROVIDER = "deepinfra"

    @classmethod
    def create_provider(
        cls,
        model_id: str,
        model_version: Optional[str] = None,
        **kwargs
    ) -> BaseVLMProvider:
        """
        model_id文字列から適切なVLMプロバイダーインスタンスを生成

        Args:
            model_id: モデルID（"provider:model_id" または "model_id" 形式）
            model_version: モデルバージョン（DeepInfra専用、オプション）
            **kwargs: プロバイダー固有の追加パラメータ

        Returns:
            BaseVLMProvider: プロバイダーインスタンス

        Raises:
            ValueError: サポートされていないプロバイダーが指定された場合

        Examples:
            >>> factory = VLMProviderFactory()
            >>> # OpenRouter
            >>> provider = factory.create_provider("openrouter:qwen/qwen3-vl-235b-a22b-thinking")
            >>> # Alibaba Cloud
            >>> provider = factory.create_provider("alibaba:qwen-vl-plus")
            >>> # DeepInfra（明示的指定）
            >>> provider = factory.create_provider("deepinfra:google/gemini-2.5-flash")
            >>> # DeepInfra（デフォルト）
            >>> provider = factory.create_provider("Qwen/Qwen3-VL-30B-A3B-Thinking")
        """
        # "provider:model_id" 形式かチェック
        if ":" in model_id and not model_id.startswith("http"):
            # URLではない場合（例: "alibaba:qwen-vl-plus"）
            parts = model_id.split(":", 1)
            if len(parts) == 2:
                provider_name = parts[0].lower()
                actual_model_id = parts[1]

                # プロバイダー名が有効かチェック
                if provider_name in cls.SUPPORTED_PROVIDERS:
                    logger.info(f"🔧 Creating {provider_name} provider for model: {actual_model_id}")
                    provider_class = cls.SUPPORTED_PROVIDERS[provider_name]

                    # DeepInfraの場合はmodel_versionも渡す
                    if provider_name == "deepinfra":
                        return provider_class(actual_model_id, model_version=model_version, **kwargs)
                    else:
                        return provider_class(actual_model_id, **kwargs)
                else:
                    raise ValueError(
                        f"サポートされていないプロバイダー: {provider_name}。"
                        f"サポートされているプロバイダー: {list(cls.SUPPORTED_PROVIDERS.keys())}"
                    )

        # "provider:" がない場合はデフォルトプロバイダー（DeepInfra）を使用
        logger.info(f"🔧 Using default provider ({cls.DEFAULT_PROVIDER}) for model: {model_id}")
        provider_class = cls.SUPPORTED_PROVIDERS[cls.DEFAULT_PROVIDER]
        return provider_class(model_id, model_version=model_version, **kwargs)

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """サポートされているプロバイダー名のリストを返す"""
        return list(cls.SUPPORTED_PROVIDERS.keys())
