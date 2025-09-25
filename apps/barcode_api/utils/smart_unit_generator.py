#!/usr/bin/env python3
"""
スマートユニット生成クラス

食品タイプと利用可能なデータに基づいて適切な栄養素単位オプションを生成する
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from ..models.nutrition import NutrientUnitOption, MainNutrients, ProductInfo, HouseholdServingInfo
from .unit_parser import UnitParser, ParsedUnit

logger = logging.getLogger(__name__)


class SmartUnitGenerator:
    """食品タイプに応じた適切な単位オプションを生成するクラス"""

    def __init__(self):
        """
        SmartUnitGeneratorの初期化
        """
        self.unit_parser = UnitParser()
        self.food_type_patterns = self._load_food_type_patterns()

        logger.info("SmartUnitGenerator初期化完了")

    def _load_food_type_patterns(self) -> Dict[str, Any]:
        """
        食品タイプ判定パターンを読み込み

        Returns:
            食品タイプ判定用パターン辞書
        """
        patterns = {
            "liquid": {
                "keywords": [
                    "juice", "milk", "water", "soda", "drink", "beverage",
                    "soup", "broth", "smoothie", "tea", "coffee",
                    "ジュース", "牛乳", "水", "飲料", "スープ", "お茶", "コーヒー"
                ],
                "preferred_units": ["ml", "fl oz", "cup", "liter"],
                "density_estimate": 1.0
            },
            "baked_goods": {
                "keywords": [
                    "cookie", "cracker", "biscuit", "wafer", "cake", "muffin",
                    "bread", "roll", "bagel", "donut", "pastry",
                    "クッキー", "クラッカー", "ケーキ", "マフィン", "パン", "ドーナツ"
                ],
                "preferred_units": ["piece", "slice", "cookie", "cracker"],
                "density_estimate": 0.4
            },
            "snacks": {
                "keywords": [
                    "chips", "popcorn", "nuts", "pretzels", "crackers",
                    "チップス", "ポップコーン", "ナッツ", "プレッツェル"
                ],
                "preferred_units": ["g", "oz", "cup", "piece"],
                "density_estimate": 0.3
            },
            "cereal": {
                "keywords": [
                    "cereal", "granola", "oats", "muesli", "flakes",
                    "シリアル", "グラノーラ", "オートミール", "フレーク"
                ],
                "preferred_units": ["cup", "g", "oz"],
                "density_estimate": 0.4
            },
            "candy": {
                "keywords": [
                    "candy", "chocolate", "gummy", "lollipop", "gum", "mint",
                    "キャンディ", "チョコレート", "グミ", "飴", "ミント"
                ],
                "preferred_units": ["piece", "g", "oz"],
                "density_estimate": 0.8
            },
            "default": {
                "keywords": [],
                "preferred_units": ["g", "oz", "cup"],
                "density_estimate": 0.6
            }
        }
        return patterns

    def _determine_food_type(self, product_info: Optional[ProductInfo]) -> str:
        """
        製品情報から食品タイプを判定

        Args:
            product_info: 製品情報

        Returns:
            食品タイプ名
        """
        if not product_info:
            return "default"

        # 製品名とブランド名を結合してテキスト分析
        search_text = " ".join(filter(None, [
            product_info.description,
            product_info.brand_name,
            product_info.ingredients
        ])).lower()

        # 各食品タイプのキーワードマッチング
        for food_type, config in self.food_type_patterns.items():
            if food_type == "default":
                continue

            keywords = config.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in search_text:
                    logger.debug(f"食品タイプ判定: {food_type} (キーワード: {keyword})")
                    return food_type

        logger.debug("食品タイプ判定: default (キーワードマッチなし)")
        return "default"

    def generate_unit_options(
        self,
        nutrients_100g: MainNutrients,
        product_info: Optional[ProductInfo] = None,
        household_serving_info: Optional[HouseholdServingInfo] = None,
        serving_size_g: Optional[float] = None
    ) -> List[NutrientUnitOption]:
        """
        適切な単位オプションを生成

        Args:
            nutrients_100g: 100gあたりの栄養素データ
            product_info: 製品情報
            household_serving_info: 家庭用サービング情報
            serving_size_g: サービングサイズ（グラム）

        Returns:
            生成された単位オプションリスト
        """
        try:
            unit_options = []

            # 食品タイプを判定
            food_type = self._determine_food_type(product_info)
            type_config = self.food_type_patterns.get(food_type, self.food_type_patterns["default"])

            # 1. 基本単位: 1g（全食品共通）
            unit_options.append(self._create_unit_option(
                unit_id="1g",
                display_name="1 gram",
                unit_type="weight",
                equivalent_weight_g=1.0,
                nutrients_100g=nutrients_100g,
                is_primary=False
            ))

            # 2. 100g（参照用）
            unit_options.append(self._create_unit_option(
                unit_id="100g",
                display_name="100 grams",
                unit_type="weight",
                equivalent_weight_g=100.0,
                nutrients_100g=nutrients_100g,
                is_primary=False
            ))

            # 3. メーカー指定サービングサイズ
            if serving_size_g and serving_size_g > 0:
                unit_options.append(self._create_unit_option(
                    unit_id=f"1serving",
                    display_name=f"1 serving ({serving_size_g}g)",
                    unit_type="serving",
                    equivalent_weight_g=serving_size_g,
                    nutrients_100g=nutrients_100g,
                    is_primary=True
                ))

            # 4. 家庭用サービング情報がある場合
            if household_serving_info and household_serving_info.weight_equivalent_g:
                unit_display = self._format_household_serving_display(household_serving_info)
                unit_options.append(self._create_unit_option(
                    unit_id=f"1{household_serving_info.unit or 'piece'}",
                    display_name=unit_display,
                    unit_type=household_serving_info.unit_type or "count",
                    equivalent_weight_g=household_serving_info.weight_equivalent_g,
                    nutrients_100g=nutrients_100g,
                    is_primary=True
                ))

            # 5. 食品タイプに応じた推奨単位
            preferred_units = type_config.get("preferred_units", [])
            density = type_config.get("density_estimate", 0.6)

            for unit in preferred_units:
                # 既に追加済みの単位はスキップ
                existing_unit_ids = [opt.unit_id for opt in unit_options]

                if unit == "cup" and "1cup" not in existing_unit_ids:
                    # カップ単位（密度を考慮）
                    cup_weight_g = 236.588 * density  # 1 US cup in ml × density
                    unit_options.append(self._create_unit_option(
                        unit_id="1cup",
                        display_name="1 cup",
                        unit_type="volume",
                        equivalent_weight_g=cup_weight_g,
                        nutrients_100g=nutrients_100g,
                        is_primary=False
                    ))

                elif unit == "oz" and "1oz" not in existing_unit_ids:
                    # オンス単位
                    unit_options.append(self._create_unit_option(
                        unit_id="1oz",
                        display_name="1 ounce",
                        unit_type="weight",
                        equivalent_weight_g=28.3495,
                        nutrients_100g=nutrients_100g,
                        is_primary=False
                    ))

                elif unit == "piece" and "1piece" not in existing_unit_ids:
                    # 一般的なピース単位（推定重量）
                    estimated_piece_weight = self._estimate_piece_weight(food_type, product_info)
                    if estimated_piece_weight:
                        unit_options.append(self._create_unit_option(
                            unit_id="1piece",
                            display_name="1 piece",
                            unit_type="count",
                            equivalent_weight_g=estimated_piece_weight,
                            nutrients_100g=nutrients_100g,
                            is_primary=False
                        ))

            # 重複除去とソート
            unit_options = self._deduplicate_units(unit_options)
            unit_options = self._sort_units(unit_options)

            logger.info(f"Generated {len(unit_options)} unit options (food type: {food_type})")
            return unit_options

        except Exception as e:
            logger.error(f"Unit option generation error: {e}")
            # エラー時は最低限の単位オプションを返す
            return self._create_fallback_units(nutrients_100g)

    def _create_unit_option(
        self,
        unit_id: str,
        display_name: str,
        unit_type: str,
        equivalent_weight_g: float,
        nutrients_100g: MainNutrients,
        is_primary: bool = False
    ) -> NutrientUnitOption:
        """
        単位オプションを作成

        Args:
            unit_id: 単位ID
            display_name: 表示名
            unit_type: 単位タイプ
            equivalent_weight_g: グラム換算値
            nutrients_100g: 100gあたり栄養素
            is_primary: メーカー推奨単位かどうか

        Returns:
            単位オプション
        """
        # グラム換算値に基づいて栄養素を計算
        factor = equivalent_weight_g / 100.0

        return NutrientUnitOption(
            unit_id=unit_id,
            display_name=display_name,
            unit_type=unit_type,
            is_primary=is_primary,
            equivalent_weight_g=equivalent_weight_g,
            energy_kcal=self._multiply_nutrient(nutrients_100g.energy_kcal, factor),
            energy_kj=self._multiply_nutrient(nutrients_100g.energy_kj, factor),
            protein_g=self._multiply_nutrient(nutrients_100g.protein_g, factor),
            fat_g=self._multiply_nutrient(nutrients_100g.fat_g, factor),
            carbohydrate_g=self._multiply_nutrient(nutrients_100g.carbohydrate_g, factor),
            fiber_g=self._multiply_nutrient(nutrients_100g.fiber_g, factor),
            sugars_g=self._multiply_nutrient(nutrients_100g.sugars_g, factor),
            saturated_fat_g=self._multiply_nutrient(nutrients_100g.saturated_fat_g, factor),
            trans_fat_g=self._multiply_nutrient(nutrients_100g.trans_fat_g, factor),
            cholesterol_mg=self._multiply_nutrient(nutrients_100g.cholesterol_mg, factor),
            sodium_mg=self._multiply_nutrient(nutrients_100g.sodium_mg, factor),
            calcium_mg=self._multiply_nutrient(nutrients_100g.calcium_mg, factor),
            iron_mg=self._multiply_nutrient(nutrients_100g.iron_mg, factor),
            potassium_mg=self._multiply_nutrient(nutrients_100g.potassium_mg, factor),
            vitamin_c_mg=self._multiply_nutrient(nutrients_100g.vitamin_c_mg, factor),
            vitamin_a_iu=self._multiply_nutrient(nutrients_100g.vitamin_a_iu, factor),
            vitamin_d_iu=self._multiply_nutrient(nutrients_100g.vitamin_d_iu, factor)
        )

    def _multiply_nutrient(self, value: Optional[float], factor: float) -> Optional[float]:
        """
        栄養素値に係数を掛ける

        Args:
            value: 栄養素値
            factor: 係数

        Returns:
            計算結果（適切な桁数で丸める）
        """
        if value is None:
            return None

        result = value * factor

        # 適切な桁数で丸める
        if result >= 10:
            return round(result, 1)
        elif result >= 1:
            return round(result, 2)
        else:
            return round(result, 3)

    def _format_household_serving_display(self, household_serving_info: HouseholdServingInfo) -> str:
        """
        家庭用サービング情報の表示名をフォーマット

        Args:
            household_serving_info: 家庭用サービング情報

        Returns:
            表示名
        """
        if household_serving_info.original_text:
            return household_serving_info.original_text

        quantity = household_serving_info.quantity or 1
        unit = household_serving_info.unit or "piece"
        weight_g = household_serving_info.weight_equivalent_g

        if weight_g:
            return f"{int(quantity)} {unit} ({weight_g}g)"
        else:
            return f"{int(quantity)} {unit}"

    def _estimate_piece_weight(self, food_type: str, product_info: Optional[ProductInfo]) -> Optional[float]:
        """
        食品タイプから1個あたりの推定重量を算出

        Args:
            food_type: 食品タイプ
            product_info: 製品情報

        Returns:
            推定重量（グラム）
        """
        # 食品タイプ別の典型的な1個重量
        typical_weights = {
            "baked_goods": 15.0,  # クッキー、クラッカー等
            "candy": 5.0,         # キャンディ、チョコレート等
            "snacks": 20.0,       # スナック菓子等
            "default": 10.0       # デフォルト
        }

        return typical_weights.get(food_type, typical_weights["default"])

    def _deduplicate_units(self, unit_options: List[NutrientUnitOption]) -> List[NutrientUnitOption]:
        """
        重複する単位オプションを除去

        Args:
            unit_options: 単位オプションリスト

        Returns:
            重複除去された単位オプションリスト
        """
        seen_unit_ids = set()
        deduplicated = []

        for option in unit_options:
            if option.unit_id not in seen_unit_ids:
                seen_unit_ids.add(option.unit_id)
                deduplicated.append(option)

        return deduplicated

    def _sort_units(self, unit_options: List[NutrientUnitOption]) -> List[NutrientUnitOption]:
        """
        単位オプションを適切な順序でソート

        Args:
            unit_options: 単位オプションリスト

        Returns:
            ソートされた単位オプションリスト
        """
        def sort_key(option: NutrientUnitOption) -> Tuple[int, float]:
            # プライマリ単位を優先、その後重量でソート
            primary_priority = 0 if option.is_primary else 1
            weight = option.equivalent_weight_g or 0
            return (primary_priority, weight)

        return sorted(unit_options, key=sort_key)

    def _create_fallback_units(self, nutrients_100g: MainNutrients) -> List[NutrientUnitOption]:
        """
        エラー時の最低限の単位オプションを作成

        Args:
            nutrients_100g: 100gあたり栄養素

        Returns:
            最低限の単位オプションリスト
        """
        try:
            return [
                self._create_unit_option(
                    unit_id="1g",
                    display_name="1 gram",
                    unit_type="weight",
                    equivalent_weight_g=1.0,
                    nutrients_100g=nutrients_100g,
                    is_primary=True
                ),
                self._create_unit_option(
                    unit_id="100g",
                    display_name="100 grams",
                    unit_type="weight",
                    equivalent_weight_g=100.0,
                    nutrients_100g=nutrients_100g,
                    is_primary=False
                )
            ]
        except Exception as e:
            logger.error(f"Fallback unit creation error: {e}")
            return []