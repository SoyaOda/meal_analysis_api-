import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig, HarmCategory, HarmBlockThreshold
from typing import Dict, Optional
import json
import logging
from PIL import Image
import io

from ..config.prompts import Phase1Prompts, Phase2Prompts

logger = logging.getLogger(__name__)

# Geminiの構造化出力のためのJSONスキーマを定義（USDA検索特化）
MEAL_ANALYSIS_GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "dishes": {
            "type": "array",
            "description": "画像から特定された料理のリスト（USDA検索用）。",
            "items": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "特定された料理の名称（USDA検索で使用される）。"},
                    "ingredients": {
                        "type": "array",
                        "description": "この料理に含まれると推定される材料のリスト（USDA検索用）。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ingredient_name": {"type": "string", "description": "材料の名称（USDA検索で使用される）。"}
                            },
                            "required": ["ingredient_name"]
                        }
                    }
                },
                "required": ["dish_name", "ingredients"]
            }
        }
    },
    "required": ["dishes"]
}

REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "dishes": {
            "type": "array",
            "description": "画像から特定・精緻化された料理/食品アイテムのリスト。",
            "items": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "特定された料理/食品アイテムの名称。"},
                    "type": {"type": "string", "description": "料理の種類（例: 主菜, 副菜, 単品食品）。"},
                    "quantity_on_plate": {"type": "string", "description": "皿の上の量。"},
                    "calculation_strategy": {
                        "type": "string",
                        "enum": ["dish_level", "ingredient_level"],
                        "description": "このアイテムの栄養計算方針。"
                    },
                    "fdc_id": {
                        "type": "integer",
                        "description": "calculation_strategyが'dish_level'の場合、この料理/食品アイテム全体のFDC ID。それ以外はnull。"
                    },
                    "usda_source_description": {
                        "type": "string",
                        "description": "calculation_strategyが'dish_level'の場合、この料理/食品アイテム全体のUSDA公式名称。それ以外はnull。"
                    },
                    "ingredients": {
                        "type": "array",
                        "description": "この料理/食品アイテムに含まれると推定される材料のリスト。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ingredient_name": {"type": "string", "description": "材料の名称。"},
                                "fdc_id": {
                                    "type": "integer",
                                    "description": "calculation_strategyが'ingredient_level'の場合、この材料のFDC ID。それ以外はnullまたは省略可。"
                                },
                                "usda_source_description": {
                                    "type": "string",
                                    "description": "calculation_strategyが'ingredient_level'の場合、この材料のUSDA公式名称。それ以外はnullまたは省略可。"
                                }
                            },
                            "required": ["ingredient_name"]
                        }
                    }
                },
                "required": ["dish_name", "type", "quantity_on_plate", "calculation_strategy", "ingredients"]
            }
        }
    },
    "required": ["dishes"]
}


class GeminiService:
    """Vertex AI経由でGeminiを使用して食事画像を分析するサービスクラス"""
    
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
        
        # generation_configを作成 (Phase1用 - 出力安定化)
        self.generation_config = GenerationConfig(
            temperature=0.0,  # 完全にdeterministicに
            top_p=1.0,       # nucleus samplingを無効化
            top_k=1,         # 最も確率の高い選択肢のみ
            max_output_tokens=8192,
            candidate_count=1,  # レスポンス候補を1つに制限
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
    
    async def analyze_phase1(
        self, 
        image_bytes: bytes, 
        image_mime_type: str, 
        optional_text: Optional[str] = None
    ) -> Dict:
        """
        Phase1: 画像とテキストを分析して食事情報を抽出
        
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
            # プロンプトを取得
            system_prompt = Phase1Prompts.get_system_prompt()
            user_prompt = Phase1Prompts.get_user_prompt(optional_text)
            
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
            
            # Gemini APIを呼び出し
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
            
            logger.info(f"Gemini Phase1 analysis completed successfully. Found {len(result.get('dishes', []))} dishes.")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise RuntimeError(f"Error processing response from Gemini: {e}") from e
        except Exception as e:
            logger.error(f"Vertex AI/Gemini API error: {e}")
            raise RuntimeError(f"Vertex AI/Gemini API request failed: {e}") from e
    
    async def analyze_phase2(
        self,
        image_bytes: bytes,
        image_mime_type: str,
        usda_candidates_text: str,
        initial_analysis_data: str
    ) -> Dict:
        """
        Phase2: USDAコンテキストを使用して画像を再分析
        
        Args:
            image_bytes: 画像のバイトデータ
            image_mime_type: 画像のMIMEタイプ
            usda_candidates_text: USDA候補情報のフォーマット済みテキスト
            initial_analysis_data: Phase1のAI出力（JSON文字列）
            
        Returns:
            精緻化された分析結果の辞書
            
        Raises:
            RuntimeError: Gemini APIエラー時
        """
        try:
            # プロンプトを取得
            system_prompt = Phase2Prompts.get_system_prompt()
            user_prompt = Phase2Prompts.get_user_prompt(
                usda_candidates_text=usda_candidates_text,
                initial_analysis_data=initial_analysis_data
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
            
            # Phase2用のGeneration Config (出力安定化)
            phase2_generation_config = GenerationConfig(
                temperature=0.0,  # 完全にdeterministicに
                top_p=1.0,       # nucleus samplingを無効化
                top_k=1,         # 最も確率の高い選択肢のみ
                max_output_tokens=8192,
                candidate_count=1,  # レスポンス候補を1つに制限
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
                raise ValueError("No response returned from Gemini.")
            
            # JSONレスポンスをパース
            result = json.loads(response.text)
            
            logger.info(f"Gemini Phase2 analysis completed successfully. Found {len(result.get('dishes', []))} dishes.")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise RuntimeError(f"Error processing response from Gemini: {e}") from e
        except Exception as e:
            logger.error(f"Vertex AI/Gemini API error: {e}")
            raise RuntimeError(f"Vertex AI/Gemini API request failed: {e}") from e 