#!/usr/bin/env python3
"""
PDCA Serving Data Debug Script
失敗した48食材の1つ「Cornstarch, cup 488cals」でサービング情報取得をデバッグ
"""

import sys
import os
import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any

# パスの設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from components.playwright_multi_food_navigator import PlaywrightMultiFoodNavigator
from components.playwright_food_data_collector import PlaywrightFoodDataCollector

def setup_logging():
    """ログの設定"""
    log_dir = os.path.join(current_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'serving_pdca_debug_{timestamp}.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)

class ServingDataDebugger:
    """サービングデータ取得の詳細デバッグクラス"""

    def __init__(self, logger):
        self.logger = logger
        self.navigator = None
        self.collector = None
        self.debug_data = {
            "target_food": "Cornstarch, cup\n488cals",  # 正確な名前（改行文字を含む）
            "navigation_attempts": [],
            "serving_detection_attempts": [],
            "raw_serving_samples": [],
            "analysis_results": {}
        }

    async def initialize_session(self):
        """セッション初期化"""
        self.logger.info("🚀 セッション初期化中...")
        self.navigator = PlaywrightMultiFoodNavigator()
        await self.navigator.initialize_session()
        self.collector = PlaywrightFoodDataCollector(self.navigator.page)
        await self.navigator.load_food_catalog()
        self.logger.info("✅ セッション初期化完了")

    async def plan_debug_strategy(self):
        """Plan: デバッグ戦略の計画"""
        self.logger.info("📋 PLAN: デバッグ戦略計画")

        strategy = {
            "target_food": self.debug_data["target_food"],
            "investigation_steps": [
                "1. 基本ナビゲーションテスト",
                "2. ページ構造の詳細分析",
                "3. サービング要素の発見",
                "4. データ取得の検証",
                "5. 抽出ロジックの改善"
            ],
            "expected_serving_format": [
                "tablespoon Xcals / Y g",
                "teaspoon Xcals / Y g",
                "gram Xcals / Y g",
                "cup Xcals / Y g"
            ]
        }

        self.debug_data["plan"] = strategy
        self.logger.info(f"🎯 対象食材: {strategy['target_food']}")
        for step in strategy["investigation_steps"]:
            self.logger.info(f"   📌 {step}")

        return strategy

    async def do_navigation_test(self):
        """Do: ナビゲーションテストの実行"""
        self.logger.info("🔍 DO: ナビゲーションテスト実行")

        target_food = self.debug_data["target_food"]

        # 1. 基本ナビゲーション
        nav_success = await self.navigator.navigate_to_food_stable(target_food)

        nav_result = {
            "step": "basic_navigation",
            "success": nav_success,
            "timestamp": datetime.now().isoformat()
        }

        self.debug_data["navigation_attempts"].append(nav_result)
        self.logger.info(f"🎯 基本ナビゲーション: {'✅成功' if nav_success else '❌失敗'}")

        if not nav_success:
            self.logger.error("❌ ナビゲーション失敗 - 調査を中断")
            return False

        # 2. ページ状態の確認
        page_info = await self.analyze_current_page()
        nav_result["page_info"] = page_info

        return nav_success

    async def analyze_current_page(self):
        """現在のページ状態を分析"""
        page = self.navigator.page

        # 基本情報
        url = page.url
        title = await page.title()

        # サービング関連の要素を探す
        serving_indicators = [
            'text="Select Serving"',
            'text="Amount eaten"',
            '[data-testid*="serving"]',
            '[class*="serving"]',
            '[class*="unit"]',
            'text*="cals"',
            'text*="gram"',
            'text*="cup"',
            'text*="tablespoon"'
        ]

        found_elements = []
        for indicator in serving_indicators:
            try:
                elements = await page.locator(indicator).all()
                if elements:
                    for i, elem in enumerate(elements[:3]):  # 最大3個まで
                        text = await elem.text_content() if elem else ""
                        found_elements.append({
                            "selector": indicator,
                            "index": i,
                            "text": text[:100],  # 長すぎる場合は切り詰め
                            "visible": await elem.is_visible() if elem else False
                        })
            except Exception as e:
                self.logger.warning(f"要素検索エラー ({indicator}): {e}")

        page_info = {
            "url": url,
            "title": title,
            "found_serving_elements": found_elements,
            "total_elements_found": len(found_elements)
        }

        self.logger.info(f"📄 ページ分析: {len(found_elements)}個のサービング関連要素発見")
        return page_info

    async def do_serving_data_extraction(self):
        """Do: サービングデータ抽出の実行"""
        self.logger.info("📊 DO: サービングデータ抽出実行")

        # 標準の方法でデータ収集を試行
        target_food = self.debug_data["target_food"]
        food_data = await self.collector.collect_complete_food_data(target_food)

        extraction_result = {
            "step": "standard_extraction",
            "success": food_data.get('collection_success', False),
            "timestamp": datetime.now().isoformat(),
            "raw_data_counts": {
                "serving": len(food_data.get('serving_options', {}).get('raw_serving_data', [])),
                "nutrition": len(food_data.get('nutrition_data', {}).get('detailed_nutrients', {}).get('raw_nutrition_data', []))
            },
            "sample_serving_data": food_data.get('serving_options', {}).get('raw_serving_data', [])[:20]
        }

        self.debug_data["serving_detection_attempts"].append(extraction_result)
        self.debug_data["raw_serving_samples"] = food_data.get('serving_options', {}).get('raw_serving_data', [])

        self.logger.info(f"📊 標準抽出結果:")
        self.logger.info(f"   成功: {extraction_result['success']}")
        self.logger.info(f"   サービングデータ数: {extraction_result['raw_data_counts']['serving']}")
        self.logger.info(f"   栄養データ数: {extraction_result['raw_data_counts']['nutrition']}")

        return extraction_result

    async def do_enhanced_serving_detection(self):
        """Do: 拡張サービング検出の実行"""
        self.logger.info("🔬 DO: 拡張サービング検出実行")

        page = self.navigator.page

        # より詳細なサービング情報の探索
        enhanced_selectors = [
            # Select Serving テーブル関連
            'text="Select Serving" >> .. >> table',
            'text="Select Serving" >> .. >> [role="table"]',
            'text="Select Serving" >> .. >> div',

            # 直接的なサービング単位検索
            ':text("tablespoon")',
            ':text("teaspoon")',
            ':text("cup")',
            ':text("gram")',
            ':text("oz")',

            # カロリー情報との組み合わせ
            ':text-matches("\\d+\\s*cals?")',
            ':text-matches("\\d+\\s*calories?")',

            # グラム重量情報
            ':text-matches("\\d+\\.?\\d*\\s*g")',
            ':text-matches("/\\s*\\d+\\.?\\d*\\s*g")',
        ]

        enhanced_data = []

        for selector in enhanced_selectors:
            try:
                elements = await page.locator(selector).all()
                for i, elem in enumerate(elements[:5]):  # 最大5個まで
                    if elem:
                        text = await elem.text_content()
                        if text and text.strip():
                            enhanced_data.append({
                                "selector": selector,
                                "index": i,
                                "text": text.strip(),
                                "length": len(text.strip())
                            })
            except Exception as e:
                self.logger.debug(f"拡張検索エラー ({selector}): {e}")

        enhanced_result = {
            "step": "enhanced_detection",
            "elements_found": len(enhanced_data),
            "data": enhanced_data,
            "timestamp": datetime.now().isoformat()
        }

        self.debug_data["serving_detection_attempts"].append(enhanced_result)

        self.logger.info(f"🔬 拡張検出結果: {len(enhanced_data)}個の要素発見")

        # 有望な要素を表示
        serving_candidates = [item for item in enhanced_data if
                            ('cal' in item['text'].lower() and 'g' in item['text']) or
                            any(unit in item['text'].lower() for unit in ['tablespoon', 'teaspoon', 'cup', 'gram'])]

        self.logger.info(f"🎯 サービング候補: {len(serving_candidates)}個")
        for candidate in serving_candidates[:10]:
            self.logger.info(f"   📌 {candidate['text'][:80]}")

        return enhanced_result

    async def check_analysis(self):
        """Check: 結果の分析と評価"""
        self.logger.info("✅ CHECK: 結果分析と評価")

        # ナビゲーション成功率
        nav_attempts = self.debug_data["navigation_attempts"]
        nav_success_rate = sum(1 for attempt in nav_attempts if attempt["success"]) / len(nav_attempts) if nav_attempts else 0

        # サービングデータ検出結果
        serving_attempts = self.debug_data["serving_detection_attempts"]
        raw_data = self.debug_data["raw_serving_samples"]

        # 実際のサービング情報があるかチェック
        valid_serving_patterns = []
        for item in raw_data[:50]:  # 最初の50個をチェック
            item_str = str(item).strip()
            # "unit Xcals / Y g" パターンを探す
            if 'cal' in item_str.lower() and 'g' in item_str and '/' in item_str:
                valid_serving_patterns.append(item_str)
            # 基本的な単位語を含むパターン
            elif any(unit in item_str.lower() for unit in ['tablespoon', 'teaspoon', 'cup', 'gram', 'oz']):
                if len(item_str) < 100:  # 短めのものを優先
                    valid_serving_patterns.append(item_str)

        analysis = {
            "navigation_success_rate": nav_success_rate,
            "total_raw_serving_items": len(raw_data),
            "valid_serving_patterns_found": len(valid_serving_patterns),
            "sample_valid_patterns": valid_serving_patterns[:10],
            "data_quality_assessment": self._assess_data_quality(raw_data),
            "improvement_recommendations": []
        }

        # 改善提案の生成
        if analysis["valid_serving_patterns_found"] == 0:
            analysis["improvement_recommendations"].append("サービング情報が全く見つからない - より詳細なページ要素分析が必要")
        elif analysis["valid_serving_patterns_found"] < 3:
            analysis["improvement_recommendations"].append("サービング情報が少ない - 抽出ロジックの改善が必要")
        else:
            analysis["improvement_recommendations"].append("サービング情報が発見された - 抽出フィルタリングロジックを調整")

        self.debug_data["analysis_results"] = analysis

        self.logger.info("📊 分析結果:")
        self.logger.info(f"   ナビゲーション成功率: {nav_success_rate:.1%}")
        self.logger.info(f"   生データ総数: {analysis['total_raw_serving_items']}")
        self.logger.info(f"   有効パターン数: {analysis['valid_serving_patterns_found']}")
        self.logger.info(f"   データ品質: {analysis['data_quality_assessment']}")

        return analysis

    def _assess_data_quality(self, raw_data: List) -> str:
        """データ品質の評価"""
        if not raw_data:
            return "データなし"

        total_items = len(raw_data)

        # ノイズ要素の検出
        noise_indicators = ['var ', 'function', '.css', '.js', 'MuiCard', 'class=', 'div', 'span']
        noise_count = sum(1 for item in raw_data if any(noise in str(item) for noise in noise_indicators))

        # 有効そうな要素の検出
        valid_indicators = ['cal', 'gram', 'cup', 'tablespoon', 'teaspoon', 'oz']
        valid_count = sum(1 for item in raw_data if any(valid in str(item).lower() for valid in valid_indicators))

        noise_ratio = noise_count / total_items
        valid_ratio = valid_count / total_items

        if noise_ratio > 0.8:
            return "高ノイズ - 主にUI要素"
        elif valid_ratio > 0.3:
            return "良好 - 食材データを含む"
        elif valid_ratio > 0.1:
            return "混合 - 食材データとノイズが混在"
        else:
            return "低品質 - 食材データが少ない"

    async def act_implement_improvements(self):
        """Act: 改善策の実装"""
        self.logger.info("🔧 ACT: 改善策の実装")

        analysis = self.debug_data["analysis_results"]
        recommendations = analysis.get("improvement_recommendations", [])

        improvements_implemented = []

        # 改善策1: より具体的なサービング要素を探す
        if analysis["valid_serving_patterns_found"] < 3:
            self.logger.info("🔧 改善策1: 具体的サービング要素の検索")

            page = self.navigator.page

            # 専用のサービング検索戦略
            serving_strategies = [
                # Strategy 1: Select Serving テーブルの直接検索
                {'name': 'select_serving_table', 'selector': 'text="Select Serving" >> .. >> table tr'},
                # Strategy 2: Amount eaten ボタン周辺
                {'name': 'amount_eaten_context', 'selector': 'text="Amount eaten" >> .. >> div'},
                # Strategy 3: カロリー表示周辺
                {'name': 'calorie_context', 'selector': ':text-matches("\\d+\\s*cal") >> ..'},
                # Strategy 4: 全体コンテンツから単位を探す
                {'name': 'unit_search', 'selector': ':text-matches("(tablespoon|teaspoon|cup|gram|oz).*\\d+.*cal")'},
            ]

            for strategy in serving_strategies:
                try:
                    elements = await page.locator(strategy['selector']).all()
                    strategy_data = []

                    for elem in elements[:10]:
                        if elem:
                            text = await elem.text_content()
                            if text and text.strip():
                                strategy_data.append(text.strip())

                    self.logger.info(f"🎯 戦略 '{strategy['name']}': {len(strategy_data)}個発見")
                    if strategy_data:
                        improvements_implemented.append({
                            "strategy": strategy['name'],
                            "elements_found": len(strategy_data),
                            "sample_data": strategy_data[:5]
                        })

                        # 有効なデータがあれば詳細表示
                        for sample in strategy_data[:3]:
                            self.logger.info(f"   📌 {sample[:100]}")

                except Exception as e:
                    self.logger.warning(f"戦略 '{strategy['name']}' でエラー: {e}")

        self.debug_data["improvements_implemented"] = improvements_implemented

        return improvements_implemented

    async def save_debug_results(self):
        """デバッグ結果の保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"serving_pdca_debug_results_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.debug_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"📄 デバッグ結果保存: {output_file}")
        return output_file

    async def cleanup_session(self):
        """セッションクリーンアップ"""
        if self.navigator:
            await self.navigator.cleanup_session()

async def main():
    """メインのPDCA実行"""
    logger = setup_logging()

    debugger = ServingDataDebugger(logger)

    try:
        logger.info("🔄 サービングデータ取得PDCA開始")
        logger.info("=" * 80)

        # セッション初期化
        await debugger.initialize_session()

        # PDCA サイクル実行
        logger.info("\n📋 PLAN フェーズ開始")
        await debugger.plan_debug_strategy()

        logger.info("\n🔍 DO フェーズ開始")
        nav_success = await debugger.do_navigation_test()
        if nav_success:
            await debugger.do_serving_data_extraction()
            await debugger.do_enhanced_serving_detection()

        logger.info("\n✅ CHECK フェーズ開始")
        analysis = await debugger.check_analysis()

        logger.info("\n🔧 ACT フェーズ開始")
        improvements = await debugger.act_implement_improvements()

        # 結果保存
        output_file = await debugger.save_debug_results()

        # 最終レポート
        logger.info("\n" + "=" * 80)
        logger.info("🎯 PDCA完了 - 最終結果:")
        logger.info("=" * 80)
        logger.info(f"対象食材: {debugger.debug_data['target_food']}")
        logger.info(f"ナビゲーション: {'✅成功' if nav_success else '❌失敗'}")
        logger.info(f"有効パターン: {analysis.get('valid_serving_patterns_found', 0)}個")
        logger.info(f"改善策実装: {len(improvements)}個")
        logger.info(f"結果ファイル: {output_file}")

        return analysis.get('valid_serving_patterns_found', 0) > 0

    except Exception as e:
        logger.error(f"❌ PDCA実行エラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False
    finally:
        await debugger.cleanup_session()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)