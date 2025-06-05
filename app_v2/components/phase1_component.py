import json
from typing import Optional

from .base import BaseComponent
from ..models.phase1_models import Phase1Input, Phase1Output, Dish, Ingredient
from ..services.gemini_service import GeminiService
from ..config import get_settings
from ..config.prompts import Phase1Prompts


class Phase1Component(BaseComponent[Phase1Input, Phase1Output]):
    """
    Phase1: 画像分析コンポーネント（USDA検索特化）
    
    Gemini AIを使用して食事画像を分析し、USDA検索に適した料理と食材名を識別します。
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
        Phase1の主処理: 画像分析（USDA検索特化）
        
        Args:
            input_data: Phase1Input (image_bytes, image_mime_type, optional_text)
            
        Returns:
            Phase1Output: 分析結果（料理名・食材名のみ）
        """
        self.logger.info(f"Starting Phase1 image analysis for USDA query generation")
        
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
                        ingredient_name=ingredient_data["ingredient_name"]
                    )
                    ingredients.append(ingredient)
                    
                    # 食材識別の推論理由をログ
                    self.log_reasoning(
                        f"ingredient_identification_dish{dish_index}_ingredient{ingredient_index}",
                        f"Identified ingredient '{ingredient_data['ingredient_name']}' for USDA search based on visual analysis",
                        confidence=0.8
                    )
                
                dish = Dish(
                    dish_name=dish_data["dish_name"],
                    ingredients=ingredients
                )
                dishes.append(dish)
                
                # 料理識別の推論理由をログ
                self.log_reasoning(
                    f"dish_identification_{dish_index}",
                    f"Identified dish as '{dish_data['dish_name']}' for USDA search based on visual characteristics",
                    confidence=0.85
                )
            
            # 分析統計の記録
            self.log_processing_detail("detected_dishes_count", len(dishes))
            self.log_processing_detail("total_ingredients_count", sum(len(dish.ingredients) for dish in dishes))
            
            # USDA検索適合性チェック
            search_terms = []
            for dish in dishes:
                search_terms.append(dish.dish_name)
                for ingredient in dish.ingredients:
                    search_terms.append(ingredient.ingredient_name)
            
            self.log_processing_detail("usda_search_terms", search_terms)
            self.log_reasoning(
                "usda_search_preparation",
                f"Generated {len(search_terms)} search terms for USDA database queries",
                confidence=0.9
            )
            
            result = Phase1Output(
                dishes=dishes,
                warnings=[]
            )
            
            self.logger.info(f"Phase1 completed: identified {len(dishes)} dishes with {len(search_terms)} total search terms")
            return result
            
        except Exception as e:
            self.logger.error(f"Phase1 processing failed: {str(e)}")
            raise 