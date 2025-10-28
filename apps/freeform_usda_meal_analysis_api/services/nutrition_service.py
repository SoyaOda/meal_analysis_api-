#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
USDA栄養素データサービス

ローカルUSDA JSONファイル（Survey + Foundation）から栄養素データを読み込み、
100gあたりの栄養素から実重量の栄養素を計算する。
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LocalUSDANutritionService:
    """
    ローカルUSDA JSONファイルから栄養素データを読み込むサービス

    起動時に1回だけSurvey + Foundationの全データをメモリにロード。
    各食材のFDC IDに対して、calories, protein_g, fat_g, carbs_g を返す。
    """

    # USDA栄養素ID → 内部キー名のマッピング
    NUTRIENT_IDS = {
        1008: "calories",      # Energy (kcal)
        1003: "protein_g",     # Protein (g)
        1004: "fat_g",         # Total lipid (fat) (g)
        1005: "carbs_g"        # Carbohydrate, by difference (g)
    }

    def __init__(
        self,
        survey_file: str,
        foundation_file: str,
        sr_legacy_file: Optional[str] = None
    ):
        """
        Args:
            survey_file: surveyDownload.json のパス
            foundation_file: FoodData_Central_foundation_food_json_*.json のパス
            sr_legacy_file: FoodData_Central_sr_legacy_food_json_*.json のパス（オプション）
        """
        self.survey_file = Path(survey_file)
        self.foundation_file = Path(foundation_file)
        self.sr_legacy_file = Path(sr_legacy_file) if sr_legacy_file else None

        # FDC ID → {calories, protein_g, fat_g, carbs_g} のマップ
        self.nutrition_db: Dict[int, Dict[str, float]] = {}

        # ロード実行
        self._load_databases()

    def _load_databases(self):
        """Survey + Foundation + SR Legacy (optional) の全てをロード"""
        logger.info(f"📂 Loading USDA Survey foods from: {self.survey_file}")
        survey_count = self._load_survey_foods()
        logger.info(f"✅ Loaded {survey_count} Survey foods")

        logger.info(f"📂 Loading USDA Foundation foods from: {self.foundation_file}")
        foundation_count = self._load_foundation_foods()
        logger.info(f"✅ Loaded {foundation_count} Foundation foods")

        # SR Legacy (optional)
        sr_legacy_count = 0
        if self.sr_legacy_file and self.sr_legacy_file.exists():
            logger.info(f"📂 Loading USDA SR Legacy foods from: {self.sr_legacy_file}")
            sr_legacy_count = self._load_sr_legacy_foods()
            logger.info(f"✅ Loaded {sr_legacy_count} SR Legacy foods")
        elif self.sr_legacy_file:
            logger.warning(f"⚠️  SR Legacy file not found: {self.sr_legacy_file}")

        logger.info(f"✅ Total USDA foods loaded: {len(self.nutrition_db)} "
                   f"(Survey: {survey_count}, Foundation: {foundation_count}, SR Legacy: {sr_legacy_count})")

    def _load_survey_foods(self) -> int:
        """Survey foods をロード"""
        with open(self.survey_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        survey_foods = data.get('SurveyFoods', [])
        self._index_foods(survey_foods, source='survey')

        return len(survey_foods)

    def _load_foundation_foods(self) -> int:
        """Foundation foods をロード"""
        with open(self.foundation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        foundation_foods = data.get('FoundationFoods', [])
        self._index_foods(foundation_foods, source='foundation')

        return len(foundation_foods)

    def _load_sr_legacy_foods(self) -> int:
        """SR Legacy foods をロード"""
        with open(self.sr_legacy_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        sr_legacy_foods = data.get('SRLegacyFoods', [])
        self._index_foods(sr_legacy_foods, source='sr_legacy')

        return len(sr_legacy_foods)

    def _index_foods(self, foods: List[Dict], source: str):
        """
        食材リストから栄養素を抽出してインデックス化

        Args:
            foods: 食材リスト（各要素は fdcId, foodNutrients を持つ）
            source: データソース名（'survey' or 'foundation'）
        """
        for food in foods:
            fdc_id = food.get('fdcId')
            if not fdc_id:
                continue

            # 栄養素を抽出
            nutrients = {}
            for food_nutrient in food.get('foodNutrients', []):
                nutrient = food_nutrient.get('nutrient', {})
                nutrient_id = nutrient.get('id')

                if nutrient_id in self.NUTRIENT_IDS:
                    amount = food_nutrient.get('amount', 0.0)
                    key = self.NUTRIENT_IDS[nutrient_id]
                    nutrients[key] = round(float(amount), 1)

            # 4つの栄養素が全て揃っていない場合は0で補完
            for key in self.NUTRIENT_IDS.values():
                if key not in nutrients:
                    nutrients[key] = 0.0

            # メモリDBに格納
            if nutrients:
                self.nutrition_db[fdc_id] = nutrients

    def get_nutrition_per_100g(self, fdc_id: int) -> Optional[Dict[str, float]]:
        """
        FDC IDに対する100gあたりの栄養素を取得

        Args:
            fdc_id: USDA FoodData Central ID

        Returns:
            {calories: float, protein_g: float, fat_g: float, carbs_g: float}
            存在しない場合は None
        """
        return self.nutrition_db.get(fdc_id)

    def has_food(self, fdc_id: int) -> bool:
        """指定されたFDC IDが存在するか確認"""
        return fdc_id in self.nutrition_db

    def get_total_foods(self) -> int:
        """ロードされた食材の総数"""
        return len(self.nutrition_db)


class NutritionCalculator:
    """
    100gあたりの栄養素から実重量の栄養素を計算するサービス
    """

    def __init__(self, nutrition_service: LocalUSDANutritionService):
        """
        Args:
            nutrition_service: LocalUSDANutritionService インスタンス
        """
        self.nutrition_service = nutrition_service

    def calculate(self, fdc_id: int, weight_g: float) -> Optional[Dict[str, float]]:
        """
        指定されたFDC IDと重量から栄養素を計算

        Formula: 栄養素 = (100gあたりの栄養素) × (weight_g / 100)

        Args:
            fdc_id: USDA FoodData Central ID
            weight_g: 食材の重量（グラム）

        Returns:
            {
                "weight_g": float,
                "calories": float,
                "protein_g": float,
                "fat_g": float,
                "carbs_g": float
            }
            FDC IDが存在しない場合は None
        """
        nutrition_per_100g = self.nutrition_service.get_nutrition_per_100g(fdc_id)

        if nutrition_per_100g is None:
            logger.warning(f"FDC ID {fdc_id} not found in nutrition database")
            return None

        # 係数計算
        factor = weight_g / 100.0

        return {
            "weight_g": round(weight_g, 1),
            "calories": round(nutrition_per_100g["calories"] * factor, 1),
            "protein_g": round(nutrition_per_100g["protein_g"] * factor, 1),
            "fat_g": round(nutrition_per_100g["fat_g"] * factor, 1),
            "carbs_g": round(nutrition_per_100g["carbs_g"] * factor, 1)
        }

    def calculate_total(self, items: List[Dict]) -> Dict[str, float]:
        """
        複数の食材の栄養素を合計

        Args:
            items: 食材リスト（各要素は 'nutrition' キーを持つ）

        Returns:
            {
                "calories": float,
                "protein_g": float,
                "fat_g": float,
                "carbs_g": float
            }
        """
        total = {
            "calories": 0.0,
            "protein_g": 0.0,
            "fat_g": 0.0,
            "carbs_g": 0.0
        }

        for item in items:
            nutrition = item.get('nutrition', {})
            for key in total:
                total[key] += nutrition.get(key, 0.0)

        # 丸め処理
        return {k: round(v, 1) for k, v in total.items()}

    def calculate_batch(
        self,
        food_items: List[Dict[str, any]]
    ) -> List[Dict]:
        """
        複数の食材に対して一括で栄養素を計算

        Args:
            food_items: [{"fdc_id": int, "weight_g": float, ...}, ...]

        Returns:
            [
                {
                    "fdc_id": int,
                    "weight_g": float,
                    "nutrition": {calories, protein_g, fat_g, carbs_g},
                    ...
                },
                ...
            ]
        """
        results = []

        for item in food_items:
            fdc_id = item.get('fdc_id')
            weight_g = item.get('weight_g', 0)

            nutrition = self.calculate(fdc_id, weight_g)

            # 元のitemをコピーして栄養素を追加
            result = item.copy()
            result['nutrition'] = nutrition
            results.append(result)

        return results
