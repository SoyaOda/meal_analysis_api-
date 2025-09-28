#!/usr/bin/env python3
"""
Serving情報のデータクラス定義
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class ServingOption:
    """個別のserving option情報"""
    unit_name: str          # 単位名（例: "cup", "oz", "ml"）
    calories: float         # カロリー
    weight: float          # 重量（グラム）
    radio_value: str       # ラジオボタンの値
    raw_text: str          # 元のテキスト

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "unit_name": self.unit_name,
            "calories": self.calories,
            "weight": self.weight,
            "radio_value": self.radio_value,
            "raw_text": self.raw_text
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ServingOption':
        """辞書から作成"""
        return cls(
            unit_name=data["unit_name"],
            calories=data["calories"],
            weight=data["weight"],
            radio_value=data["radio_value"],
            raw_text=data["raw_text"]
        )


@dataclass
class FoodData:
    """食材データ"""
    food_index: int                          # 食材番号
    food_name: str                          # 食材名
    serving_options: List[ServingOption]    # serving options
    timestamp: str                          # 取得時刻

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "food_index": self.food_index,
            "food_name": self.food_name,
            "serving_options": [option.to_dict() for option in self.serving_options],
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'FoodData':
        """辞書から作成"""
        return cls(
            food_index=data["food_index"],
            food_name=data["food_name"],
            serving_options=[ServingOption.from_dict(opt) for opt in data["serving_options"]],
            timestamp=data["timestamp"]
        )


@dataclass
class ExtractionResult:
    """抽出結果の全体データ"""
    extraction_info: Dict                   # 抽出情報
    foods: List[FoodData]                  # 食材データリスト
    metadata: Dict                         # メタデータ

    def to_dict(self) -> Dict:
        """辞書形式に変換（JSONシリアライズ用）"""
        return {
            "extraction_info": self.extraction_info,
            "foods": [food.to_dict() for food in self.foods],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ExtractionResult':
        """辞書から作成"""
        return cls(
            extraction_info=data["extraction_info"],
            foods=[FoodData.from_dict(food) for food in data["foods"]],
            metadata=data["metadata"]
        )

    def add_food(self, food_data: FoodData):
        """食材データを追加"""
        self.foods.append(food_data)

    def get_total_serving_options(self) -> int:
        """総serving options数を取得"""
        return sum(len(food.serving_options) for food in self.foods)

    @classmethod
    def create_empty(cls, method: str = "component_extraction") -> 'ExtractionResult':
        """空の抽出結果を作成"""
        return cls(
            extraction_info={
                "timestamp": datetime.now().isoformat(),
                "total_foods_processed": 0,
                "method": method,
                "description": "コンポーネント版serving情報抽出",
                "total_serving_options": 0
            },
            foods=[],
            metadata={
                "source_platform": "MyNetDiary",
                "category": "未設定",
                "extraction_method": "selenium_component_analysis",
                "data_quality": "raw_complete_serving_options"
            }
        )