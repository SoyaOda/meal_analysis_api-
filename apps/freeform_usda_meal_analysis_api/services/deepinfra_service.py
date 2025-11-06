# apps/freeform_usda_meal_analysis_api/services/deepinfra_service.py

import os
import base64
import logging
import json
import hashlib
from typing import Dict, Any, List, Union, Optional, Tuple

from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError

# ロガーの設定
logger = logging.getLogger(__name__)

# Config
from ..config import get_settings

class DeepInfraService:
    """
    Deep Infraのオープンai互換APIと通信するためのサービス。
    gemma-3-27b-itのようなマルチモーダルモデルを使用した画像分析を処理する。
    モデルIDを動的に設定可能。
    """

    def __init__(self, model_id: str = None, model_version: str = None):
        """
        環境変数から設定を読み込み、非同期OpenAIクライアントを初期化する。

        Args:
            model_id: 使用するモデルID。Noneの場合はデフォルトを使用。
            model_version: モデルのバージョンID。指定された場合MODEL:VERSION形式でpin。
        """
        # 設定を読み込み
        from ..config import get_settings
        self.settings = get_settings()

        # API keyの取得（環境変数から）
        api_key = os.getenv("DEEPINFRA_API_KEY")
        if not api_key:
            raise ValueError("Deep Infra API keyが設定されていません。環境変数 'DEEPINFRA_API_KEY' を設定してください。")

        # モデルIDの決定
        base_model = model_id or os.getenv("DEEPINFRA_MODEL_ID", "Qwen/Qwen3-VL-30B-A3B-Thinking")
        # バージョンpin機能：MODEL:VERSION形式で固定
        self.model_id = f"{base_model}:{model_version}" if model_version else base_model

        base_url = os.getenv("DEEPINFRA_BASE_URL", "https://api.deepinfra.com/v1/openai")

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
        image_mime_type: str = "image/jpeg",
        prompt: str = "Describe what you see in this image.",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        return_usage: bool = False
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        画像を分析してJSON形式で結果を返す

        Args:
            image_bytes: 画像データ（バイト列）
            image_mime_type: 画像のMIMEタイプ（例: "image/jpeg", "image/png"）
            prompt: VLMへのプロンプト
            max_tokens: 最大出力トークン数（Noneの場合は config から取得）
            temperature: ランダム性制御（Noneの場合は config から取得）
            seed: 再現性のためのシード値（Noneの場合は config から取得）
            thinking_budget: Thinkingモデルの推論トークン数の上限（Noneの場合は config から取得）
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
        if thinking_budget is None:
            thinking_budget = settings.DEFAULT_THINKING_BUDGET

        logger.info(f"🔧 VLM Parameters: max_tokens={max_tokens}, temperature={temperature}, seed={seed}, thinking_budget={thinking_budget}")

        # Base64エンコード
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # 画像のハッシュ値を計算（キャッシュキー用）
        image_hash = hashlib.sha256(image_bytes).hexdigest()

        try:
            logger.info(f"🖼️  Analyzing image with DeepInfra VLM (model: {self.model_id})")
            logger.info(f"   Prompt length: {len(prompt)} chars")
            logger.info(f"   Image size: {len(image_bytes)} bytes")
            logger.info(f"   Image hash: {image_hash[:16]}...")

            # メッセージ構築
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

            # API呼び出し
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                seed=seed,
                extra_body={"thinking_budget": thinking_budget} if thinking_budget else {}
            )

            # 応答が空でないかチェック
            if not response.choices or not response.choices[0].message.content:
                logger.error("❌ API response is empty or invalid.")
                logger.error(f"Response object: {response}")
                raise ValueError(f"[DeepInfra Service] Empty or invalid API response. Response: {response}")

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

            # JSONの妥当性を検証（JSONクリーニング処理を追加）
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

                # 1. <think>...</think> タグの除去（Gemini等のThinking出力対応）
                import re
                # <think>タグとその内容を除去
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

                # 3. trailing commaの除去（JSON仕様違反）
                # オブジェクトや配列の末尾のカンマを削除
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
                    
                    # 完全なJSONをファイルに保存（デバッグ用）
                    debug_file = f"/tmp/debug_json_error_{image_hash[:8]}.txt"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    logger.error(f"Full JSON content saved to: {debug_file}")

                    # JSONパース失敗時は例外を発生させる
                    raise ValueError(
                        f"[DeepInfra Service] Failed to parse JSON response after cleaning attempts. "
                        f"Error: {e2}. Debug file saved to: {debug_file}"
                    ) from e2

            # return_usageがTrueの場合はusage情報も返す
            if return_usage:
                return raw_json_content, usage_dict
            return raw_json_content

        except (RateLimitError, APIConnectionError) as e:
            logger.error(f"API communication error (retriable): {e}", exc_info=True)
            # TODO: ここに指数バックオフ付きのリトライロジックを実装することを推奨
            raise Exception(f"APIとの通信に一時的な問題が発生しました: {e}") from e
        except APIError as e:
            logger.error(f"A non-retriable API error occurred: {e}", exc_info=True)
            raise Exception(f"APIエラーが発生しました: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during image analysis: {e}", exc_info=True)
            raise 

    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = "Qwen/Qwen3-Embedding-8B"
    ) -> List[List[float]]:
        """
        テキストのembeddingを生成（DeepInfra API使用）

        Args:
            texts: embedding生成対象のテキストリスト
            model: 使用するembeddingモデル

        Returns:
            embedding vector のリスト
        """
        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=model,
                encoding_format="float"  # DeepInfra requires 'float'
            )

            # embeddingを抽出
            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def rerank(
        self,
        query: str,
        documents: List[str],
        model: str = "Qwen/Qwen3-Reranker-8B",
        top_n: Optional[int] = None
    ) -> Tuple[int, List[float]]:
        """
        文書をリランキング（DeepInfra API使用）

        Args:
            query: クエリテキスト
            documents: リランキング対象の文書リスト
            model: 使用するrerankingモデル
            top_n: 上位何件を返すか（Noneの場合は全件）

        Returns:
            (best_index, scores)のタプル
            - best_index: 最高スコアのインデックス
            - scores: 全文書のスコアリスト
        """
        try:
            # DeepInfra Reranker API エンドポイント
            import httpx

            api_key = os.getenv("DEEPINFRA_API_KEY") or os.getenv("DEEPINFRA_TOKEN")
            url = f"https://api.deepinfra.com/v1/inference/{model}"

            async with httpx.AsyncClient() as client:
                # 正しいフォーマット: queries は list
                payload = {
                    "queries": [query],  # list形式
                    "documents": documents
                }
                if top_n is not None:
                    payload["top_n"] = top_n

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                result = response.json()

                # Extract scores (scoresフィールドから直接取得)
                scores = result.get("scores", [])
                if not scores:
                    logger.error(f"No scores returned from reranker API. Response: {result}")
                    raise ValueError(f"[DeepInfra Service] Reranker API returned no scores. Response: {result}")

                best_idx = scores.index(max(scores)) if scores else 0

                return best_idx, scores

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            raise
