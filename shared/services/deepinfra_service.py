# app_v2/services/deepinfra_service.py

import os
import base64
import logging
import json
import hashlib
from typing import Dict, Any, List, Union, Optional, Tuple

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
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        return_usage: bool = False,
        thinking_budget: Optional[int] = None
    ) -> Any:
        """
        画像とプロンプトをDeep Infraに送信し、分析結果をJSONとして受け取る。

        Args:
            image_bytes: 分析対象の画像のバイトデータ。
            image_mime_type: 画像のMIMEタイプ (例: 'image/jpeg')。
            prompt: モデルに与える指示プロンプト。
            max_tokens: 生成される最大トークン数。Noneの場合、config設定値を使用。
            temperature: 生成のランダム性を制御する値。Noneの場合、config設定値を使用。
            seed: 再現性のためのシード値。Noneの場合、config設定値を使用。
            return_usage: Trueの場合、(content, usage)のタプルを返す。
            thinking_budget: Thinkingモデルの推論トークン数の上限。Noneの場合、config設定値を使用。

        Returns:
            return_usage=False: モデルからのJSONレスポンス文字列。
            return_usage=True: (JSONレスポンス文字列, usage辞書)のタプル。

        Raises:
            ValueError: レスポンスが不正な場合に発生。
            Exception: Deep Infra APIとの通信でエラーが発生した場合に発生。
        """
        # config からデフォルト値を取得
        settings = get_settings()
        if max_tokens is None:
            max_tokens = settings.VLM_MAX_TOKENS
        if temperature is None:
            temperature = settings.VLM_TEMPERATURE
        if seed is None:
            seed = settings.VLM_SEED
        if thinking_budget is None:
            thinking_budget = settings.VLM_THINKING_BUDGET

        logger.info(f"Starting image analysis with model {self.model_id}.")

        # 入力完全一致の検証ハッシュをログ出力
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        logger.info(f"[input_digest] model={self.model_id} image_sha256={image_hash} prompt_sha256={prompt_hash} temp={temperature} seed={seed}")

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

        # Thinkingモデル検出（モデル名に"Thinking"が含まれる場合）
        is_thinking_model = "thinking" in self.model_id.lower()

        if is_thinking_model:
            logger.info(f"Detected Thinking model: {self.model_id}. Disabling response_format to allow thinking tags.")

            # Thinkingモデルの推奨設定: temperature=0.6 (greedy decodingは性能低下を引き起こす)
            if temperature == 0.0:
                logger.warning(f"Thinking model with temperature=0.0 detected. Overriding to recommended value 0.6 to prevent performance degradation.")
                temperature = 0.6

        try:
            # API呼び出しパラメータを構築
            api_params = {
                "model": self.model_id,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "seed": seed,
            }

            # Thinkingモデルの場合、推奨パラメータを設定
            if is_thinking_model:
                api_params["top_p"] = 0.95
                logger.info(f"Using recommended Thinking model parameters: temperature={temperature}, top_p=0.95, top_k=20")
            else:
                api_params["top_p"] = 1.0

            # Thinkingモデルの場合、thinking_budgetを設定
            if is_thinking_model:
                # extra_bodyでthinking_budget、enable_thinking、top_kを渡す
                api_params["extra_body"] = {
                    "enable_thinking": True,
                    "thinking_budget": thinking_budget,
                    "top_k": 20
                }
                logger.info(f"Thinking model: thinking_budget={thinking_budget}, max_tokens={max_tokens}")
                logger.info(f"API params extra_body: {api_params.get('extra_body')}")
            else:
                # Thinkingモデルでない場合のみJSON強制モードを有効化
                api_params["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**api_params)

            # レスポンスの詳細をログ出力
            logger.info(f"API Response received. Choices count: {len(response.choices) if response.choices else 0}")
            if response.choices and len(response.choices) > 0:
                logger.info(f"First choice finish_reason: {response.choices[0].finish_reason}")

                # Thinkingモデルの場合、reasoning_contentをチェック
                if is_thinking_model:
                    reasoning_content = getattr(response.choices[0].message, 'reasoning_content', None)
                    if reasoning_content:
                        logger.info(f"Reasoning content length: {len(reasoning_content)}")

                content = response.choices[0].message.content
                logger.info(f"Content length: {len(content) if content else 0}")

                if response.choices[0].finish_reason == 'length':
                    logger.warning(f"⚠️ Response was cut off due to max_tokens limit. Consider increasing max_tokens.")
                    if is_thinking_model and not content:
                        raise ValueError(f"Thinkingモデルが推論に全トークンを使い果たしました。max_tokensを増やしてください。現在: {max_tokens}")

            if not response.choices or not response.choices[0].message.content:
                logger.error("API response is empty or invalid.")
                raise ValueError("APIからのレスポンスが空です。")

            # JSON文字列を取得
            raw_json_content = response.choices[0].message.content

            # usage情報を辞書形式に変換
            usage_dict = None
            if response.usage:
                usage_dict = {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0,
                    "total_tokens": response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
                }

            logger.info(f"Successfully received JSON response from API. Usage: {usage_dict}")

            # Thinkingモデルの場合、<think>...</think>ブロックを除去
            if is_thinking_model:
                import re
                # <think>タグとその中身を削除
                cleaned_content = re.sub(r'<think>.*?</think>', '', raw_json_content, flags=re.DOTALL)
                cleaned_content = cleaned_content.strip()
                
                # タグ削除後の内容をログ出力
                logger.info(f"Removed <think> tags from Thinking model output. Original length: {len(raw_json_content)}, Cleaned length: {len(cleaned_content)}")
                
                raw_json_content = cleaned_content

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
                
                # 1. Markdown コードブロックの除去
                if cleaned_content.startswith("```json"):
                    cleaned_content = cleaned_content[7:]
                if cleaned_content.startswith("```"):
                    cleaned_content = cleaned_content[3:]
                if cleaned_content.endswith("```"):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()
                
                # 2. trailing commaの除去（JSON仕様違反）
                import re
                # オブジェクトや配列の末尾のカンマを削除
                cleaned_content = re.sub(r',(\s*[}\]])', r'\1', cleaned_content)
                
                # 3. 再パース試行
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
                    
                    raise ValueError(f"APIから無効なJSONが返されました: {e2}")

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
            logger.error(f"An unexpected error occurred during API call: {e}", exc_info=True)
            raise ValueError(f"予期せぬエラーが発生しました: {e}") from e 

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
            model: 使用するrerankerモデル
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
                    logger.warning(f"No scores returned from reranker API. Response: {result}")
                    scores = [0.0] * len(documents)

                best_idx = scores.index(max(scores)) if scores else 0

                return best_idx, scores

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            raise
