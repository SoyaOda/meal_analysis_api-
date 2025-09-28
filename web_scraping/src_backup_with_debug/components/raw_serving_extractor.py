#!/usr/bin/env python3
"""
生データ専用Serving情報抽出コンポーネント
正規表現パースを一切行わず、raw_textのみ保存
"""

from selenium.webdriver.common.by import By
from typing import List, Dict, Any


class RawServingExtractor:
    """Select Servingモーダルから生データのみを抽出するコンポーネント"""

    def __init__(self, driver):
        self.driver = driver

    def extract_raw_serving_options(self) -> Dict[str, Any]:
        """
        Select Servingモーダルから完全な生データを抽出
        栄養素と同様にページ内の全serving情報を生データとして保存

        Returns:
            Dict: 生serving data
        """
        try:
            print("      🔍 生serving options抽出中（完全生データ方式）...")
            
            # Select Servingモーダル内の全テキストを取得
            all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            all_serving_texts = []
            
            for elem in all_elements:
                text = elem.text.strip()
                if text and len(text) <= 100:  # 適度な長さのテキストのみ
                    # serving情報らしいテキストを検出（カロリー情報を含む）
                    import re
                    if re.search(r'\d+\s*cals?', text, re.IGNORECASE) or re.search(r'\d+\s*g\b', text):
                        all_serving_texts.append(text)
                        print(f"        📊 Servingデータ: {text}")

            # 生情報として全serving データを保存
            from datetime import datetime
            raw_serving_data = {
                'raw_serving_data': all_serving_texts,
                'extraction_method': 'raw_data_all_servings',
                'total_servings_found': len(all_serving_texts),
                'extracted_at': datetime.now().isoformat()
            }

            # 各serving テキストを個別エントリとしても保存
            for i, serving_text in enumerate(all_serving_texts, 1):
                raw_serving_data[f'serving_{i:02d}'] = {
                    'raw_text': serving_text,
                    'sequence': i,
                    'extracted_at': datetime.now().isoformat()
                }

            print(f"      ✅ 生servingデータ抽出完了: {len(all_serving_texts)}個のserving情報")
            return raw_serving_data

        except Exception as e:
            print(f"      ❌ 生serving options抽出エラー: {e}")
            return {}

    def is_serving_modal_open(self) -> bool:
        """Select Servingモーダルが開いているかチェック"""
        try:
            modal_indicators = [
                "//*[contains(text(), 'Select Serving')]",
                "//div[@role='radiogroup']"
            ]

            for pattern in modal_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    if any(el.is_displayed() for el in elements):
                        return True
                except:
                    continue
            return False

        except Exception as e:
            print(f"        ⚠️ モーダル確認エラー: {e}")
            return False