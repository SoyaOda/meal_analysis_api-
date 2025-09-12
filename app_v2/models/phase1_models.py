from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class AttributeType(str, Enum):
    """属性タイプの列挙"""
    INGREDIENT = "ingredient"
    PREPARATION = "preparation"
    COLOR = "color"
    TEXTURE = "texture"
    COOKING_METHOD = "cooking_method"
    SERVING_STYLE = "serving_style"
    ALLERGEN = "allergen"


class FoodAttribute(BaseModel):
    """食品属性モデル（材料、調理法など）"""
    type: AttributeType = Field(..., description="属性のタイプ")
    value: str = Field(..., description="属性の値")
    confidence: float = Field(..., ge=0.0, le=1.0, description="この属性の信頼度スコア")


class DetectedFoodItem(BaseModel):
    """検出された食品アイテム（構造化）"""
    item_name: str = Field(..., description="食品名（主要な候補）")
    confidence: float = Field(..., ge=0.0, le=1.0, description="食品名の信頼度スコア")
    attributes: List[FoodAttribute] = Field(default=[], description="食品の属性リスト（材料、調理法など）")
    brand: Optional[str] = Field(None, description="認識されたブランド名（該当する場合）")
    category_hints: List[str] = Field(default=[], description="推定される食品カテゴリ")
    negative_cues: List[str] = Field(default=[], description="画像から判断できる「含まれない」要素")


class Ingredient(BaseModel):
    """食材情報モデル（栄養データベース検索用・従来互換性）"""
    ingredient_name: str = Field(..., description="食材の名称（栄養データベース検索で使用）")
    weight_g: float = Field(..., gt=0, description="写真から推定される食材の重量（グラム）")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="食材特定の信頼度")
    detected_attributes: List[FoodAttribute] = Field(default=[], description="この食材に関連する属性")


class Dish(BaseModel):
    """料理情報モデル（栄養データベース検索用・従来互換性）"""
    dish_name: str = Field(..., description="特定された料理の名称（栄養データベース検索で使用）")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="料理特定の信頼度")
    ingredients: List[Ingredient] = Field(..., description="その料理に含まれる食材のリスト")
    detected_attributes: List[FoodAttribute] = Field(default=[], description="この料理に関連する属性")


class Phase1Input(BaseModel):
    """Phase1コンポーネントの入力モデル"""
    image_bytes: bytes = Field(..., description="画像データ（バイト形式）")
    image_mime_type: str = Field(..., description="画像のMIMEタイプ")
    optional_text: Optional[str] = Field(None, description="オプションのテキスト情報")
    model_id: Optional[str] = Field(None, description="DeepInfra Model ID（指定されない場合はデフォルト使用）")

    class Config:
        arbitrary_types_allowed = True
        protected_namespaces = ()


class Phase1Output(BaseModel):
    """Phase1コンポーネントの出力モデル（構造化・拡張版）"""
    # 新しい構造化出力
    detected_food_items: List[DetectedFoodItem] = Field(default=[], description="認識された食品アイテムのリスト（構造化）")
    
    # 従来互換性のための出力
    dishes: List[Dish] = Field(..., description="画像から特定された料理のリスト")
    
    # メタデータ
    analysis_confidence: float = Field(..., ge=0.0, le=1.0, description="全体的な分析の信頼度")
    processing_notes: List[str] = Field(default=[], description="処理に関する注記")
    warnings: Optional[List[str]] = Field(None, description="処理中の警告メッセージ")

    def get_all_ingredient_names(self) -> List[str]:
        """全ての食材名のリストを取得（栄養データベース検索用・従来互換性）"""
        ingredient_names = []
        for dish in self.dishes:
            for ingredient in dish.ingredients:
                ingredient_names.append(ingredient.ingredient_name)
        return ingredient_names

    def get_all_dish_names(self) -> List[str]:
        """全ての料理名のリストを取得（栄養データベース検索用・従来互換性）"""
        return [dish.dish_name for dish in self.dishes]
    
    def get_structured_search_terms(self) -> Dict[str, Any]:
        """構造化された検索用語を取得（新しい検索戦略用）"""
        return {
            "high_confidence_items": [
                {
                    "item_name": item.item_name,
                    "confidence": item.confidence,
                    "brand": item.brand
                }
                for item in self.detected_food_items 
                if item.confidence >= 0.8
            ],
            "medium_confidence_items": [
                {
                    "item_name": item.item_name,
                    "confidence": item.confidence,
                    "brand": item.brand
                }
                for item in self.detected_food_items 
                if 0.5 <= item.confidence < 0.8
            ],
            "brands": [
                item.brand for item in self.detected_food_items 
                if item.brand is not None and item.brand != ""
            ],
            "ingredients": [
                attr.value for item in self.detected_food_items 
                for attr in item.attributes 
                if attr.type == AttributeType.INGREDIENT
            ],
            "cooking_methods": [
                attr.value for item in self.detected_food_items 
                for attr in item.attributes 
                if attr.type == AttributeType.PREPARATION
            ],
            "negative_cues": [
                cue for item in self.detected_food_items 
                for cue in item.negative_cues
            ]
        }
    
    def get_primary_search_terms(self) -> List[str]:
        """プライマリ検索用語を取得（高信頼度アイテム）"""
        primary_terms = []
        
        # 高信頼度の検出アイテム
        for item in self.detected_food_items:
            if item.confidence >= 0.7:
                primary_terms.append(item.item_name)
        
        # フォールバック: 従来の料理名と食材名
        if not primary_terms:
            primary_terms.extend(self.get_all_dish_names())
            primary_terms.extend(self.get_all_ingredient_names())
        
        return primary_terms 