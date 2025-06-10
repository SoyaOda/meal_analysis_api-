#!/usr/bin/env python3
"""
Nutrition Search Models

ローカル栄養データベース検索で使用する純粋なローカル形式のモデル
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


class NutritionMatch(BaseModel):
    """栄養データベース照合結果モデル（純粋なローカル形式）"""
    id: Union[int, str] = Field(..., description="食品ID（ローカルID）")
    search_name: str = Field(..., description="検索名（簡潔な名称）")
    description: Optional[str] = Field(None, description="詳細説明")
    data_type: str = Field(..., description="データタイプ (dish, ingredient, branded)")
    source: str = Field(default="local_database", description="データソース（'local_database'）")
    
    # ローカルDBの生の栄養データ（100gあたり正規化済み）
    nutrition: Dict[str, float] = Field(default_factory=dict, description="ローカルDBの栄養データ（100gあたり）")
    weight: Optional[float] = Field(None, description="元データの重量（g）")
    
    # 検索スコア
    score: Optional[float] = Field(None, description="検索結果の関連度スコア")
    
    # 検索に関するメタデータ
    search_metadata: Optional[Dict[str, Any]] = Field(None, description="検索に関するメタデータ")


class NutritionQueryInput(BaseModel):
    """栄養データベース検索入力モデル（純粋なローカル形式）"""
    ingredient_names: List[str] = Field(default_factory=list, description="食材名のリスト")
    dish_names: List[str] = Field(default_factory=list, description="料理名のリスト")
    search_options: Optional[Dict[str, Any]] = Field(None, description="検索オプション")
    preferred_source: str = Field(default="local_database", description="優先データソース")

    def get_all_search_terms(self) -> List[str]:
        """全ての検索語彙を取得"""
        return list(set(self.ingredient_names + self.dish_names))


class NutritionQueryOutput(BaseModel):
    """栄養データベース検索結果モデル（純粋なローカル形式）"""
    matches: Dict[str, NutritionMatch] = Field(default_factory=dict, description="検索語彙と対応する照合結果のマッピング")
    search_summary: Dict[str, Union[int, float, str]] = Field(default_factory=dict, description="検索結果のサマリー情報")
    warnings: Optional[List[str]] = Field(None, description="警告メッセージのリスト")
    errors: Optional[List[str]] = Field(None, description="エラーメッセージのリスト")

    def get_match_rate(self) -> float:
        """照合成功率を計算"""
        total_searches = self.search_summary.get("total_searches", 0)
        successful_matches = self.search_summary.get("successful_matches", 0)
        if total_searches == 0:
            return 0.0
        return successful_matches / total_searches

    def get_total_matches(self) -> int:
        """総照合件数を取得"""
        return len(self.matches)
    
    def has_errors(self) -> bool:
        """エラーが存在するかチェック"""
        return self.errors is not None and len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """警告が存在するかチェック"""
        return self.warnings is not None and len(self.warnings) > 0 