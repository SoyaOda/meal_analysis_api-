"""
Enhanced Phase1コンポーネント
仕様書のフェーズC：Gemini Phase 1プロンプト改良の実装
"""
import json
import logging
from typing import Optional, Dict, Any, List

from .base import BaseComponent
from ..models.phase1_models import Phase1Input, Phase1Output, Dish, Ingredient
from ..services.gemini_service import GeminiService
from ..config import get_settings

logger = logging.getLogger(__name__)


class EnhancedPhase1Component(BaseComponent[Phase1Input, Phase1Output]):
    """
    Enhanced Phase1: Elasticsearch検索特化画像分析コンポーネント
    
    仕様書に基づく構造化JSON出力を生成し、Elasticsearch検索を最適化します。
    """
    
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("EnhancedPhase1Component")
        
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
        Enhanced Phase1の主処理: Elasticsearch検索特化画像分析
        
        仕様書に基づく構造化JSON出力を生成
        """
        self.logger.info("Starting Enhanced Phase1 image analysis for Elasticsearch search optimization")
        
        # 仕様書に基づくプロンプト生成
        system_prompt = self._get_enhanced_system_prompt()
        user_prompt = self._get_enhanced_user_prompt(input_data.optional_text)
        
        self.log_prompt("enhanced_system_prompt", system_prompt)
        self.log_prompt("enhanced_user_prompt", user_prompt, {
            "optional_text": input_data.optional_text,
            "image_mime_type": input_data.image_mime_type
        })
        
        # 画像情報のログ記録
        self.log_processing_detail("image_size_bytes", len(input_data.image_bytes))
        self.log_processing_detail("image_mime_type", input_data.image_mime_type)
        
        try:
            # Enhanced Gemini AI分析
            self.log_processing_detail("enhanced_gemini_api_call_start", "Calling Enhanced Gemini API for structured analysis")
            
            # 構造化JSON出力を要求するGemini呼び出し
            enhanced_result = await self._call_enhanced_gemini_analysis(
                input_data.image_bytes,
                input_data.image_mime_type,
                input_data.optional_text
            )
            
            self.log_processing_detail("enhanced_gemini_raw_response", enhanced_result)
            
            # 仕様書形式のJSON出力を解析
            structured_output = self._parse_enhanced_gemini_output(enhanced_result)
            
            # 従来形式に変換（既存システムとの互換性）
            dishes = self._convert_to_legacy_format(structured_output)
            
            # Elasticsearch検索最適化情報をログ
            self._log_elasticsearch_optimization_details(structured_output)
            
            result = Phase1Output(
                dishes=dishes,
                warnings=[],
                # 拡張情報（仕様書の構造化出力）
                enhanced_output=structured_output
            )
            
            self.logger.info(f"Enhanced Phase1 completed: {len(dishes)} dishes, optimized for Elasticsearch")
            return result
            
        except Exception as e:
            self.logger.error(f"Enhanced Phase1 processing failed: {str(e)}")
            raise
    
    def _get_enhanced_system_prompt(self) -> str:
        """仕様書に基づくシステムプロンプト"""
        return """あなたは食品認識のエキスパートアシスタントです。食事画像を分析し、Elasticsearch検索に最適化された構造化されたJSONオブジェクトを返してください。

あなたの役割：
1. 食事画像から主要な食品アイテムを特定
2. Elasticsearch検索用の最適なキーワードを生成
3. 栄養プロファイル目標値の推定
4. 調理法や状態の詳細な記述

重要な要件：
- 必ず有効なJSON形式で回答してください
- elasticsearch_query_termsは検索効率を最大化するキーワードを選択
- target_nutrition_vectorは画像全体の料理から推定してください
- 日本語と英語の両方の食品名を考慮してください"""
    
    def _get_enhanced_user_prompt(self, optional_text: Optional[str]) -> str:
        """仕様書に基づくユーザープロンプト"""
        base_prompt = """この画像を分析し、以下の構造化されたJSON形式で情報を提供してください：

{
  "elasticsearch_query_terms": "string (Elasticsearch検索用の主要キーワード。例: 'コーンフレーク シリアル いちご')",
  "identified_items": [
    {
      "item_name": "string (認識された食品名。例: 'コーンフレークシリアル')",
      "estimated_quantity_raw": "string (認識された量と単位。例: '1杯', '約100g')",
      "brand": "string or null (認識されたブランド名。例: 'ケロッグ')",
      "attributes": ["string (調理法や状態など。例: '牛乳かけ', '朝食')"]
    }
  ],
  "overall_dish_description": "string (画像全体の料理の説明)",
  "target_nutrition_vector": {
    "calories": float (推定カロリー 例: 350),
    "protein_g": float (推定タンパク質g 例: 8),
    "fat_total_g": float (推定脂質g 例: 5),
    "carbohydrate_by_difference_g": float (推定炭水化物g 例: 70)
  },
  "confidence_level": "High/Medium/Low",
  "analysis_notes": "string (分析時の注意点や補足)"
}"""
        
        if optional_text:
            base_prompt += f"\n\n追加情報: {optional_text}"
        
        return base_prompt
    
    async def _call_enhanced_gemini_analysis(
        self, 
        image_bytes: bytes, 
        image_mime_type: str, 
        optional_text: Optional[str]
    ) -> Dict[str, Any]:
        """Enhanced Gemini API呼び出し"""
        # カスタムプロンプトでGeminiサービスを呼び出し
        try:
            # 現在のGeminiServiceを拡張するか、直接API呼び出しを実装
            # ここでは既存のGeminiServiceを使用し、結果を構造化形式で解析
            raw_result = await self.gemini_service.analyze_phase1(
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                optional_text=optional_text,
                custom_system_prompt=self._get_enhanced_system_prompt(),
                custom_user_prompt=self._get_enhanced_user_prompt(optional_text)
            )
            
            return raw_result
            
        except Exception as e:
            self.logger.error(f"Enhanced Gemini API call failed: {e}")
            raise
    
    def _parse_enhanced_gemini_output(self, gemini_result: Dict[str, Any]) -> Dict[str, Any]:
        """仕様書形式のJSON出力を解析"""
        try:
            # Geminiの出力が既に構造化されている場合はそのまま返す
            if "elasticsearch_query_terms" in gemini_result:
                return gemini_result
            
            # 従来形式から新形式に変換
            structured_output = {
                "elasticsearch_query_terms": "",
                "identified_items": [],
                "overall_dish_description": "",
                "target_nutrition_vector": {
                    "calories": 250.0,
                    "protein_g": 10.0,
                    "fat_total_g": 8.0,
                    "carbohydrate_by_difference_g": 35.0
                },
                "confidence_level": "Medium",
                "analysis_notes": "Converted from legacy format"
            }
            
            # 従来のdishes形式から変換
            if "dishes" in gemini_result:
                dishes = gemini_result["dishes"]
                query_terms = []
                items = []
                
                for dish in dishes:
                    query_terms.append(dish.get("dish_name", ""))
                    
                    # 料理アイテムを追加
                    items.append({
                        "item_name": dish.get("dish_name", ""),
                        "estimated_quantity_raw": "1 serving",
                        "brand": None,
                        "attributes": ["composite dish"]
                    })
                    
                    # 食材アイテムを追加
                    for ingredient in dish.get("ingredients", []):
                        query_terms.append(ingredient.get("ingredient_name", ""))
                        items.append({
                            "item_name": ingredient.get("ingredient_name", ""),
                            "estimated_quantity_raw": "portion",
                            "brand": None,
                            "attributes": ["ingredient"]
                        })
                
                structured_output["elasticsearch_query_terms"] = " ".join(query_terms)
                structured_output["identified_items"] = items
                structured_output["overall_dish_description"] = f"Meal with {len(dishes)} main dish(es)"
            
            return structured_output
            
        except Exception as e:
            self.logger.error(f"Failed to parse enhanced Gemini output: {e}")
            # フォールバック：デフォルト構造を返す
            return {
                "elasticsearch_query_terms": "food meal",
                "identified_items": [],
                "overall_dish_description": "Unable to analyze image",
                "target_nutrition_vector": {
                    "calories": 200.0,
                    "protein_g": 8.0,
                    "fat_total_g": 6.0,
                    "carbohydrate_by_difference_g": 25.0
                },
                "confidence_level": "Low",
                "analysis_notes": f"Parse error: {str(e)}"
            }
    
    def _convert_to_legacy_format(self, structured_output: Dict[str, Any]) -> List[Dish]:
        """構造化出力を従来のDish形式に変換（後方互換性）"""
        dishes = []
        
        try:
            items = structured_output.get("identified_items", [])
            
            # アイテムを料理と食材に分類
            dish_items = [item for item in items if "composite dish" in item.get("attributes", [])]
            ingredient_items = [item for item in items if "ingredient" in item.get("attributes", [])]
            
            if dish_items:
                # 料理ベースの構造
                for dish_item in dish_items:
                    ingredients = []
                    for ingredient_item in ingredient_items:
                        ingredients.append(Ingredient(
                            ingredient_name=ingredient_item["item_name"]
                        ))
                    
                    dishes.append(Dish(
                        dish_name=dish_item["item_name"],
                        ingredients=ingredients
                    ))
            else:
                # 食材のみの場合
                if ingredient_items:
                    ingredients = []
                    for ingredient_item in ingredient_items:
                        ingredients.append(Ingredient(
                            ingredient_name=ingredient_item["item_name"]
                        ))
                    
                    dishes.append(Dish(
                        dish_name="Mixed ingredients",
                        ingredients=ingredients
                    ))
                else:
                    # 汎用アイテムの場合
                    for item in items:
                        dishes.append(Dish(
                            dish_name=item["item_name"],
                            ingredients=[]
                        ))
            
            return dishes
            
        except Exception as e:
            self.logger.error(f"Failed to convert to legacy format: {e}")
            return []
    
    def _log_elasticsearch_optimization_details(self, structured_output: Dict[str, Any]) -> None:
        """Elasticsearch最適化の詳細をログ"""
        self.log_processing_detail("elasticsearch_query_terms", structured_output.get("elasticsearch_query_terms"))
        self.log_processing_detail("identified_items_count", len(structured_output.get("identified_items", [])))
        self.log_processing_detail("target_nutrition_vector", structured_output.get("target_nutrition_vector"))
        self.log_processing_detail("confidence_level", structured_output.get("confidence_level"))
        
        # 検索最適化の推論理由
        self.log_reasoning(
            "elasticsearch_optimization",
            f"Generated optimized search terms: '{structured_output.get('elasticsearch_query_terms')}' "
            f"with {len(structured_output.get('identified_items', []))} food items identified"
        )
        
        # 栄養プロファイル推定の推論理由  
        nutrition_vector = structured_output.get("target_nutrition_vector", {})
        self.log_reasoning(
            "nutrition_profile_estimation",
            f"Estimated nutritional profile: {nutrition_vector.get('calories', 0):.0f} kcal, "
            f"{nutrition_vector.get('protein_g', 0):.1f}g protein, "
            f"{nutrition_vector.get('fat_total_g', 0):.1f}g fat, "
            f"{nutrition_vector.get('carbohydrate_by_difference_g', 0):.1f}g carbs"
        ) 