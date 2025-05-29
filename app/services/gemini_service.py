import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig, HarmCategory, HarmBlockThreshold
from typing import Dict, Optional
import json
import logging
from PIL import Image
import io

# 新しいスキーマをインポート
from ..api.v1.schemas.meal import PHASE_1_GEMINI_SCHEMA, PHASE_2_GEMINI_SCHEMA, MEAL_ANALYSIS_GEMINI_SCHEMA, REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA
from ..prompts import PromptLoader

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
    """Vertex AI経由でGeminiを使用して食事画像を分析するクラス (v2.1対応)"""
    
    def __init__(self, project_id: str, location: str, model_name: str = "gemini-2.5-flash-preview-05-20"):
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
        
        # プロンプトローダーの初期化（必須）
        self.prompt_loader = PromptLoader()
        
        # セーフティ設定
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

    async def analyze_image_phase1(
        self,
        image_bytes: bytes,
        image_mime_type: str,
        optional_text: Optional[str] = None
    ) -> Dict:
        """
        Phase 1: 画像を分析し、料理・食材とUSDAクエリ候補を抽出 (v2.1仕様)
        """
        try:
            system_prompt = self.prompt_loader.get_phase1_system_prompt()
            user_prompt = self.prompt_loader.get_phase1_user_prompt(optional_text)
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            contents = [Part.from_text(full_prompt), Part.from_data(data=image_bytes, mime_type=image_mime_type)]

            generation_config = GenerationConfig(
                temperature=0.3, # 候補を広げるために少し上げることも検討
                top_p=0.9,
                top_k=20,
                max_output_tokens=16384, # トークン制限を増やす
                response_mime_type="application/json",
                # NEW: Phase 1 用のスキーマを使用
                response_schema=PHASE_1_GEMINI_SCHEMA
            )

            response = await self.model.generate_content_async(
                contents=contents,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )

            if not response.text:
                raise ValueError("No response returned from Gemini (Phase 1).")

            result = json.loads(response.text)
            logger.info(f"Gemini Phase 1 analysis completed. Found {len(result.get('dishes', []))} dishes.")
            return result

        except Exception as e:
            logger.error(f"Vertex AI/Gemini API error (Phase 1): {e}")
            raise RuntimeError(f"Vertex AI/Gemini (Phase 1) API request failed: {e}") from e

    async def refine_analysis_phase2(
        self,
        image_bytes: bytes,
        image_mime_type: str,
        phase1_output_text: str, # Phase 1 の生 JSON 出力
        usda_results_text: str # 整形された全 USDA 検索結果
    ) -> Dict:
        """
        Phase 2: USDA候補に基づき、calculation_strategy を決定し、FDC ID を選択 (v2.1仕様)
        """
        try:
            system_prompt = self.prompt_loader.get_phase2_system_prompt()
            user_prompt = self.prompt_loader.get_phase2_user_prompt(
                initial_ai_output=phase1_output_text,
                usda_candidates=usda_results_text
            )
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            contents = [Part.from_text(full_prompt), Part.from_data(data=image_bytes, mime_type=image_mime_type)]

            generation_config = GenerationConfig(
                temperature=0.1, # 決定論的な出力を目指すため低めに設定
                top_p=0.8,
                top_k=10,
                max_output_tokens=16384, # トークン制限を増やす
                response_mime_type="application/json",
                # NEW: Phase 2 用のスキーマを使用
                response_schema=PHASE_2_GEMINI_SCHEMA
            )

            response = await self.model.generate_content_async(
                contents=contents,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )

            if not response.text:
                raise ValueError("No response returned from Gemini (Phase 2).")

            result = json.loads(response.text)
            logger.info(f"Gemini Phase 2 analysis completed. Processed {len(result.get('dishes', []))} dishes.")
            return result

        except Exception as e:
            logger.error(f"Vertex AI/Gemini API error (Phase 2): {e}")
            raise RuntimeError(f"Vertex AI/Gemini (Phase 2) API request failed: {e}") from e

    # 後方互換性のために既存メソッドも保持
    async def analyze_image_and_text(
        self, 
        image_bytes: bytes, 
        image_mime_type: str, 
        optional_text: Optional[str] = None
    ) -> Dict:
        """
        後方互換性のための既存メソッド（既存のPhase 1として動作）
        """
        try:
            # プロンプトローダーからプロンプトを取得
            system_prompt = self.prompt_loader.get_phase1_system_prompt()
            user_prompt = self.prompt_loader.get_phase1_user_prompt(optional_text)
            
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
            
            # 後方互換性のため既存スキーマを使用
            generation_config = GenerationConfig(
                temperature=0.2,
                top_p=0.9,
                top_k=20,
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_schema=MEAL_ANALYSIS_GEMINI_SCHEMA
            )
            
            # Gemini APIを呼び出し（非同期メソッドを使用）
            response = await self.model.generate_content_async(
                contents=contents,
                generation_config=generation_config,
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
        後方互換性のための既存メソッド（既存のPhase 2として動作）
        """
        try:
            # プロンプトローダーからプロンプトを取得
            system_prompt = self.prompt_loader.get_phase2_system_prompt()
            user_prompt = self.prompt_loader.get_phase2_user_prompt(
                initial_ai_output=initial_ai_output_text or "{}",
                usda_candidates=usda_candidates_text
            )
            
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
                raise ValueError("No response returned from Gemini Phase 2.")
            
            # JSONレスポンスをパース
            result = json.loads(response.text)
            
            logger.info(f"Gemini Phase 2 refinement completed successfully. Processed {len(result.get('dishes', []))} dishes.")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in Phase 2: {e}")
            raise RuntimeError(f"Error processing Phase 2 response from Gemini: {e}") from e
        except Exception as e:
            logger.error(f"Vertex AI/Gemini API error in Phase 2: {e}")
            raise RuntimeError(f"Vertex AI/Gemini Phase 2 API request failed: {e}") from e


def get_gemini_analyzer(project_id: str, location: str, model_name: str) -> GeminiMealAnalyzer:
    """GeminiMealAnalyzerのインスタンスを作成して返す"""
    return GeminiMealAnalyzer(project_id=project_id, location=location, model_name=model_name) 