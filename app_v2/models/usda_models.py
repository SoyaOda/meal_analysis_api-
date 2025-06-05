from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class USDANutrient(BaseModel):
    """USDA栄養素情報モデル"""
    name: str = Field(..., description="栄養素名")
    amount: float = Field(..., description="100gまたは100mlあたりの量")
    unit_name: str = Field(..., description="単位名 (例: g, mg, kcal)")
    nutrient_id: Optional[int] = Field(None, description="USDA栄養素ID")
    nutrient_number: Optional[str] = Field(None, description="USDA栄養素番号")


class USDAMatch(BaseModel):
    """USDA照合結果モデル"""
    fdc_id: int = Field(..., description="USDA FoodData Central ID")
    description: str = Field(..., description="食品の公式名称")
    data_type: Optional[str] = Field(None, description="USDAデータタイプ (例: SR Legacy, Branded)")
    brand_owner: Optional[str] = Field(None, description="ブランド所有者 (Branded Foodsの場合)")
    ingredients_text: Optional[str] = Field(None, description="原材料リスト文字列 (Branded Foodsの場合)")
    food_nutrients: List[USDANutrient] = Field(default_factory=list, description="主要な栄養素情報のリスト")
    score: Optional[float] = Field(None, description="検索結果の関連度スコア")
    original_usda_data: Optional[Dict] = Field(None, description="USDA APIからのオリジナルJSONデータ")


class USDAQueryInput(BaseModel):
    """USDAクエリコンポーネントの入力モデル"""
    ingredient_names: List[str] = Field(..., description="検索する食材名のリスト")
    dish_names: List[str] = Field(default_factory=list, description="検索する料理名のリスト")
    search_options: Optional[Dict] = Field(None, description="検索オプション")

    def get_all_search_terms(self) -> List[str]:
        """全ての検索用語を取得"""
        return list(set(self.ingredient_names + self.dish_names))


class USDAQueryOutput(BaseModel):
    """USDAクエリコンポーネントの出力モデル"""
    matches: Dict[str, USDAMatch] = Field(default_factory=dict, description="検索語彙とマッチした結果のマップ")
    search_summary: Dict[str, int] = Field(default_factory=dict, description="検索サマリー（成功数、失敗数など）")
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