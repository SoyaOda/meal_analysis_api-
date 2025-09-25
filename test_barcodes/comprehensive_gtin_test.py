#!/usr/bin/env python3
"""
GTIN正規化サービス包括テストスクリプト

生成されたテストデータを使用してGTIN機能を徹底的にテスト
"""

import json
import sys
import os
from pathlib import Path

# パス設定
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from apps.barcode_api.services.gtin_service import GTINService


def load_test_data():
    """テストデータを読み込み"""
    test_data_path = Path(__file__).parent / "generated_valid_barcodes.json"

    if not test_data_path.exists():
        print(f"❌ テストデータファイルが見つかりません: {test_data_path}")
        return None

    with open(test_data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_normalization(test_data):
    """正規化機能のテスト"""
    print("\n🔄 GTIN正規化機能テスト")
    print("=" * 40)

    success_count = 0
    total_count = 0

    for category, samples in test_data.items():
        print(f"\n--- {category} カテゴリ ---")

        for sample in samples:
            total_count += 1
            barcode = sample['barcode']
            expected_normalized = sample['expected_normalized']

            # 正規化実行
            normalized = GTINService.normalize_gtin(barcode)

            print(f"入力: {barcode}")
            print(f"期待値: {expected_normalized}")
            print(f"実際: {normalized}")

            # 結果判定
            if normalized == expected_normalized:
                print("✅ 正規化成功")
                success_count += 1
            else:
                print("❌ 正規化失敗")

            print()

    print(f"🎯 正規化テスト結果: {success_count}/{total_count} 成功")
    return success_count == total_count


def test_validation(test_data):
    """チェックデジット検証のテスト"""
    print("\n🔍 チェックデジット検証テスト")
    print("=" * 40)

    success_count = 0
    total_count = 0

    for category, samples in test_data.items():
        print(f"\n--- {category} カテゴリ ---")

        for sample in samples:
            total_count += 1
            barcode = sample['barcode']
            expected_valid = sample['check_digit_valid']

            # 検証実行
            gtin_info = GTINService.get_gtin_info(barcode)
            actual_valid = gtin_info['check_digit_valid']

            print(f"バーコード: {barcode}")
            print(f"期待値: {'有効' if expected_valid else '無効'}")
            print(f"実際: {'有効' if actual_valid else '無効'}")

            # 結果判定
            if actual_valid == expected_valid:
                print("✅ 検証成功")
                success_count += 1
            else:
                print("❌ 検証失敗")

            print()

    print(f"🎯 検証テスト結果: {success_count}/{total_count} 成功")
    return success_count == total_count


def test_edge_cases():
    """エッジケースのテスト"""
    print("\n⚡ エッジケーステスト")
    print("=" * 40)

    edge_cases = [
        {
            'input': '   000000016872   ',
            'description': '前後に空白',
            'expected_normalized': '0000000016872'
        },
        {
            'input': '0-77890-27049-3',
            'description': 'ハイフン付きUPC-12',
            'expected_normalized': '0077890270493'
        },
        {
            'input': '16872',
            'description': '短縮形（ゼロ埋め）',
            'expected_normalized': '0000000016872'
        },
        {
            'input': '',
            'description': '空文字列',
            'expected_normalized': None
        },
        {
            'input': 'abc123def',
            'description': '英数字混在',
            'expected_normalized': None
        }
    ]

    success_count = 0

    for case in edge_cases:
        input_barcode = case['input']
        expected = case['expected_normalized']
        description = case['description']

        print(f"テスト: {description}")
        print(f"入力: '{input_barcode}'")

        normalized = GTINService.normalize_gtin(input_barcode)
        print(f"期待値: {expected}")
        print(f"実際: {normalized}")

        if normalized == expected:
            print("✅ エッジケース成功")
            success_count += 1
        else:
            print("❌ エッジケース失敗")

        print()

    print(f"🎯 エッジケーステスト結果: {success_count}/{len(edge_cases)} 成功")
    return success_count == len(edge_cases)


def test_performance():
    """パフォーマンステスト"""
    print("\n🚀 パフォーマンステスト")
    print("=" * 40)

    import time

    test_barcode = '000000016872'
    iterations = 1000

    # 正規化パフォーマンス
    start_time = time.time()
    for _ in range(iterations):
        GTINService.normalize_gtin(test_barcode)
    normalization_time = time.time() - start_time

    # 詳細情報取得パフォーマンス
    start_time = time.time()
    for _ in range(iterations):
        GTINService.get_gtin_info(test_barcode)
    info_time = time.time() - start_time

    print(f"正規化処理: {iterations}回実行")
    print(f"  総時間: {normalization_time:.4f}秒")
    print(f"  1回あたり: {normalization_time/iterations*1000:.2f}ms")

    print(f"詳細情報取得: {iterations}回実行")
    print(f"  総時間: {info_time:.4f}秒")
    print(f"  1回あたり: {info_time/iterations*1000:.2f}ms")

    # パフォーマンス評価
    acceptable_time_per_call = 0.001  # 1ms
    performance_ok = (normalization_time/iterations < acceptable_time_per_call and
                     info_time/iterations < acceptable_time_per_call)

    print(f"🎯 パフォーマンス: {'✅ 良好' if performance_ok else '⚠️ 要改善'}")
    return performance_ok


def main():
    """メイン実行"""
    print("=" * 60)
    print("🧪 GTIN正規化サービス包括テスト")
    print("=" * 60)

    # テストデータ読み込み
    test_data = load_test_data()
    if not test_data:
        return False

    print(f"📋 読み込んだテストデータ:")
    for category, samples in test_data.items():
        print(f"  - {category}: {len(samples)}件")

    # 各テスト実行
    tests_results = []

    tests_results.append(test_normalization(test_data))
    tests_results.append(test_validation(test_data))
    tests_results.append(test_edge_cases())
    tests_results.append(test_performance())

    # 総合結果
    total_success = sum(tests_results)
    total_tests = len(tests_results)

    print("\n" + "=" * 60)
    print(f"🎉 総合テスト結果: {total_success}/{total_tests} 成功")

    if total_success == total_tests:
        print("✅ すべてのテストが成功しました！")
        print("\n🎯 実装完了機能:")
        print("  - UPC-12 → EAN-13 変換")
        print("  - チェックデジット検証（UPC-12/EAN-13）")
        print("  - GTIN正規化（ゼロ埋め、文字除去）")
        print("  - エッジケース処理")
        print("  - 高速パフォーマンス（< 1ms/call）")
        return True
    else:
        print("❌ 一部テストが失敗しました")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)