#!/usr/bin/env python3
"""
単位解析・変換ユーティリティモジュール

FDCデータの多様な単位表記を解析し、統一された単位に変換するためのモジュール
"""

import json
import re
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ParsedUnit:
    """解析された単位情報"""
    original_text: str
    unit_type: str  # volume, weight, count
    quantity: float
    unit: str
    weight_equivalent_g: Optional[float] = None
    volume_equivalent_ml: Optional[float] = None


class UnitParser:
    """単位解析・変換クラス"""

    def __init__(self):
        self.data_path = Path(__file__).parent.parent / "data"
        self.unit_conversions = self._load_unit_conversions()
        self.density_data = self._load_density_data()

    def _load_unit_conversions(self) -> Dict[str, Any]:
        """単位変換データを読み込み"""
        with open(self.data_path / "unit_conversions.json", 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_density_data(self) -> Dict[str, Any]:
        """密度データを読み込み"""
        with open(self.data_path / "food_density_data.json", 'r', encoding='utf-8') as f:
            return json.load(f)

    def parse_household_serving(self, text: str, product_description: str = "") -> Optional[ParsedUnit]:
        """
        household_serving_fulltextを解析

        Args:
            text: 解析するテキスト
            product_description: 製品説明（密度推定用）

        Returns:
            ParsedUnit または None
        """
        if not text or not text.strip():
            return None

        # 分数を小数に変換
        text = self._convert_fractions_to_decimals(text)

        # 体積単位の検出
        volume_match = self._parse_volume_unit(text)
        if volume_match:
            return volume_match

        # 個数単位の検出
        count_match = self._parse_count_unit(text)
        if count_match:
            return count_match

        # 重量単位の検出（括弧内）
        weight_match = self._parse_weight_unit(text)
        if weight_match:
            return weight_match

        return None

    def _convert_fractions_to_decimals(self, text: str) -> str:
        """分数を小数に変換"""
        # 帯分数 (1 1/2 → 1.5)
        mixed_pattern = r'\b(\d+)\s+(\d+)/(\d+)\b'
        def mixed_replacer(match):
            whole = int(match.group(1))
            num = int(match.group(2))
            den = int(match.group(3))
            return str(whole + num / den)
        text = re.sub(mixed_pattern, mixed_replacer, text)

        # 普通分数 (1/2 → 0.5)
        fraction_pattern = r'\b(\d+)/(\d+)\b'
        def fraction_replacer(match):
            num = int(match.group(1))
            den = int(match.group(2))
            return str(num / den)
        text = re.sub(fraction_pattern, fraction_replacer, text)

        return text

    def _parse_volume_unit(self, text: str) -> Optional[ParsedUnit]:
        """体積単位を解析"""
        pattern = self.unit_conversions["parsing_patterns"]["volume_regex"]
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            quantity_str = match.group(1)
            unit = match.group(2).lower().strip()

            # 数量が空の場合は1とする
            quantity = float(quantity_str) if quantity_str else 1.0

            # 単位を正規化
            normalized_unit = self._normalize_volume_unit(unit)
            if normalized_unit in self.unit_conversions["volume_units"]:
                base_ml = self.unit_conversions["volume_units"][normalized_unit]["base_ml"]
                total_ml = quantity * base_ml

                return ParsedUnit(
                    original_text=text,
                    unit_type="volume",
                    quantity=quantity,
                    unit=normalized_unit,
                    volume_equivalent_ml=total_ml
                )

        return None

    def _parse_count_unit(self, text: str) -> Optional[ParsedUnit]:
        """個数単位を解析"""
        pattern = self.unit_conversions["parsing_patterns"]["count_regex"]
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            quantity = float(match.group(1))
            unit = match.group(2).lower().strip()

            # 単位を正規化（複数形→単数形）
            normalized_unit = self._normalize_count_unit(unit)

            return ParsedUnit(
                original_text=text,
                unit_type="count",
                quantity=quantity,
                unit=normalized_unit
            )

        return None

    def _parse_weight_unit(self, text: str) -> Optional[ParsedUnit]:
        """重量単位を解析（主に括弧内）"""
        pattern = self.unit_conversions["parsing_patterns"]["weight_in_parens"]
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            quantity = float(match.group(1))
            unit = match.group(2).lower().strip()

            if unit in self.unit_conversions["weight_units"]:
                base_g = self.unit_conversions["weight_units"][unit]["base_g"]
                total_g = quantity * base_g

                return ParsedUnit(
                    original_text=text,
                    unit_type="weight",
                    quantity=quantity,
                    unit=unit,
                    weight_equivalent_g=total_g
                )

        return None

    def _normalize_volume_unit(self, unit: str) -> str:
        """体積単位を正規化"""
        unit = unit.lower().strip()

        # 一般的な異形を正規化
        normalizations = {
            "cups": "cup",
            "fl oz": "fl oz",
            "fl.oz": "fl oz",
            "tbsp": "tbsp",
            "tsp": "tsp",
            "ml": "ml",
            "mL": "ml",
            "liters": "liter",
            "gallons": "gallon",
            "pints": "pint",
            "quarts": "quart"
        }

        return normalizations.get(unit, unit)

    def _normalize_count_unit(self, unit: str) -> str:
        """個数単位を正規化（複数形→単数形）"""
        unit = unit.lower().strip()

        # 複数形を単数形に変換
        plurals_to_singular = {
            "pieces": "piece",
            "items": "item",
            "bars": "bar",
            "slices": "slice",
            "cookies": "cookie",
            "crackers": "cracker",
            "chips": "chip",
            "links": "link",
            "pastries": "pastry",
            "pizzas": "pizza",
            "waffles": "waffle"
        }

        return plurals_to_singular.get(unit, unit)

    def estimate_weight_from_volume(self, volume_ml: float, product_description: str = "") -> Optional[float]:
        """体積から重量を推定"""
        # 製品説明から密度を推定
        density = self._estimate_density(product_description)
        return volume_ml * density if density else None

    def estimate_volume_from_weight(self, weight_g: float, product_description: str = "") -> Optional[float]:
        """重量から体積を推定"""
        # 製品説明から密度を推定
        density = self._estimate_density(product_description)
        return weight_g / density if density else None

    def _estimate_density(self, product_description: str) -> float:
        """製品説明から密度を推定"""
        product_description = product_description.lower()

        # 密度推定ルールを適用
        for rule in self.density_data["estimation_rules"]:
            if rule["condition"] != "default_solid":
                keywords = rule["keywords"]
                if any(keyword in product_description for keyword in keywords):
                    return rule["density"]

        # デフォルト値
        return self.density_data["estimation_rules"][-1]["density"]

    def calculate_alternative_units(self, base_nutrients: Dict[str, float],
                                 serving_weight_g: float,
                                 household_unit: ParsedUnit,
                                 product_description: str = "") -> List[Dict[str, Any]]:
        """
        代替単位での栄養価を計算

        Args:
            base_nutrients: 100gあたりの栄養素
            serving_weight_g: 1サービングの重量（グラム）
            household_unit: 解析された家庭用単位
            product_description: 製品説明

        Returns:
            代替単位での栄養価リスト
        """
        alternatives = []

        if household_unit.unit_type == "volume":
            # 体積単位での栄養価
            if household_unit.volume_equivalent_ml:
                estimated_weight = self.estimate_weight_from_volume(
                    household_unit.volume_equivalent_ml, product_description
                )
                if estimated_weight:
                    ratio = estimated_weight / 100.0
                    nutrients = {k: v * ratio if v else None for k, v in base_nutrients.items()}
                    alternatives.append({
                        "unit_description": f"per {household_unit.quantity} {household_unit.unit}",
                        **nutrients
                    })

                    # 1単位あたり
                    if household_unit.quantity != 1.0:
                        single_ratio = estimated_weight / (100.0 * household_unit.quantity)
                        single_nutrients = {k: v * single_ratio if v else None for k, v in base_nutrients.items()}
                        alternatives.append({
                            "unit_description": f"per 1 {household_unit.unit}",
                            **single_nutrients
                        })

        elif household_unit.unit_type == "count":
            # 個数単位での栄養価
            serving_ratio = serving_weight_g / 100.0
            total_nutrients = {k: v * serving_ratio if v else None for k, v in base_nutrients.items()}

            # 1個あたり
            if household_unit.quantity > 0:
                single_ratio = serving_ratio / household_unit.quantity
                single_nutrients = {k: v * single_ratio if v else None for k, v in base_nutrients.items()}
                alternatives.append({
                    "unit_description": f"per 1 {household_unit.unit}",
                    **single_nutrients
                })

        return alternatives