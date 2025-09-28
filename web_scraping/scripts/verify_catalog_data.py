#!/usr/bin/env python3
"""
カタログデータ検証スクリプト
保存済み食材カタログの構造と検索機能を確認
"""

import json
import re
from pathlib import Path
from datetime import datetime


class CatalogDataVerifier:
    """カタログデータ検証クラス"""

    def __init__(self):
        self.food_catalog = {}
        self.food_index = {}

    def load_catalog_data(self):
        """保存済みカタログデータを読み込み"""
        print("📁 保存済みカタログデータを読み込み中...")

        data_dir = Path("food_catalog_data")
        json_files = [f for f in data_dir.glob("*.json") if not f.name.startswith(("collection_summary", "navigation_test"))]

        if not json_files:
            print("❌ カタログデータが見つかりません")
            return False

        total_foods = 0
        for file in json_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                category_name = data['category_data']['name']
                foods = data['category_data']['foods']

                self.food_catalog[category_name] = {
                    "category_info": {
                        "name": category_name,
                        "xpath": data['category_data']['xpath'],
                        "file_source": file.name
                    },
                    "foods": foods,
                    "food_count": len(foods)
                }

                # 食材インデックスを構築
                for food in foods:
                    normalized_name = self._normalize_food_name(food['food_name'])
                    self.food_index[normalized_name] = {
                        "original_name": food['food_name'],
                        "category": category_name,
                        "navigation_info": food
                    }

                total_foods += len(foods)

            except Exception as e:
                print(f"⚠️ ファイル読み込みエラー: {file.name} - {e}")
                continue

        print(f"✅ カタログ読み込み完了:")
        print(f"   📂 カテゴリ数: {len(self.food_catalog)}個")
        print(f"   🍽️ 総食材数: {total_foods}個")
        print(f"   🔍 検索インデックス: {len(self.food_index)}個")

        return len(self.food_catalog) > 0

    def _normalize_food_name(self, food_name):
        """食材名を正規化（検索用）"""
        return food_name.lower().strip().replace('\n', ' ')

    def verify_data_structure(self):
        """データ構造を検証"""
        print("\n🔍 データ構造検証")
        print("="*60)

        for category_name, category_data in self.food_catalog.items():
            print(f"\n📂 カテゴリ: {category_name}")
            print(f"   📄 ソースファイル: {category_data['category_info']['file_source']}")
            print(f"   🥗 食材数: {category_data['food_count']}個")
            print(f"   🎯 XPath: {category_data['category_info']['xpath']}")

            # 食材サンプルを表示
            foods = category_data['foods']
            sample_count = min(3, len(foods))
            print(f"   📋 食材サンプル ({sample_count}個):")

            for i in range(sample_count):
                food = foods[i]
                food_name = food['food_name'][:50] + "..." if len(food['food_name']) > 50 else food['food_name']
                print(f"     {i+1}. {food_name}")
                print(f"        ページ: {food['page_number']}, 位置: {food['position_in_page']}")
                print(f"        XPath: {food['xpath']}")

    def test_food_search(self, search_queries):
        """食材検索機能をテスト"""
        print(f"\n🔍 食材検索テスト")
        print("="*60)

        for query in search_queries:
            print(f"\n🔎 検索クエリ: '{query}'")

            # 部分一致検索
            matches = self._search_foods(query)

            if matches:
                print(f"✅ {len(matches)}個の食材が見つかりました:")
                for i, match in enumerate(matches[:5], 1):  # 最大5個表示
                    food_info = match['navigation_info']
                    print(f"  {i}. {match['original_name'][:60]}...")
                    print(f"     📂 カテゴリ: {match['category']}")
                    print(f"     📄 ページ: {food_info['page_number']}, 位置: {food_info['position_in_page']}")

                if len(matches) > 5:
                    print(f"     ... 他 {len(matches) - 5}個")
            else:
                print("❌ 該当する食材が見つかりませんでした")

    def _search_foods(self, query):
        """食材検索（部分一致）"""
        normalized_query = query.lower().strip()
        matches = []

        for normalized_name, food_info in self.food_index.items():
            if normalized_query in normalized_name:
                matches.append(food_info)

        return matches

    def analyze_navigation_requirements(self):
        """ナビゲーション要件を分析"""
        print(f"\n📊 ナビゲーション要件分析")
        print("="*60)

        # ページ数統計
        page_stats = {}
        position_stats = {}
        xpath_patterns = {}

        for category_name, category_data in self.food_catalog.items():
            for food in category_data['foods']:
                # ページ数統計
                page_num = food['page_number']
                page_stats[page_num] = page_stats.get(page_num, 0) + 1

                # 位置統計
                position = food['position_in_page']
                position_stats[position] = position_stats.get(position, 0) + 1

                # XPathパターン分析
                xpath = food['xpath']
                pattern = re.search(r'\[(\d+)\]$', xpath)
                if pattern:
                    xpath_index = int(pattern.group(1))
                    xpath_patterns[xpath_index] = xpath_patterns.get(xpath_index, 0) + 1

        print(f"📄 ページ分布:")
        for page in sorted(page_stats.keys()):
            print(f"   ページ{page}: {page_stats[page]}個の食材")

        print(f"\n📍 ページ内位置分布 (上位10):")
        for position in sorted(position_stats.keys())[:10]:
            print(f"   位置{position}: {position_stats[position]}個の食材")

        print(f"\n🎯 XPathインデックス分布 (上位10):")
        for xpath_idx in sorted(xpath_patterns.keys())[:10]:
            print(f"   インデックス{xpath_idx}: {xpath_patterns[xpath_idx]}個の食材")

    def generate_navigation_examples(self):
        """ナビゲーション例を生成"""
        print(f"\n💡 ナビゲーション例")
        print("="*60)

        example_foods = []
        for category_name, category_data in self.food_catalog.items():
            foods = category_data['foods']
            if foods:
                # 各カテゴリから1つ選択
                example_foods.append((category_name, foods[0]))

        for category_name, food in example_foods:
            print(f"\n🥗 例: {food['food_name'][:50]}...")
            print(f"   📂 カテゴリ: {category_name}")
            print(f"   🎯 ナビゲーション手順:")
            print(f"     1. Staple Foodsをクリック")
            print(f"     2. {category_name}をクリック")
            if food['page_number'] > 1:
                print(f"     3. {food['page_number']}ページまで移動")
            print(f"     4. {food['position_in_page']}番目の食材をクリック")
            print(f"   📋 技術的情報:")
            print(f"     - カテゴリXPath: {self.food_catalog[category_name]['category_info']['xpath']}")
            print(f"     - 食材XPath: {food['xpath']}")

    def save_verification_report(self):
        """検証レポートを保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"food_catalog_data/catalog_verification_report_{timestamp}.json"

        report_data = {
            "verification_report": {
                "timestamp": datetime.now().isoformat(),
                "total_categories": len(self.food_catalog),
                "total_foods": len(self.food_index),
                "categories_summary": {}
            },
            "category_details": {},
            "navigation_examples": {}
        }

        # カテゴリ詳細
        for category_name, category_data in self.food_catalog.items():
            report_data["categories_summary"][category_name] = {
                "food_count": category_data["food_count"],
                "xpath": category_data["category_info"]["xpath"],
                "source_file": category_data["category_info"]["file_source"]
            }

            # ナビゲーション例
            if category_data["foods"]:
                sample_food = category_data["foods"][0]
                report_data["navigation_examples"][category_name] = {
                    "food_name": sample_food["food_name"],
                    "navigation_steps": [
                        "Staple Foodsをクリック",
                        f"{category_name}をクリック",
                        f"ページ{sample_food['page_number']}に移動（必要に応じて）",
                        f"{sample_food['position_in_page']}番目の食材をクリック"
                    ],
                    "technical_info": {
                        "category_xpath": category_data["category_info"]["xpath"],
                        "food_xpath": sample_food["xpath"],
                        "page_number": sample_food["page_number"],
                        "position_in_page": sample_food["position_in_page"]
                    }
                }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 検証レポートを保存: {filename}")
        return filename

    def run_verification(self):
        """検証を実行"""
        print("🔍 カタログデータ検証開始")
        print("="*80)

        # データ読み込み
        if not self.load_catalog_data():
            return False

        # 構造検証
        self.verify_data_structure()

        # 検索テスト
        test_queries = [
            "milk",
            "cheese",
            "bread",
            "beer",
            "chicken"
        ]
        self.test_food_search(test_queries)

        # ナビゲーション要件分析
        self.analyze_navigation_requirements()

        # ナビゲーション例生成
        self.generate_navigation_examples()

        # レポート保存
        report_file = self.save_verification_report()

        print(f"\n✅ カタログデータ検証完了！")
        print(f"📁 レポート: {report_file}")

        return True


def main():
    verifier = CatalogDataVerifier()
    success = verifier.run_verification()

    if success:
        print(f"\n🎉 検証が正常に完了しました！")
    else:
        print(f"\n💥 検証に失敗しました。")


if __name__ == "__main__":
    main()