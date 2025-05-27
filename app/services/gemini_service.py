import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig, HarmCategory, HarmBlockThreshold
from typing import Dict, Optional
import json
import logging
from PIL import Image
import io

from ..api.v1.schemas.meal import REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA

logger = logging.getLogger(__name__)

# Geminiの構造化出力のためのJSONスキーマを定義
MEAL_ANALYSIS_GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "dishes": {
            "type": "array",
            "description": "画像から特定された料理のリスト。",
            "items": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "特定された料理の名称。"},
                    "type": {"type": "string", "description": "料理の種類（例: 主菜, 副菜, スープ, デザート）。"},
                    "quantity_on_plate": {"type": "string", "description": "皿の上に載っている料理のおおよその量や個数（例: '1杯', '2切れ', '約200g'）。"},
                    "ingredients": {
                        "type": "array",
                        "description": "この料理に含まれると推定される材料のリスト。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ingredient_name": {"type": "string", "description": "材料の名称。"},
                                "weight_g": {"type": "number", "description": "その材料の推定重量（グラム単位）。"}
                            },
                            "required": ["ingredient_name", "weight_g"]
                        }
                    }
                },
                "required": ["dish_name", "type", "quantity_on_plate", "ingredients"]
            }
        }
    },
    "required": ["dishes"]
}


class GeminiMealAnalyzer:
    """Vertex AI経由でGeminiを使用して食事画像を分析するクラス"""
    
    def __init__(self, project_id: str, location: str, model_name: str = "gemini-1.5-flash"):
        """
        初期化
        
        Args:
            project_id: GCPプロジェクトID
            location: Vertex AIのロケーション（例: us-central1）
            model_name: 使用するモデル名
        """
        # Vertex AIの初期化
        vertexai.init(project=project_id, location=location)
        
        # モデルの初期化
        self.model = GenerativeModel(model_name=model_name)
        
        # generation_configを作成
        self.generation_config = GenerationConfig(
            temperature=0.2,
            top_p=0.9,
            top_k=20,
            max_output_tokens=8192,
            response_mime_type="application/json",
            response_schema=MEAL_ANALYSIS_GEMINI_SCHEMA
        )
        
        # セーフティ設定
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    
    async def analyze_image_and_text(
        self, 
        image_bytes: bytes, 
        image_mime_type: str, 
        optional_text: Optional[str] = None
    ) -> Dict:
        """
        画像とテキストを分析して食事情報を抽出
        
        Args:
            image_bytes: 画像のバイトデータ
            image_mime_type: 画像のMIMEタイプ
            optional_text: オプションのテキスト説明
            
        Returns:
            分析結果の辞書
            
        Raises:
            RuntimeError: Gemini APIエラー時
        """
        try:
            # プロンプトの構築
            system_prompt = """You are an experienced culinary analyst. Your task is to analyze meal images and provide a detailed breakdown of dishes and their ingredients in JSON format.

IMPORTANT: You MUST provide ALL responses in English only. This includes dish names, ingredient names, types, and any other text fields.

Please note the following:
1. Carefully observe the image including the plate and make detailed estimates based on surrounding context.
2. Identify all dishes present in the image, determine their types, the quantity of each dish on the plate, and the ingredients contained with their respective amounts.
3. There may be multiple dishes in a single image, so provide information about each dish and its ingredients separately.
4. Your output will be used for nutritional calculations, so ensure your estimates are as accurate as possible.
5. Strictly follow the provided JSON schema in your response.
6. ALL text must be in English (dish names, ingredient names, types, etc.)."""

            # テキストプロンプトの追加
            if optional_text and optional_text.strip():
                user_prompt = f"Please analyze the provided meal image and respond in English. Additional information from user: {optional_text}"
            else:
                user_prompt = "Please analyze the provided meal image and respond in English."
            
            # 完全なプロンプトを構築
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # コンテンツリストを作成
            contents = [
                Part.from_text(full_prompt),
                Part.from_data(
                    data=image_bytes,
                    mime_type=image_mime_type
                )
            ]
            
            # Gemini APIを呼び出し（非同期メソッドを使用）
            response = await self.model.generate_content_async(
                contents=contents,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            # レスポンスのテキストを取得
            if not response.text:
                raise ValueError("No response returned from Gemini.")
            
            # JSONレスポンスをパース
            result = json.loads(response.text)
            
            logger.info(f"Gemini analysis completed successfully. Found {len(result.get('dishes', []))} dishes.")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise RuntimeError(f"Error processing response from Gemini: {e}") from e
        except Exception as e:
            logger.error(f"Vertex AI/Gemini API error: {e}")
            raise RuntimeError(f"Vertex AI/Gemini API request failed: {e}") from e
    
    async def analyze_image_with_usda_context(
        self,
        image_bytes: bytes,
        image_mime_type: str,
        usda_candidates_text: str,
        initial_ai_output_text: Optional[str] = None
    ) -> Dict:
        """
        USDAコンテキストを使用して画像を再分析（フェーズ2）
        
        Args:
            image_bytes: 画像のバイトデータ
            image_mime_type: 画像のMIMEタイプ
            usda_candidates_text: USDA候補情報のフォーマット済みテキスト
            initial_ai_output_text: フェーズ1のAI出力（JSON文字列）
            
        Returns:
            精緻化された分析結果の辞書
            
        Raises:
            RuntimeError: Gemini APIエラー時
        """
        try:
            # フェーズ2用のシステムプロンプト
            system_prompt = """You are an experienced nutritionist and food analysis expert. Comprehensively evaluate the provided meal image, initial AI analysis results, and candidate information from the USDA food database, then refine the initial AI analysis results.

IMPORTANT: You MUST provide ALL responses in English only. This includes dish names, ingredient names, types, and any other text fields.

Your tasks are as follows:
1. For each dish and ingredient included in the initial AI analysis results, select the most appropriate option from the presented USDA food candidates. When making your selection, consider the content of the image, typical uses of ingredients, and the plausibility of nutritional values.
2. Identify the FDC ID of the selected USDA food.
3. Output the final dish/ingredient names, their types, quantities on the plate, and each ingredient (corresponding to the selected USDA food) with its name, estimated weight (in grams), and FDC ID, strictly following the specified JSON schema.
4. If an ingredient from the initial AI analysis results doesn't have appropriate candidates in USDA, or differs significantly from the image, take this into consideration and make the most reasonable judgment.
5. Your output will form the basis for accurate nutritional calculations.
6. ALL text must be in English."""
            
            # プロンプトの構築
            prompt_parts = []
            
            if initial_ai_output_text:
                prompt_parts.append(f"Initial AI analysis results:\n{initial_ai_output_text}\n")
            
            prompt_parts.append(f"USDA food database candidate information for the above analysis results and image:\n{usda_candidates_text}\n")
            prompt_parts.append("Based on this information, generate the final analysis results in JSON format following the system instructions.")
            
            # 完全なプロンプトを構築
            full_prompt = f"{system_prompt}\n\n" + "\n".join(prompt_parts)
            
            # コンテンツリストを作成
            contents = [
                Part.from_text(full_prompt),
                Part.from_data(
                    data=image_bytes,
                    mime_type=image_mime_type
                )
            ]
            
            # フェーズ2用のGeneration Config
            phase2_generation_config = GenerationConfig(
                temperature=0.2,
                top_p=0.9,
                top_k=20,
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_schema=REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA
            )
            
            # Gemini APIを呼び出し
            response = await self.model.generate_content_async(
                contents=contents,
                generation_config=phase2_generation_config,
                safety_settings=self.safety_settings
            )
            
            # レスポンスのテキストを取得
            if not response.text:
                raise ValueError("No response returned from Gemini (Phase 2).")
            
            # JSONレスポンスをパース
            result = json.loads(response.text)
            
            logger.info(f"Gemini phase 2 analysis completed successfully. Found {len(result.get('dishes', []))} dishes.")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in phase 2: {e}. Raw response: {getattr(response, 'text', 'N/A')}")
            raise RuntimeError(f"Error processing response from Gemini (Phase 2): {e}") from e
        except Exception as e:
            import traceback
            logger.error(f"Vertex AI/Gemini API error in phase 2: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(f"Vertex AI/Gemini (Phase 2) API request failed: {e}") from e 