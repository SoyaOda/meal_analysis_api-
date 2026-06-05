#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
USDA栄養素データサービス

metadata.json（栄養素データを含む）から栄養素データを読み込み、
100gあたりの栄養素から実重量の栄養素を計算する。
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LocalUSDANutritionService:
    """
    metadata.jsonから栄養素データを読み込むサービス

    起動時に1回だけmetadata.jsonの全データをメモリにロード。
    各食材のFDC IDに対して、calories, protein_g, fat_g, carbs_g を返す。
    """

    def __init__(self, metadata_file: str):
        """
        Args:
            metadata_file: usda_metadata.json のパス (栄養素データを含む)
        """
        self.metadata_file = Path(metadata_file)

        # FDC ID → {calories, protein_g, fat_g, carbs_g} のマップ
        self.nutrition_db: Dict[int, Dict[str, float]] = {}

        # ロード実行
        self._load_from_metadata()

    def _load_from_metadata(self):
        """metadata.jsonから栄養素データをロード"""
        logger.info(
            f"📂 Loading USDA nutrition data from metadata: {self.metadata_file}"
        )

        with open(self.metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # FDC ID → nutrition のマップを作成
        for item in metadata:
            fdc_id = item.get("fdc_id")
            nutrition = item.get("nutrition")

            if fdc_id and nutrition:
                self.nutrition_db[fdc_id] = nutrition

        logger.info(f"✅ Loaded {len(self.nutrition_db)} foods with nutrition data")

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
            "carbs_g": round(nutrition_per_100g["carbs_g"] * factor, 1),
        }

    def calculate_mixture(
        self,
        topk_candidates: List[Dict],
        weight_g: float,
        temperature: float = 1.0,
    ) -> Optional[Dict[str, float]]:
        """E7: top-k 候補の密度(per-100g)を rerank-score の softmax で混合して重量を掛ける。

        E[nutrition] = E[kcal/100g] × (weight_g/100)。grams は VLM 由来で固定し、density のみ
        top-k 分布で期待値化する（密度誤差は総カロリー誤差の ~50%）。栄養が引けた候補のみで
        重みを再正規化。1件も引けなければ None（呼び出し側は top-1 計算にフォールバックしない＝
        その時は None のまま＝従来の「該当なし」と同じ扱い）。
        """
        import math

        per100: List[Dict[str, float]] = []
        scores: List[float] = []
        for c in topk_candidates or []:
            n = self.nutrition_service.get_nutrition_per_100g(c.get("fdc_id"))
            if n is not None:
                per100.append(n)
                scores.append(float(c.get("rerank_score", 0.0)))
        if not per100:
            return None

        keys = ("calories", "protein_g", "fat_g", "carbs_g")
        if len(per100) == 1:
            mixed = {k: per100[0][k] for k in keys}
        else:
            t = temperature if temperature and temperature > 0 else 1.0
            m = max(scores)
            exps = [math.exp((s - m) / t) for s in scores]
            z = sum(exps) or 1.0
            w = [e / z for e in exps]
            mixed = {k: sum(wi * p[k] for wi, p in zip(w, per100)) for k in keys}

        factor = weight_g / 100.0
        return {
            "weight_g": round(weight_g, 1),
            "calories": round(mixed["calories"] * factor, 1),
            "protein_g": round(mixed["protein_g"] * factor, 1),
            "fat_g": round(mixed["fat_g"] * factor, 1),
            "carbs_g": round(mixed["carbs_g"] * factor, 1),
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
        total = {"calories": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0}

        for item in items:
            nutrition = item.get("nutrition", {})
            for key in total:
                total[key] += nutrition.get(key, 0.0)

        # 丸め処理
        return {k: round(v, 1) for k, v in total.items()}

    def calculate_batch(self, food_items: List[Dict[str, any]]) -> List[Dict]:
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
            fdc_id = item.get("fdc_id")
            weight_g = item.get("weight_g", 0)

            nutrition = self.calculate(fdc_id, weight_g)

            # 元のitemをコピーして栄養素を追加
            result = item.copy()
            result["nutrition"] = nutrition
            results.append(result)

        return results
