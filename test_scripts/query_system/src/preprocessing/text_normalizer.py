"""
テキスト正規化モジュール

クエリとUSDA食品名の正規化を提供します。
"""

import re
from typing import Tuple


def normalize_text(text: str) -> str:
    """
    テキストを正規化

    Args:
        text: 正規化するテキスト

    Returns:
        正規化後のテキスト（小文字、アルファベットとスペースのみ）

    Examples:
        >>> normalize_text("Chicken, Broiled")
        'chicken broiled'
        >>> normalize_text("French-Fries (Deep-Fried)")
        'french fries deep fried'
    """
    if not text:
        return ""

    # 小文字化
    text = text.lower()

    # 特殊文字を削除（アルファベットとスペースのみ残す）
    text = re.sub(r'[^a-z\s]', ' ', text)

    # 複数スペースを単一スペースに
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def parse_usda_name(usda_name: str) -> Tuple[str, str]:
    """
    USDA名から search_name と description を抽出

    USDA形式: "Num. search_name, description1, description2"
    例: "11001. Chicken, broilers or fryers, breast, meat only, cooked, roasted"
        → search_name="Chicken", description="broilers or fryers, breast, meat only, cooked, roasted"

    Args:
        usda_name: USDA食品名（"Num. " プレフィックスを含むまたは含まない）

    Returns:
        (search_name, description) のタプル

    Examples:
        >>> parse_usda_name("11001. Chicken, broilers, breast, cooked")
        ('Chicken', 'broilers, breast, cooked')
        >>> parse_usda_name("Chicken breast")
        ('Chicken breast', '')
    """
    # "Num. " プレフィックスを除去
    if '. ' in usda_name:
        parts = usda_name.split('. ', 1)
        name_part = parts[1] if len(parts) > 1 else usda_name
    else:
        name_part = usda_name

    # カンマで分割
    components = [c.strip() for c in name_part.split(',')]
    search_name = components[0] if components else ""
    description = ', '.join(components[1:]) if len(components) > 1 else ""

    return search_name, description


def build_query_text(search_name: str, description: str = "") -> str:
    """
    search_name と description を結合して正規化前のクエリテキストを作成

    Args:
        search_name: 食品名（主要部分）
        description: 食品の説明（オプション）

    Returns:
        結合後の正規化前テキスト

    Examples:
        >>> build_query_text("chicken breast", "grilled")
        'chicken breast grilled'
        >>> build_query_text("rice", "")
        'rice'
    """
    if description:
        return f"{search_name} {description}".strip()
    return search_name.strip()


def build_usda_text(usda_item: dict) -> str:
    """
    USDAアイテム辞書から埋め込み用テキスト（正規化前）を作成

    Args:
        usda_item: USDA食品アイテム（'default_usda.name' を含む）

    Returns:
        正規化前テキスト（search_name + description）

    Examples:
        >>> item = {"default_usda": {"name": "11001. Chicken, broiled, skinless"}}
        >>> build_usda_text(item)
        'Chicken broiled, skinless'
    """
    if 'default_usda' not in usda_item or 'name' not in usda_item['default_usda']:
        return ""

    usda_name = usda_item['default_usda']['name']
    search_name, description = parse_usda_name(usda_name)

    return build_query_text(search_name, description)