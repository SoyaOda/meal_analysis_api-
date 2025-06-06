#!/usr/bin/env python3
"""
Nutrition Search Models

USDA database queryとローカル栄養データベース検索の両方で使用できる汎用的なモデル
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


class NutritionNutrient(BaseModel):
    """栄養素情報モデル（汎用）"""
    name: str = Field(..., description="栄養素名")
    amount: float = Field(..., description="100gまたは100mlあたりの量")
    unit_name: str = Field(..., description="単位名 (例: g, mg, kcal)")
    nutrient_id: Optional[Union[int, str]] = Field(None, description="栄養素ID（USDA IDまたはローカルID）")
    nutrient_number: Optional[str] = Field(None, description="栄養素番号")


class NutritionMatch(BaseModel):
    """栄養データベース照合結果モデル（汎用）"""
    id: Union[int, str] = Field(..., description="食品ID（USDA FDC IDまたはローカルID）")
    description: str = Field(..., description="食品の名称")
    data_type: Optional[str] = Field(None, description="データタイプ (例: SR Legacy, Branded, Local_Dish)")
    source: str = Field(..., description="データソース（'usda_api' または 'local_database'）")
    brand_owner: Optional[str] = Field(None, description="ブランド所有者 (Branded Foodsの場合)")
    ingredients_text: Optional[str] = Field(None, description="原材料リスト文字列")
    nutrients: List[NutritionNutrient] = Field(default_factory=list, description="栄養素情報のリスト")
    score: Optional[float] = Field(None, description="検索結果の関連度スコア")
    original_data: Optional[Dict[str, Any]] = Field(None, description="元のデータベースからのオリジナルデータ")
    
    # USDA互換性のためのプロパティ
    @property
    def fdc_id(self) -> Union[int, str]:
        """USDA互換性のためのfdc_idプロパティ"""
        return self.id
    
    @property 
    def food_nutrients(self) -> List[NutritionNutrient]:
        """USDA互換性のためのfood_nutrientsプロパティ"""
        return self.nutrients
    
    @property
    def original_usda_data(self) -> Optional[Dict[str, Any]]:
        """USDA互換性のためのoriginal_usda_dataプロパティ"""
        return self.original_data


class NutritionQueryInput(BaseModel):
    """栄養検索コンポーネントの入力モデル（汎用）"""
    ingredient_names: List[str] = Field(..., description="検索する食材名のリスト")
    dish_names: List[str] = Field(default_factory=list, description="検索する料理名のリスト")
    search_options: Optional[Dict[str, Any]] = Field(None, description="検索オプション")
    preferred_source: Optional[str] = Field(None, description="優先データソース（'usda_api' または 'local_database'）")

    def get_all_search_terms(self) -> List[str]:
        """全ての検索用語を取得"""
        return list(set(self.ingredient_names + self.dish_names))


class NutritionQueryOutput(BaseModel):
    """栄養検索コンポーネントの出力モデル（汎用）"""
    matches: Dict[str, NutritionMatch] = Field(default_factory=dict, description="検索語彙とマッチした結果のマップ")
    search_summary: Dict[str, Any] = Field(default_factory=dict, description="検索サマリー（成功数、失敗数、検索方法など）")
    warnings: Optional[List[str]] = Field(None, description="処理中の警告メッセージ")
    errors: Optional[List[str]] = Field(None, description="処理中のエラーメッセージ")

    def get_match_rate(self) -> float:
        """照合成功率を計算"""
        total_searches = self.search_summary.get("total_searches", 0)
        successful_matches = self.search_summary.get("successful_matches", 0)
        if total_searches == 0:
            return 0.0
        return successful_matches / total_searches

    def has_match(self, search_term: str) -> bool:
        """指定された検索語彙にマッチがあるかチェック"""
        return search_term in self.matches and self.matches[search_term] is not None
    
    def get_source_summary(self) -> Dict[str, int]:
        """データソース別のマッチ数サマリーを取得"""
        source_counts = {}
        for match in self.matches.values():
            source = match.source
            source_counts[source] = source_counts.get(source, 0) + 1
        return source_counts


# USDA互換性のためのアダプター関数
def convert_usda_query_input_to_nutrition(usda_input) -> NutritionQueryInput:
    """USDAQueryInputをNutritionQueryInputに変換"""
    return NutritionQueryInput(
        ingredient_names=usda_input.ingredient_names,
        dish_names=usda_input.dish_names,
        search_options=usda_input.search_options,
        preferred_source="usda_api"
    )

def convert_nutrition_to_usda_query_output(nutrition_output: NutritionQueryOutput):
    """NutritionQueryOutputをUSDAQueryOutput互換形式に変換"""
    from .usda_models import USDAQueryOutput, USDAMatch, USDANutrient
    
    # USDAMatchに変換
    usda_matches = {}
    for term, nutrition_match in nutrition_output.matches.items():
        usda_nutrients = []
        for nutrient in nutrition_match.nutrients:
            usda_nutrients.append(USDANutrient(
                name=nutrient.name,
                amount=nutrient.amount,
                unit_name=nutrient.unit_name,
                nutrient_id=nutrient.nutrient_id if isinstance(nutrient.nutrient_id, int) else None,
                nutrient_number=nutrient.nutrient_number
            ))
        
        usda_matches[term] = USDAMatch(
            fdc_id=nutrition_match.id if isinstance(nutrition_match.id, int) else 0,
            description=nutrition_match.description,
            data_type=nutrition_match.data_type,
            brand_owner=nutrition_match.brand_owner,
            ingredients_text=nutrition_match.ingredients_text,
            food_nutrients=usda_nutrients,
            score=nutrition_match.score,
            original_usda_data=nutrition_match.original_data
        )
    
    # 数値のみのsearch_summaryを作成（USDA互換性のため）
    numeric_summary = {}
    for key, value in nutrition_output.search_summary.items():
        if isinstance(value, (int, float)):
            numeric_summary[key] = int(value)
        elif key in ["total_searches", "successful_matches", "failed_searches", "match_rate_percent"]:
            try:
                numeric_summary[key] = int(value) if value is not None else 0
            except (ValueError, TypeError):
                numeric_summary[key] = 0
    
    return USDAQueryOutput(
        matches=usda_matches,
        search_summary=numeric_summary,
        warnings=nutrition_output.warnings,
        errors=nutrition_output.errors
    ) 