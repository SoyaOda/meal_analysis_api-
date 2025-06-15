# app_v2/services/deepinfra_service.py

import os
import base64
import logging
import json
from typing import Dict, Any, List

from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError
from ..config import get_settings

# ロガーの設定
logger = logging.getLogger(__name__)

class DeepInfraService:
    """
    Deep InfraのOpenAI互換APIと通信するためのサービス。
    gemma-3-27b-itのようなマルチモーダルモデルを使用した画像分析を処理する。
    """

    def __init__(self):
        """
        設定ファイルから設定を読み込み、非同期OpenAIクライアントを初期化する。
        """
        settings = get_settings()
        
        # API keyの取得（設定ファイル優先、環境変数フォールバック）
        api_key = settings.DEEPINFRA_API_KEY or os.getenv("DEEPINFRA_API_KEY")
        if not api_key:
            raise ValueError("Deep Infra API keyが設定されていません。設定ファイルまたは環境変数 'DEEPINFRA_API_KEY' を設定してください。")

        self.model_id = settings.DEEPINFRA_MODEL_ID
        base_url = settings.DEEPINFRA_BASE_URL

        # 非同期クライアントの初期化
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        logger.info(f"DeepInfraService initialized for model: {self.model_id}")

    def _encode_image_to_base64(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        """
        画像バイトをAPIが必要とするBase64エンコードされたデータURI文字列に変換する。
        """
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{base64_image}"

    async def analyze_image(
        self,
        image_bytes: bytes,
        image_mime_type: str,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.0
    ) -> str:
        """
        画像とプロンプトをDeep Infraに送信し、分析結果をJSONとして受け取る。

        Args:
            image_bytes: 分析対象の画像のバイトデータ。
            image_mime_type: 画像のMIMEタイプ (例: 'image/jpeg')。
            prompt: モデルに与える指示プロンプト。
            max_tokens: 生成される最大トークン数。
            temperature: 生成のランダム性を制御する値 (0に近いほど決定的)。

        Returns:
            モデルからのJSONレスポンス文字列。

        Raises:
            ValueError: レスポンスが不正な場合に発生。
            APIError: Deep Infra APIとの通信でエラーが発生した場合に発生。
        """
        logger.info(f"Starting image analysis with model {self.model_id}.")

        base64_image_url = self._encode_image_to_base64(image_bytes, image_mime_type)

        # OpenAI互換のマルチモーダルメッセージペイロードを構築
        messages: List[Dict[str, Any]] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": base64_image_url
                        }
                    }
                ]
            }
        ]

        try:
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                # JSONモードを有効化し、構造化された出力を強制する
                response_format={"type": "json_object"},
            )

            if not response.choices or not response.choices[0].message.content:
                logger.error("API response is empty or invalid.")
                raise ValueError("APIからのレスポンスが空です。")

            # JSON文字列を取得
            raw_json_content = response.choices[0].message.content
            logger.info(f"Successfully received JSON response from API. Usage: {response.usage}")
            
            # JSONの妥当性を検証
            try:
                json.loads(raw_json_content)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received from API: {e}")
                raise ValueError(f"APIから無効なJSONが返されました: {e}")
            
            return raw_json_content

        except (RateLimitError, APIConnectionError) as e:
            logger.error(f"API communication error (retriable): {e}", exc_info=True)
            # TODO: ここに指数バックオフ付きのリトライロジックを実装することを推奨
            raise ValueError(f"APIとの通信に一時的な問題が発生しました: {e}") from e
        except APIError as e:
            logger.error(f"A non-retriable API error occurred: {e}", exc_info=True)
            raise ValueError(f"APIエラーが発生しました: {e}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during API call: {e}", exc_info=True)
            raise ValueError(f"予期せぬエラーが発生しました: {e}") from e 