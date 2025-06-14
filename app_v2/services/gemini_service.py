import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig, HarmCategory, HarmBlockThreshold
from typing import Dict, Optional
import json
import logging
from PIL import Image
import io

from ..config.prompts import Phase1Prompts

logger = logging.getLogger(__name__)

# Phase1用JSONスキーマ
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
                    "ingredients": {
                        "type": "array",
                        "description": "この料理に含まれると推定される材料のリスト。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ingredient_name": {"type": "string", "description": "材料の名称。"}
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

# 新しい構造化出力スキーマ
STRUCTURED_MEAL_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "detected_food_items": {
            "type": "array",
            "description": "認識された食品アイテムのリスト（構造化）。",
            "items": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string", "description": "食品名（主要な候補）"},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "食品名の信頼度スコア"},
                    "attributes": {
                        "type": "array",
                        "description": "食品の属性リスト（材料、調理法など）",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string", 
                                    "enum": ["ingredient", "preparation", "color", "texture", "cooking_method", "serving_style", "allergen"],
                                    "description": "属性のタイプ"
                                },
                                "value": {"type": "string", "description": "属性の値"},
                                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "この属性の信頼度スコア"}
                            },
                            "required": ["type", "value", "confidence"]
                        }
                    },
                    "brand": {"type": "string", "description": "認識されたブランド名（該当する場合、nullの場合は空文字列）"},
                    "category_hints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "推定される食品カテゴリ"
                    },
                    "negative_cues": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "画像から判断できる「含まれない」要素"
                    }
                },
                "required": ["item_name", "confidence", "attributes"]
            }
        },
        "dishes": {
            "type": "array",
            "description": "従来互換性のための料理リスト",
            "items": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "料理名"},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "料理特定の信頼度"},
                    "ingredients": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ingredient_name": {"type": "string", "description": "食材名"},
                                "weight_g": {"type": "number", "minimum": 0.1, "description": "写真から推定される食材の重量（グラム）"},
                                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "食材特定の信頼度"},
                                "attributes": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string", "description": "属性タイプ"},
                                            "value": {"type": "string", "description": "属性値"},
                                            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                                        },
                                        "required": ["type", "value", "confidence"]
                                    }
                                }
                            },
                            "required": ["ingredient_name", "weight_g"]
                        }
                    },
                    "attributes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "value": {"type": "string"},
                                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                            },
                            "required": ["type", "value", "confidence"]
                        }
                    }
                },
                "required": ["dish_name", "ingredients"]
            }
        },
        "analysis_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "全体的な分析の信頼度"}
    },
    "required": ["detected_food_items", "dishes", "analysis_confidence"]
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
        
        # generation_configを作成 (Phase1用 - 従来版)
        self.generation_config = GenerationConfig(
            temperature=0.0,  # 完全にdeterministicに
            top_p=1.0,       # nucleus samplingを無効化
            top_k=1,         # 最も確率の高い選択肢のみ
            max_output_tokens=8192,
            candidate_count=1,  # レスポンス候補を1つに制限
            response_mime_type="application/json",
            response_schema=MEAL_ANALYSIS_GEMINI_SCHEMA
        )
        
        # 構造化分析用のgeneration_config
        self.structured_generation_config = GenerationConfig(
            temperature=0.1,  # わずかな変動を許可（より詳細な分析のため）
            top_p=0.95,
            top_k=40,
            max_output_tokens=16384,  # より多くの出力を許可
            candidate_count=1,
            response_mime_type="application/json",
            response_schema=STRUCTURED_MEAL_ANALYSIS_SCHEMA
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
        Phase1: 画像とテキストを分析して食事情報を抽出（従来版）
        
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
    
    async def analyze_phase1_structured(
        self, 
        image_bytes: bytes, 
        image_mime_type: str, 
        optional_text: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """
        Phase1: 構造化された詳細な画像分析（信頼度スコア、属性、ブランド情報等を含む）
        
        Args:
            image_bytes: 画像のバイトデータ
            image_mime_type: 画像のMIMEタイプ
            optional_text: オプションのテキスト説明
            system_prompt: カスタムシステムプロンプト（指定されない場合はデフォルト使用）
            
        Returns:
            構造化された分析結果の辞書
            
        Raises:
            RuntimeError: Gemini APIエラー時
        """
        try:
            # プロンプトを準備
            if system_prompt is None:
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
            
            logger.info("Starting structured Gemini Phase1 analysis...")
            
            # Gemini APIを呼び出し（構造化設定使用）
            response = await self.model.generate_content_async(
                contents=contents,
                generation_config=self.structured_generation_config,
                safety_settings=self.safety_settings
            )
            
            # レスポンスのテキストを取得
            if not response.text:
                raise ValueError("No response returned from Gemini structured analysis.")
            
            # JSONレスポンスをパース
            result = json.loads(response.text)
            
            # 結果の検証と修正
            result = self._validate_and_fix_structured_result(result)
            
            detected_items_count = len(result.get('detected_food_items', []))
            dishes_count = len(result.get('dishes', []))
            overall_confidence = result.get('analysis_confidence', 0.5)
            
            logger.info(f"Gemini Phase1 structured analysis completed: {detected_items_count} items, "
                       f"{dishes_count} dishes, confidence {overall_confidence:.2f}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in structured analysis: {e}")
            raise RuntimeError(f"Error processing structured response from Gemini: {e}") from e
        except Exception as e:
            logger.error(f"Vertex AI/Gemini structured API error: {e}")
            raise RuntimeError(f"Vertex AI/Gemini structured API request failed: {e}") from e
    
    def _validate_and_fix_structured_result(self, result: Dict) -> Dict:
        """構造化分析結果を検証し、必要に応じて修正"""
        # detected_food_itemsが存在しない場合の処理
        if 'detected_food_items' not in result:
            result['detected_food_items'] = []
        
        # dishesが存在しない場合の処理
        if 'dishes' not in result:
            result['dishes'] = []
        
        # analysis_confidenceが存在しない場合の処理
        if 'analysis_confidence' not in result:
            # 各アイテムの平均信頼度を計算
            confidences = []
            for item in result['detected_food_items']:
                if 'confidence' in item:
                    confidences.append(item['confidence'])
            
            for dish in result['dishes']:
                if 'confidence' in dish and dish['confidence'] is not None:
                    confidences.append(dish['confidence'])
            
            result['analysis_confidence'] = sum(confidences) / len(confidences) if confidences else 0.5
        
        # 各detected_food_itemの検証
        for item in result['detected_food_items']:
            # 必須フィールドのデフォルト値設定
            if 'confidence' not in item:
                item['confidence'] = 0.5
            if 'attributes' not in item:
                item['attributes'] = []
            if 'category_hints' not in item:
                item['category_hints'] = []
            if 'negative_cues' not in item:
                item['negative_cues'] = []
            
            # 属性の検証
            for attr in item['attributes']:
                if 'confidence' not in attr:
                    attr['confidence'] = 0.5
                if 'type' not in attr:
                    attr['type'] = 'ingredient'
        
        return result
    
 