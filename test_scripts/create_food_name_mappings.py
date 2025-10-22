#!/usr/bin/env python
"""
spec2.mdの統合提案を基にUSDAデータベースから適切なマッピングを生成
"""

import json
from pathlib import Path
from collections import defaultdict
import re

# パス設定
project_root = Path(__file__).parent.parent
usda_names_dir = project_root / "usda_database" / "names_list"

def load_usda_database(file_path):
    """USDAデータベースファイルを読み込み"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def search_usda_matches(keyword, usda_items):
    """キーワードに一致するUSDA項目を検索"""
    matches = []
    keyword_lower = keyword.lower()

    for item in usda_items:
        item_lower = item.lower()
        # キーワードが含まれているか
        if keyword_lower in item_lower:
            # スコアを計算（より具体的な一致ほど高スコア）
            score = 0

            # NFSまたはNSが含まれている（最も汎用的）
            if "nfs" in item_lower or ", ns " in item_lower:
                score += 100

            # キーワードで始まる
            if item_lower.startswith(keyword_lower):
                score += 50

            # 完全一致
            if item_lower == keyword_lower:
                score += 200

            # 短い名前（シンプル）
            score -= len(item) * 0.1

            matches.append((score, item))

    # スコア順にソート（高い順）
    matches.sort(reverse=True, key=lambda x: x[0])
    return [(item, score) for score, item in matches]

def create_mappings():
    """spec2.mdの統合提案に基づきマッピングを生成"""

    # 各データベースファイルを読み込み
    db_files = {
        'survey': 'survey_food_names.txt',
        'sr_legacy': 'sr_legacy_food_names.txt',
        'foundation': 'foundation_food_names.txt',
        'branded': 'branded_food_names.txt'
    }

    all_usda_items = {}
    for db_name, file_name in db_files.items():
        db_path = usda_names_dir / file_name
        if db_path.exists():
            items = load_usda_database(db_path)
            for item in items:
                if item not in all_usda_items:
                    all_usda_items[item] = db_name

    # spec2.mdから抽出した統合提案
    mappings = {}

    # カテゴリ: 乳製品・卵類
    dairy_eggs = {
        "Cheese": {
            "display_name": "Cheese",
            "category": "dairy_eggs",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "視覚的に種類判別が難しく、一括「チーズ」として識別",
            "keywords": ["cheese"],
            "exclude_keywords": ["cream cheese", "cottage", "ricotta", "sauce"]
        },
        "Milk": {
            "display_name": "Milk",
            "category": "dairy_eggs",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "画像から脂肪分等の判別困難なため統合",
            "keywords": ["milk"],
            "exclude_keywords": ["chocolate milk", "buttermilk", "evaporated", "condensed", "soy", "almond", "oat"]
        },
        "Yogurt": {
            "display_name": "Yogurt",
            "category": "dairy_eggs",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "ギリシャヨーグルト等の質感差異は限定的",
            "keywords": ["yogurt"],
            "exclude_keywords": ["frozen"]
        },
        "Butter": {
            "display_name": "Butter",
            "category": "dairy_eggs",
            "keywords": ["butter"],
            "exclude_keywords": ["peanut butter", "apple butter"]
        },
        "Egg_boiled": {
            "display_name": "Egg (boiled)",
            "category": "dairy_eggs",
            "keywords": ["egg", "boiled"],
            "specific_search": ["egg, whole, hard-boiled", "egg, whole, boiled"]
        },
        "Egg_fried": {
            "display_name": "Egg (fried)",
            "category": "dairy_eggs",
            "keywords": ["egg", "fried"],
            "specific_search": ["egg, whole, fried"]
        },
        "Omelette": {
            "display_name": "Omelette",
            "category": "dairy_eggs",
            "keywords": ["omelet", "omelette"]
        }
    }

    # カテゴリ: パン・穀類
    bread_grains = {
        "Bread": {
            "display_name": "Bread",
            "category": "bread_grains",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "白パンや全粒パンの見た目の差は小さい",
            "keywords": ["bread"],
            "exclude_keywords": ["garlic bread", "cornbread", "breadcrumb", "gingerbread"]
        },
        "Rice": {
            "display_name": "Rice",
            "category": "bread_grains",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "白米と玄米の色違いのみで判別困難",
            "keywords": ["rice"],
            "exclude_keywords": ["rice cake", "rice pudding", "rice crispy", "wild rice"]
        },
        "Pasta": {
            "display_name": "Pasta",
            "category": "bread_grains",
            "keywords": ["pasta", "spaghetti", "macaroni", "noodles"],
            "exclude_keywords": ["rice noodles", "asian", "ramen", "udon", "soba"]
        },
        "Oatmeal": {
            "display_name": "Oatmeal",
            "category": "bread_grains",
            "keywords": ["oatmeal", "oat", "porridge"]
        },
        "Cereal": {
            "display_name": "Cereal",
            "category": "bread_grains",
            "spec2_rule": "統合（汎化）",
            "keywords": ["cereal"],
            "exclude_keywords": ["cooked"]
        },
        "Tortilla": {
            "display_name": "Tortilla",
            "category": "bread_grains",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "コーン/小麦粉の違いは見た目が似ており区別不要",
            "keywords": ["tortilla"]
        }
    }

    # カテゴリ: パスタ・麺類
    pasta_noodles = {
        "Spaghetti": {
            "display_name": "Spaghetti",
            "category": "pasta_noodles",
            "keywords": ["spaghetti"]
        },
        "Lasagna": {
            "display_name": "Lasagna",
            "category": "pasta_noodles",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "肉入り/菜食の見た目判別困難",
            "keywords": ["lasagna", "lasagne"]
        },
        "Ramen": {
            "display_name": "Ramen",
            "category": "pasta_noodles",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "スープ違いの差分が小さい",
            "keywords": ["ramen"]
        },
        "Fried_noodles": {
            "display_name": "Fried noodles",
            "category": "pasta_noodles",
            "spec2_rule": "名称統一",
            "keywords": ["lo mein", "chow mein", "pad thai", "fried noodles"]
        }
    }

    # カテゴリ: サラダ
    salads = {
        "Green_salad": {
            "display_name": "Green salad",
            "category": "salads",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "葉物野菜サラダ全般を統合",
            "keywords": ["salad", "green", "garden", "tossed"],
            "exclude_keywords": ["potato", "fruit", "macaroni", "pasta", "coleslaw", "chicken", "tuna", "egg"]
        },
        "Coleslaw": {
            "display_name": "Coleslaw",
            "category": "salads",
            "keywords": ["coleslaw", "cole slaw"]
        },
        "Potato_salad": {
            "display_name": "Potato salad",
            "category": "salads",
            "keywords": ["potato salad"]
        }
    }

    # カテゴリ: メキシコ料理
    mexican = {
        "Taco": {
            "display_name": "Taco",
            "category": "mexican",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "ハード/ソフトシェルの違いを統合",
            "keywords": ["taco"]
        },
        "Burrito": {
            "display_name": "Burrito",
            "category": "mexican",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "具材違いは外見から判別困難",
            "keywords": ["burrito"]
        },
        "Quesadilla": {
            "display_name": "Quesadilla",
            "category": "mexican",
            "keywords": ["quesadilla"]
        },
        "Nachos": {
            "display_name": "Nachos",
            "category": "mexican",
            "keywords": ["nachos"]
        }
    }

    # カテゴリ: ファストフード・サンドイッチ
    fast_food = {
        "Hamburger": {
            "display_name": "Hamburger",
            "category": "fast_food_sandwiches",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "チーズバーガーを含めて統合",
            "keywords": ["hamburger", "cheeseburger", "burger"],
            "exclude_keywords": ["veggie", "turkey"]
        },
        "Sandwich": {
            "display_name": "Sandwich",
            "category": "fast_food_sandwiches",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "中身の違いは見た目で区別困難",
            "keywords": ["sandwich"],
            "exclude_keywords": ["ice cream"]
        },
        "Hot_dog": {
            "display_name": "Hot dog",
            "category": "fast_food_sandwiches",
            "keywords": ["hot dog", "hotdog", "frankfurter"]
        },
        "French_fries": {
            "display_name": "French fries",
            "category": "fast_food_sandwiches",
            "keywords": ["french fries", "potato, french fries", "fries"]
        }
    }

    # カテゴリ: ピザ
    pizza = {
        "Pizza": {
            "display_name": "Pizza",
            "category": "pizza",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "トッピング違いを基本的に統合",
            "keywords": ["pizza"]
        }
    }

    # カテゴリ: デザート・菓子
    desserts = {
        "Ice_cream": {
            "display_name": "Ice cream",
            "category": "desserts_sweets",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "フレーバー違いは色以外の差が小さい",
            "keywords": ["ice cream", "gelato", "sorbet"]
        },
        "Cake": {
            "display_name": "Cake",
            "category": "desserts_sweets",
            "keywords": ["cake"],
            "exclude_keywords": ["pancake", "rice cake", "crab cake"]
        },
        "Cookie": {
            "display_name": "Cookie",
            "category": "desserts_sweets",
            "spec2_rule": "名称統一",
            "keywords": ["cookie", "biscuit"],
            "exclude_keywords": ["dog biscuit"]
        },
        "Donut": {
            "display_name": "Donut",
            "category": "desserts_sweets",
            "spec2_rule": "名称統一",
            "keywords": ["donut", "doughnut"]
        }
    }

    # カテゴリ: 飲料
    beverages = {
        "Water": {
            "display_name": "Water",
            "category": "beverages",
            "spec2_rule": "統合（汎化）",
            "keywords": ["water"],
            "exclude_keywords": ["watermelon", "water chestnut"]
        },
        "Coffee": {
            "display_name": "Coffee",
            "category": "beverages",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "ブラック/ラテ等を統合",
            "keywords": ["coffee"]
        },
        "Tea": {
            "display_name": "Tea",
            "category": "beverages",
            "spec2_rule": "統合（汎化）",
            "spec2_reason": "緑茶・紅茶等を統合",
            "keywords": ["tea"],
            "exclude_keywords": ["sweet potato"]
        },
        "Soda": {
            "display_name": "Soda",
            "category": "beverages",
            "keywords": ["soda", "soft drink", "cola", "carbonated"]
        },
        "Juice": {
            "display_name": "Juice",
            "category": "beverages",
            "keywords": ["juice"]
        }
    }

    # すべてのカテゴリを統合
    all_categories = {
        **dairy_eggs,
        **bread_grains,
        **pasta_noodles,
        **salads,
        **mexican,
        **fast_food,
        **pizza,
        **desserts,
        **beverages
    }

    # 各食品に対してUSDAマッピングを検索
    for food_id, food_info in all_categories.items():
        # デフォルトのUSDA項目を探す
        keywords = food_info.get("keywords", [])
        exclude = food_info.get("exclude_keywords", [])
        specific = food_info.get("specific_search", [])

        # 該当するUSDA項目を収集
        candidates = []

        # 特定の検索がある場合は優先
        if specific:
            for search_term in specific:
                for usda_item, db in all_usda_items.items():
                    if search_term.lower() in usda_item.lower():
                        candidates.append({
                            "name": usda_item,
                            "database": db,
                            "priority": 100  # 最優先
                        })

        # キーワード検索
        for keyword in keywords:
            for usda_item, db in all_usda_items.items():
                usda_lower = usda_item.lower()

                # 除外キーワードチェック
                excluded = False
                for ex in exclude:
                    if ex in usda_lower:
                        excluded = True
                        break

                if not excluded and keyword in usda_lower:
                    priority = 0

                    # NFS/NSがあれば優先度高
                    if "nfs" in usda_lower or ", ns " in usda_lower:
                        priority += 50

                    # キーワードで始まる
                    if usda_lower.startswith(keyword):
                        priority += 30

                    # 短い名前（シンプル）
                    priority -= len(usda_item) * 0.01

                    candidates.append({
                        "name": usda_item,
                        "database": db,
                        "priority": priority
                    })

        # 重複を除去し、優先度順にソート
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c["name"] not in seen:
                seen.add(c["name"])
                unique_candidates.append(c)

        unique_candidates.sort(key=lambda x: x["priority"], reverse=True)

        # デフォルトを選定（最も優先度が高いもの）
        default_usda = None
        if unique_candidates:
            top_candidate = unique_candidates[0]
            default_usda = {
                "name": top_candidate["name"],
                "database": top_candidate["database"]
            }

        # マッピング情報を構築
        mappings[food_id] = {
            "display_name": food_info["display_name"],
            "category": food_info["category"],
            "spec2_rule": food_info.get("spec2_rule", ""),
            "spec2_reason": food_info.get("spec2_reason", ""),
            "default_usda": default_usda,
            "all_usda_mappings": unique_candidates[:10]  # 上位10件まで
        }

    return mappings

def main():
    print("="*80)
    print("食品名マッピング生成")
    print("="*80)
    print()

    mappings = create_mappings()

    # 統計情報
    total = len(mappings)
    with_default = sum(1 for m in mappings.values() if m["default_usda"])

    print(f"総マッピング数: {total}")
    print(f"デフォルトUSDA項目が見つかった: {with_default} ({with_default/total*100:.1f}%)")
    print()

    # カテゴリ別に表示
    by_category = defaultdict(list)
    for food_id, info in mappings.items():
        by_category[info["category"]].append(info)

    for category, items in sorted(by_category.items()):
        print(f"\n【{category}】({len(items)}項目)")
        for item in items:
            display = item["display_name"]
            if item["default_usda"]:
                usda = item["default_usda"]["name"]
                print(f"  {display:20} → {usda}")
            else:
                print(f"  {display:20} → (マッピングなし)")

    # JSONファイルに保存
    output_file = Path(__file__).parent / "mappings" / "food_name_mappings.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, ensure_ascii=False, indent=2)

    print(f"\n✅ マッピングファイルを保存: {output_file}")

if __name__ == "__main__":
    main()