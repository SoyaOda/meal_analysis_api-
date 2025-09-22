"""
DeepInfra LLMを使用したNLU（自然言語理解）サービス

音声認識されたテキストから料理名・食材名・重量を抽出する機能を提供します。
"""
import os
import json
import logging
import httpx
from typing import Dict, Any, Optional

from ..config.settings import get_settings
from ..config.prompts import VoicePrompts

logger = logging.getLogger(__name__)


class NLUService:
    """DeepInfra LLMを使用した食品抽出サービス"""

    def __init__(self, model_id: Optional[str] = None):
        """
        NLUサービスの初期化

        Args:
            model_id: 使用するモデルID（指定しない場合は設定ファイルのデフォルト）
        """
        self.settings = get_settings()

        # DeepInfra API設定
        self.api_key = os.getenv("DEEPINFRA_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPINFRA_API_KEY environment variable is required")

        # モデルIDの決定
        self.model_id = model_id or self.settings.DEEPINFRA_MODEL_ID
        self.base_url = "https://api.deepinfra.com/v1/inference"

        logger.info(f"NLU Service initialized with model: {self.model_id}")

    async def extract_foods_from_text(
        self, 
        text: str, 
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        テキストから料理・食材・量を抽出してJSON構造を返す

        Args:
            text: 音声認識されたテキスト
            model_id: 使用するモデルID（オプション）
            temperature: AI推論のランダム性制御 (0.0-1.0, デフォルト: 0.0)
            seed: 再現性のためのシード値（オプション）

        Returns:
            抽出された食事情報のJSON構造

        Raises:
            RuntimeError: LLM処理が失敗した場合
        """
        effective_model = model_id or self.model_id
        effective_temperature = temperature if temperature is not None else 0.0
        
        logger.info(f"Extracting food information from text using model: {effective_model}")
        logger.info(f"Input text: '{text[:200]}{'...' if len(text) > 200 else ''}'")
        
        if temperature is not None:
            logger.info(f"Using temperature: {effective_temperature}, seed: {seed}")

        try:
            # プロンプトを構築
            system_prompt = self._build_system_prompt()
            user_prompt = text

            # DeepInfra APIエンドポイント
            url = f"{self.base_url}/{effective_model}"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # APIリクエストペイロード
            payload = {
                "input": f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:",
                "max_tokens": 1024,
                "temperature": effective_temperature,
                "top_p": 0.9,
                "stream": False
            }
            
            # seedパラメータがある場合は追加
            if seed is not None:
                payload["seed"] = seed

            # HTTPクライアントでAPI呼び出し
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Calling DeepInfra API: {url}")
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                result_data = response.json()
                logger.info(f"DeepInfra API response received")

            # レスポンスからテキストを抽出
            if "results" in result_data and len(result_data["results"]) > 0:
                generated_text = result_data["results"][0]["generated_text"]
            elif "output" in result_data:
                generated_text = result_data["output"]
            else:
                logger.error(f"Unexpected API response format: {result_data}")
                raise RuntimeError("Invalid API response format")

            logger.info(f"LLM generated text: '{generated_text[:300]}{'...' if len(generated_text) > 300 else ''}'")

            # JSONパース
            try:
                # JSONの開始と終了を検出
                json_start = generated_text.find('{')
                json_end = generated_text.rfind('}') + 1

                if json_start == -1 or json_end == 0:
                    raise ValueError("No JSON structure found in response")

                json_text = generated_text[json_start:json_end]
                result_json = json.loads(json_text)

                logger.info(f"Successfully parsed JSON response with {len(result_json.get('dishes', []))} dishes")
                return result_json

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse LLM output as JSON: {e}")
                logger.error(f"Raw output: {generated_text}")

                # フォールバック：簡単な構造を生成
                fallback_result = self._create_fallback_result(text)
                logger.warning(f"Using fallback result: {fallback_result}")
                return fallback_result

        except httpx.TimeoutException:
            logger.error("DeepInfra API request timed out")
            raise RuntimeError("LLM service request timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepInfra API HTTP error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"LLM service error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error during food extraction: {e}")
            raise RuntimeError(f"Food extraction failed: {e}") from e

    def _build_system_prompt(self, use_mynetdiary_constraint: bool = True) -> str:
        """
        食品抽出用のシステムプロンプトを構築

        Args:
            use_mynetdiary_constraint: MyNetDiary制約を使用するかどうか

        Returns:
            システムプロンプト文字列
        """
        return VoicePrompts.get_complete_prompt(
            use_mynetdiary_constraint=use_mynetdiary_constraint,
            include_examples=True
        )

    def _create_fallback_result(self, text: str) -> Dict[str, Any]:
        """JSONパースが失敗した場合のフォールバック結果を作成"""
        # VoicePromptsクラスから統一されたフォールバック食品リストを取得
        common_foods = VoicePrompts.get_fallback_foods()

        detected_foods = []
        text_lower = text.lower()

        for food, weight in common_foods.items():
            if food in text_lower:
                detected_foods.append({
                    "ingredient_name": food.rstrip('s'),  # Remove plural 's'
                    "weight_g": float(weight)
                })

        if not detected_foods:
            # 最低限の結果を生成
            detected_foods = [{
                "ingredient_name": "unknown food",
                "weight_g": 100.0
            }]

        return {
            "dishes": [{
                "dish_name": "Meal from voice input",
                "confidence": 0.5,
                "ingredients": detected_foods
            }]
        }