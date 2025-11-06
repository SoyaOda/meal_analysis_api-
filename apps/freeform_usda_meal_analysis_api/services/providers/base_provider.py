# apps/freeform_usda_meal_analysis_api/services/providers/base_provider.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Union, Optional


class BaseVLMProvider(ABC):
    """
    VLM (Vision Language Model) プロバイダーの抽象基底クラス

    全てのVLMプロバイダー（DeepInfra, Alibaba Cloud等）はこのクラスを継承し、
    analyze_imageメソッドを実装する必要があります。
    """

    def __init__(self, model_id: str, **kwargs):
        """
        プロバイダーを初期化

        Args:
            model_id: 使用するモデルID
            **kwargs: プロバイダー固有の追加パラメータ
        """
        self.model_id = model_id

    @abstractmethod
    async def analyze_image(
        self,
        image_bytes: bytes,
        image_mime_type: str = "image/jpeg",
        prompt: str = "Describe what you see in this image.",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        enable_thinking: Optional[bool] = None,
        return_usage: bool = False
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        画像を分析してVLMの応答を取得

        Args:
            image_bytes: 画像データ（バイト列）
            image_mime_type: 画像のMIMEタイプ
            prompt: VLMへのプロンプト
            max_tokens: 最大出力トークン数
            temperature: ランダム性制御
            seed: 再現性のためのシード値
            thinking_budget: Thinkingモデルの推論トークン数の上限
            enable_thinking: Thinking modeのon/off（Alibabaのqwen3-vl-plus等で使用）
            return_usage: Trueの場合、(response, usage_dict) のタプルを返す

        Returns:
            VLMの応答JSON文字列（return_usage=Falseの場合）
            または (response, usage_dict) のタプル（return_usage=Trueの場合）
        """
        pass

    @property
    def provider_name(self) -> str:
        """プロバイダー名を返す"""
        return self.__class__.__name__.replace("Provider", "").lower()
