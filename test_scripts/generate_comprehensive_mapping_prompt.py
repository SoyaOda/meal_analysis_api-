#!/usr/bin/env python
"""
未マップ食品から包括的なマッピング生成プロンプトを作成
実際の未マップ分析レポートを全て読み込んで正確に処理
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter

# ファイルパス
mappings_file = Path(__file__).parent / "mappings" / "mappings.json"
survey_names_file = Path(__file__).parent.parent / "usda_database" / "names_list" / "survey_food_names.txt"
foundation_names_file = Path(__file__).parent.parent / "usda_database" / "names_list" / "foundation_food_names.txt"
output_prompt = Path(__file__).parent / "mappings" / "prompt" / "comprehensive_mapping_prompt.md"

def load_existing_mapped_names():
    """既存マッピングから全食品名を取得"""
    with open(mappings_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mapped_names = set()
    for key, mapping in data['mappings'].items():
        if 'default_usda' in mapping and mapping['default_usda']:
            if 'name' in mapping['default_usda']:
                mapped_names.add(mapping['default_usda']['name'])

        if 'survey_alternative' in mapping:
            if 'name' in mapping['survey_alternative']:
                mapped_names.add(mapping['survey_alternative']['name'])

        if 'all_usda_mappings' in mapping:
            for item in mapping['all_usda_mappings']:
                if isinstance(item, dict) and 'name' in item:
                    mapped_names.add(item['name'])
                elif isinstance(item, str):
                    mapped_names.add(item)

    return mapped_names

def load_all_usda_names():
    """全USDA食品名を読み込み"""
    survey_names = []
    with open(survey_names_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # 番号を除去
                if '. ' in line and line.split('. ', 1)[0].isdigit():
                    name = line.split('. ', 1)[1]
                else:
                    name = line
                survey_names.append(name)

    foundation_names = []
    with open(foundation_names_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '. ' in line and line.split('. ', 1)[0].isdigit():
                    name = line.split('. ', 1)[1]
                else:
                    name = line
                foundation_names.append(name)

    return survey_names, foundation_names

def categorize_foods(unmapped_foods):
    """食品を詳細にカテゴリ分類"""
    categories = defaultdict(list)

    # カテゴリ判定ルール（優先順位順）
    category_rules = [
        # Baby food (最優先で除外)
        ('Baby food', lambda f: any(word in f.lower() for word in ['baby', 'toddler', 'infant'])),

        # School/Institutional
        ('School/Institutional', lambda f: any(word in f.lower() for word in ['school', 'cafeteria', 'wic', 'usda commodity'])),

        # Restaurant brands
        ('Restaurant brands', lambda f: any(brand in f.lower() for brand in
            ['mcdonald', 'burger king', 'subway', 'pizza hut', 'kfc', 'wendy', 'taco bell',
             'domino', 'starbucks', 'dunkin', 'chipotle', 'panera'])),

        # 主要な料理カテゴリ
        ('Meat loaf varieties', lambda f: 'meat loaf' in f.lower()),
        ('Caesar varieties', lambda f: 'caesar' in f.lower()),
        ('Pizza varieties', lambda f: 'pizza' in f.lower() and 'roll' not in f.lower()),
        ('Sandwich varieties', lambda f: 'sandwich' in f.lower()),
        ('Burger varieties', lambda f: 'burger' in f.lower() or 'hamburger' in f.lower()),
        ('Taco/Mexican', lambda f: any(word in f.lower() for word in ['taco', 'burrito', 'enchilada', 'quesadilla', 'fajita', 'chimichanga'])),
        ('Asian dishes', lambda f: any(word in f.lower() for word in
            ['chinese', 'asian', 'korean', 'japanese', 'thai', 'vietnamese', 'kung pao', 'pad thai',
             'bibimbap', 'sushi', 'ramen', 'pho', 'dim sum', 'chow mein', 'lo mein'])),
        ('Italian dishes', lambda f: any(word in f.lower() for word in
            ['italian', 'pasta', 'spaghetti', 'lasagna', 'ravioli', 'alfredo', 'marinara', 'parmesan'])),
        ('Indian dishes', lambda f: any(word in f.lower() for word in
            ['indian', 'curry', 'tandoori', 'tikka', 'biryani', 'naan', 'samosa', 'dal', 'paneer'])),

        # Breakfast
        ('Breakfast items', lambda f: any(word in f.lower() for word in
            ['breakfast', 'cereal', 'pancake', 'waffle', 'french toast', 'omelet', 'bacon', 'sausage'])),

        # Salads
        ('Salad varieties', lambda f: 'salad' in f.lower()),

        # Soups & Stews
        ('Soups and stews', lambda f: any(word in f.lower() for word in ['soup', 'stew', 'chowder', 'bisque', 'broth'])),

        # Desserts
        ('Desserts and sweets', lambda f: any(word in f.lower() for word in
            ['cake', 'cookie', 'pie', 'pudding', 'ice cream', 'candy', 'chocolate', 'sweet', 'dessert',
             'brownie', 'donut', 'doughnut', 'pastry', 'tart'])),

        # Beverages
        ('Beverages', lambda f: any(word in f.lower() for word in
            ['drink', 'juice', 'soda', 'coffee', 'tea', 'milk', 'shake', 'smoothie', 'water',
             'beer', 'wine', 'cocktail', 'alcoholic'])),

        # Snacks
        ('Snacks', lambda f: any(word in f.lower() for word in
            ['chips', 'crackers', 'popcorn', 'pretzel', 'nuts', 'trail mix', 'snack'])),

        # Condiments/Sauces
        ('Sauces and condiments', lambda f: any(word in f.lower() for word in
            ['sauce', 'dressing', 'dip', 'mayo', 'ketchup', 'mustard', 'salsa', 'gravy', 'marinade'])),

        # Preparation methods
        ('Fried foods', lambda f: 'fried' in f.lower() or 'fries' in f.lower()),
        ('Grilled/BBQ', lambda f: any(word in f.lower() for word in ['grilled', 'barbecue', 'bbq', 'roasted'])),
        ('Baked goods', lambda f: 'baked' in f.lower() or 'baking' in f.lower()),

        # Mixed/Complex dishes
        ('Mixed dishes with meat', lambda f: ('beef' in f.lower() or 'pork' in f.lower() or 'chicken' in f.lower())
            and any(word in f.lower() for word in ['with', 'and'])),
        ('Vegetable dishes', lambda f: any(veg in f.lower() for veg in
            ['broccoli', 'carrot', 'potato', 'tomato', 'lettuce', 'cabbage', 'spinach', 'bean', 'corn', 'pea'])
            and 'salad' not in f.lower()),

        # Seafood
        ('Seafood dishes', lambda f: any(word in f.lower() for word in
            ['fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'seafood', 'calamari', 'oyster'])),

        # Default
        ('Other foods', lambda f: True)
    ]

    # 各食品をカテゴリに分類
    for food in unmapped_foods:
        categorized = False
        for category_name, rule_func in category_rules:
            if rule_func(food):
                categories[category_name].append(food)
                categorized = True
                break

        if not categorized:
            categories['Other foods'].append(food)

    return categories

def create_comprehensive_prompt(categories):
    """包括的なプロンプトを作成"""

    prompt = """# USDA食品マッピング生成プロンプト v3.0 - 包括版

## 🎯 ミッション

未マップのUSDA食品（Survey FNDDS: 4,290個、Foundation Food: 84個）から、実用的で効率的なマッピングを生成する。

## 📊 現状分析

### マッピング済み
- **487個**の汎用食品カテゴリがマッピング済み
- 基本食材と一般的な料理をカバー

### 未マップの内訳
- **79%**のSurvey FNDDS食品が未マップ
- 主に以下のタイプ：
  - 具体的な料理名（Meat loaf, Caesar salad等）
  - ブランド別商品（McDonald's, Burger King等）
  - 調理法別バリエーション（fried, grilled, baked）
  - ソース・調味料別（with cheese sauce, with gravy）
  - 栄養調整版（fat free, light, reduced sodium）

## 🔧 マッピング戦略

### 1. 優先順位の原則

#### 高優先度（必ずマッピング）
- **頻出食品**: レストラン、家庭料理でよく見る
- **視覚的に特徴的**: 写真で明確に識別可能
- **栄養的に重要**: カロリー/栄養素が大きく異なる

#### 低優先度（除外対象）
- Baby/Toddler food（91個）
- 学校給食専用品
- WIC/USDA commodity foods
- 極めて特殊な地域料理
- ブランド固有の細かいバリエーション

### 2. 統合ルール

#### 積極的統合
```
例: Meat loaf varieties → "meat_loaf"
- Meat loaf made with beef
- Meat loaf made with beef and pork
- Meat loaf made with turkey
→ 全て"meat_loaf"に統合（肉種の違いは視覚的に判別困難）
```

#### 条件付き統合
```
例: Caesar salad varieties → "caesar_salad"
- Caesar salad, with romaine, no dressing
- Chicken caesar salad
- Caesar salad with shrimp
→ 基本は"caesar_salad"、チキン/シュリンプは視覚的に判別可能なら分離も検討
```

#### 分離維持
```
例: Pizza types
- Pizza (cheese) → "pizza"
- Pizza rolls → "pizza_rolls"（形状が全く異なる）
- Dessert pizza → "dessert_pizza"（デザート系は別カテゴリ）
```

### 3. 命名規則

#### キー名（JSON key）
- 小文字、アンダースコア区切り
- 例: `meat_loaf`, `caesar_salad`, `french_fries`

#### display_name
- 自然な英語表記、タイトルケース
- 例: "Meat loaf", "Caesar salad", "French fries"

#### default_usda選定
- 最も一般的/代表的なバリエーション
- NFSがある場合は優先（汎用的）
- 無い場合は最もシンプルな名称

### 4. カテゴリ設定

既存カテゴリを優先使用:
- `meat_dishes` - 肉料理全般
- `salads` - サラダ類
- `sandwiches` - サンドイッチ類
- `mexican` - メキシコ料理
- `asian` - アジア料理
- `italian` - イタリア料理
- `indian` - インド料理
- `breakfast` - 朝食系
- `desserts` - デザート
- `beverages` - 飲み物
- `snacks` - スナック類
- `seafood` - シーフード
- `soups_stews` - スープ・シチュー
- `potato_dishes` - じゃがいも料理
- `mixed_dishes` - 複合料理

## 📝 詳細マッピング例

```json
{
  "meat_loaf": {
    "display_name": "Meat loaf",
    "category": "meat_dishes",
    "spec2_rule": "統合（汎化）",
    "spec2_reason": "肉種の違いは視覚的に判別困難、栄養価も類似",
    "default_usda": {
      "name": "Meat loaf made with beef",
      "database": "survey_fndds",
      "reason": "最も一般的な牛肉ベース"
    },
    "all_usda_mappings": [
      {"name": "Meat loaf made with beef", "database": "survey_fndds", "specificity": "specific"},
      {"name": "Meat loaf made with beef and pork", "database": "survey_fndds", "specificity": "specific"},
      {"name": "Meat loaf made with beef, veal and pork", "database": "survey_fndds", "specificity": "specific"},
      {"name": "Meat loaf made with turkey", "database": "survey_fndds", "specificity": "specific"},
      {"name": "Meat loaf dinner, NFS, frozen meal", "database": "survey_fndds", "specificity": "generic"}
    ],
    "aliases": ["meatloaf", "meat loaf", "ground meat loaf"],
    "visual_hints": ["loaf shaped", "brown exterior", "sliced", "ground meat texture", "often with glaze"],
    "is_new_mapping": true,
    "data_sources": ["survey_fndds"],
    "nutritional_variance": "low"  // 栄養価のばらつき: low/medium/high
  },

  "caesar_salad": {
    "display_name": "Caesar salad",
    "category": "salads",
    "spec2_rule": "統合（汎化）",
    "spec2_reason": "基本構成は同じ、トッピングの有無を統合",
    "default_usda": {
      "name": "Caesar salad, with romaine, no dressing",
      "database": "survey_fndds",
      "reason": "ドレッシング別添えを想定した基本形"
    },
    "all_usda_mappings": [
      {"name": "Caesar salad, with romaine, no dressing", "database": "survey_fndds", "specificity": "generic"},
      {"name": "Caesar dressing", "database": "survey_fndds", "specificity": "component"},
      {"name": "Chicken or turkey caesar garden salad, chicken and/or turkey, lettuce, tomato, cheese, no dressing",
       "database": "survey_fndds", "specificity": "specific"}
    ],
    "aliases": ["caesar", "caesar salad", "chicken caesar", "romaine salad"],
    "visual_hints": ["romaine lettuce", "parmesan shavings", "croutons", "creamy white dressing", "anchovies optional"],
    "is_new_mapping": true,
    "common_additions": ["grilled chicken", "shrimp", "salmon"],
    "nutritional_variance": "medium"
  },

  "bibimbap": {
    "display_name": "Bibimbap",
    "category": "asian",
    "spec2_rule": "維持",
    "spec2_reason": "韓国の代表的料理、視覚的に特徴的",
    "default_usda": {
      "name": "Bibimbap, Korean",
      "database": "survey_fndds",
      "reason": "韓国の混ぜご飯料理"
    },
    "all_usda_mappings": [
      {"name": "Bibimbap, Korean", "database": "survey_fndds", "specificity": "specific"}
    ],
    "aliases": ["bibimbap", "korean mixed rice", "비빔밥"],
    "visual_hints": ["bowl presentation", "colorful vegetables arranged", "fried egg on top", "rice base", "gochujang sauce"],
    "is_new_mapping": true,
    "cultural_cuisine": "Korean",
    "nutritional_variance": "medium"
  }
}
```

## 🎯 生成対象食品（カテゴリ別）

"""

    # Baby food以外のカテゴリを追加
    skip_categories = {'Baby food', 'School/Institutional'}

    # 重要カテゴリを優先順位順に
    priority_order = [
        'Meat loaf varieties',
        'Caesar varieties',
        'Pizza varieties',
        'Sandwich varieties',
        'Burger varieties',
        'Taco/Mexican',
        'Asian dishes',
        'Italian dishes',
        'Indian dishes',
        'Breakfast items',
        'Salad varieties',
        'Soups and stews',
        'Desserts and sweets',
        'Beverages',
        'Seafood dishes',
        'Mixed dishes with meat',
        'Fried foods',
        'Grilled/BBQ',
        'Sauces and condiments',
        'Snacks',
        'Restaurant brands',
        'Other foods'
    ]

    # カテゴリごとに食品リストを追加
    for category_name in priority_order:
        if category_name in categories and category_name not in skip_categories:
            foods = categories[category_name]
            if foods:
                # サンプル数を調整（重要カテゴリは多め）
                sample_size = 30 if category_name in ['Meat loaf varieties', 'Caesar varieties', 'Pizza varieties'] else 20

                prompt += f"\n### {category_name} ({len(foods)}個)\n\n"
                prompt += "```\n"
                for i, food in enumerate(foods[:sample_size], 1):
                    prompt += f"{i}. {food}\n"
                if len(foods) > sample_size:
                    prompt += f"\n... 他 {len(foods)-sample_size}個\n"
                prompt += "```\n"

    prompt += """

## 📋 生成ガイドライン

### 必須フィールド
- `display_name`: ユーザー表示用の自然な名称
- `category`: 既存カテゴリから選択
- `spec2_rule`: "統合（汎化）"、"維持"、"分離"のいずれか
- `spec2_reason`: 判断理由を簡潔に
- `default_usda`: 最も代表的なUSDA名
- `all_usda_mappings`: 全ての関連USDA名をリスト化
- `aliases`: 検索用の別名
- `visual_hints`: 画像認識の手がかり

### オプションフィールド
- `is_new_mapping`: true（新規マッピング）
- `nutritional_variance`: "low"/"medium"/"high"
- `common_additions`: よくあるトッピング/追加食材
- `cultural_cuisine`: 料理の文化圏
- `preparation_method`: 主な調理法

### 生成のコツ
1. **1つのキーに多くのバリエーションをまとめる**
   - 視覚的に似ているものは積極統合
   - all_usda_mappingsを充実させる

2. **実用性を重視**
   - レストランメニューでよく見るものを優先
   - 家庭料理の定番を押さえる

3. **画像認識を意識**
   - visual_hintsは具体的に
   - 色、形、質感、盛り付けを記述

4. **栄養価の違いを考慮**
   - 大きく異なる場合は分離も検討
   - nutritional_varianceで示す

## 📦 期待する出力

1. **JSONマッピング**: 上記形式で50-100個程度の新規マッピング
2. **除外リスト**: マッピング不要と判断した食品とその理由
3. **統合提案**: 既存マッピングと統合可能な項目があれば提案

優先的に以下をマッピング:
- Meat loaf全バリエーション
- Caesar salad全バリエーション
- 主要なpizza種類（dessert pizza除く）
- 一般的なsandwich類
- 代表的なethnic dishes
- 頻出するmixed dishes

生成開始してください。
"""

    return prompt, categories

def main():
    print("="*80)
    print("包括的マッピングプロンプト生成")
    print("="*80)
    print()

    # 既存マッピングを読み込み
    print("📚 データ読み込み中...")
    mapped_names = load_existing_mapped_names()
    survey_names, foundation_names = load_all_usda_names()

    # 未マップを特定
    unmapped_survey = [name for name in survey_names if name not in mapped_names]
    unmapped_foundation = [name for name in foundation_names if name not in mapped_names]
    all_unmapped = unmapped_survey + unmapped_foundation

    print(f"   マップ済み: {len(mapped_names)}個")
    print(f"   未マップSurvey: {len(unmapped_survey)}個")
    print(f"   未マップFoundation: {len(unmapped_foundation)}個")

    # カテゴリ分類
    print("\n🏷️ カテゴリ分類中...")
    categories = categorize_foods(all_unmapped)

    # 統計表示
    print(f"\n📊 カテゴリ別統計:")
    total_categorized = sum(len(foods) for foods in categories.values())

    # サイズ順にソート
    sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)

    for category, foods in sorted_categories[:15]:  # Top 15カテゴリ
        percentage = len(foods) / total_categorized * 100
        print(f"   {category:30s}: {len(foods):4d}個 ({percentage:5.1f}%)")

    # プロンプト生成
    print("\n✍️ プロンプト生成中...")
    prompt, categories_dict = create_comprehensive_prompt(categories)

    # ファイル保存
    output_prompt.parent.mkdir(parents=True, exist_ok=True)
    with open(output_prompt, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print(f"\n📁 プロンプト保存: {output_prompt}")
    print(f"   ファイルサイズ: {len(prompt):,} 文字")

    # 重要な未マップ食品のハイライト
    print("\n⭐ 優先マッピング対象（例）:")
    highlight_items = [
        "Meat loaf made with beef",
        "Caesar salad, with romaine, no dressing",
        "Pizza, pepperoni, from restaurant or fast food",
        "Hamburger, plain, on white bun",
        "Bibimbap, Korean",
        "Pad Thai",
        "Chicken tikka masala"
    ]

    for item in highlight_items:
        if item in all_unmapped:
            print(f"   ✓ {item}")

    print("\n" + "="*80)
    print("✅ 完了")
    print("="*80)

if __name__ == "__main__":
    main()