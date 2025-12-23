# apps/freeform_usda_meal_analysis_api/services/providers/openrouter_provider.py

import os
import base64
import logging
import json
import hashlib
import re
from typing import Dict, Any, Tuple, Union, Optional

from openai import AsyncOpenAI

from .base_provider import BaseVLMProvider
from ...config import get_settings
from ...core.retry import llm_retry
from ...core.circuit_breaker import vlm_breaker, with_circuit_breaker

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseVLMProvider):
    """
    OpenRouter APIを使用したVLMプロバイダー

    OpenAI互換のエンドポイント経由でOpenRouterの複数モデルにアクセスします。
    サポートされるモデル: qwen/qwen3-vl-235b-a22b-thinking, 他多数
    """

    def __init__(self, model_id: str):
        """
        OpenRouterプロバイダーを初期化

        Args:
            model_id: 使用するモデルID（例: qwen/qwen3-vl-235b-a22b-thinking）
        """
        super().__init__(model_id)

        # 設定を読み込み
        self.settings = get_settings()

        # API keyの取得
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenRouter API keyが設定されていません。"
                "環境変数 'OPENROUTER_API_KEY' を設定してください。"
            )

        # OpenRouterのエンドポイント
        base_url = "https://openrouter.ai/api/v1"

        # 非同期クライアントの初期化（Reasoning有効時は処理時間が長いため120秒に設定）
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=120.0,
        )
        logger.info(f"OpenRouterProvider initialized for model: {self.model_id}")

    @llm_retry
    @with_circuit_breaker(vlm_breaker)
    async def _call_chat_api(
        self,
        messages: list,
        max_tokens: int,
        temperature: float,
        seed: Optional[int] = None,
        extra_body: Optional[dict] = None
    ):
        """
        Chat Completions API呼び出し（リトライ + Circuit Breaker付き）

        耐障害性:
        - tenacity: タイムアウト、接続エラー、RateLimitで自動リトライ
        - Circuit Breaker: 連続5回失敗でOPEN状態に遷移、60秒後に再試行
        """
        params = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if seed is not None:
            params["seed"] = seed
        if extra_body is not None:
            params["extra_body"] = extra_body

        return await self.client.chat.completions.create(**params)

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
        OpenRouter API経由で画像を分析

        Args:
            image_bytes: 画像データ（バイト列）
            image_mime_type: 画像のMIMEタイプ
            prompt: VLMへのプロンプト
            max_tokens: 最大出力トークン数
            temperature: ランダム性制御
            seed: 再現性のためのシード値
            reasoning_effort: Reasoning effort レベル
                             "minimal" (10%), "low" (20%), "medium" (50%), "high" (80%), "xhigh" (95%)
                             → OpenRouter の reasoning.effort にマッピング
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

        if temperature is None:
            temperature = settings.DEFAULT_TEMPERATURE
        if seed is None:
            seed = settings.DEFAULT_SEED

        # ✅ 追加: 受け取ったpromptの内容を確認
        logger.info(f"📝 [OpenRouter] Received prompt (length: {len(prompt)} chars)")
        prompt_preview = prompt[:300] if len(prompt) > 300 else prompt
        logger.info(f"📝 [OpenRouter] Prompt preview (first 300 chars):\n{prompt_preview}")

        logger.info(f"🔧 VLM Parameters: max_tokens={max_tokens}, temperature={temperature}, seed={seed}")

        # ========== Reasoning パラメータの構築 ==========
        extra_body = {"usage": {"include": True}}  # OpenRouterのコスト情報を取得

        # Reasoning設定を構築（呼び出し時指定 > デフォルト設定）
        effective_effort = reasoning_effort if reasoning_effort is not None else settings.DEFAULT_REASONING_EFFORT
        logger.info(f"🔧 Reasoning Parameters: reasoning_effort={reasoning_effort} (effective: {effective_effort})")

        valid_efforts = ["minimal", "low", "medium", "high", "xhigh"]
        if effective_effort not in valid_efforts:
            logger.warning(f"⚠️ Invalid reasoning_effort '{effective_effort}', must be one of {valid_efforts}")
        else:
            extra_body["reasoning"] = {"effort": effective_effort}
            logger.info(f"🧠 Reasoning enabled with effort: {effective_effort}")

        # Base64エンコード
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # 画像のハッシュ値を計算
        image_hash = hashlib.sha256(image_bytes).hexdigest()

        try:
            logger.info(f"🖼️  Analyzing image with OpenRouter VLM (model: {self.model_id})")
            logger.info(f"   Prompt length: {len(prompt)} chars")
            logger.info(f"   Image size: {len(image_bytes)} bytes")
            logger.info(f"   Image hash: {image_hash[:16]}...")
            if "reasoning" in extra_body:
                logger.info(f"   Reasoning config: {extra_body['reasoning']}")

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

            # API呼び出し（tenacity + Circuit Breaker でリトライ）
            response = await self._call_chat_api(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                seed=seed,
                extra_body=extra_body
            )

            # 応答が空でないかチェック
            if not response.choices or not response.choices[0].message.content:
                logger.error("❌ API response is empty or invalid.")
                raise ValueError("[OpenRouter Provider] Empty or invalid API response")

            # 応答内容を取得
            raw_json_content = response.choices[0].message.content.strip()

            logger.info(f"✅ VLM response received ({len(raw_json_content)} chars)")
            logger.debug(f"Raw response preview: {raw_json_content[:200]}...")

            # usage情報を取得（OpenRouterはコスト情報も含む）
            usage_dict = {}
            if response.usage:
                # デバッグ: response.usageの全属性をログ出力
                logger.debug(f"🔍 response.usage attributes: {dir(response.usage)}")
                logger.debug(f"🔍 response.usage dict: {response.usage.model_dump() if hasattr(response.usage, 'model_dump') else response.usage}")

                usage_dict = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

                # OpenRouterのコスト情報を取得（存在する場合）
                # model_extraやdictから取得を試みる
                cost = None
                if hasattr(response.usage, 'cost'):
                    cost = response.usage.cost
                elif hasattr(response.usage, 'model_extra') and response.usage.model_extra:
                    cost = response.usage.model_extra.get('cost')
                elif hasattr(response.usage, 'model_dump'):
                    usage_dump = response.usage.model_dump()
                    cost = usage_dump.get('cost')

                if cost is not None:
                    usage_dict["cost_usd"] = cost
                    logger.info(f"📊 Token usage: prompt={usage_dict['prompt_tokens']}, "
                              f"completion={usage_dict['completion_tokens']}, "
                              f"total={usage_dict['total_tokens']}, "
                              f"💰 cost=${usage_dict['cost_usd']:.4f}")
                else:
                    logger.info(f"📊 Token usage: prompt={usage_dict['prompt_tokens']}, "
                              f"completion={usage_dict['completion_tokens']}, "
                              f"total={usage_dict['total_tokens']}")
                    logger.warning("⚠️  Cost information not found in response.usage")

            # JSONの妥当性を検証（JSONクリーニング処理）
            try:
                # まず元のJSONをパース試行
                json.loads(raw_json_content)
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

                # 1.5. GLM-4.5V の特殊トークンの除去（修正版）
                cleaned_content = cleaned_content.replace('<|begin_of_box|>', '')
                cleaned_content = cleaned_content.replace('<|end_of_box|>', '')
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

                # 4. オブジェクト終了括弧の修正: JSONフィールドの後に]が来ているパターンを修正
                # パターン: オブジェクトのフィールド終了後、次の行のインデントが多い]の場合、それは}であるべき
                lines = cleaned_content.split('\n')
                fixed_lines = []
                for i, line in enumerate(lines):
                    current_stripped = line.strip()
                    # 現在の行が']'だけの場合
                    if current_stripped == ']' and i > 0:
                        prev_line = lines[i-1].strip()
                        # 前の行がオブジェクトのフィールド（数値/文字列/bool）で終わっている
                        if prev_line and not prev_line.endswith(',') and not prev_line.endswith('{') and not prev_line.endswith('[') and not prev_line.endswith('}') and not prev_line.endswith(']'):
                            # インデントを比較して、前の行より2スペース少ない場合はオブジェクトの終了
                            current_indent = len(line) - len(line.lstrip())
                            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                            if current_indent <= prev_indent:
                                # この]は}に置き換えるべき
                                fixed_lines.append(' ' * current_indent + '}')
                                continue
                    fixed_lines.append(line)
                cleaned_content = '\n'.join(fixed_lines)

                # 5. 再パース試行
                try:
                    json.loads(cleaned_content)
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
                        f"[OpenRouter Provider] Failed to parse JSON response after cleaning attempts. "
                        f"Error: {e2}. Debug file saved to: {debug_file}"
                    ) from e2

            # return_usageがTrueの場合はusage情報も返す
            if return_usage:
                return raw_json_content, usage_dict
            return raw_json_content

        except Exception as e:
            # リトライループ内で処理されなかった例外（JSONパースエラーなど）
            error_msg = f"Unexpected error during image analysis: {str(e) or type(e).__name__}"
            logger.error(error_msg, exc_info=True)
            # エラーメッセージを含めて例外を再発生
            raise Exception(error_msg) from e

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
            logger.info(f"📝 Analyzing text with OpenRouter LLM (model: {self.model_id})")
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

            # API呼び出し（tenacity + Circuit Breaker でリトライ）
            response = await self._call_chat_api(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                seed=seed
            )

            # 応答が空でないかチェック
            if not response.choices or not response.choices[0].message.content:
                logger.error("❌ API response is empty or invalid.")
                raise ValueError("[OpenRouter Provider] Empty or invalid API response")

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

        except Exception as e:
            error_msg = f"Unexpected error during text analysis: {str(e) or type(e).__name__}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
