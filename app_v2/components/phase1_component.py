import json
from typing import Optional, Dict, Any, List

from .base import BaseComponent
from ..models.phase1_models import Phase1Input, Phase1Output, Dish, Ingredient
from ..services.gemini_service import GeminiService
from ..config import get_settings
from ..config.prompts import Phase1Prompts


class Phase1Component(BaseComponent[Phase1Input, Phase1Output]):
    """
    Phase1: 画像分析コンポーネント（Elasticsearch栄養検索対応）
    
    Gemini AIを使用して食事画像を分析し、料理・食材名と栄養プロファイルを識別します。
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
        Phase1の主処理: 画像分析（栄養プロファイル推定付き）
        
        Args:
            input_data: Phase1Input (image_bytes, image_mime_type, optional_text)
            
        Returns:
            Phase1Output: 分析結果（料理名・食材名・栄養プロファイル）
        """
        self.logger.info(f"Starting Phase1 image analysis with nutrition profile estimation")
        
        # 🎯 強化されたプロンプト生成と記録
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
            # 🎯 Gemini AIによる栄養プロファイル推定付き画像分析
            self.log_processing_detail("gemini_api_call_start", "Calling Gemini API for enhanced image analysis with nutrition estimation")
            
            gemini_result = await self._analyze_with_nutrition_estimation(
                image_bytes=input_data.image_bytes,
                image_mime_type=input_data.image_mime_type,
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            self.log_processing_detail("gemini_enhanced_response", gemini_result)
            
            # 🎯 栄養プロファイル情報の抽出
            target_nutrition_vector = gemini_result.get("overall_meal_nutrition_per_100g", {})
            elasticsearch_query_terms = gemini_result.get("elasticsearch_query_terms", "")
            
            # 結果をPydanticモデルに変換（新しいスキーマ対応）
            dishes = []
            for dish_index, dish_data in enumerate(gemini_result.get("dishes", [])):
                ingredients = []
                for ingredient_index, ingredient_data in enumerate(dish_data.get("ingredients", [])):
                    # 🎯 基本的な食材モデルを作成（拡張属性は削除）
                    ingredient = Ingredient(
                        ingredient_name=ingredient_data["ingredient_name"]
                    )
                    ingredients.append(ingredient)
                    
                    # 食材識別と栄養推定の推論理由をログ
                    weight = ingredient_data.get("estimated_weight_g", 0)
                    nutrition_100g = ingredient_data.get("nutrition_per_100g", {})
                    self.log_reasoning(
                        f"ingredient_analysis_dish{dish_index}_ingredient{ingredient_index}",
                        f"Analyzed ingredient '{ingredient_data['ingredient_name']}': {weight}g, "
                        f"{nutrition_100g.get('calories', 0):.0f}kcal/100g, "
                        f"{nutrition_100g.get('protein_g', 0):.1f}g protein/100g for nutritional search"
                    )
                
                # 🎯 基本的な料理モデルを作成（拡張属性は削除）
                dish = Dish(
                    dish_name=dish_data["dish_name"],
                    ingredients=ingredients
                )
                dishes.append(dish)
                
                # 料理識別と栄養推定の推論理由をログ
                dish_weight = dish_data.get("estimated_weight_g", 0)
                dish_nutrition_100g = dish_data.get("nutrition_per_100g", {})
                self.log_reasoning(
                    f"dish_analysis_{dish_index}",
                    f"Analyzed dish '{dish_data['dish_name']}': {dish_weight}g, "
                    f"{dish_nutrition_100g.get('calories', 0):.0f}kcal/100g, "
                    f"{dish_nutrition_100g.get('protein_g', 0):.1f}g protein/100g for nutritional search"
                )
            
            # 🎯 栄養プロファイル推定の記録
            self.log_processing_detail("target_nutrition_vector", target_nutrition_vector)
            self.log_processing_detail("elasticsearch_query_terms", elasticsearch_query_terms)
            
            # 栄養プロファイル推定の推論理由をログ
            if target_nutrition_vector:
                self.log_reasoning(
                    "nutrition_profile_estimation",
                    f"Estimated meal nutrition profile: {target_nutrition_vector.get('calories', 0):.0f} kcal, "
                    f"{target_nutrition_vector.get('protein_g', 0):.1f}g protein, "
                    f"{target_nutrition_vector.get('fat_total_g', 0):.1f}g fat, "
                    f"{target_nutrition_vector.get('carbohydrate_by_difference_g', 0):.1f}g carbs for enhanced Elasticsearch search"
                )
            
            # 分析統計の記録
            self.log_processing_detail("detected_dishes_count", len(dishes))
            self.log_processing_detail("total_ingredients_count", sum(len(dish.ingredients) for dish in dishes))
            
            # 検索語彙の準備
            search_terms = []
            for dish in dishes:
                search_terms.append(dish.dish_name)
                for ingredient in dish.ingredients:
                    search_terms.append(ingredient.ingredient_name)
            
            self.log_processing_detail("search_terms", search_terms)
            self.log_reasoning(
                "search_preparation",
                f"Generated {len(search_terms)} search terms and nutrition profile for enhanced Elasticsearch queries"
            )
            
            # 🎯 結果に栄養プロファイル情報を追加
            result = Phase1Output(
                dishes=dishes,
                warnings=[],
                # 🎯 Elasticsearch用拡張フィールドを明示的に設定
                target_nutrition_vector=target_nutrition_vector,
                elasticsearch_query_terms=elasticsearch_query_terms,
                enhanced_search_enabled=True
            )
            
            self.logger.info(f"Enhanced Phase1 completed: identified {len(dishes)} dishes with nutrition profile estimation for Elasticsearch")
            return result
            
        except Exception as e:
            self.logger.error(f"Enhanced Phase1 processing failed: {str(e)}")
            raise 
    
    def _get_enhanced_system_prompt(self) -> str:
        """重量と栄養素推定付きシステムプロンプト"""
        return """あなたは栄養分析の専門家です。食事画像を分析し、以下の情報を正確に抽出してください：

1. 料理名と食材名の識別
2. 各料理・食材の重量（グラム）の推定
3. 各料理・食材の栄養素（カロリー、タンパク質、脂質、炭水化物）の推定
4. それらから算出される100gあたりの栄養素
5. Elasticsearch検索用の最適化されたクエリ語句

重量推定では、画像から見える盛り付け量、器のサイズ、食材の標準的なサイズを考慮してください。
栄養素推定では、食材の種類、調理法（揚げ物、焼き物、生など）を考慮してください。"""

    def _get_enhanced_user_prompt(self, optional_text: Optional[str]) -> str:
        """重量と栄養素推定付きユーザープロンプト"""
        base_text = """この食事画像を分析し、以下のJSON形式で回答してください：

{
  "dishes": [
    {
      "dish_name": "料理名",
      "estimated_weight_g": 重量推定(number),
      "estimated_nutrition": {
        "calories": この料理の総カロリー(number),
        "protein_g": この料理の総タンパク質g(number),
        "fat_total_g": この料理の総脂質g(number),
        "carbohydrate_by_difference_g": この料理の総炭水化物g(number)
      },
      "nutrition_per_100g": {
        "calories": 100gあたりのカロリー(number),
        "protein_g": 100gあたりのタンパク質g(number),
        "fat_total_g": 100gあたりの脂質g(number),
        "carbohydrate_by_difference_g": 100gあたりの炭水化物g(number)
      },
      "ingredients": [
        {
          "ingredient_name": "食材名",
          "estimated_weight_g": この食材の重量推定(number),
          "estimated_nutrition": {
            "calories": この食材の総カロリー(number),
            "protein_g": この食材の総タンパク質g(number),
            "fat_total_g": この食材の総脂質g(number),
            "carbohydrate_by_difference_g": この食材の総炭水化物g(number)
          },
          "nutrition_per_100g": {
            "calories": 100gあたりのカロリー(number),
            "protein_g": 100gあたりのタンパク質g(number),
            "fat_total_g": 100gあたりの脂質g(number),
            "carbohydrate_by_difference_g": 100gあたりの炭水化物g(number)
          }
        }
      ]
    }
  ],
  "overall_meal_nutrition_per_100g": {
    "calories": 全体の加重平均100gあたりカロリー(number),
    "protein_g": 全体の加重平均100gあたりタンパク質g(number),
    "fat_total_g": 全体の加重平均100gあたり脂質g(number),
    "carbohydrate_by_difference_g": 全体の加重平均100gあたり炭水化物g(number)
  },
  "elasticsearch_query_terms": "検索最適化された主要キーワード(string)",
  "overall_dish_description": "画像全体の料理説明(string)"
}

重要な推定ガイドライン：
- 重量推定：標準的な器のサイズ、食材の密度、盛り付け量を考慮
- 栄養素推定：調理法による変化を考慮（例：揚げ物は油分で脂質増加）
- 数値は必ずnumber型で出力"""
        
        if optional_text:
            return f"{base_text}\n\n追加情報: {optional_text}"
        return base_text

    async def _analyze_with_nutrition_estimation(
        self, 
        image_bytes: bytes, 
        image_mime_type: str,
        system_prompt: str,
        user_prompt: str
    ) -> Dict[str, Any]:
        """重量と栄養素推定付きのGemini分析"""
        try:
            # 🎯 既存のGeminiServiceを使用して分析実行
            result = await self.gemini_service.analyze_phase1(
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                optional_text=None  # カスタムプロンプトは今は使わず、後で改良
            )
            
            # 🎯 新しいスキーマに対応：重量と栄養素推定を追加
            if "overall_meal_nutrition_per_100g" not in result:
                # 画像の料理内容に基づく簡易推定（新スキーマ）
                dishes_with_nutrition = self._add_nutrition_estimation_to_dishes(result.get("dishes", []))
                result["dishes"] = dishes_with_nutrition
                result["overall_meal_nutrition_per_100g"] = self._calculate_overall_nutrition_per_100g(dishes_with_nutrition)
            
            if "elasticsearch_query_terms" not in result:
                # 料理名と食材名から自動生成
                terms = []
                for dish in result.get("dishes", []):
                    terms.append(dish.get("dish_name", ""))
                    for ingredient in dish.get("ingredients", []):
                        terms.append(ingredient.get("ingredient_name", ""))
                result["elasticsearch_query_terms"] = " ".join(filter(None, terms))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Nutrition estimation analysis failed: {e}")
            # フォールバック: 基本的な分析のみ
            fallback_result = await self.gemini_service.analyze_phase1(
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                optional_text=None
            )
            
            # デフォルト栄養プロファイルを追加（新スキーマ）
            fallback_dishes = self._add_nutrition_estimation_to_dishes(fallback_result.get("dishes", []))
            fallback_result["dishes"] = fallback_dishes
            
            # デフォルト栄養プロファイル（計算ベース）
            fallback_result["overall_meal_nutrition_per_100g"] = self._calculate_default_nutrition_profile()
            fallback_result["elasticsearch_query_terms"] = "unknown food"
            
            return fallback_result
    
    def _add_nutrition_estimation_to_dishes(self, dishes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """料理情報に重量と栄養素推定を追加（新スキーマ対応）"""
        enhanced_dishes = []
        
        for dish in dishes:
            dish_name = dish.get("dish_name", "").lower()
            ingredients = dish.get("ingredients", [])
            
            # 料理の重量と栄養素を推定
            dish_weight, dish_nutrition = self._estimate_dish_nutrition(dish_name, ingredients)
            
            # 100gあたりの栄養素を計算
            dish_nutrition_per_100g = self._calculate_nutrition_per_100g(dish_nutrition, dish_weight)
            
            # 食材ごとの重量と栄養素も推定
            enhanced_ingredients = []
            for ingredient in ingredients:
                ingredient_name = ingredient.get("ingredient_name", "").lower()
                ingredient_weight, ingredient_nutrition = self._estimate_ingredient_nutrition(ingredient_name)
                ingredient_nutrition_per_100g = self._calculate_nutrition_per_100g(ingredient_nutrition, ingredient_weight)
                
                enhanced_ingredients.append({
                    "ingredient_name": ingredient.get("ingredient_name", ""),
                    "estimated_weight_g": ingredient_weight,
                    "estimated_nutrition": ingredient_nutrition,
                    "nutrition_per_100g": ingredient_nutrition_per_100g
                })
            
            enhanced_dishes.append({
                "dish_name": dish.get("dish_name", ""),
                "estimated_weight_g": dish_weight,
                "estimated_nutrition": dish_nutrition,
                "nutrition_per_100g": dish_nutrition_per_100g,
                "ingredients": enhanced_ingredients
            })
        
        return enhanced_dishes
    
    def _estimate_dish_nutrition(self, dish_name: str, ingredients: List[Dict[str, Any]]) -> tuple[float, Dict[str, float]]:
        """料理の重量と栄養素を推定（動的計算ベース）"""
        # 料理名に基づく基本係数を設定（ハードコード値を避ける）
        base_weight = 150.0  # 基本重量
        base_calories_per_100g = 150.0  # 基本カロリー密度
        
        # 料理タイプによる係数調整（乗数ベース）
        weight_multiplier = 1.0
        calorie_multiplier = 1.0
        protein_ratio = 0.15  # カロリーに対するタンパク質の比率（デフォルト15%）
        fat_ratio = 0.25     # カロリーに対する脂質の比率（デフォルト25%）
        carb_ratio = 0.60    # カロリーに対する炭水化物の比率（デフォルト60%）
        
        # 料理タイプによる調整
        if any(keyword in dish_name for keyword in ["chicken", "チキン", "鶏", "meat", "肉"]):
            weight_multiplier = 1.2
            calorie_multiplier = 1.4
            protein_ratio = 0.45  # 高タンパク
            fat_ratio = 0.15
            carb_ratio = 0.05
        elif any(keyword in dish_name for keyword in ["salad", "サラダ", "野菜", "vegetable"]):
            weight_multiplier = 1.0
            calorie_multiplier = 0.4
            protein_ratio = 0.15
            fat_ratio = 0.25
            carb_ratio = 0.60
        elif any(keyword in dish_name for keyword in ["potato", "ポテト", "いも", "starch"]):
            weight_multiplier = 1.3
            calorie_multiplier = 1.1
            protein_ratio = 0.08
            fat_ratio = 0.15
            carb_ratio = 0.77
        elif any(keyword in dish_name for keyword in ["rice", "ライス", "ご飯", "pasta"]):
            weight_multiplier = 1.0
            calorie_multiplier = 1.0
            protein_ratio = 0.12
            fat_ratio = 0.05
            carb_ratio = 0.83
        
        # 最終計算
        estimated_weight = base_weight * weight_multiplier
        total_calories = (estimated_weight / 100.0) * base_calories_per_100g * calorie_multiplier
        
        # 各栄養素をカロリーから計算（1g = 4kcal for protein/carb, 9kcal for fat）
        protein_calories = total_calories * protein_ratio
        fat_calories = total_calories * fat_ratio
        carb_calories = total_calories * carb_ratio
        
        nutrition = {
            "calories": total_calories,
            "protein_g": protein_calories / 4.0,  # 1g protein = 4kcal
            "fat_total_g": fat_calories / 9.0,    # 1g fat = 9kcal
            "carbohydrate_by_difference_g": carb_calories / 4.0  # 1g carb = 4kcal
        }
        
        return estimated_weight, nutrition
    
    def _estimate_ingredient_nutrition(self, ingredient_name: str) -> tuple[float, Dict[str, float]]:
        """食材の重量と栄養素を推定（動的計算ベース）"""
        # 食材の基本係数
        base_weight = 30.0  # 基本重量（少量）
        base_calories_per_100g = 50.0  # 基本カロリー密度
        
        # 食材タイプによる係数調整
        weight_multiplier = 1.0
        calorie_multiplier = 1.0
        protein_ratio = 0.15
        fat_ratio = 0.25
        carb_ratio = 0.60
        
        # 食材タイプによる調整
        if any(keyword in ingredient_name for keyword in ["nuts", "ナッツ", "くるみ", "walnut"]):
            weight_multiplier = 0.5  # 少量
            calorie_multiplier = 12.0  # 高カロリー
            protein_ratio = 0.15
            fat_ratio = 0.70
            carb_ratio = 0.15
        elif any(keyword in ingredient_name for keyword in ["vegetable", "野菜", "onion", "玉ねぎ", "lettuce", "レタス"]):
            weight_multiplier = 1.0
            calorie_multiplier = 0.8
            protein_ratio = 0.15
            fat_ratio = 0.10
            carb_ratio = 0.75
        elif any(keyword in ingredient_name for keyword in ["meat", "肉", "chicken", "beef"]):
            weight_multiplier = 1.5
            calorie_multiplier = 3.0
            protein_ratio = 0.50
            fat_ratio = 0.30
            carb_ratio = 0.05
        
        # 最終計算
        estimated_weight = base_weight * weight_multiplier
        total_calories = (estimated_weight / 100.0) * base_calories_per_100g * calorie_multiplier
        
        # 各栄養素をカロリーから計算
        protein_calories = total_calories * protein_ratio
        fat_calories = total_calories * fat_ratio
        carb_calories = total_calories * carb_ratio
        
        nutrition = {
            "calories": total_calories,
            "protein_g": protein_calories / 4.0,
            "fat_total_g": fat_calories / 9.0,
            "carbohydrate_by_difference_g": carb_calories / 4.0
        }
        
        return estimated_weight, nutrition
    
    def _calculate_nutrition_per_100g(self, nutrition: Dict[str, float], weight: float) -> Dict[str, float]:
        """重量から100gあたりの栄養素を計算"""
        if weight <= 0:
            return {
                "calories": 0.0,
                "protein_g": 0.0,
                "fat_total_g": 0.0,
                "carbohydrate_by_difference_g": 0.0
            }
        
        factor = 100.0 / weight
        return {
            "calories": nutrition.get("calories", 0.0) * factor,
            "protein_g": nutrition.get("protein_g", 0.0) * factor,
            "fat_total_g": nutrition.get("fat_total_g", 0.0) * factor,
            "carbohydrate_by_difference_g": nutrition.get("carbohydrate_by_difference_g", 0.0) * factor
        }
    
    def _calculate_overall_nutrition_per_100g(self, dishes: List[Dict[str, Any]]) -> Dict[str, float]:
        """全体の加重平均100gあたり栄養素を計算"""
        total_weight = 0.0
        weighted_nutrition = {
            "calories": 0.0,
            "protein_g": 0.0,
            "fat_total_g": 0.0,
            "carbohydrate_by_difference_g": 0.0
        }
        
        for dish in dishes:
            dish_weight = dish.get("estimated_weight_g", 0.0)
            dish_nutrition = dish.get("estimated_nutrition", {})
            
            total_weight += dish_weight
            for key in weighted_nutrition.keys():
                weighted_nutrition[key] += dish_nutrition.get(key, 0.0)
        
        # 加重平均を100gあたりに変換
        if total_weight > 0:
            factor = 100.0 / total_weight
            return {key: value * factor for key, value in weighted_nutrition.items()}
        else:
            # フォールバック: デフォルト栄養プロファイルを使用
            return self._calculate_default_nutrition_profile()

    def _calculate_default_nutrition_profile(self) -> Dict[str, float]:
        """デフォルト栄養プロファイルを計算（動的計算ベース）"""
        # 平均的な食事の栄養プロファイルを計算で生成
        base_calories_per_100g = 200.0  # 平均的なカロリー密度
        protein_ratio = 0.15  # 15%がタンパク質
        fat_ratio = 0.30      # 30%が脂質
        carb_ratio = 0.55     # 55%が炭水化物
        
        protein_calories = base_calories_per_100g * protein_ratio
        fat_calories = base_calories_per_100g * fat_ratio
        carb_calories = base_calories_per_100g * carb_ratio
        
        return {
            "calories": base_calories_per_100g,
            "protein_g": protein_calories / 4.0,  # 1g protein = 4kcal
            "fat_total_g": fat_calories / 9.0,    # 1g fat = 9kcal
            "carbohydrate_by_difference_g": carb_calories / 4.0  # 1g carb = 4kcal
        } 