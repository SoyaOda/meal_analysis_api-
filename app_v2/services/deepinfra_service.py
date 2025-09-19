# app_v2/services/deepinfra_service.py

import os
import base64
import logging
import json
import hashlib
from typing import Dict, Any, List

from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError
from ..config import get_settings

# ロガーの設定
logger = logging.getLogger(__name__)

class DeepInfraService:
    """
    Deep Infraのオープンai互換APIと通信するためのサービス。
    gemma-3-27b-itのようなマルチモーダルモデルを使用した画像分析を処理する。
    モデルIDを動的に設定可能。
    """

    def __init__(self, model_id: str = None, model_version: str = None):
        """
        設定ファイルから設定を読み込み、非同期OpenAIクライアントを初期化する。

        Args:
            model_id: 使用するモデルID。Noneの場合は設定ファイルのデフォルトを使用。
            model_version: モデルのバージョンID。指定された場合MODEL:VERSION形式でpin。
        """
        settings = get_settings()

        # API keyの取得（設定ファイル優先、環境変数フォールバック）
        api_key = settings.DEEPINFRA_API_KEY or os.getenv("DEEPINFRA_API_KEY")
        if not api_key:
            raise ValueError("Deep Infra API keyが設定されていません。設定ファイルまたは環境変数 'DEEPINFRA_API_KEY' を設定してください。")

        # モデルIDの決定（パラメータ優先、設定ファイルフォールバック）
        base_model = model_id or settings.DEEPINFRA_MODEL_ID
        # バージョンpin機能：MODEL:VERSION形式で固定
        self.model_id = f"{base_model}:{model_version}" if model_version else base_model
        
        # モデル検証
        if not settings.validate_model_id(self.model_id):
            logger.warning(f"指定されたモデル '{self.model_id}' はサポートリストにありません。利用可能モデル: {settings.SUPPORTED_VISION_MODELS}")
        
        # モデル設定を取得
        self.model_config = settings.get_model_config(self.model_id)
        
        base_url = settings.DEEPINFRA_BASE_URL

        # 非同期クライアントの初期化
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        logger.info(f"DeepInfraService initialized for model: {self.model_id}")
        if self.model_config:
            logger.info(f"Model config: {self.model_config}")

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
        temperature: float = 0.0,
        seed: int = 123456
    ) -> str:
        """
        画像とプロンプトをDeep Infraに送信し、分析結果をJSONとして受け取る。

        Args:
            image_bytes: 分析対象の画像のバイトデータ。
            image_mime_type: 画像のMIMEタイプ (例: 'image/jpeg')。
            prompt: モデルに与える指示プロンプト。
            max_tokens: 生成される最大トークン数。
            temperature: 生成のランダム性を制御する値 (0に近いほど決定的)。
            seed: 再現性のためのシード値。

        Returns:
            モデルからのJSONレスポンス文字列。

        Raises:
            ValueError: レスポンスが不正な場合に発生。
            Exception: Deep Infra APIとの通信でエラーが発生した場合に発生。
        """
        logger.info(f"Starting image analysis with model {self.model_id}.")

        # 入力完全一致の検証ハッシュをログ出力
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        logger.info(f"[input_digest] model={self.model_id} image_sha256={image_hash} prompt_sha256={prompt_hash} temp={temperature} seed={seed}")

        # 期待される処理時間をログに出力
        if self.model_config and "expected_response_time_ms" in self.model_config:
            expected_time = self.model_config["expected_response_time_ms"]
            logger.info(f"Expected response time for {self.model_id}: {expected_time}ms")

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
                seed=seed,
                top_p=1.0,
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
            raise Exception(f"APIとの通信に一時的な問題が発生しました: {e}") from e
        except APIError as e:
            logger.error(f"A non-retriable API error occurred: {e}", exc_info=True)
            raise Exception(f"APIエラーが発生しました: {e}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during API call: {e}", exc_info=True)
            raise ValueError(f"予期せぬエラーが発生しました: {e}") from e 