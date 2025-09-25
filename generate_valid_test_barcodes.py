#!/usr/bin/env python3
"""
有効なテストバーコード生成スクリプト

正しいチェックデジットを持つテストバーコードを生成・検証
"""

import json
import sys
sys.path.append('/Users/odasoya/meal_analysis_api_2')

from apps.barcode_api.services.gtin_service import GTINService


def generate_valid_upc12(base_digits: str) -> str:
    """
    有効なUPC-12を生成（チェックデジット自動計算）

    Args:
        base_digits: 最初の11桁

    Returns:
        チェックデジット付きの12桁UPC-12
    """
    if len(base_digits) != 11:
        raise ValueError(f"Base digits must be 11 characters: {base_digits}")

    # チェックデジット計算
    odd_sum = sum(int(base_digits[i]) for i in range(0, 11, 2))  # 0,2,4,6,8,10
    even_sum = sum(int(base_digits[i]) for i in range(1, 11, 2))  # 1,3,5,7,9

    total = (odd_sum * 3) + even_sum
    check_digit = (10 - (total % 10)) % 10

    return base_digits + str(check_digit)


def generate_valid_ean13(base_digits: str) -> str:
    """
    有効なEAN-13を生成（チェックデジット自動計算）

    Args:
        base_digits: 最初の12桁

    Returns:
        チェックデジット付きの13桁EAN-13
    """
    if len(base_digits) != 12:
        raise ValueError(f"Base digits must be 12 characters: {base_digits}")

    # チェックデジット計算
    odd_sum = sum(int(base_digits[i]) for i in range(0, 12, 2))   # 0,2,4,6,8,10
    even_sum = sum(int(base_digits[i]) for i in range(1, 12, 2))  # 1,3,5,7,9,11

    total = odd_sum + (even_sum * 3)
    check_digit = (10 - (total % 10)) % 10

    return base_digits + str(check_digit)


def create_comprehensive_test_data():
    """包括的なテストデータを作成"""

    # 有効なUPC-12サンプル生成
    valid_upc12_bases = [
        "00000001687",  # FDC実データ
        "01234567890",  # 標準テスト
        "03600029145",  # Coca-Cola風
        "07164109095",  # General Mills風
        "07789027049",  # ハイフン例用
    ]

    valid_upc12_samples = []
    for base in valid_upc12_bases:
        upc12 = generate_valid_upc12(base)
        ean13 = GTINService.normalize_gtin(upc12)

        sample = {
            "barcode": upc12,
            "expected_normalized": ean13,
            "format": "UPC-12",
            "check_digit_valid": GTINService._validate_upc12_check_digit(upc12),
            "ean13_valid": GTINService._validate_ean13_check_digit(ean13) if ean13 else False
        }
        valid_upc12_samples.append(sample)
        print(f"Generated UPC-12: {upc12} -> EAN-13: {ean13}")

    # 有効なEAN-13サンプル生成
    valid_ean13_bases = [
        "490243073505",  # 日本（花王風）
        "590123412345",  # ヨーロッパ
        "380123456789",  # ブルガリア
    ]

    valid_ean13_samples = []
    for base in valid_ean13_bases:
        ean13 = generate_valid_ean13(base)

        sample = {
            "barcode": ean13,
            "expected_normalized": ean13,
            "format": "EAN-13",
            "check_digit_valid": GTINService._validate_ean13_check_digit(ean13)
        }
        valid_ean13_samples.append(sample)
        print(f"Generated EAN-13: {ean13}")

    # 無効なサンプル（チェックデジット間違い）
    invalid_samples = []
    for base in valid_upc12_bases[:2]:  # 最初の2つだけ
        invalid_upc12 = base + "0"  # 間違ったチェックデジット

        sample = {
            "barcode": invalid_upc12,
            "expected_normalized": None,
            "format": "invalid",
            "check_digit_valid": GTINService._validate_upc12_check_digit(invalid_upc12)
        }
        invalid_samples.append(sample)
        print(f"Generated invalid UPC-12: {invalid_upc12}")

    return {
        "valid_upc12": valid_upc12_samples,
        "valid_ean13": valid_ean13_samples,
        "invalid": invalid_samples
    }


def verify_test_data(test_data):
    """テストデータの整合性を検証"""
    print("\n🔍 テストデータ検証中...")

    all_valid = True

    for category, samples in test_data.items():
        print(f"\n--- {category} ---")

        for sample in samples:
            barcode = sample['barcode']
            expected_valid = sample['check_digit_valid']

            # GTINServiceでの検証
            gtin_info = GTINService.get_gtin_info(barcode)
            service_valid = gtin_info['check_digit_valid']

            if expected_valid == service_valid:
                print(f"✅ {barcode}: 期待値={expected_valid}, 実際={service_valid}")
            else:
                print(f"❌ {barcode}: 期待値={expected_valid}, 実際={service_valid}")
                all_valid = False

    return all_valid


def main():
    """メイン実行"""
    print("🏭 有効なテストバーコード生成開始")

    # テストデータ生成
    test_data = create_comprehensive_test_data()

    # 整合性検証
    is_valid = verify_test_data(test_data)

    if is_valid:
        # JSONファイルに保存
        output_path = "test_barcodes/generated_valid_barcodes.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 有効なテストデータを生成しました: {output_path}")

        # サマリー表示
        total_valid = len(test_data['valid_upc12']) + len(test_data['valid_ean13'])
        total_invalid = len(test_data['invalid'])
        print(f"📊 生成データ: 有効 {total_valid}件, 無効 {total_invalid}件")

    else:
        print("\n❌ テストデータに不整合があります")


if __name__ == "__main__":
    main()