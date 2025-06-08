from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    """食材情報モデル（USDA検索用）"""
    ingredient_name: str = Field(..., description="食材の名称（USDA検索で使用）")


class Dish(BaseModel):
    """料理情報モデル（USDA検索用）"""
    dish_name: str = Field(..., description="特定された料理の名称（USDA検索で使用）")
    ingredients: List[Ingredient] = Field(..., description="その料理に含まれる食材のリスト")


class Phase1Input(BaseModel):
    """Phase1コンポーネントの入力モデル"""
    image_bytes: bytes = Field(..., description="画像データ（バイト形式）")
    image_mime_type: str = Field(..., description="画像のMIMEタイプ")
    optional_text: Optional[str] = Field(None, description="オプションのテキスト情報")

    class Config:
        arbitrary_types_allowed = True


class Phase1Output(BaseModel):
    """Phase1コンポーネントの出力モデル（USDA検索特化 + Elasticsearch拡張対応）"""
    dishes: List[Dish] = Field(..., description="画像から特定された料理のリスト")
    warnings: Optional[List[str]] = Field(None, description="処理中の警告メッセージ")
    
    # 🎯 Elasticsearch用拡張フィールド（オプショナル）
    target_nutrition_vector: Optional[Dict[str, float]] = Field(None, description="画像全体の栄養プロファイル（100gあたり）")
    elasticsearch_query_terms: Optional[str] = Field(None, description="Elasticsearch検索用の最適化されたクエリ語句")
    enhanced_search_enabled: Optional[bool] = Field(None, description="拡張検索機能が有効かどうか")

    def get_all_ingredient_names(self) -> List[str]:
        """全ての食材名のリストを取得（USDA検索用）"""
        ingredient_names = []
        for dish in self.dishes:
            for ingredient in dish.ingredients:
                ingredient_names.append(ingredient.ingredient_name)
        return ingredient_names

    def get_all_dish_names(self) -> List[str]:
        """全ての料理名のリストを取得（USDA検索用）"""
        return [dish.dish_name for dish in self.dishes] 