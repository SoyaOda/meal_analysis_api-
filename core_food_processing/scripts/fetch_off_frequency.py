#!/usr/bin/env python3
"""
fetch_off_frequency.py

Open Food Facts APIから頻度データを取得して、
FoodOnから抽出した料理/食材にスコアを付与するスクリプト

spec2.mdに基づく実装：
- OFF facet APIでカテゴリ・原材料のヒット件数を取得
- レート制限対策でバッチ化＆キャッシュ

Usage:
    python core_food_processing/scripts/fetch_off_frequency.py
"""

import sys
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).parent.parent.parent

try:
    import requests
except ImportError:
    print("❌ エラー: requestsがインストールされていません")
    print("次のコマンドでインストールしてください:")
    print("  pip install requests")
    sys.exit(1)


# Open Food Facts API設定
OFF_API_BASE = "https://world.openfoodfacts.org/api/v2"
OFF_SEARCH_URL = f"{OFF_API_BASE}/search"

# リクエスト間隔（秒）- レート制限対策
REQUEST_INTERVAL = 0.5

# キャッシュディレクトリ
CACHE_DIR = PROJECT_ROOT / "core_food_processing" / "output" / "off_cache"


def normalize_for_search(text: str) -> str:
    """
    検索用に正規化

    Args:
        text: 元のテキスト

    Returns:
        正規化されたテキスト
    """
    # 小文字化
    text = text.lower()

    # 括弧内の情報を削除
    text = re.sub(r'\([^)]*\)', '', text)

    # 余分な空白を削除
    text = ' '.join(text.split())

    return text.strip()


def search_off_product_count(query: str, search_type: str = "category") -> int:
    """
    Open Food Facts APIで製品数を検索

    Args:
        query: 検索クエリ
        search_type: "category" または "ingredient"

    Returns:
        製品数（ヒット件数）
    """
    # 正規化
    normalized_query = normalize_for_search(query)

    # キャッシュ確認
    cache_file = CACHE_DIR / f"{search_type}_{normalized_query.replace(' ', '_')}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                return cache_data.get('count', 0)
        except:
            pass

    # APIリクエスト
    params = {
        'page_size': 1,  # 件数だけ取得
        'fields': 'none',  # フィールドは不要
    }

    # カテゴリまたは原材料で検索
    if search_type == "category":
        params['categories_tags'] = normalized_query
    elif search_type == "ingredient":
        params['ingredients_tags'] = normalized_query
    else:
        # 一般検索
        params['search_terms'] = normalized_query

    try:
        response = requests.get(OFF_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        count = data.get('count', 0)

        # キャッシュに保存
        CACHE_DIR.mkdir(exist_ok=True, parents=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({'query': query, 'normalized_query': normalized_query, 'count': count}, f, indent=2)

        # レート制限対策
        time.sleep(REQUEST_INTERVAL)

        return count

    except Exception as e:
        print(f"⚠️  警告: API呼び出しエラー ({query}): {e}")
        return 0


def main():
    """メイン処理"""
    print("="*80)
    print("Open Food Facts 頻度データ取得スクリプト")
    print("="*80)
    print()

    # 入力ファイル
    dishes_json = PROJECT_ROOT / "core_food_processing" / "output" / "dishes_raw.json"
    ingredients_json = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_raw.json"

    if not dishes_json.exists() or not ingredients_json.exists():
        print("❌ エラー: 入力ファイルが存在しません")
        print(f"   {dishes_json}")
        print(f"   {ingredients_json}")
        print()
        print("まず extract_foodon_with_reasoner.py を実行してください")
        sys.exit(1)

    # データを読み込み
    print("📖 FoodOnデータを読み込み中...")
    with open(dishes_json, 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    with open(ingredients_json, 'r', encoding='utf-8') as f:
        ingredients = json.load(f)

    print(f"  料理候補: {len(dishes):,} 項目")
    print(f"  食材候補: {len(ingredients):,} 項目")
    print()

    # キャッシュディレクトリを作成
    CACHE_DIR.mkdir(exist_ok=True, parents=True)

    # 料理候補に頻度を付与
    print("🔍 料理候補のOFF頻度を取得中...")
    print(f"   ※ {len(dishes):,}項目 × API呼び出し = 時間がかかります")
    print(f"   （既存のキャッシュがある場合は再利用されます）")
    print()

    for i, dish in enumerate(dishes, 1):
        if i % 100 == 0:
            print(f"   進捗: {i:,} / {len(dishes):,} ({i*100//len(dishes)}%)")

        label = dish['label']

        # カテゴリとして検索
        category_count = search_off_product_count(label, "category")

        # 一般検索でも試す
        general_count = search_off_product_count(label, "general")

        # より多い方を採用
        dish['off_count'] = max(category_count, general_count)

    print(f"   完了: {len(dishes):,} 項目")
    print()

    # 食材候補に頻度を付与
    print("🔍 食材候補のOFF頻度を取得中...")
    print(f"   ※ {len(ingredients):,}項目 × API呼び出し = 時間がかかります")
    print()

    for i, ingredient in enumerate(ingredients, 1):
        if i % 100 == 0:
            print(f"   進捗: {i:,} / {len(ingredients):,} ({i*100//len(ingredients)}%)")

        label = ingredient['label']

        # 原材料として検索
        ingredient_count = search_off_product_count(label, "ingredient")

        # 一般検索でも試す
        general_count = search_off_product_count(label, "general")

        # より多い方を採用
        ingredient['off_count'] = max(ingredient_count, general_count)

    print(f"   完了: {len(ingredients):,} 項目")
    print()

    # 結果を保存
    output_dir = PROJECT_ROOT / "core_food_processing" / "output"
    dishes_with_freq = output_dir / "dishes_with_off_freq.json"
    ingredients_with_freq = output_dir / "ingredients_with_off_freq.json"

    print("💾 結果を保存中...")
    with open(dishes_with_freq, 'w', encoding='utf-8') as f:
        json.dump(dishes, f, indent=2, ensure_ascii=False)
    print(f"  料理候補: {dishes_with_freq}")

    with open(ingredients_with_freq, 'w', encoding='utf-8') as f:
        json.dump(ingredients, f, indent=2, ensure_ascii=False)
    print(f"  食材候補: {ingredients_with_freq}")
    print()

    # 統計情報
    print("="*80)
    print("統計情報")
    print("="*80)

    # 料理の統計
    dish_counts = [d['off_count'] for d in dishes]
    dish_with_hits = [c for c in dish_counts if c > 0]
    print(f"料理候補:")
    print(f"  総数: {len(dishes):,}")
    print(f"  OFFでヒットした項目: {len(dish_with_hits):,} ({len(dish_with_hits)*100//len(dishes)}%)")
    if dish_with_hits:
        print(f"  平均ヒット数: {sum(dish_with_hits)//len(dish_with_hits):,}")
        print(f"  最大ヒット数: {max(dish_with_hits):,}")
    print()

    # 食材の統計
    ing_counts = [i['off_count'] for i in ingredients]
    ing_with_hits = [c for c in ing_counts if c > 0]
    print(f"食材候補:")
    print(f"  総数: {len(ingredients):,}")
    print(f "  OFFでヒットした項目: {len(ing_with_hits):,} ({len(ing_with_hits)*100//len(ingredients)}%)")
    if ing_with_hits:
        print(f"  平均ヒット数: {sum(ing_with_hits)//len(ing_with_hits):,}")
        print(f"  最大ヒット数: {max(ing_with_hits):,}")
    print()

    # トップ10を表示
    print("料理候補トップ10（OFFヒット数）:")
    print("-"*80)
    dishes_sorted = sorted(dishes, key=lambda x: x['off_count'], reverse=True)
    for i, dish in enumerate(dishes_sorted[:10], 1):
        print(f"{i:3d}. {dish['label']:50s} ({dish['off_count']:,} ヒット)")
    print()

    print("食材候補トップ10（OFFヒット数）:")
    print("-"*80)
    ingredients_sorted = sorted(ingredients, key=lambda x: x['off_count'], reverse=True)
    for i, ing in enumerate(ingredients_sorted[:10], 1):
        print(f"{i:3d}. {ing['label']:50s} ({ing['off_count']:,} ヒット)")
    print()

    print("✅ 次のステップ:")
    print("  1. スコアリング（0.5*log1p(OFF) + 0.4*log1p(Recipe1M) + 0.1*WWEIA）")
    print("  2. 上位選択（Base ~600、Ingredient ~1000）")
    print("  3. CORE食品リストの生成")
    print()


if __name__ == "__main__":
    main()
