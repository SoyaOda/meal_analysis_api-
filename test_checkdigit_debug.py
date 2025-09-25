#!/usr/bin/env python3
"""
チェックデジット計算デバッグスクリプト

実際のバーコードでチェックデジット計算を検証
"""

def debug_upc12_checkdigit(upc12: str):
    """UPC-12チェックデジット計算をデバッグ"""
    print(f"UPC-12: {upc12}")
    print("位置:", " ".join(f"{i+1:2}" for i in range(12)))
    print("数字:", " ".join(f"{d:2}" for d in upc12))

    # 奇数位置（1,3,5,7,9,11）の数字 × 3
    odd_positions = [0, 2, 4, 6, 8, 10]  # 0-indexedでの奇数位置
    odd_sum = sum(int(upc12[i]) for i in odd_positions)
    print(f"奇数位置の合計: {odd_sum}")

    # 偶数位置（2,4,6,8,10）の数字
    even_positions = [1, 3, 5, 7, 9]  # 0-indexedでの偶数位置
    even_sum = sum(int(upc12[i]) for i in even_positions)
    print(f"偶数位置の合計: {even_sum}")

    total = (odd_sum * 3) + even_sum
    calculated_check = (10 - (total % 10)) % 10
    actual_check = int(upc12[11])

    print(f"計算: ({odd_sum} × 3) + {even_sum} = {total}")
    print(f"チェックデジット: (10 - ({total} % 10)) % 10 = {calculated_check}")
    print(f"実際のチェックデジット: {actual_check}")
    print(f"一致: {'✅' if calculated_check == actual_check else '❌'}")


def debug_ean13_checkdigit(ean13: str):
    """EAN-13チェックデジット計算をデバッグ"""
    print(f"EAN-13: {ean13}")
    print("位置:", " ".join(f"{i+1:2}" for i in range(13)))
    print("数字:", " ".join(f"{d:2}" for d in ean13))

    # 奇数位置（1,3,5...）の数字
    odd_positions = [0, 2, 4, 6, 8, 10]  # 0-indexedでの奇数位置
    odd_sum = sum(int(ean13[i]) for i in odd_positions)
    print(f"奇数位置の合計: {odd_sum}")

    # 偶数位置（2,4,6...）の数字 × 3
    even_positions = [1, 3, 5, 7, 9, 11]  # 0-indexedでの偶数位置
    even_sum = sum(int(ean13[i]) for i in even_positions)
    print(f"偶数位置の合計: {even_sum}")

    total = odd_sum + (even_sum * 3)
    calculated_check = (10 - (total % 10)) % 10
    actual_check = int(ean13[12])

    print(f"計算: {odd_sum} + ({even_sum} × 3) = {total}")
    print(f"チェックデジット: (10 - ({total} % 10)) % 10 = {calculated_check}")
    print(f"実際のチェックデジット: {actual_check}")
    print(f"一致: {'✅' if calculated_check == actual_check else '❌'}")


# 実際のバーコードでテスト
test_cases = [
    ('000000016872', 'UPC-12として'),  # 現在のAPI成功例
    ('012345678905', 'UPC-12として'),  # 標準例
    ('0000000016872', 'EAN-13として'),  # EAN-13例
]

for code, description in test_cases:
    print("=" * 50)
    print(f"{description}: {code}")
    print("=" * 50)

    if len(code) == 12:
        debug_upc12_checkdigit(code)
    elif len(code) == 13:
        debug_ean13_checkdigit(code)
    print()