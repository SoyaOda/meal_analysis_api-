import json
from typing import Optional

from .base import BaseComponent
from ..models.phase1_models import Phase1Input, Phase1Output, Dish, Ingredient
from ..services.gemini_service import GeminiService
from ..config import get_settings
from ..config.prompts import Phase1Prompts


class Phase1Component(BaseComponent[Phase1Input, Phase1Output]):
    """
    Phase1: 画像分析コンポーネント
    
    Gemini AIを使用して食事画像を分析し、料理と食材を識別します。
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
        Phase1の主処理: 画像分析
        
        Args:
            input_data: Phase1Input (image_bytes, image_mime_type, optional_text)
            
        Returns:
            Phase1Output: 分析結果
        """
        self.logger.info(f"Starting Phase1 image analysis")
        
        # プロンプト生成と記録
        system_prompt = Phase1Prompts.get_system_prompt()
        user_prompt = Phase1Prompts.get_user_prompt(input_data.optional_text)
        
        self.log_prompt("system_prompt", system_prompt)
        self.log_prompt("user_prompt", user_prompt, {
            "optional_text": input_data.optional_text,
            "image_mime_type": input_data.image_mime_type
        })
        
        # 画像情報のログ記録
        self.log_processing_detail("image_size_bytes", len(input_data.image_bytes))
        self.log_processing_detail("image_mime_type", input_data.image_mime_type)
        
        try:
            # Gemini AIによる画像分析
            self.log_processing_detail("gemini_api_call_start", "Calling Gemini API for image analysis")
            
            gemini_result = await self.gemini_service.analyze_phase1(
                image_bytes=input_data.image_bytes,
                image_mime_type=input_data.image_mime_type,
                optional_text=input_data.optional_text
            )
            
            self.log_processing_detail("gemini_raw_response", gemini_result)
            
            # 結果をPydanticモデルに変換
            dishes = []
            for dish_index, dish_data in enumerate(gemini_result.get("dishes", [])):
                ingredients = []
                for ingredient_index, ingredient_data in enumerate(dish_data.get("ingredients", [])):
                    ingredient = Ingredient(
                        ingredient_name=ingredient_data["ingredient_name"],
                        weight_g=float(ingredient_data["weight_g"])
                    )
                    ingredients.append(ingredient)
                    
                    # 食材選択の推論理由をログ
                    self.log_reasoning(
                        f"ingredient_selection_dish{dish_index}_ingredient{ingredient_index}",
                        f"Selected ingredient '{ingredient_data['ingredient_name']}' with weight {ingredient_data['weight_g']}g based on visual analysis of the dish",
                        confidence=0.8  # 暫定値
                    )
                
                dish = Dish(
                    dish_name=dish_data["dish_name"],
                    type=dish_data["type"],
                    quantity_on_plate=dish_data["quantity_on_plate"],
                    ingredients=ingredients
                )
                dishes.append(dish)
                
                # 料理選択の推論理由をログ
                self.log_reasoning(
                    f"dish_identification_{dish_index}",
                    f"Identified dish as '{dish_data['dish_name']}' based on visual characteristics, ingredient composition, and presentation style",
                    confidence=0.85  # 暫定値
                )
            
            # 分析の信頼度を計算（簡単な実装）
            confidence = self._calculate_confidence(dishes)
            self.log_confidence_score("overall_analysis_confidence", confidence)
            
            # 分析統計の記録
            self.log_processing_detail("detected_dishes_count", len(dishes))
            self.log_processing_detail("total_ingredients_count", sum(len(dish.ingredients) for dish in dishes))
            
            # 重量妥当性チェック
            for dish_index, dish in enumerate(dishes):
                for ingredient_index, ingredient in enumerate(dish.ingredients):
                    if ingredient.weight_g < 5.0:
                        self.log_warning(f"Very light weight detected for {ingredient.ingredient_name}: {ingredient.weight_g}g")
                    elif ingredient.weight_g > 500.0:
                        self.log_warning(f"Very heavy weight detected for {ingredient.ingredient_name}: {ingredient.weight_g}g")
            
            result = Phase1Output(
                dishes=dishes,
                analysis_confidence=confidence,
                warnings=[]
            )
            
            self.logger.info(f"Phase1 completed: detected {len(dishes)} dishes")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase1 processing failed: {str(e)}")
            raise
    
    def _calculate_confidence(self, dishes: list) -> float:
        """
        分析結果の信頼度を計算
        
        Args:
            dishes: 検出された料理のリスト
            
        Returns:
            信頼度 (0.0-1.0)
        """
        if not dishes:
            self.log_reasoning("confidence_calculation", "No dishes detected, confidence set to 0.0", 0.0)
            return 0.0
        
        # 簡単な信頼度計算
        # - 料理数が適切な範囲にある: +0.3
        # - 各料理に食材が含まれている: +0.4
        # - 食材の重量が妥当: +0.3
        
        confidence = 0.0
        
        # 料理数チェック (1-5皿が適切)
        if 1 <= len(dishes) <= 5:
            confidence += 0.3
            self.log_reasoning("confidence_dish_count", f"Appropriate number of dishes ({len(dishes)}), +0.3 confidence", 0.3)
        else:
            self.log_reasoning("confidence_dish_count", f"Unusual number of dishes ({len(dishes)}), no confidence bonus", 0.0)
        
        # 食材の存在チェック
        total_ingredients = sum(len(dish.ingredients) for dish in dishes)
        if total_ingredients > 0:
            confidence += 0.4
            self.log_reasoning("confidence_ingredients", f"Found {total_ingredients} ingredients, +0.4 confidence", 0.4)
        
        # 重量の妥当性チェック
        valid_weights = 0
        total_weights = 0
        for dish in dishes:
            for ingredient in dish.ingredients:
                total_weights += 1
                # 5g～500gの範囲が妥当
                if 5.0 <= ingredient.weight_g <= 500.0:
                    valid_weights += 1
        
        if total_weights > 0:
            weight_ratio = valid_weights / total_weights
            weight_confidence = 0.3 * weight_ratio
            confidence += weight_confidence
            self.log_reasoning("confidence_weights", f"Weight validity: {valid_weights}/{total_weights} valid, +{weight_confidence:.2f} confidence", weight_confidence)
        
        final_confidence = min(confidence, 1.0)
        self.log_reasoning("final_confidence", f"Total calculated confidence: {final_confidence}", final_confidence)
        
        return final_confidence 