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


def normalize_compound_words(text: str) -> str:
    """
    正規化: 複合語や表記ゆれを統一
    
    Args:
        text: 入力テキスト
    
    Returns:
        正規化されたテキスト
    
    Examples:
        >>> normalize_compound_words("cherry tomatoes")
        'tomatoes cherry'
        >>> normalize_compound_words("green onion")
        'scallion'
    """
    # 小文字化
    text_lower = text.lower().strip()
    
    # 複合語マッピング（検索精度向上のため）
    compound_mappings = {
        # Vegetables
        "cherry tomatoes": "tomatoes cherry",
        "cherry tomato": "tomatoes cherry",
        "grape tomatoes": "tomatoes cherry",
        "green onion": "scallion",
        "green onions": "scallion",
        "spring onion": "scallion",
        "spring onions": "scallion",
        "yellow squash": "squash summer yellow",
        "zucchini squash": "squash summer",
        
        # Meats
        "beef steak": "steak beef",
        "pork chop": "chop pork",
        "chicken breast": "breast chicken",
        "chicken thigh": "thigh chicken",
        
        # Grains
        "brown rice": "rice brown",
        "white rice": "rice white",
        "wild rice": "rice wild",
        
        # Dairy
        "greek yogurt": "yogurt greek",
        "sour cream": "cream sour",
        
        # Others
        "sweet potato": "potato sweet",
        "sweet potatoes": "potato sweet",
        "red wine": "wine red",
        "white wine": "wine white",
    }
    
    # マッピング適用
    normalized = compound_mappings.get(text_lower, text_lower)
    
    # 複数形を単数形に（基本的な変換のみ）
    # より高度な複数形処理が必要な場合はinflectライブラリを使用
    if normalized.endswith('ies'):
        normalized = normalized[:-3] + 'y'
    elif normalized.endswith('es') and not normalized.endswith(('ches', 'shes', 'sses', 'xes')):
        normalized = normalized[:-2]
    elif normalized.endswith('s') and not normalized.endswith('ss'):
        # 単純なs除去（過度な変換を避けるため慎重に）
        # asparagus, broccoli などは変換しない
        singular_exceptions = ['asparagus', 'broccoli', 'lettuce', 'cabbage', 'spinach']
        if not any(normalized.endswith(exc) for exc in singular_exceptions):
            normalized = normalized[:-1]
    
    return normalized


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


# =============================================================================
# spec3.md方針: 二系統テキスト生成（Stage1用）
# =============================================================================

def build_main_only_text(main_name: str) -> str:
    """
    主食材名のみのテキストを生成（Stage1のmain_only埋め込み用）

    目的: 主名の取り違え防止（"fried rice" vs "fried chicken"）
    Phase 1改善: 複合語の正規化を適用

    Args:
        main_name: 主食材名

    Returns:
        主食材名のみ（複合語正規化済み）

    Examples:
        >>> build_main_only_text("cherry tomatoes")
        'tomatoes cherry'
        >>> build_main_only_text("Chicken")
        'chicken'
    """
    # 複合語の正規化を適用
    normalized = normalize_compound_words(main_name)
    return normalized


def build_full_text(main_name: str, descriptors: str = "") -> str:
    """
    主食材名 + セパレータ + 修飾語のテキストを生成（Stage1のfull埋め込み用）

    目的: 意味的な近傍を考慮しつつ、主名と修飾を明示的に区切る
    セパレータ ';' で主名と修飾を区別
    Phase 1改善: 複合語の正規化を適用

    Args:
        main_name: 主食材名
        descriptors: 修飾語（調理法、状態等）

    Returns:
        "main_name ; descriptors" 形式のテキスト（複合語正規化済み）

    Examples:
        >>> build_full_text("cherry tomatoes", "raw")
        'tomatoes cherry ; raw'
        >>> build_full_text("Chicken", "broilers, breast, cooked, roasted")
        'chicken ; broilers breast cooked roasted'
    """
    # 複合語の正規化を適用
    normalized_main = normalize_compound_words(main_name)
    
    if descriptors:
        # カンマを削除してスペース区切りに
        desc_clean = descriptors.replace(',', ' ')
        desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()
        return f"{normalized_main} ; {desc_clean}"
    return normalized_main


# =============================================================================
# spec3.md方針: フィールド明示テンプレート（Stage2用）
# =============================================================================

def build_rerank_text(main_name: str, descriptors: str = "", is_query: bool = True) -> str:
    """
    再ランキング用のフィールド明示テキストを生成（Stage2用）

    目的: BGE-rerankerにフィールドラベルで主名を明示的に強調

    Args:
        main_name: 主食材名
        descriptors: 修飾語（調理法、状態等）
        is_query: クエリ側かどうか（True: query, False: candidate）

    Returns:
        "name: ...\ndescription: ..." 形式のテキスト

    Examples:
        >>> build_rerank_text("chicken breast", "grilled", is_query=True)
        'name: chicken breast\\ndescription: grilled'
        >>> build_rerank_text("Chicken", "broilers, cooked, roasted", is_query=False)
        'name: Chicken\\ndescription: broilers, cooked, roasted'
        >>> build_rerank_text("rice", "", is_query=True)
        'name: rice\\ndescription: N/A'
    """
    name_field = main_name.strip() if main_name else "N/A"
    desc_field = descriptors.strip() if descriptors else "N/A"

    return f"name: {name_field}\ndescription: {desc_field}"