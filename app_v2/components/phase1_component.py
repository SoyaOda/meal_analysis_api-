import json
from typing import Optional

from .base import BaseComponent
from ..models.phase1_models import (
    Phase1Input, Phase1Output, Dish, Ingredient, 
    DetectedFoodItem, FoodAttribute, AttributeType
)
from ..services.gemini_service import GeminiService
from ..config import get_settings
from ..config.prompts import Phase1Prompts


class Phase1Component(BaseComponent[Phase1Input, Phase1Output]):
    """
    Phase1: 画像分析コンポーネント（構造化出力対応・栄養データベース検索特化）
    
    Gemini AIを使用して食事画像を分析し、構造化された詳細情報
    （信頼度スコア、属性、ブランド情報等）を含む栄養データベース検索に適した出力を生成します。
    """
    
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Phase1Component")
        
        # GeminiServiceの初期化
        if gemini_service is None:
            settings = get_settings()
            self.gemini_service = GeminiService(
                project_id=settings.GEMINI_PROJECT_ID,
                location=settings.GEMINI_LOCATION,
                model_name=settings.GEMINI_MODEL_NAME
            )
        else:
            self.gemini_service = gemini_service
    
    async def process(self, input_data: Phase1Input) -> Phase1Output:
        """
        Phase1の主処理: 構造化画像分析（栄養データベース検索特化）
        
        Args:
            input_data: Phase1Input (image_bytes, image_mime_type, optional_text)
            
        Returns:
            Phase1Output: 構造化された分析結果（信頼度スコア、属性、ブランド情報等を含む）
        """
        self.logger.info(f"Starting Phase1 structured image analysis for enhanced nutrition database query generation")
        
        # プロンプト生成と記録（統一されたプロンプトシステム使用）
        system_prompt = Phase1Prompts.get_system_prompt()
        user_prompt = Phase1Prompts.get_user_prompt(input_data.optional_text)
        
        self.log_prompt("structured_system_prompt", system_prompt)
        self.log_prompt("user_prompt", user_prompt, {
            "optional_text": input_data.optional_text,
            "image_mime_type": input_data.image_mime_type
        })
        
        # 画像情報のログ記録
        self.log_processing_detail("image_size_bytes", len(input_data.image_bytes))
        self.log_processing_detail("image_mime_type", input_data.image_mime_type)
        
        try:
            # Gemini AIによる構造化画像分析
            self.log_processing_detail("gemini_structured_api_call_start", "Calling Gemini API for structured image analysis")
            
            gemini_result = await self.gemini_service.analyze_phase1_structured(
                image_bytes=input_data.image_bytes,
                image_mime_type=input_data.image_mime_type,
                optional_text=input_data.optional_text,
                system_prompt=system_prompt
            )
            
            self.log_processing_detail("gemini_structured_response", gemini_result)
            
            # 構造化データを処理
            detected_food_items = []
            if "detected_food_items" in gemini_result:
                for item_index, item_data in enumerate(gemini_result["detected_food_items"]):
                    # 属性を処理
                    attributes = []
                    for attr_data in item_data.get("attributes", []):
                        # AttributeTypeに存在しない場合はPREPARATIONにフォールバック
                        attr_type_str = attr_data.get("type", "ingredient")
                        try:
                            attr_type = AttributeType(attr_type_str)
                        except ValueError:
                            # 未知の属性タイプの場合は最も近い既存タイプにマッピング
                            if attr_type_str in ["cut", "chopped", "sliced", "diced"]:
                                attr_type = AttributeType.PREPARATION
                            elif attr_type_str in ["fresh", "cooked", "raw", "fried", "grilled"]:
                                attr_type = AttributeType.COOKING_METHOD
                            elif attr_type_str in ["sweet", "salty", "spicy", "sour"]:
                                attr_type = AttributeType.TEXTURE
                            else:
                                attr_type = AttributeType.PREPARATION  # デフォルト
                        
                        attribute = FoodAttribute(
                            type=attr_type,
                            value=attr_data["value"],
                            confidence=attr_data.get("confidence", 0.5)
                        )
                        attributes.append(attribute)
                    
                    # DetectedFoodItemを作成
                    detected_item = DetectedFoodItem(
                        item_name=item_data["item_name"],
                        confidence=item_data.get("confidence", 0.5),
                        attributes=attributes,
                        brand=item_data.get("brand"),
                        category_hints=item_data.get("category_hints", []),
                        negative_cues=item_data.get("negative_cues", [])
                    )
                    detected_food_items.append(detected_item)
                    
                    # 構造化アイテム識別の推論理由をログ
                    self.log_reasoning(
                        f"structured_item_identification_{item_index}",
                        f"Structured identification: '{item_data['item_name']}' (confidence: {item_data.get('confidence', 0.5):.2f}, "
                        f"attributes: {len(attributes)}, brand: {item_data.get('brand', 'N/A')})"
                    )
            
            # 従来互換性のためのdishesも生成
            dishes = []
            if "dishes" in gemini_result:
                for dish_index, dish_data in enumerate(gemini_result.get("dishes", [])):
                    ingredients = []
                    for ingredient_index, ingredient_data in enumerate(dish_data.get("ingredients", [])):
                        # 構造化属性を従来形式に変換
                        ingredient_attributes = []
                        if "attributes" in ingredient_data:
                            for attr_data in ingredient_data["attributes"]:
                                # AttributeTypeに存在しない場合の処理
                                attr_type_str = attr_data.get("type", "ingredient")
                                try:
                                    attr_type = AttributeType(attr_type_str)
                                except ValueError:
                                    # 未知の属性タイプの場合はマッピング
                                    if attr_type_str in ["cut", "chopped", "sliced", "diced"]:
                                        attr_type = AttributeType.PREPARATION
                                    elif attr_type_str in ["fresh", "cooked", "raw", "fried", "grilled"]:
                                        attr_type = AttributeType.COOKING_METHOD
                                    elif attr_type_str in ["sweet", "salty", "spicy", "sour"]:
                                        attr_type = AttributeType.TEXTURE
                                    else:
                                        attr_type = AttributeType.PREPARATION
                                
                                attr = FoodAttribute(
                                    type=attr_type,
                                    value=attr_data["value"],
                                    confidence=attr_data.get("confidence", 0.5)
                                )
                                ingredient_attributes.append(attr)
                        
                        # weight_gが必須フィールドなので、存在しない場合はエラー
                        if "weight_g" not in ingredient_data:
                            error_msg = f"Missing required field 'weight_g' for ingredient '{ingredient_data.get('ingredient_name', 'unknown')}'. Gemini must provide weight estimation for all ingredients."
                            self.logger.error(error_msg)
                            raise ValueError(error_msg)
                        
                        ingredient = Ingredient(
                            ingredient_name=ingredient_data["ingredient_name"],
                            weight_g=ingredient_data["weight_g"],
                            confidence=ingredient_data.get("confidence"),
                            detected_attributes=ingredient_attributes
                        )
                        ingredients.append(ingredient)
                    
                    # 料理レベルの属性
                    dish_attributes = []
                    if "attributes" in dish_data:
                        for attr_data in dish_data["attributes"]:
                            # AttributeTypeに存在しない場合の処理
                            attr_type_str = attr_data.get("type", "preparation")
                            try:
                                attr_type = AttributeType(attr_type_str)
                            except ValueError:
                                # 未知の属性タイプの場合はマッピング
                                if attr_type_str in ["cut", "chopped", "sliced", "diced"]:
                                    attr_type = AttributeType.PREPARATION
                                elif attr_type_str in ["fresh", "cooked", "raw", "fried", "grilled"]:
                                    attr_type = AttributeType.COOKING_METHOD
                                elif attr_type_str in ["sweet", "salty", "spicy", "sour"]:
                                    attr_type = AttributeType.TEXTURE
                                else:
                                    attr_type = AttributeType.PREPARATION
                            
                            attr = FoodAttribute(
                                type=attr_type,
                                value=attr_data["value"],
                                confidence=attr_data.get("confidence", 0.5)
                            )
                            dish_attributes.append(attr)
                    
                    dish = Dish(
                        dish_name=dish_data["dish_name"],
                        confidence=dish_data.get("confidence"),
                        ingredients=ingredients,
                        detected_attributes=dish_attributes
                    )
                    dishes.append(dish)
            
            # フォールバック: 構造化データから従来形式を生成
            if not dishes and detected_food_items:
                dishes = self._convert_structured_to_legacy(detected_food_items)
            
            # 分析統計の記録
            self.log_processing_detail("detected_structured_items_count", len(detected_food_items))
            self.log_processing_detail("detected_dishes_count", len(dishes))
            self.log_processing_detail("total_ingredients_count", sum(len(dish.ingredients) for dish in dishes))
            
            # 全体的な分析信頼度を計算
            overall_confidence = self._calculate_overall_confidence(detected_food_items, dishes)
            
            # 処理ノートを生成
            processing_notes = [
                f"Structured analysis generated {len(detected_food_items)} food items",
                f"Overall confidence: {overall_confidence:.2f}",
                f"Legacy compatibility: {len(dishes)} dishes generated"
            ]
            
            result = Phase1Output(
                detected_food_items=detected_food_items,
                dishes=dishes,
                analysis_confidence=overall_confidence,
                processing_notes=processing_notes,
                warnings=[]
            )
            
            self.log_processing_detail("structured_search_terms", result.get_structured_search_terms())
            self.log_reasoning(
                "structured_analysis_completion",
                f"Phase1 structured analysis completed: {len(detected_food_items)} structured items, "
                f"overall confidence {overall_confidence:.2f}"
            )
            
            self.logger.info(f"Phase1 structured analysis completed: {len(detected_food_items)} items, "
                           f"confidence {overall_confidence:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase1 structured processing failed: {str(e)}")
            raise
    

    
    def _convert_structured_to_legacy(self, detected_items: list) -> list:
        """構造化データを従来形式に変換（フォールバック用）"""
        # このメソッドは重量情報が不完全な場合に使用されるため、エラーを発生させる
        error_msg = "Cannot convert structured data to legacy format without weight information. Gemini must provide weight_g for all ingredients in the standard dishes format."
        self.logger.error(error_msg)
        raise ValueError(error_msg)
    
    def _calculate_overall_confidence(self, structured_items: list, dishes: list) -> float:
        """全体的な分析信頼度を計算"""
        if not structured_items and not dishes:
            return 0.0
        
        total_confidence = 0.0
        count = 0
        
        # 構造化アイテムの信頼度
        for item in structured_items:
            total_confidence += item.confidence
            count += 1
        
        # 料理の信頼度
        for dish in dishes:
            if dish.confidence is not None:
                total_confidence += dish.confidence
                count += 1
        
        return total_confidence / count if count > 0 else 0.5 