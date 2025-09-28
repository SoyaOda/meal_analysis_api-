"""
Data Models for MyNetDiary Scraping
スクレイピング結果のデータ構造定義
"""

from .serving_data import ServingOption, FoodData, ExtractionResult

__all__ = [
    'ServingOption',
    'FoodData',
    'ExtractionResult'
]