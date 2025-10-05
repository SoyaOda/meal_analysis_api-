#!/usr/bin/env python3
"""
Amount eaten要素検出問題をPDCAで解決するデバッグスクリプト
現在処理中の食材でAmount eaten要素の詳細分析を実行
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# パス設定
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from components.playwright_multi_food_navigator import PlaywrightMultiFoodNavigator


class AmountEatenDebugger:
    """Amount eaten要素検出デバッガー"""

    def __init__(self):
        self.navigator = None
        self.debug_logs = []

    async def initialize_session(self) -> bool:
        """デバッグ用セッション初期化"""
        try:
            print("🔍 Amount eaten要素検出デバッグセッション開始")
            print("="*80)

            self.navigator = PlaywrightMultiFoodNavigator()
            session_success = await self.navigator.initialize_session()

            if not session_success:
                print("❌ セッション初期化失敗")
                return False

            print("✅ セッション初期化完了")
            return True

        except Exception as e:
            print(f"❌ セッション初期化エラー: {e}")
            return False

    async def navigate_to_specific_food(self, food_name: str, category: str) -> bool:
        """特定の食材に移動"""
        try:
            print(f"🎯 食材に移動: {food_name} (カテゴリ: {category})")

            # 食材カタログ読み込み
            await self.navigator.load_food_catalog()

            # 食材ベース画面に移動
            await self.navigator._navigate_to_food_base()

            # カテゴリ選択
            print(f"📂 カテゴリ選択: {category}")
            category_success = await self.navigator._select_category(
                category,
                f"//span[text()='{category}']"
            )

            if not category_success:
                print(f"❌ カテゴリ選択失敗: {category}")
                return False

            # 食材選択
            print(f"🍽️ 食材選択: {food_name}")
            food_success = await self.navigator._select_food_in_category(
                food_name,
                {"name": food_name}
            )

            if not food_success:
                print(f"❌ 食材選択失敗: {food_name}")
                return False

            print(f"✅ 食材移動成功: {food_name}")
            return True

        except Exception as e:
            print(f"❌ 食材移動エラー: {e}")
            return False

    async def debug_amount_eaten_detection(self) -> Dict[str, Any]:
        """Amount eaten要素の詳細検出分析"""
        debug_results = {
            "timestamp": datetime.now().isoformat(),
            "selectors_tested": [],
            "elements_found": [],
            "page_analysis": {}
        }

        try:
            print("\n🔍 Amount eaten要素検出デバッグ開始")
            print("-" * 60)

            # 複数のセレクタパターンをテスト
            selectors_to_test = [
                # 現在使用中のセレクタ
                "//input[@placeholder='Amount eaten']",
                "//input[contains(@placeholder, 'Amount')]",

                # MUI/React系セレクタ
                "//input[contains(@class, 'MuiInputBase-input')]",
                "//input[contains(@class, 'MuiTextField')]",
                "//div[contains(@class, 'MuiTextField-root')]//input",

                # フォーム関連セレクタ
                "//form//input[@type='number']",
                "//form//input[@type='text']",
                "//input[@name='amount']",
                "//input[@id*='amount']",

                # テキスト含有セレクタ
                "//*[contains(text(), 'Amount')]/..//input",
                "//*[contains(text(), 'eaten')]/..//input",
                "//*[contains(text(), 'serving')]/..//input",

                # 汎用セレクタ
                "//input[@type='number']",
                "//input[@type='text']",
                "//input[not(@type) or @type='']",
            ]

            for i, selector in enumerate(selectors_to_test):
                try:
                    print(f"   {i+1:2d}. テスト中: {selector}")

                    elements = await self.navigator.page.query_selector_all(selector)
                    element_count = len(elements)

                    selector_result = {
                        "selector": selector,
                        "elements_found": element_count,
                        "details": []
                    }

                    if element_count > 0:
                        print(f"       ✅ 発見: {element_count}個の要素")

                        # 各要素の詳細情報を取得
                        for j, element in enumerate(elements[:5]):  # 最初の5個まで
                            try:
                                # 要素の属性情報取得
                                placeholder = await element.get_attribute('placeholder') or ''
                                name = await element.get_attribute('name') or ''
                                id_attr = await element.get_attribute('id') or ''
                                class_attr = await element.get_attribute('class') or ''
                                type_attr = await element.get_attribute('type') or ''
                                value = await element.get_attribute('value') or ''

                                # 親要素のテキスト取得
                                parent = await element.query_selector('..')
                                parent_text = ''
                                if parent:
                                    parent_text = (await parent.text_content() or '').strip()[:100]

                                element_detail = {
                                    "index": j,
                                    "placeholder": placeholder,
                                    "name": name,
                                    "id": id_attr,
                                    "class": class_attr,
                                    "type": type_attr,
                                    "value": value,
                                    "parent_text": parent_text,
                                    "visible": await element.is_visible(),
                                    "enabled": await element.is_enabled()
                                }

                                selector_result["details"].append(element_detail)

                                print(f"         要素{j+1}: placeholder='{placeholder}', name='{name}', type='{type_attr}', visible={await element.is_visible()}")

                            except Exception as detail_error:
                                print(f"         要素{j+1} 詳細取得エラー: {detail_error}")
                    else:
                        print(f"       ❌ 要素なし")

                    debug_results["selectors_tested"].append(selector_result)

                except Exception as selector_error:
                    print(f"       ❌ セレクタエラー: {selector_error}")
                    debug_results["selectors_tested"].append({
                        "selector": selector,
                        "error": str(selector_error)
                    })

            # ページ全体の分析
            print(f"\n📊 ページ全体分析:")

            # 全てのinput要素を取得
            all_inputs = await self.navigator.page.query_selector_all("//input")
            print(f"   🔢 総input要素数: {len(all_inputs)}")

            # フォーム要素分析
            forms = await self.navigator.page.query_selector_all("//form")
            print(f"   📝 フォーム数: {len(forms)}")

            # Amount/serving関連のテキストを含む要素
            amount_texts = await self.navigator.page.query_selector_all("//*[contains(text(), 'Amount') or contains(text(), 'amount') or contains(text(), 'serving') or contains(text(), 'Serving')]")
            print(f"   📋 Amount/Serving関連テキスト要素: {len(amount_texts)}")

            if amount_texts:
                print("      関連テキスト例:")
                for i, text_elem in enumerate(amount_texts[:5]):
                    try:
                        text_content = (await text_elem.text_content() or '').strip()
                        if text_content:
                            print(f"        {i+1}. '{text_content[:50]}...'")
                    except:
                        pass

            debug_results["page_analysis"] = {
                "total_inputs": len(all_inputs),
                "total_forms": len(forms),
                "amount_related_texts": len(amount_texts)
            }

            return debug_results

        except Exception as e:
            print(f"❌ Amount eaten検出デバッグエラー: {e}")
            debug_results["error"] = str(e)
            return debug_results

    async def test_amount_eaten_interaction(self, test_selectors: List[str]) -> Dict[str, Any]:
        """Amount eaten要素との相互作用テスト"""
        interaction_results = {
            "timestamp": datetime.now().isoformat(),
            "interaction_tests": []
        }

        try:
            print("\n🧪 Amount eaten要素相互作用テスト")
            print("-" * 60)

            for i, selector in enumerate(test_selectors):
                try:
                    print(f"   テスト {i+1}: {selector}")

                    elements = await self.navigator.page.query_selector_all(selector)
                    if not elements:
                        print(f"     ❌ 要素が見つかりません")
                        continue

                    # 最初の要素でテスト
                    element = elements[0]

                    test_result = {
                        "selector": selector,
                        "element_found": True,
                        "interactions": {}
                    }

                    # 可視性チェック
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    print(f"     可視性: {is_visible}, 有効: {is_enabled}")

                    test_result["interactions"]["visibility"] = {
                        "visible": is_visible,
                        "enabled": is_enabled
                    }

                    if is_visible and is_enabled:
                        # クリックテスト
                        try:
                            await element.click(timeout=5000)
                            print(f"     ✅ クリック成功")
                            test_result["interactions"]["click"] = {"success": True}

                            # 入力テスト
                            try:
                                await element.fill("1.5", timeout=5000)
                                print(f"     ✅ 入力成功: '1.5'")
                                test_result["interactions"]["input"] = {"success": True, "value": "1.5"}

                                # 値の確認
                                value = await element.input_value()
                                print(f"     📋 入力後の値: '{value}'")
                                test_result["interactions"]["input"]["final_value"] = value

                            except Exception as input_error:
                                print(f"     ❌ 入力失敗: {input_error}")
                                test_result["interactions"]["input"] = {"success": False, "error": str(input_error)}

                        except Exception as click_error:
                            print(f"     ❌ クリック失敗: {click_error}")
                            test_result["interactions"]["click"] = {"success": False, "error": str(click_error)}

                    interaction_results["interaction_tests"].append(test_result)

                except Exception as test_error:
                    print(f"     ❌ テストエラー: {test_error}")
                    interaction_results["interaction_tests"].append({
                        "selector": selector,
                        "error": str(test_error)
                    })

            return interaction_results

        except Exception as e:
            print(f"❌ 相互作用テストエラー: {e}")
            interaction_results["error"] = str(e)
            return interaction_results

    async def save_debug_results(self, results: Dict[str, Any], filename: str):
        """デバッグ結果を保存"""
        try:
            debug_dir = Path("debug")
            debug_dir.mkdir(exist_ok=True)

            filepath = debug_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"💾 デバッグ結果保存: {filepath}")

        except Exception as e:
            print(f"❌ デバッグ結果保存エラー: {e}")

    async def run_full_debug_cycle(self, food_name: str, category: str):
        """完全なデバッグサイクルを実行"""
        try:
            print(f"🚀 Amount eaten要素検出 完全デバッグサイクル開始")
            print(f"   対象食材: {food_name}")
            print(f"   カテゴリ: {category}")
            print("="*80)

            # Step 1: 食材に移動
            navigation_success = await self.navigate_to_specific_food(food_name, category)
            if not navigation_success:
                print("❌ 食材移動失敗 - デバッグ中止")
                return

            # Step 2: Amount eaten要素検出分析
            detection_results = await self.debug_amount_eaten_detection()

            # Step 3: 成功した候補でテスト
            successful_selectors = [
                result["selector"] for result in detection_results["selectors_tested"]
                if isinstance(result.get("elements_found"), int) and result["elements_found"] > 0
            ]

            print(f"\n🎯 成功セレクタ ({len(successful_selectors)}個) で相互作用テスト:")
            for selector in successful_selectors[:5]:  # 上位5個をテスト
                print(f"   - {selector}")

            interaction_results = await self.test_amount_eaten_interaction(successful_selectors[:5])

            # Step 4: 結果をまとめて保存
            final_results = {
                "food_name": food_name,
                "category": category,
                "detection_analysis": detection_results,
                "interaction_tests": interaction_results,
                "recommendations": self.generate_recommendations(detection_results, interaction_results)
            }

            # Step 5: 結果保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await self.save_debug_results(
                final_results,
                f"amount_eaten_debug_{food_name.replace(' ', '_').replace(',', '')}_{timestamp}.json"
            )

            # Step 6: 推奨事項表示
            print("\n🎯 推奨事項:")
            for i, rec in enumerate(final_results["recommendations"], 1):
                print(f"   {i}. {rec}")

        except Exception as e:
            print(f"❌ 完全デバッグサイクルエラー: {e}")

    def generate_recommendations(self, detection_results: Dict, interaction_results: Dict) -> List[str]:
        """分析結果から推奨事項を生成"""
        recommendations = []

        # 成功したセレクタがある場合
        successful_detections = [
            result for result in detection_results["selectors_tested"]
            if isinstance(result.get("elements_found"), int) and result["elements_found"] > 0
        ]

        if successful_detections:
            # 最も多くの要素を見つけたセレクタ
            best_selector = max(successful_detections, key=lambda x: x["elements_found"])
            recommendations.append(f"最適セレクタ: {best_selector['selector']} ({best_selector['elements_found']}個の要素)")

            # 相互作用テストが成功したセレクタ
            successful_interactions = [
                test for test in interaction_results.get("interaction_tests", [])
                if test.get("interactions", {}).get("input", {}).get("success", False)
            ]

            if successful_interactions:
                working_selector = successful_interactions[0]["selector"]
                recommendations.append(f"動作確認済みセレクタ: {working_selector}")
            else:
                recommendations.append("入力テストに成功したセレクタはありませんでした - 別のアプローチが必要")
        else:
            recommendations.append("Amount eaten要素が全く検出されませんでした - ページ構造の変更が必要")

        return recommendations

    async def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.navigator:
                await self.navigator.cleanup_session()
            print("✅ デバッグセッションクリーンアップ完了")
        except Exception as e:
            print(f"❌ クリーンアップエラー: {e}")


async def main():
    """メイン実行関数"""
    debugger = AmountEatenDebugger()

    try:
        # セッション初期化
        init_success = await debugger.initialize_session()
        if not init_success:
            return

        # 現在処理中の食材でテスト
        test_foods = [
            ("Salt, cup", "Spices & Herbs"),
            ("Paprika, tbsp", "Spices & Herbs"),
            ("Water, cup", "Beverages")  # 以前失敗した食材も含める
        ]

        for food_name, category in test_foods:
            print(f"\n{'='*80}")
            print(f"🧪 テスト食材: {food_name} ({category})")
            print(f"{'='*80}")

            await debugger.run_full_debug_cycle(food_name, category)

            # 次のテストまで少し待機
            await asyncio.sleep(2)

    except Exception as e:
        print(f"❌ メイン実行エラー: {e}")

    finally:
        await debugger.cleanup()


if __name__ == "__main__":
    asyncio.run(main())