"""
Unit Normalizer Service

バーコードAPIのunit_optionsを正規化し、
freeform_usda_meal_analysis_apiのNormalizedUnit形式と互換性のある出力を生成する。

USDA FDCとOpen Food Factsの両方のデータソースに対応。
"""

import re
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class NormalizedUnit:
    """
    正規化された単位（freeform_usda_meal_analysis_apiと互換性のある形式）

    Flutterアプリの ServingUnit.fromBarcodeUnitOptions() で直接使用可能
    """
    name: str           # 表示名 (例: "cup", "oz", "serving")
    abbreviation: str   # 略称 (例: "cup", "oz", "srv")
    grams_per_unit: float  # 1単位あたりのグラム数
    original_description: str  # 元のdescription
    is_base_unit: bool = False  # gの場合True


# 単位の正規化マッピング（freeform APIと同一）
# USDAメタデータ分析に基づき、出現頻度の高い単位を網羅（カバー率74%）
UNIT_MAPPING = {
    # 基本単位
    'g': ('g', 'g'),
    'gram': ('g', 'g'),
    'grams': ('g', 'g'),
    'ml': ('ml', 'ml'),
    'milliliter': ('ml', 'ml'),
    'milliliters': ('ml', 'ml'),
    # cup系
    'cup': ('cup', 'cup'),
    'cups': ('cup', 'cup'),
    # oz系 (fl oz除外)
    'oz': ('oz', 'oz'),
    'ounce': ('oz', 'oz'),
    'ounces': ('oz', 'oz'),
    # fl oz系
    'fl': ('fl oz', 'fl oz'),
    # tbsp系
    'tbsp': ('tbsp', 'tbsp'),
    'tablespoon': ('tbsp', 'tbsp'),
    'tablespoons': ('tbsp', 'tbsp'),
    # tsp系
    'tsp': ('tsp', 'tsp'),
    'teaspoon': ('tsp', 'tsp'),
    'teaspoons': ('tsp', 'tsp'),
    # slice系
    'slice': ('slice', 'slice'),
    'slices': ('slice', 'slice'),
    # piece系
    'piece': ('piece', 'pc'),
    'pieces': ('piece', 'pc'),
    'piece/slice': ('piece', 'pc'),
    # serving系
    'serving': ('serving', 'srv'),
    'servings': ('serving', 'srv'),
    'portion': ('portion', 'portion'),
    # サイズ系
    'large': ('large', 'lg'),
    'medium': ('medium', 'md'),
    'small': ('small', 'sm'),
    'extra-large': ('extra large', 'xl'),
    'extra': ('extra large', 'xl'),
    'regular': ('regular', 'reg'),
    'mini': ('mini', 'mini'),
    'bite': ('bite', 'bite'),
    'single': ('single', 'single'),
    'thin': ('thin', 'thin'),
    'thick': ('thick', 'thick'),
    # lb系
    'lb': ('lb', 'lb'),
    'pound': ('lb', 'lb'),
    'pounds': ('lb', 'lb'),
    # 体積単位
    'quart': ('quart', 'qt'),
    'pint': ('pint', 'pt'),
    'gallon': ('gallon', 'gal'),
    # 容器系
    'can': ('can', 'can'),
    'bottle': ('bottle', 'btl'),
    'container': ('container', 'cont'),
    'package': ('package', 'pkg'),
    'packet': ('packet', 'pkt'),
    'pouch': ('pouch', 'pouch'),
    'jar': ('jar', 'jar'),
    'tub': ('tub', 'tub'),
    'box': ('box', 'box'),
    # バー・スティック系
    'bar': ('bar', 'bar'),
    'stick': ('stick', 'stick'),
    'strip': ('strip', 'strip'),
    'link': ('link', 'link'),
    # 分量系
    'whole': ('whole', 'whole'),
    'half': ('half', 'half'),
    'quarter': ('quarter', 'qtr'),
    # 肉類
    'fillet': ('fillet', 'fillet'),
    'breast': ('breast', 'breast'),
    'thigh': ('thigh', 'thigh'),
    'wing': ('wing', 'wing'),
    'leg': ('leg', 'leg'),
    'drumstick': ('drumstick', 'drum'),
    'chop': ('chop', 'chop'),
    'steak': ('steak', 'steak'),
    'roast': ('roast', 'roast'),
    'patty': ('patty', 'patty'),
    'cutlet': ('cutlet', 'cutlet'),
    'rib': ('rib', 'rib'),
    # 野菜・果物
    'leaf': ('leaf', 'leaf'),
    'leaves': ('leaf', 'leaf'),
    'spear': ('spear', 'spear'),
    'fruit': ('fruit', 'fruit'),
    'head': ('head', 'head'),
    'ear': ('ear', 'ear'),
    'clove': ('clove', 'clove'),
    # ベーキング・スナック系
    'cookie': ('cookie', 'cookie'),
    'cookies': ('cookie', 'cookie'),
    'cracker': ('cracker', 'cracker'),
    'crackers': ('cracker', 'cracker'),
    'chip': ('chip', 'chip'),
    'chips': ('chip', 'chip'),
    'pretzel': ('pretzel', 'pretzel'),
    'pretzels': ('pretzel', 'pretzel'),
    'muffin': ('muffin', 'muffin'),
    'cake': ('cake', 'cake'),
    'pie': ('pie', 'pie'),
    'roll': ('roll', 'roll'),
    'biscuit': ('biscuit', 'biscuit'),
    'wafer': ('wafer', 'wafer'),
    'brownie': ('brownie', 'brownie'),
    'donut': ('donut', 'donut'),
    'doughnut': ('donut', 'donut'),
    'bagel': ('bagel', 'bagel'),
    'croissant': ('croissant', 'croissant'),
    'pancake': ('pancake', 'pancake'),
    'waffle': ('waffle', 'waffle'),
    # 食事系
    'sandwich': ('sandwich', 'sand'),
    'pizza': ('pizza', 'pizza'),
    'burger': ('burger', 'burger'),
    'taco': ('taco', 'taco'),
    'wrap': ('wrap', 'wrap'),
    'submarine': ('sub', 'sub'),
    'sub': ('sub', 'sub'),
    # その他食品形状
    'egg': ('egg', 'egg'),
    'item': ('item', 'item'),
    'unit': ('unit', 'unit'),
    'scoop': ('scoop', 'scoop'),
    'drink': ('drink', 'drink'),
    'nut': ('nut', 'nut'),
    'kernel': ('kernel', 'kernel'),
    'ring': ('ring', 'ring'),
    'ball': ('ball', 'ball'),
    'cube': ('cube', 'cube'),
    'wedge': ('wedge', 'wedge'),
    'square': ('square', 'sq'),
    # 特殊形状
    'tube': ('tube', 'tube'),
    'cone': ('cone', 'cone'),
    'individual': ('individual', 'indiv'),
    'personal': ('personal', 'pers'),
    'miniature': ('mini', 'mini'),
    'miniature/bite': ('mini', 'mini'),
    'miniature/slider': ('mini', 'mini'),
    'baby': ('baby', 'baby'),
    'snack': ('snack', 'snack'),
    # Open Food Facts追加単位
    'row': ('row', 'row'),
    'triangle': ('triangle', 'tri'),
    'triangles': ('triangle', 'tri'),
    'flatbread': ('flatbread', 'flatbread'),
    'tortilla': ('tortilla', 'tortilla'),
    'tin': ('tin', 'tin'),
    'shot': ('shot', 'shot'),
}


def _extract_quantity_and_unit(text: str) -> Tuple[Optional[float], str]:
    """
    テキストから数量と単位部分を抽出

    例:
    "15 g" → (15.0, "g")
    "1 can (330 ml)" → (1.0, "can")
    "2 cookies (30g)" → (2.0, "cookies")
    "0.25 cup" → (0.25, "cup")
    """
    if not text:
        return (None, "")

    text = text.strip()

    # パターン1: "数量 単位 (補足)" 形式
    match = re.match(r'^([\d.]+)\s*([a-zA-Z][a-zA-Z\s/]*?)(?:\s*\(.*\))?$', text)
    if match:
        try:
            qty = float(match.group(1))
            unit_part = match.group(2).strip()
            return (qty, unit_part)
        except ValueError:
            pass

    # パターン2: "数量単位" 形式（スペースなし）
    match = re.match(r'^([\d.]+)([a-zA-Z]+)$', text)
    if match:
        try:
            qty = float(match.group(1))
            unit_part = match.group(2).strip()
            return (qty, unit_part)
        except ValueError:
            pass

    return (None, text)


def _normalize_unit_name(unit_part: str) -> Optional[Tuple[str, str]]:
    """
    単位部分を正規化して (name, abbreviation) を返す
    """
    if not unit_part:
        return None

    unit_lower = unit_part.lower().strip()

    # fl oz の特別処理
    if unit_lower.startswith('fl oz') or unit_lower.startswith('fl. oz'):
        return ('fl oz', 'fl oz')
    if unit_lower.startswith('fluid oz'):
        return ('fl oz', 'fl oz')

    # 最初の単語を取得（カンマや括弧の前まで）
    first_word = re.split(r'[,\s(]', unit_lower)[0].rstrip(',.')

    if first_word in UNIT_MAPPING:
        return UNIT_MAPPING[first_word]

    # マッチしない場合はNoneを返す（数字のみや不明な単位を除外）
    # 数字のみの場合も除外
    if first_word.isdigit() or not first_word:
        return None

    # 英字で構成された不明な単位のみ許可（10文字以下）
    if first_word.isalpha() and len(first_word) <= 10:
        return (first_word, first_word)

    return None


class UnitNormalizer:
    """
    単位正規化サービス

    USDA FDCとOpen Food Factsの両方のデータから
    統一されたNormalizedUnit形式を生成する
    """

    def __init__(self):
        logger.info("UnitNormalizer initialized")

    def normalize_for_fdc(
        self,
        serving_size_g: Optional[float],
        household_serving_fulltext: Optional[str],
        product_description: Optional[str] = None
    ) -> List[NormalizedUnit]:
        """
        FDC (USDA) データからNormalizedUnitリストを生成

        Args:
            serving_size_g: サービングサイズ（グラム）
            household_serving_fulltext: 家庭用サービング表記 (例: "2 cookies (30g)")
            product_description: 製品説明（食品タイプ判定用）

        Returns:
            正規化された単位リスト
        """
        units = []

        # 1. gは常に先頭に追加
        units.append(NormalizedUnit(
            name='g',
            abbreviation='g',
            grams_per_unit=1.0,
            original_description='gram (base unit)',
            is_base_unit=True
        ))

        # 2. ozは常に追加（固定換算）
        units.append(NormalizedUnit(
            name='oz',
            abbreviation='oz',
            grams_per_unit=28.35,
            original_description='1 ounce',
            is_base_unit=False
        ))

        # 3. servingサイズがある場合
        if serving_size_g and serving_size_g > 0:
            units.append(NormalizedUnit(
                name='serving',
                abbreviation='srv',
                grams_per_unit=serving_size_g,
                original_description=f'1 serving ({serving_size_g}g)',
                is_base_unit=False
            ))

        # 4. household_serving_fulltextを解析
        if household_serving_fulltext:
            parsed = self._parse_household_serving(
                household_serving_fulltext,
                serving_size_g
            )
            if parsed and parsed.name not in [u.name for u in units]:
                units.append(parsed)

        return units

    def normalize_for_off(
        self,
        serving_size_text: Optional[str],
        serving_quantity_g: Optional[float],
        product_name: Optional[str] = None
    ) -> List[NormalizedUnit]:
        """
        Open Food Facts データからNormalizedUnitリストを生成

        Args:
            serving_size_text: サービングサイズテキスト (例: "15 g", "1 can (330 ml)")
            serving_quantity_g: サービング量（グラムまたはml）
            product_name: 製品名（食品タイプ判定用）

        Returns:
            正規化された単位リスト
        """
        units = []

        # 1. gは常に先頭に追加
        units.append(NormalizedUnit(
            name='g',
            abbreviation='g',
            grams_per_unit=1.0,
            original_description='gram (base unit)',
            is_base_unit=True
        ))

        # 2. ozは常に追加（固定換算）
        units.append(NormalizedUnit(
            name='oz',
            abbreviation='oz',
            grams_per_unit=28.35,
            original_description='1 ounce',
            is_base_unit=False
        ))

        # 3. serving_size_textを解析
        if serving_size_text:
            qty, unit_part = _extract_quantity_and_unit(serving_size_text)
            normalized = _normalize_unit_name(unit_part) if unit_part else None

            if normalized and serving_quantity_g and serving_quantity_g > 0:
                name, abbrev = normalized

                # 数量で割って1単位あたりのグラム数を計算
                grams_per_unit = serving_quantity_g
                if qty and qty > 0:
                    grams_per_unit = serving_quantity_g / qty

                # g, oz以外の場合のみ追加
                if name not in ['g', 'oz', 'ml']:
                    units.append(NormalizedUnit(
                        name=name,
                        abbreviation=abbrev,
                        grams_per_unit=round(grams_per_unit, 2),
                        original_description=serving_size_text,
                        is_base_unit=False
                    ))
                elif name == 'ml':
                    # mlの場合は密度1.0として追加
                    units.append(NormalizedUnit(
                        name='ml',
                        abbreviation='ml',
                        grams_per_unit=1.0,  # 水ベース
                        original_description=serving_size_text,
                        is_base_unit=False
                    ))

            # serving単位も追加（テキストがある場合）
            if serving_quantity_g and serving_quantity_g > 0:
                # 既にserving以外の単位が追加されている場合も、servingを追加
                if not any(u.name == 'serving' for u in units):
                    units.append(NormalizedUnit(
                        name='serving',
                        abbreviation='srv',
                        grams_per_unit=serving_quantity_g,
                        original_description=f'1 serving ({serving_quantity_g}g)',
                        is_base_unit=False
                    ))

        return units

    def _parse_household_serving(
        self,
        text: str,
        serving_size_g: Optional[float]
    ) -> Optional[NormalizedUnit]:
        """
        FDCのhousehold_serving_fulltextを解析

        例:
        "2 cookies (30g)" → NormalizedUnit(name='cookie', grams_per_unit=15.0)
        "0.25 cup" → NormalizedUnit(name='cup', grams_per_unit=serving_size_g/0.25)
        """
        if not text:
            return None

        qty, unit_part = _extract_quantity_and_unit(text)
        if not unit_part:
            return None

        normalized = _normalize_unit_name(unit_part)
        if not normalized:
            return None

        name, abbrev = normalized

        # g, ozは既に追加されているのでスキップ
        if name in ['g', 'oz']:
            return None

        # グラム数を計算
        grams_per_unit = None

        # テキストから直接グラム数を抽出 (例: "30g" in "(30g)")
        gram_match = re.search(r'\((\d+(?:\.\d+)?)\s*g\)', text)
        if gram_match and qty and qty > 0:
            total_grams = float(gram_match.group(1))
            grams_per_unit = total_grams / qty
        elif serving_size_g and qty and qty > 0:
            # serving_size_gを使用
            grams_per_unit = serving_size_g / qty

        if grams_per_unit and grams_per_unit > 0:
            return NormalizedUnit(
                name=name,
                abbreviation=abbrev,
                grams_per_unit=round(grams_per_unit, 2),
                original_description=text,
                is_base_unit=False
            )

        return None

    def to_dict_list(self, units: List[NormalizedUnit]) -> List[dict]:
        """
        NormalizedUnitリストを辞書リストに変換（APIレスポンス用）
        """
        return [asdict(u) for u in units]


# シングルトンインスタンス
_normalizer_instance: Optional[UnitNormalizer] = None


def get_unit_normalizer() -> UnitNormalizer:
    """UnitNormalizerのシングルトンインスタンスを取得"""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = UnitNormalizer()
    return _normalizer_instance
