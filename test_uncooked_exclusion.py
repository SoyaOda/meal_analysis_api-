#!/usr/bin/env python3
"""
uncooked除外機能のテストスクリプト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.utils.mynetdiary_utils import load_mynetdiary_ingredient_names, format_mynetdiary_ingredients_for_prompt
from shared.config.prompts.common_prompts import CommonPrompts

def test_uncooked_exclusion():
    """uncooked除外機能をテスト"""
    print("🧪 Testing uncooked exclusion functionality...")

    # 1. 元データ（uncooked含む）の件数
    original_data = load_mynetdiary_ingredient_names(exclude_uncooked=False)
    print(f"📊 Original data count: {len(original_data)}")

    # 2. uncooked除外データの件数
    filtered_data = load_mynetdiary_ingredient_names(exclude_uncooked=True)
    print(f"📊 Filtered data count: {len(filtered_data)}")

    # 3. 除外された項目数
    excluded_count = len(original_data) - len(filtered_data)
    print(f"❌ Excluded items count: {excluded_count}")

    # 4. 除外されたアイテムを確認（uncooked含む項目）
    excluded_items = [item for item in original_data if 'uncooked' in item.lower() and item not in filtered_data]
    print(f"🔍 Sample excluded uncooked items ({len(excluded_items)} total):")
    for i, item in enumerate(excluded_items[:5]):  # 最初の5項目を表示
        print(f"  {i+1}. {item}")
    if len(excluded_items) > 5:
        print(f"  ... and {len(excluded_items) - 5} more items")

    # 5. プロンプト生成テスト
    print("\n🔧 Testing prompt generation...")

    # 5.1 uncooked除外版プロンプト
    prompt_filtered = CommonPrompts.get_mynetdiary_ingredients_list_with_header(exclude_uncooked=True)
    print(f"✅ Filtered prompt generated (length: {len(prompt_filtered)} chars)")

    # 5.2 元版プロンプト
    prompt_original = CommonPrompts.get_mynetdiary_ingredients_list_with_header(exclude_uncooked=False)
    print(f"📝 Original prompt generated (length: {len(prompt_original)} chars)")

    # 5.3 サイズ比較
    size_reduction = len(prompt_original) - len(prompt_filtered)
    print(f"📉 Prompt size reduction: {size_reduction} chars ({size_reduction/len(prompt_original)*100:.1f}%)")

    # 6. プロンプト内容確認（uncookedが除外されているか）
    uncooked_in_filtered = 'uncooked' in prompt_filtered.lower()
    uncooked_in_original = 'uncooked' in prompt_original.lower()

    print(f"\n🔍 Prompt content verification:")
    print(f"  - Uncooked in filtered prompt: {uncooked_in_filtered}")
    print(f"  - Uncooked in original prompt: {uncooked_in_original}")

    # 7. テスト結果の総合評価
    print(f"\n📋 Test Results Summary:")
    print(f"  ✅ Data filtering: {excluded_count} uncooked items excluded")
    print(f"  ✅ Prompt generation: Both versions working")
    print(f"  ✅ Content verification: {'PASS' if not uncooked_in_filtered and uncooked_in_original else 'FAIL'}")

    if excluded_count == 30 and not uncooked_in_filtered and uncooked_in_original:
        print(f"\n🎉 ALL TESTS PASSED! uncooked exclusion is working correctly.")
        return True
    else:
        print(f"\n❌ TESTS FAILED! Please check the implementation.")
        return False

if __name__ == "__main__":
    success = test_uncooked_exclusion()
    sys.exit(0 if success else 1)