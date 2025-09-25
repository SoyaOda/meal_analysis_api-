#!/usr/bin/env python3
"""
GTIN正規化・検証サービス

UPC-12からEAN-13への変換、チェックデジット検証、GTIN正規化処理を提供
"""

import re
import logging
from typing import Optional, Tuple


logger = logging.getLogger(__name__)


class GTINService:
    """GTIN（Global Trade Item Number）正規化・検証サービス"""

    @staticmethod
    def normalize_gtin(gtin: str) -> Optional[str]:
        """
        GTINを正規化してEAN-13形式に変換

        Args:
            gtin: 入力GTIN（UPC-12, EAN-13等）

        Returns:
            正規化されたEAN-13形式のGTIN、無効な場合はNone
        """
        if not gtin:
            return None

        # 数字以外の文字を除去
        clean_gtin = re.sub(r'[^0-9]', '', gtin.strip())

        if not clean_gtin:
            return None

        # 元の文字列と数字のみの文字列の長さが大幅に違う場合は無効とする
        # (英数字混在など、バーコードとして不適切な入力を除外)
        original_length = len(gtin.strip())
        if original_length > 0 and len(clean_gtin) < original_length * 0.8:
            logger.warning(f"数字以外の文字が多すぎるため無効: {gtin}")
            return None

        # 長さに応じて処理分岐
        if len(clean_gtin) == 12:
            # UPC-12をEAN-13に変換
            return GTINService._upc12_to_ean13(clean_gtin)
        elif len(clean_gtin) == 13:
            # EAN-13の場合、チェックデジット検証
            if GTINService._validate_ean13_check_digit(clean_gtin):
                return clean_gtin
            else:
                logger.warning(f"EAN-13チェックデジット検証失敗: {clean_gtin}")
                return None
        elif len(clean_gtin) == 14:
            # GTIN-14の場合、下位13桁を抽出してEAN-13として扱う
            ean13_candidate = clean_gtin[1:]
            if GTINService._validate_ean13_check_digit(ean13_candidate):
                return ean13_candidate
            else:
                logger.warning(f"GTIN-14からEAN-13変換時のチェックデジット検証失敗: {ean13_candidate}")
                return None
        elif len(clean_gtin) < 12:
            # 短い場合は左ゼロ埋めしてUPC-12として扱う
            if len(clean_gtin) <= 12:
                padded_gtin = clean_gtin.zfill(12)
                return GTINService._upc12_to_ean13(padded_gtin)

        logger.warning(f"サポートされていないGTIN長: {len(clean_gtin)} ({clean_gtin})")
        return None

    @staticmethod
    def _upc12_to_ean13(upc12: str) -> Optional[str]:
        """
        UPC-12をEAN-13に変換

        Args:
            upc12: 12桁のUPCコード

        Returns:
            13桁のEAN-13コード、無効な場合はNone
        """
        if len(upc12) != 12:
            return None

        # UPC-12のチェックデジット検証
        if not GTINService._validate_upc12_check_digit(upc12):
            logger.warning(f"UPC-12チェックデジット検証失敗: {upc12}")
            return None

        # EAN-13に変換（先頭に0を付加）
        ean13 = '0' + upc12

        # EAN-13のチェックデジットを再計算
        correct_check_digit = GTINService._calculate_ean13_check_digit(ean13[:-1])
        ean13_corrected = ean13[:-1] + str(correct_check_digit)

        logger.info(f"UPC-12 {upc12} をEAN-13 {ean13_corrected} に変換")
        return ean13_corrected

    @staticmethod
    def _validate_upc12_check_digit(upc12: str) -> bool:
        """
        UPC-12のチェックデジット検証

        Args:
            upc12: 12桁のUPCコード

        Returns:
            チェックデジットが正しい場合True
        """
        if len(upc12) != 12 or not upc12.isdigit():
            return False

        # UPC-12チェックデジット計算
        # 奇数位置（1,3,5...）の数字の合計 × 3 + 偶数位置（2,4,6...）の数字の合計
        # インデックス0,2,4,6,8,10 = 奇数位置、インデックス1,3,5,7,9 = 偶数位置
        odd_sum = sum(int(upc12[i]) for i in range(0, 11, 2))  # 0,2,4,6,8,10
        even_sum = sum(int(upc12[i]) for i in range(1, 11, 2))  # 1,3,5,7,9

        total = (odd_sum * 3) + even_sum
        check_digit = (10 - (total % 10)) % 10

        return int(upc12[11]) == check_digit

    @staticmethod
    def _validate_ean13_check_digit(ean13: str) -> bool:
        """
        EAN-13のチェックデジット検証

        Args:
            ean13: 13桁のEAN-13コード

        Returns:
            チェックデジットが正しい場合True
        """
        if len(ean13) != 13 or not ean13.isdigit():
            return False

        calculated_check_digit = GTINService._calculate_ean13_check_digit(ean13[:-1])
        return int(ean13[12]) == calculated_check_digit

    @staticmethod
    def _calculate_ean13_check_digit(ean12: str) -> int:
        """
        EAN-13の最初の12桁からチェックデジットを計算

        Args:
            ean12: 12桁のEANコード（チェックデジット除く）

        Returns:
            チェックデジット（0-9）
        """
        if len(ean12) != 12 or not ean12.isdigit():
            raise ValueError(f"無効なEAN-12: {ean12}")

        # EAN-13チェックデジット計算
        # 奇数位置の数字の合計 + 偶数位置の数字の合計 × 3
        odd_sum = sum(int(ean12[i]) for i in range(0, 12, 2))   # 1,3,5,7,9,11番目
        even_sum = sum(int(ean12[i]) for i in range(1, 12, 2))  # 2,4,6,8,10,12番目

        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10

        return check_digit

    @staticmethod
    def get_gtin_info(gtin: str) -> dict:
        """
        GTINの詳細情報を取得

        Args:
            gtin: GTIN文字列

        Returns:
            GTIN情報の辞書
        """
        normalized = GTINService.normalize_gtin(gtin)

        info = {
            'original': gtin,
            'normalized': normalized,
            'valid': normalized is not None,
            'format': None,
            'check_digit_valid': False
        }

        if normalized:
            info['format'] = 'EAN-13'
            info['check_digit_valid'] = GTINService._validate_ean13_check_digit(normalized)

            # 国コード判定（簡易版）
            if normalized.startswith('0'):
                info['country_code'] = 'US/CA (UPC)'
            elif normalized.startswith('49'):
                info['country_code'] = 'Japan'
            elif normalized.startswith('45') or normalized.startswith('46'):
                info['country_code'] = 'Russia/China'
            else:
                info['country_code'] = 'Other'

        return info

    @staticmethod
    def is_valid_gtin(gtin: str) -> bool:
        """
        GTINが有効かどうかを判定

        Args:
            gtin: GTIN文字列

        Returns:
            有効な場合True
        """
        return GTINService.normalize_gtin(gtin) is not None