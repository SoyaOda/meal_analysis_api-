#!/usr/bin/env python3
"""
生データ専用のServing情報データクラス定義
"""

from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime


@dataclass
class RawServingOption:
    """個別の生serving option情報"""
    radio_value: str       # ラジオボタンの値
    raw_text: str          # 元のテキスト（そのまま保存）
    option_index: int      # オプション番号

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "radio_value": self.radio_value,
            "raw_text": self.raw_text,
            "option_index": self.option_index
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'RawServingOption':
        """辞書から作成"""
        return cls(
            radio_value=data["radio_value"],
            raw_text=data["raw_text"],
            option_index=data["option_index"]
        )


@dataclass
class RawFoodData:
    """食材の生データ"""
    food_index: int                              # 食材番号
    food_name: str                              # 食材名
    raw_serving_options: List[RawServingOption] # 生serving options
    timestamp: str                              # 取得時刻

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "food_index": self.food_index,
            "food_name": self.food_name,
            "raw_serving_options": [option.to_dict() for option in self.raw_serving_options],
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'RawFoodData':
        """辞書から作成"""
        return cls(
            food_index=data["food_index"],
            food_name=data["food_name"],
            raw_serving_options=[RawServingOption.from_dict(opt) for opt in data["raw_serving_options"]],
            timestamp=data["timestamp"]
        )


@dataclass
class RawExtractionResult:
    """生データ抽出結果の全体データ"""
    extraction_info: Dict                   # 抽出情報
    foods: List[RawFoodData]               # 食材データリスト
    metadata: Dict                         # メタデータ

    def to_dict(self) -> Dict:
        """辞書形式に変換（JSONシリアライズ用）"""
        return {
            "extraction_info": self.extraction_info,
            "foods": [food.to_dict() for food in self.foods],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'RawExtractionResult':
        """辞書から作成"""
        return cls(
            extraction_info=data["extraction_info"],
            foods=[RawFoodData.from_dict(food) for food in data["foods"]],
            metadata=data["metadata"]
        )

    def add_food(self, food_data: RawFoodData):
        """食材データを追加"""
        self.foods.append(food_data)

    def get_total_raw_serving_options(self) -> int:
        """総生serving options数を取得"""
        return sum(len(food.raw_serving_options) for food in self.foods)

    @classmethod
    def create_empty(cls, method: str = "raw_component_extraction") -> 'RawExtractionResult':
        """空の抽出結果を作成"""
        return cls(
            extraction_info={
                "timestamp": datetime.now().isoformat(),
                "total_foods_processed": 0,
                "method": method,
                "description": "生データコンポーネント版serving情報抽出",
                "total_raw_serving_options": 0
            },
            foods=[],
            metadata={
                "source_platform": "MyNetDiary",
                "category": "未設定",
                "extraction_method": "selenium_raw_component_analysis",
                "data_quality": "raw_unprocessed_serving_options"
            }
        )