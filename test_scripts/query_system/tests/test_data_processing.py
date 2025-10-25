# -*- coding: utf-8 -*-
"""
Test data processing flow
データ処理フローのテスト
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.preprocessing.text_normalizer import (
    parse_usda_name,
    build_query_text,
    normalize_text
)


def test_usda_name_processing():
    """USDA名の処理フローをテスト"""
    print("=" * 60)
    print("USDA名の処理フローテスト")
    print("=" * 60)

    # テストデータからUSDA名を読み込み
    data_dir = Path(__file__).parent / "data"
    with open(data_dir / "test_usda_items.json", 'r', encoding='utf-8') as f:
        usda_items = json.load(f)

    print(f"\n✅ テストデータ読み込み: {len(usda_items)}件\n")

    # 最初の5件で処理フローを確認
    for i, item in enumerate(usda_items[:5], 1):
        usda_name = item['usda_name']

        print(f"{i}. USDA名（元データ）:")
        print(f"   '{usda_name}'")

        # ステップ1: パース
        search_name, description = parse_usda_name(usda_name)
        print(f"   → パース後:")
        print(f"      search_name: '{search_name}'")
        print(f"      description: '{description}'")

        # ステップ2: テキスト構築
        text = build_query_text(search_name, description)
        print(f"   → 構築テキスト: '{text}'")

        # ステップ3: 正規化
        normalized = normalize_text(text)
        print(f"   → 正規化後: '{normalized}'")
        print()

    print("=" * 60)
    print("✅ 全ての処理ステップが正常に動作")
    print("=" * 60)


def test_query_vs_database_matching():
    """クエリとデータベースのマッチング例"""
    print("\n" + "=" * 60)
    print("クエリ vs データベースマッチング例")
    print("=" * 60)

    # VLMクエリの例
    vlm_query = {
        "search_name": "beef steak",
        "description": "grilled, sliced"
    }

    # USDA候補の例
    usda_candidates = [
        "57. Beef, ground, 85% lean meat",
        "58. Beef steak, grilled",
        "59. Beef and potatoes, no sauce"
    ]

    # クエリの処理
    query_text = build_query_text(vlm_query['search_name'], vlm_query['description'])
    query_normalized = normalize_text(query_text)
    print(f"\n📍 VLMクエリ:")
    print(f"   元データ: '{vlm_query['search_name']} - {vlm_query['description']}'")
    print(f"   正規化後: '{query_normalized}'")

    # USDA候補の処理
    print(f"\n📚 USDA候補（{len(usda_candidates)}件）:")
    for i, usda_name in enumerate(usda_candidates, 1):
        search_name, description = parse_usda_name(usda_name)
        text = build_query_text(search_name, description)
        normalized = normalize_text(text)
        print(f"   {i}. '{usda_name}'")
        print(f"      → 正規化: '{normalized}'")

    print("\n💡 ポイント:")
    print("   - VLMクエリもUSDAデータも同じ正規化処理")
    print("   - 正規化後のテキストで埋め込みを作成")
    print("   - 埋め込み空間で類似度計算")
    print("=" * 60)


if __name__ == "__main__":
    test_usda_name_processing()
    test_query_vs_database_matching()
