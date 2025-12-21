# apps/freeform_usda_meal_analysis_api/services/providers/alibaba_provider.py

import os
import base64
import logging
import json
import hashlib
import re
from typing import Dict, Any, Tuple, Union, Optional

from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError

from .base_provider import BaseVLMProvider
from ...config import get_settings

logger = logging.getLogger(__name__)


class AlibabaProvider(BaseVLMProvider):
    """
    Alibaba Cloud DashScope APIを使用したVLMプロバイダー

    OpenAI互換のエンドポイント経由でAlibaba Cloud (DashScope) のQwen-VLモデルにアクセスします。
    サポートされるモデル: qwen-vl-max, qwen-vl-plus, qvq-max, qwen2.5-vl-72b-instruct等
    """

    def __init__(self, model_id: str, region: str = "intl"):
        """
        Alibabaプロバイダーを初期化

        Args:
            model_id: 使用するモデルID（例: qwen-vl-plus, qwen-vl-max）
            region: リージョン選択 ("intl" = Singapore, "cn" = China Beijing)
        """
        super().__init__(model_id)

        # 設定を読み込み
        self.settings = get_settings()

        # API keyの取得
        api_key = os.getenv("ALIBABA_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError(
                "Alibaba Cloud API keyが設定されていません。"
                "環境変数 'ALIBABA_API_KEY' または 'DASHSCOPE_API_KEY' を設定してください。"
            )

        # リージョン別のエンドポイント
        if region == "cn":
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        else:  # デフォルトはシンガポール（国際リージョン）
            base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        self.region = region

        # 非同期クライアントの初期化
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        logger.info(f"AlibabaProvider initialized for model: {self.model_id} (region: {region})")

    async def analyze_image(
        self,
        image_bytes: bytes,
        image_mime_type: str = "image/jpeg",
        prompt: str = "Describe what you see in this image.",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        return_usage: bool = False
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Alibaba Cloud DashScope API経由で画像を分析

        Args:
            image_bytes: 画像データ（バイト列）
            image_mime_type: 画像のMIMEタイプ
            prompt: VLMへのプロンプト
            max_tokens: 最大出力トークン数
            temperature: ランダム性制御
            seed: 再現性のためのシード値
            reasoning_effort: Reasoning effort レベル（Alibabaでは未使用）
            return_usage: Trueの場合、(response, usage_dict) のタプルを返す

        Returns:
            VLMの応答JSON文字列（return_usage=Falseの場合）
            または (response, usage_dict) のタプル（return_usage=Trueの場合）
        """
        # config から設定を取得
        settings = get_settings()

        # パラメータのデフォルト値を設定
        if max_tokens is None:
            max_tokens = settings.DEFAULT_MAX_TOKENS

        # Alibaba API の max_tokens 上限は 8192
        if max_tokens > 8192:
            logger.warning(f"⚠️  max_tokens={max_tokens} exceeds Alibaba API limit (8192), adjusting to 8192")
            max_tokens = 8192

        if temperature is None:
            temperature = settings.DEFAULT_TEMPERATURE
        if seed is None:
            seed = settings.DEFAULT_SEED

        logger.info(f"🔧 VLM Parameters: max_tokens={max_tokens}, temperature={temperature}, seed={seed}")
        if reasoning_effort is not None:
            logger.warning(f"⚠️ reasoning_effort={reasoning_effort} is not used by Alibaba")

        # Base64エンコード
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # 画像のハッシュ値を計算
        image_hash = hashlib.sha256(image_bytes).hexdigest()

        try:
            logger.info(f"🖼️  Analyzing image with Alibaba Cloud VLM (model: {self.model_id}, region: {self.region})")
            logger.info(f"   Prompt length: {len(prompt)} chars")
            logger.info(f"   Image size: {len(image_bytes)} bytes")
            logger.info(f"   Image hash: {image_hash[:16]}...")

            # メッセージ構築（OpenAI互換形式）
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_mime_type};base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]

            # API呼び出し（OpenAI互換）
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                seed=seed
            )

            # 応答が空でないかチェック
            if not response.choices or not response.choices[0].message.content:
                logger.error("❌ API response is empty or invalid.")
                logger.error(f"Response object: {response}")
                raise ValueError(f"[Alibaba Provider] Empty or invalid API response. Response: {response}")

            # 応答内容を取得
            raw_json_content = response.choices[0].message.content.strip()

            logger.info(f"✅ VLM response received ({len(raw_json_content)} chars)")
            logger.debug(f"Raw response preview: {raw_json_content[:200]}...")

            # usage情報を取得
            usage_dict = {}
            if response.usage:
                usage_dict = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                logger.info(f"📊 Token usage: prompt={usage_dict['prompt_tokens']}, "
                          f"completion={usage_dict['completion_tokens']}, "
                          f"total={usage_dict['total_tokens']}")

            # JSONの妥当性を検証（JSONクリーニング処理）
            try:
                # まず元のJSONをパース試行
                parsed_json = json.loads(raw_json_content)
            except json.JSONDecodeError as e:
                logger.warning(f"Initial JSON parsing failed: {e}")

                # エラー箇所の周辺を表示
                error_pos = e.pos if hasattr(e, 'pos') else 0
                context_start = max(0, error_pos - 100)
                context_end = min(len(raw_json_content), error_pos + 100)
                logger.warning(f"Error context: ...{raw_json_content[context_start:context_end]}...")

                # JSONクリーニング処理
                cleaned_content = raw_json_content

                # 1. <think>...</think> タグの除去
                cleaned_content = re.sub(r'<think>.*?</think>', '', cleaned_content, flags=re.DOTALL)
                cleaned_content = cleaned_content.strip()

                # 2. Markdown コードブロックの除去
                if cleaned_content.startswith("```json"):
                    cleaned_content = cleaned_content[7:]
                if cleaned_content.startswith("```"):
                    cleaned_content = cleaned_content[3:]
                if cleaned_content.endswith("```"):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()

                # 3. trailing commaの除去
                cleaned_content = re.sub(r',(\s*[}\]])', r'\1', cleaned_content)

                # 4. 再パース試行
                try:
                    parsed_json = json.loads(cleaned_content)
                    raw_json_content = cleaned_content  # クリーニング成功
                    logger.info("JSON cleaning successful")
                except json.JSONDecodeError as e2:
                    # さらに詳細なエラー情報を出力
                    logger.error(f"JSON cleaning failed after all attempts: {e2}")
                    logger.error(f"Error line: {e2.lineno if hasattr(e2, 'lineno') else 'unknown'}")
                    logger.error(f"Error column: {e2.colno if hasattr(e2, 'colno') else 'unknown'}")

                    # エラー行の内容を表示
                    lines = cleaned_content.split('\n')
                    if hasattr(e2, 'lineno') and e2.lineno <= len(lines):
                        error_line_idx = e2.lineno - 1
                        logger.error(f"Error line content: {lines[error_line_idx]}")
                        if error_line_idx > 0:
                            logger.error(f"Previous line: {lines[error_line_idx - 1]}")
                        if error_line_idx < len(lines) - 1:
                            logger.error(f"Next line: {lines[error_line_idx + 1]}")

                    # 完全なJSONをファイルに保存
                    debug_file = f"/tmp/debug_json_error_{image_hash[:8]}.txt"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    logger.error(f"Full JSON content saved to: {debug_file}")

                    raise ValueError(
                        f"[Alibaba Provider] Failed to parse JSON response after cleaning attempts. "
                        f"Error: {e2}. Debug file saved to: {debug_file}"
                    ) from e2

            # return_usageがTrueの場合はusage情報も返す
            if return_usage:
                return raw_json_content, usage_dict
            return raw_json_content

        except (RateLimitError, APIConnectionError) as e:
            logger.error(f"API communication error (retriable): {e}", exc_info=True)
            raise Exception(f"APIとの通信に一時的な問題が発生しました: {e}") from e
        except APIError as e:
            logger.error(f"A non-retriable API error occurred: {e}", exc_info=True)
            raise Exception(f"APIエラーが発生しました: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during image analysis: {e}", exc_info=True)
            raise

    async def analyze_text(
        self,
        text: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        return_usage: bool = False
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        テキスト入力を分析してLLMの応答を取得（Voice入力用）

        画像なしでテキストのみを処理する。音声入力から変換されたテキストの
        分析に使用される。

        Args:
            text: 分析対象のテキスト（音声認識結果など）
            prompt: LLMへのシステムプロンプト
            max_tokens: 最大出力トークン数
            temperature: ランダム性制御
            seed: 再現性のためのシード値
            return_usage: Trueの場合、(response, usage_dict) のタプルを返す

        Returns:
            LLMの応答JSON文字列（return_usage=Falseの場合）
            または (response, usage_dict) のタプル（return_usage=Trueの場合）
        """
        # config から設定を取得
        settings = get_settings()

        # パラメータのデフォルト値を設定
        if max_tokens is None:
            max_tokens = settings.DEFAULT_VOICE_MAX_TOKENS
        if temperature is None:
            temperature = settings.DEFAULT_VOICE_TEMPERATURE
        if seed is None:
            seed = settings.DEFAULT_SEED

        logger.info(f"🔧 LLM Parameters (text mode): max_tokens={max_tokens}, temperature={temperature}, seed={seed}")

        try:
            logger.info(f"📝 Analyzing text with Alibaba LLM (model: {self.model_id})")
            logger.info(f"   Prompt length: {len(prompt)} chars")
            logger.info(f"   Text length: {len(text)} chars")

            # メッセージ構築（テキストのみ）
            messages = [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": text
                }
            ]

            # API呼び出し
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                seed=seed
            )

            # 応答が空でないかチェック
            if not response.choices or not response.choices[0].message.content:
                logger.error("❌ API response is empty or invalid.")
                raise ValueError(f"[Alibaba Provider] Empty or invalid API response")

            # 応答内容を取得
            raw_content = response.choices[0].message.content.strip()

            logger.info(f"✅ LLM response received ({len(raw_content)} chars)")

            # usage情報を取得
            usage_dict = {}
            if response.usage:
                usage_dict = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                logger.info(f"📊 Token usage: prompt={usage_dict['prompt_tokens']}, "
                          f"completion={usage_dict['completion_tokens']}, "
                          f"total={usage_dict['total_tokens']}")

            if return_usage:
                return raw_content, usage_dict
            return raw_content

        except (RateLimitError, APIConnectionError) as e:
            logger.error(f"API communication error (retriable): {e}", exc_info=True)
            raise Exception(f"APIとの通信に一時的な問題が発生しました: {e}") from e
        except APIError as e:
            logger.error(f"A non-retriable API error occurred: {e}", exc_info=True)
            raise Exception(f"APIエラーが発生しました: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during text analysis: {e}", exc_info=True)
            raise
