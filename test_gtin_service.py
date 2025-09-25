#!/usr/bin/env python3
"""
GTIN正規化サービステストスクリプト

UPC-12→EAN-13変換、チェックデジット検証の動作確認
"""

import sys
import os
sys.path.append('/Users/odasoya/meal_analysis_api_2')

from apps.barcode_api.services.gtin_service import GTINService


def test_gtin_normalization():
    """GTIN正規化機能のテスト"""
    print("🔍 GTIN正規化サービステスト開始")

    # テストケース定義
    test_cases = [
        {
            'input': '000000016872',  # 現在のAPIで成功しているGTIN
            'expected_format': 'EAN-13',
            'description': '実データ: SUNRIDGE ZEN PARTY MIX'
        },
        {
            'input': '16872',  # 短縮形
            'expected_format': 'EAN-13',
            'description': '短縮形からの変換'
        },
        {
            'input': '0-77890-27049',  # ハイフン付きUPC-12
            'expected_format': 'EAN-13',
            'description': 'ハイフン付きUPC-12'
        },
        {
            'input': '7622210951672',  # 標準的なEAN-13
            'expected_format': 'EAN-13',
            'description': '標準的なEAN-13'
        },
        {
            'input': '123456789012',  # UPC-12形式
            'expected_format': 'EAN-13',
            'description': 'UPC-12からEAN-13変換'
        },
        {
            'input': 'invalid',  # 無効な入力
            'expected_format': None,
            'description': '無効な入力'
        }
    ]

    print(f"\n📋 テストケース: {len(test_cases)}件")

    success_count = 0

    for i, case in enumerate(test_cases, 1):
        print(f"\n--- テスト {i}: {case['description']} ---")
        print(f"入力: {case['input']}")

        # GTIN正規化実行
        normalized = GTINService.normalize_gtin(case['input'])
        gtin_info = GTINService.get_gtin_info(case['input'])

        print(f"正規化結果: {normalized}")
        print(f"有効性: {gtin_info['valid']}")

        if gtin_info['valid']:
            print(f"フォーマット: {gtin_info['format']}")
            print(f"チェックデジット検証: {gtin_info['check_digit_valid']}")
            if 'country_code' in gtin_info:
                print(f"国コード: {gtin_info['country_code']}")

        # 期待値との比較
        if case['expected_format'] is None:
            # 無効な入力のテスト
            if not gtin_info['valid']:
                print("✅ 期待通り無効と判定")
                success_count += 1
            else:
                print("❌ 無効であるべきですが有効と判定されました")
        else:
            # 有効な入力のテスト
            if gtin_info['valid'] and gtin_info['format'] == case['expected_format']:
                print("✅ 期待通り正規化成功")
                success_count += 1
            else:
                print("❌ 正規化失敗")

    print(f"\n🎯 テスト結果: {success_count}/{len(test_cases)} 成功")
    return success_count == len(test_cases)


def test_upc12_ean13_conversion():
    """UPC-12→EAN-13変換の詳細テスト"""
    print("\n🔄 UPC-12→EAN-13変換詳細テスト")

    # 実際のUPC-12コード（チェックデジット付き）
    upc12_samples = [
        '012345678905',  # 標準的なUPC-12
        '078915140088',  # 実際の商品コード例
        '036000291452',  # Coca-Cola例
    ]

    for upc12 in upc12_samples:
        print(f"\n📦 UPC-12: {upc12}")

        # GTINサービスでの変換
        ean13 = GTINService.normalize_gtin(upc12)
        print(f"EAN-13: {ean13}")

        if ean13:
            # チェックデジット検証
            is_valid = GTINService._validate_ean13_check_digit(ean13)
            print(f"チェックデジット検証: {'✅ 有効' if is_valid else '❌ 無効'}")

            # 元のUPC-12のチェックデジット検証
            upc12_valid = GTINService._validate_upc12_check_digit(upc12)
            print(f"元UPC-12の検証: {'✅ 有効' if upc12_valid else '❌ 無効'}")


def test_api_integration():
    """既存のAPIとの統合テスト"""
    print("\n🔗 API統合テスト")

    # 現在のAPIで成功しているGTIN
    current_gtin = '000000016872'

    print(f"現在のAPI成功GTIN: {current_gtin}")

    # GTIN正規化
    normalized = GTINService.normalize_gtin(current_gtin)
    info = GTINService.get_gtin_info(current_gtin)

    print(f"正規化後: {normalized}")
    print(f"詳細情報: {info}")

    # APIで検索テスト（現在動作中のAPIサーバーに対して）
    import requests
    try:
        response = requests.post(
            'http://localhost:8003/api/v1/barcode/lookup',
            json={'gtin': normalized, 'include_all_nutrients': False},
            timeout=5
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ API検索成功: {result['product']['description']}")
        else:
            print(f"❌ API検索失敗: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"⚠️ API接続エラー (APIサーバーが起動していない可能性): {e}")


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🧪 GTIN正規化サービス包括テスト")
    print("=" * 60)

    # 基本機能テスト
    basic_test_success = test_gtin_normalization()

    # UPC-12→EAN-13変換テスト
    test_upc12_ean13_conversion()

    # API統合テスト
    test_api_integration()

    if basic_test_success:
        print("\n🎉 GTIN正規化サービス実装完了!")
        print("\n✅ 実装された機能:")
        print("  - UPC-12 → EAN-13変換")
        print("  - チェックデジット検証（UPC-12/EAN-13）")
        print("  - GTIN正規化（0埋め処理）")
        print("  - 国コード判定")
        print("  - 包括的なエラーハンドリング")
    else:
        print("\n❌ テスト失敗 - 実装を確認してください")


if __name__ == "__main__":
    main()