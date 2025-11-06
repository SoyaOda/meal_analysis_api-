# apps/freeform_usda_meal_analysis_api/services/providers/__init__.py

"""
VLM (Vision Language Model) プロバイダーパッケージ

複数のVLMプロバイダー（DeepInfra, Alibaba Cloud等）をサポートするための
プロバイダー抽象化レイヤー。

使用例:
    >>> from services.providers import VLMProviderFactory
    >>>
    >>> # Alibaba Cloud
    >>> provider = VLMProviderFactory.create_provider("alibaba:qwen-vl-plus")
    >>>
    >>> # DeepInfra
    >>> provider = VLMProviderFactory.create_provider("deepinfra:google/gemini-2.5-flash")
    >>>
    >>> # デフォルト（DeepInfra）
    >>> provider = VLMProviderFactory.create_provider("Qwen/Qwen3-VL-30B-A3B-Thinking")
    >>>
    >>> # 画像分析
    >>> result = await provider.analyze_image(image_bytes, prompt="...", return_usage=True)
"""

from .base_provider import BaseVLMProvider
from .deepinfra_provider import DeepInfraProvider
from .alibaba_provider import AlibabaProvider
from .factory import VLMProviderFactory

__all__ = [
    "BaseVLMProvider",
    "DeepInfraProvider",
    "AlibabaProvider",
    "VLMProviderFactory",
]
