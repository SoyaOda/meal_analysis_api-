"""
DeepInfra API Service for Freeform USDA Meal Analysis API

VLM、Embedding、Rerankerの3つの機能を提供する自己完結型サービス。
"""

import os
import base64
import logging
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple

from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError

logger = logging.getLogger(__name__)


class DeepInfraService:
    """
    DeepInfra APIサービス（VLM、Embedding、Reranker）

    環境変数から直接設定を読み込む自己完結型の実装。
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        model_version: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepinfra.com/v1/openai"
    ):
        """
        DeepInfraサービスを初期化

        Args:
            model_id: 使用するモデルID（VLM用）
            model_version: モデルバージョン（オプション）
            api_key: DeepInfra API Key（Noneの場合は環境変数から取得）
            base_url: APIベースURL
        """
        # API Key取得
        self.api_key = api_key or os.getenv("DEEPINFRA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DEEPINFRA_API_KEY が設定されていません。"
                "環境変数 DEEPINFRA_API_KEY を設定してください。"
            )

        # モデルID設定
        if model_id:
            self.model_id = f"{model_id}:{model_version}" if model_version else model_id
        else:
            self.model_id = os.getenv("VLM_MODEL_ID", "Qwen/Qwen3-VL-30B-A3B-Thinking")

        # OpenAI互換クライアント初期化
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )

        logger.info(f"✅ DeepInfraService initialized for model: {self.model_id}")

    def _encode_image_to_base64(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        """画像バイトをBase64エンコードされたデータURI文字列に変換"""
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{base64_image}"

    async def analyze_image(
        self,
        image_bytes: bytes,
        image_mime_type: str,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        seed: int = 123456,
        thinking_budget: int = 2048,
        return_usage: bool = False,
    ) -> Any:
        """
        VLMで画像分析を実行

        Args:
            image_bytes: 画像バイトデータ
            image_mime_type: 画像MIMEタイプ
            prompt: プロンプト
            max_tokens: 最大トークン数
            temperature: 生成温度
            seed: シード値
            thinking_budget: Thinkingモデルの推論トークン数
            return_usage: usage情報を返すか

        Returns:
            JSON文字列、またはusage付きタプル
        """
        logger.info(f"🔍 Starting image analysis with model {self.model_id}")

        # 入力ハッシュをログ出力
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        logger.info(
            f"[input_digest] model={self.model_id} "
            f"image_sha256={image_hash} prompt_sha256={prompt_hash} "
            f"temp={temperature} seed={seed}"
        )

        # Base64エンコード
        base64_image_url = self._encode_image_to_base64(image_bytes, image_mime_type)

        # メッセージ構築
        messages: List[Dict[str, Any]] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": base64_image_url}}
                ]
            }
        ]

        # Thinkingモデル検出
        is_thinking_model = "thinking" in self.model_id.lower()

        if is_thinking_model:
            logger.info(f"💭 Detected Thinking model: {self.model_id}")
            # Thinking モデルは temperature=0.0 を避ける（性能低下）
            if temperature == 0.0:
                logger.warning("Overriding temperature=0.0 → 0.6 for Thinking model")
                temperature = 0.6

        try:
            # API パラメータ構築
            api_params = {
                "model": self.model_id,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "seed": seed,
            }

            # Thinkingモデル用パラメータ
            if is_thinking_model:
                api_params["top_p"] = 0.95
                api_params["extra_body"] = {
                    "enable_thinking": True,
                    "thinking_budget": thinking_budget,
                    "top_k": 20
                }
                logger.info(f"💡 Thinking budget: {thinking_budget}, max_tokens: {max_tokens}")
            else:
                api_params["top_p"] = 1.0
                api_params["response_format"] = {"type": "json_object"}

            # API呼び出し
            response = await self.client.chat.completions.create(**api_params)

            # レスポンス検証
            if not response.choices or not response.choices[0].message.content:
                raise ValueError("APIからのレスポンスが空です。")

            raw_json_content = response.choices[0].message.content

            # Usage情報取得
            usage_dict = None
            if response.usage:
                usage_dict = {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0)
                }

            logger.info(f"✅ API response received. Usage: {usage_dict}")

            # Thinkingタグ除去
            if is_thinking_model:
                import re
                cleaned_content = re.sub(r'<think>.*?</think>', '', raw_json_content, flags=re.DOTALL)
                cleaned_content = cleaned_content.strip()
                logger.info(
                    f"🧹 Removed <think> tags: "
                    f"{len(raw_json_content)} → {len(cleaned_content)} chars"
                )
                raw_json_content = cleaned_content

            # JSON検証とクリーニング
            try:
                json.loads(raw_json_content)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Initial JSON parsing failed: {e}")

                # JSONクリーニング
                cleaned = raw_json_content.strip()

                # Markdownコードブロック除去
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                # Trailing comma除去
                import re
                cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)

                # 再パース
                try:
                    json.loads(cleaned)
                    raw_json_content = cleaned
                    logger.info("✅ JSON cleaning successful")
                except json.JSONDecodeError as e2:
                    logger.error(f"❌ JSON cleaning failed: {e2}")
                    raise ValueError(f"APIから無効なJSONが返されました: {e2}")

            # 結果返却
            if return_usage:
                return raw_json_content, usage_dict
            return raw_json_content

        except (RateLimitError, APIConnectionError) as e:
            logger.error(f"API通信エラー: {e}", exc_info=True)
            raise Exception(f"APIとの通信に一時的な問題が発生しました: {e}") from e
        except APIError as e:
            logger.error(f"APIエラー: {e}", exc_info=True)
            raise Exception(f"APIエラーが発生しました: {e}") from e
        except Exception as e:
            logger.error(f"予期せぬエラー: {e}", exc_info=True)
            raise ValueError(f"予期せぬエラーが発生しました: {e}") from e

    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = "Qwen/Qwen3-Embedding-8B"
    ) -> List[List[float]]:
        """
        テキストのembeddingを生成（DeepInfra API）

        Args:
            texts: テキストリスト
            model: Embeddingモデル

        Returns:
            embedding vectorのリスト
        """
        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=model,
                encoding_format="float"  # DeepInfra requires 'float'
            )

            embeddings = [item.embedding for item in response.data]
            logger.debug(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Embedding生成失敗: {e}")
            raise

    async def rerank(
        self,
        query: str,
        documents: List[str],
        model: str = "Qwen/Qwen3-Reranker-8B",
        top_n: Optional[int] = None
    ) -> Tuple[int, List[float]]:
        """
        文書をリランキング（DeepInfra API）

        Args:
            query: クエリテキスト
            documents: 文書リスト
            model: Rerankerモデル
            top_n: 上位N件（Noneの場合は全件）

        Returns:
            (best_index, scores)のタプル
        """
        try:
            import httpx

            url = f"https://api.deepinfra.com/v1/inference/{model}"

            async with httpx.AsyncClient() as client:
                payload = {
                    "queries": [query],  # リスト形式（重要）
                    "documents": documents
                }
                if top_n is not None:
                    payload["top_n"] = top_n

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                result = response.json()

                # スコア抽出
                scores = result.get("scores", [])
                if not scores:
                    logger.warning(f"⚠️ No scores returned. Response: {result}")
                    scores = [0.0] * len(documents)

                best_idx = scores.index(max(scores)) if scores else 0
                logger.debug(f"✅ Reranking complete. Best index: {best_idx}")

                return best_idx, scores

        except Exception as e:
            logger.error(f"Reranking失敗: {e}")
            raise
