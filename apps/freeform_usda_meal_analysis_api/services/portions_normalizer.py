"""
Portions Normalizer Service

USDAメタデータのportionsフィールドを正規化し、
アプリのUI用に使いやすい単位リストを生成する。

主な機能:
- 数量の正規化 (3.0 oz → 1 oz あたりに換算)
- 単位名の正規化 (tablespoon → tbsp)
- 不要なエントリの除外 (Quantity not specified, yields等)
- 重複の除去 (同じ単位で複数ある場合はNFS優先)
"""

import re
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class NormalizedUnit:
    """正規化された単位"""
    name: str           # 表示名 (例: "cup", "oz")
    abbreviation: str   # 略称 (例: "cup", "oz")
    grams_per_unit: float  # 1単位あたりのグラム数
    original_description: str  # 元のdescription
    is_base_unit: bool = False  # gの場合True


# 単位の正規化マッピング
UNIT_MAPPING = {
    # cup系
    'cup': ('cup', 'cup'),
    'cups': ('cup', 'cup'),
    # oz系 (fl oz除外)
    'oz': ('oz', 'oz'),
    'ounce': ('oz', 'oz'),
    'ounces': ('oz', 'oz'),
    # fl oz系
    'fl': ('fl oz', 'fl oz'),  # "fl oz" の先頭
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
    # サイズ系
    'large': ('large', 'lg'),
    'medium': ('medium', 'md'),
    'small': ('small', 'sm'),
    'extra-large': ('extra large', 'xl'),
    'regular': ('regular', 'reg'),
    # lb系
    'lb': ('lb', 'lb'),
    'pound': ('lb', 'lb'),
    'pounds': ('lb', 'lb'),
    # その他よく使われる単位
    'can': ('can', 'can'),
    'bottle': ('bottle', 'btl'),
    'container': ('container', 'cont'),
    'package': ('package', 'pkg'),
    'packet': ('packet', 'pkt'),
    'pouch': ('pouch', 'pouch'),
    'jar': ('jar', 'jar'),
    'bar': ('bar', 'bar'),
    'patty': ('patty', 'patty'),
    'link': ('link', 'link'),
    'strip': ('strip', 'strip'),
    'stick': ('stick', 'stick'),
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
    # 食品形状
    'egg': ('egg', 'egg'),
    'fruit': ('fruit', 'fruit'),
    'item': ('item', 'item'),
    'unit': ('unit', 'unit'),
    'sandwich': ('sandwich', 'sand'),
    'cookie': ('cookie', 'cookie'),
    'cracker': ('cracker', 'cracker'),
    'pretzel': ('pretzel', 'pretzel'),
    'scoop': ('scoop', 'scoop'),
    'drink': ('drink', 'drink'),
    # 特殊形状
    'tube': ('tube', 'tube'),
    'cone': ('cone', 'cone'),
    'individual': ('individual', 'indiv'),
    'personal': ('personal', 'pers'),
    'miniature': ('mini', 'mini'),
    'miniature/bite': ('mini', 'mini'),
    'miniature/slider': ('mini', 'mini'),
    'baby': ('baby', 'baby'),
}

# 除外すべきパターン
EXCLUDE_PATTERNS = [
    'quantity not specified',
    'guideline',
    'yields',  # "1 oz yields" は調理後換算なので除外
    'nlea',    # NLEA serving は規制用
]


def _should_exclude(description: str) -> bool:
    """除外すべきdescriptionかどうか判定"""
    desc_lower = description.lower()
    return any(pattern in desc_lower for pattern in EXCLUDE_PATTERNS)


def _extract_quantity_and_unit(description: str) -> tuple[float, str]:
    """
    descriptionから数量と単位部分を抽出

    例:
    "3.0 oz" → (3.0, "oz")
    "1 cup, shredded" → (1.0, "cup, shredded")
    "Quantity not specified" → (1.0, "quantity not specified")
    """
    match = re.match(r'^([\d.]+)\s*(.+)', description.strip())
    if match:
        try:
            qty = float(match.group(1))
            unit_part = match.group(2).strip()
            return (qty, unit_part)
        except ValueError:
            pass
    return (1.0, description.strip())


def _normalize_unit_name(unit_part: str) -> Optional[tuple[str, str]]:
    """
    単位部分を正規化して (name, abbreviation) を返す

    マッチしない場合はNoneを返す
    """
    unit_lower = unit_part.lower()

    # fl oz の特別処理
    if unit_lower.startswith('fl oz') or unit_lower.startswith('fl. oz'):
        return ('fl oz', 'fl oz')
    if unit_lower.startswith('fluid oz'):
        return ('fl oz', 'fl oz')

    # 最初の単語を取得（カンマや括弧の前まで）
    first_word = re.split(r'[,\s(]', unit_lower)[0].rstrip(',.')

    if first_word in UNIT_MAPPING:
        return UNIT_MAPPING[first_word]

    return None


def _is_plain_description(description: str, unit_part: str) -> bool:
    """
    修飾語なしのシンプルなdescriptionかどうか判定
    (NFS優先のため)
    """
    desc_lower = description.lower()
    unit_lower = unit_part.lower()

    # "NFS" が含まれている場合は優先
    if 'nfs' in desc_lower:
        return True

    # 単位のみ（修飾語なし）の場合
    # 例: "1 cup" vs "1 cup, shredded"
    words = re.split(r'[,\s(]', unit_lower)
    words = [w.strip() for w in words if w.strip()]

    return len(words) <= 1


def normalize_portion(
    description: str,
    gram_weight: float
) -> Optional[NormalizedUnit]:
    """
    単一のportionエントリを正規化

    Args:
        description: portionのdescription (例: "3.0 oz")
        gram_weight: グラム重量

    Returns:
        NormalizedUnit または None (除外すべき場合)
    """
    if gram_weight <= 0:
        return None

    if _should_exclude(description):
        return None

    qty, unit_part = _extract_quantity_and_unit(description)

    if qty <= 0:
        return None

    # 1単位あたりのグラム数を計算
    grams_per_unit = gram_weight / qty

    # 単位名の正規化
    normalized = _normalize_unit_name(unit_part)

    if normalized is None:
        return None

    name, abbreviation = normalized

    return NormalizedUnit(
        name=name,
        abbreviation=abbreviation,
        grams_per_unit=round(grams_per_unit, 2),
        original_description=description,
        is_base_unit=False
    )


def normalize_portions_for_food(
    portions: Optional[list[dict]],
    include_gram: bool = True
) -> list[NormalizedUnit]:
    """
    食品のportionsリストを正規化してUI用の単位リストを生成

    戦略:
    1. 除外パターンをフィルタリング
    2. 数量が1以外の場合は1単位あたりに換算
    3. 同じ単位で複数ある場合はNFS/plain優先
    4. gは常に先頭に追加（オプション）

    Args:
        portions: USDAメタデータのportionsリスト
        include_gram: gを常に含めるか

    Returns:
        正規化された単位リスト
    """
    result = []

    # gを先頭に追加
    if include_gram:
        result.append(NormalizedUnit(
            name='g',
            abbreviation='g',
            grams_per_unit=1.0,
            original_description='gram (base unit)',
            is_base_unit=True
        ))

    if not portions:
        return result

    # 単位ごとに候補を収集
    # key: normalized_name, value: list of (NormalizedUnit, is_plain)
    candidates: dict[str, list[tuple[NormalizedUnit, bool]]] = {}

    for portion in portions:
        desc = portion.get('description', '')
        gw = portion.get('gram_weight', 0)

        if not desc or not gw:
            continue

        normalized = normalize_portion(desc, gw)

        if normalized is None:
            continue

        qty, unit_part = _extract_quantity_and_unit(desc)
        is_plain = _is_plain_description(desc, unit_part)

        if normalized.name not in candidates:
            candidates[normalized.name] = []

        candidates[normalized.name].append((normalized, is_plain))

    # 各単位から最適なものを選択
    for unit_name, unit_candidates in candidates.items():
        # plain (NFS/修飾語なし) を優先
        unit_candidates.sort(key=lambda x: (not x[1], x[0].grams_per_unit))
        best = unit_candidates[0][0]
        result.append(best)

    return result


def normalize_all_metadata(
    metadata: list[dict],
    include_gram: bool = True
) -> dict[str, dict]:
    """
    全メタデータを正規化

    Args:
        metadata: USDAメタデータのリスト
        include_gram: gを常に含めるか

    Returns:
        fdc_id -> {description, units: [...]} のdict
    """
    result = {}

    for item in metadata:
        fdc_id = str(item.get('fdc_id', item.get('id', '')))
        description = item.get('description', '')
        portions = item.get('portions', [])

        units = normalize_portions_for_food(portions, include_gram)

        result[fdc_id] = {
            'description': description,
            'units': [asdict(u) for u in units]
        }

    return result


def generate_validation_report(
    metadata: list[dict],
    normalized_data: dict[str, dict]
) -> dict:
    """
    正規化結果の検証レポートを生成

    Returns:
        検証レポート (統計情報、問題点等)
    """
    total = len(metadata)

    # 統計
    units_count = {}  # 単位名 -> 出現食品数
    grams_per_unit_stats = {}  # 単位名 -> [grams_per_unit values]
    foods_without_db_units = []  # gのみの食品
    foods_with_many_units = []  # 5個以上の単位を持つ食品

    for fdc_id, data in normalized_data.items():
        units = data['units']

        # gのみの食品
        non_base_units = [u for u in units if not u.get('is_base_unit', False)]
        if len(non_base_units) == 0:
            foods_without_db_units.append({
                'fdc_id': fdc_id,
                'description': data['description']
            })

        # 5個以上の単位
        if len(units) >= 5:
            foods_with_many_units.append({
                'fdc_id': fdc_id,
                'description': data['description'],
                'unit_count': len(units)
            })

        # 単位ごとの統計
        for unit in units:
            name = unit['name']
            grams = unit['grams_per_unit']

            if name not in units_count:
                units_count[name] = 0
                grams_per_unit_stats[name] = []

            units_count[name] += 1
            if not unit.get('is_base_unit', False):
                grams_per_unit_stats[name].append(grams)

    # grams_per_unitの統計を計算
    grams_stats = {}
    for name, values in grams_per_unit_stats.items():
        if values:
            grams_stats[name] = {
                'count': len(values),
                'min': round(min(values), 2),
                'max': round(max(values), 2),
                'avg': round(sum(values) / len(values), 2)
            }

    return {
        'summary': {
            'total_foods': total,
            'foods_with_db_units': total - len(foods_without_db_units),
            'foods_without_db_units': len(foods_without_db_units),
            'coverage_rate': round((total - len(foods_without_db_units)) / total * 100, 1)
        },
        'unit_coverage': dict(sorted(
            units_count.items(),
            key=lambda x: x[1],
            reverse=True
        )),
        'grams_per_unit_stats': grams_stats,
        'issues': {
            'foods_without_db_units_sample': foods_without_db_units[:20],
            'foods_with_many_units_sample': foods_with_many_units[:10]
        }
    }


# CLI用のエントリポイント
if __name__ == '__main__':
    import json
    import sys
    from pathlib import Path

    # メタデータ読み込み
    data_path = Path(__file__).parent.parent / 'data' / 'faiss' / 'usda_metadata.json'

    if not data_path.exists():
        print(f"Error: {data_path} not found")
        sys.exit(1)

    print(f"Loading metadata from {data_path}...")
    with open(data_path, 'r') as f:
        metadata = json.load(f)

    print(f"Loaded {len(metadata)} items")

    # 正規化実行
    print("Normalizing portions...")
    normalized = normalize_all_metadata(metadata)

    # 検証レポート生成
    print("Generating validation report...")
    report = generate_validation_report(metadata, normalized)

    # 結果を出力
    output_dir = Path(__file__).parent.parent / 'data'

    # 正規化データ出力
    normalized_path = output_dir / 'normalized_portions.json'
    with open(normalized_path, 'w') as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)
    print(f"Saved normalized data to {normalized_path}")

    # レポート出力
    report_path = output_dir / 'portions_validation_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Saved validation report to {report_path}")

    # サマリー表示
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    print(f"Total foods: {report['summary']['total_foods']}")
    print(f"Foods with DB units: {report['summary']['foods_with_db_units']}")
    print(f"Foods without DB units (g only): {report['summary']['foods_without_db_units']}")
    print(f"Coverage rate: {report['summary']['coverage_rate']}%")
    print("\nTop 10 units by coverage:")
    for i, (unit, count) in enumerate(list(report['unit_coverage'].items())[:10]):
        print(f"  {unit}: {count} foods")
