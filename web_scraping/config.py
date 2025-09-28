#!/usr/bin/env python3
"""
MyNetDiary Web Scraping Configuration
"""

import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ScrapingConfig:
    """スクレイピング設定クラス"""

    # MyNetDiary認証情報
    USERNAME: str = "odssuu@gmail.com"
    PASSWORD: str = "hojihoji2025"

    # URL設定
    BASE_URL: str = "https://www.mynetdiary.com"
    LOGIN_URL: str = f"{BASE_URL}/logonPage.do"
    FOOD_SEARCH_URL: str = f"{BASE_URL}/foodSearch.do"
    MEALS_URL: str = f"{BASE_URL}/meals.do#fe"

    # ブラウザ設定（バックグラウンド実行のためヘッドレス有効）
    HEADLESS: bool = True
    TIMEOUT: int = 15
    IMPLICIT_WAIT: int = 5

    # アクセス制御
    REQUEST_DELAY: float = 1.0  # リクエスト間の待機時間（秒）
    MAX_RETRIES: int = 3

    # 出力設定
    OUTPUT_DIR: str = "web_scraping/data"
    LOG_LEVEL: str = "INFO"

    # テスト用食品名
    def __post_init__(self):
        self.TEST_FOODS = [
            "apple",
            "chicken breast", 
            "brown rice"
        ]

    # User-Agent
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 設定インスタンス
config = ScrapingConfig()

# 出力ディレクトリを作成
os.makedirs(config.OUTPUT_DIR, exist_ok=True)