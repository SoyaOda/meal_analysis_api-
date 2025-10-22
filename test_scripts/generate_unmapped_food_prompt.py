#!/usr/bin/env python
"""
未マップ食品からマッピング生成用プロンプトを作成
Baby food以外のカテゴリを対象
"""

import json
from pathlib import Path
from collections import defaultdict

# ファイルパス
unmapped_report = Path(__file__).parent / "mappings" / "unmapped_foods_analysis.md"
output_prompt = Path(__file__).parent / "mappings" / "prompt" / "generate_mapping_prompt_v2.md"

def extract_unmapped_categories():
    """未マップレポートからカテゴリ別食品を抽出"""

    categories = defaultdict(list)
    current_category = None
    in_survey_section = False
    skip_categories = ['Baby food']

    with open(unmapped_report, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        # Survey FNDDS セクションの開始
        if "## 🔍 Survey FNDDS 未マップ食品" in line:
            in_survey_section = True
            continue

        # Foundation Food セクションの開始で終了
        if "## 🔍 Foundation Food 未マップ食品" in line:
            break

        if not in_survey_section:
            continue

        # カテゴリヘッダーの検出
        if line.startswith("### ") and "個)" in line:
            # カテゴリ名を抽出
            category = line.split("### ")[1].split(" (")[0]
            if category not in skip_categories:
                current_category = category
            else:
                current_category = None

        # 食品項目の抽出
        elif current_category and line.startswith("- ") and not line.startswith("  "):
            food_name = line[2:].strip()
            # "→ 類似:" の部分を除去
            if "→" not in food_name:
                categories[current_category].append(food_name)

    return categories

def create_enhanced_prompt(categories):
    """改良版プロンプトを作成"""

    prompt = """# USDA食品マッピング生成プロンプト v2.0

## 🎯 命令

以下の未マップUSDA食品に対して、実用的なマッピングを生成してください。

### 重要な前提条件
1. **用途**: AIが画像から食品を識別 → 栄養データベースと照合 → 栄養価計算
2. **優先順位**:
   - 視覚的に識別可能で頻出する食品を優先
   - 特殊な調理法や細かいバリエーションは統合
   - ブランド固有の商品は除外またはgeneric版に統合

## 📋 マッピング生成方針（改良版）

### 1. 統合の原則
- **視覚的類似性**: 写真で区別困難なものは統合
- **栄養的類似性**: 栄養価が近似するものは統合
- **実用性**: 一般的な食事シーンで頻出するものを優先

### 2. カテゴリ別の処理方針

#### Beverages（飲料）
- アルコール度数の違いは統合（例: beer → Beer）
- フレーバーの違いは基本統合（例: flavored water → Water）
- 主要な果汁飲料は独立維持（Orange juice, Apple juice等）

#### Restaurant/Fast Food
- ブランド名を除去して汎用化（例: "McDonald's burger" → "Hamburger"）
- 主要チェーン固有のメニューは除外または最も近い汎用カテゴリに統合

#### Ethnic Dishes（各国料理）
- 代表的な料理は独立カテゴリ（例: Pad Thai, Tandoori chicken）
- 細かいバリエーションは統合（例: various curry types → "Curry"）
- 視覚的に特徴的な料理を優先

#### Mixed Dishes（複合料理）
- 主材料で分類（例: "Beef and rice" → beef_dishesカテゴリ）
- ソースの違いは基本統合（with gravy/with sauce → 統一）
- "NFS"や"NS as to"表記は除去

#### Desserts
- 主要なデザートタイプごとに分類
- フレーバーバリエーションは限定的に（chocolate, vanilla程度）
- トッピングの有無は統合

### 3. 除外基準
以下は**マッピング不要**:
- Baby/Toddler food全般
- 学校給食専用メニュー（School lunch specific）
- WIC/USDA commodity foods
- 栄養補助食品（Supplement drinks等）
- 極めて特殊な地域料理

### 4. 命名規則
- NFSやNS表記を削除
- 調理法は主要なもののみ（fried, grilled, baked）
- 括弧内の詳細は基本削除
- display_nameは自然な英語表記

## 📝 マッピング例（改良版）

```json
{
  "meat_loaf": {
    "display_name": "Meat loaf",
    "category": "meat_dishes",
    "spec2_rule": "統合（汎化）",
    "spec2_reason": "牛肉・豚肉等の違いは視覚的に判別困難",
    "default_usda": {
      "name": "Meat loaf made with beef",
      "database": "survey_fndds",
      "reason": "最も一般的な牛肉ベースのミートローフ"
    },
    "all_usda_mappings": [
      {
        "name": "Meat loaf made with beef",
        "database": "survey_fndds",
        "specificity": "specific"
      },
      {
        "name": "Meat loaf made with beef and pork",
        "database": "survey_fndds",
        "specificity": "specific"
      },
      {
        "name": "Meat loaf made with beef, veal and pork",
        "database": "survey_fndds",
        "specificity": "specific"
      },
      {
        "name": "Meat loaf dinner, NFS, frozen meal",
        "database": "survey_fndds",
        "specificity": "generic"
      }
    ],
    "aliases": ["meatloaf", "meat loaf", "ground meat loaf"],
    "visual_hints": ["loaf shaped", "brown", "sliced", "ground meat texture"]
  },

  "caesar_salad": {
    "display_name": "Caesar salad",
    "category": "salads",
    "spec2_rule": "統合（汎化）",
    "spec2_reason": "ドレッシングの有無やトッピングの違いを統合",
    "default_usda": {
      "name": "Caesar salad, with romaine, no dressing",
      "database": "survey_fndds",
      "reason": "基本的なシーザーサラダ（ドレッシング別添え想定）"
    },
    "all_usda_mappings": [
      {
        "name": "Caesar salad, with romaine, no dressing",
        "database": "survey_fndds",
        "specificity": "generic"
      },
      {
        "name": "Chicken or turkey caesar garden salad, chicken and/or turkey, lettuce, tomato, cheese, no dressing",
        "database": "survey_fndds",
        "specificity": "specific"
      }
    ],
    "aliases": ["caesar", "caesar salad", "chicken caesar"],
    "visual_hints": ["romaine lettuce", "parmesan", "croutons", "creamy dressing"]
  },

  "french_fries": {
    "display_name": "French fries",
    "category": "potato_dishes",
    "spec2_rule": "統合（汎化）",
    "spec2_reason": "調理法や味付けの違いは視覚的に判別困難",
    "default_usda": {
      "name": "French fries, from fresh, deep fried",
      "database": "survey_fndds",
      "reason": "最も一般的なフライドポテト"
    },
    "all_usda_mappings": [
      {
        "name": "French fries, from fresh, deep fried",
        "database": "survey_fndds",
        "specificity": "generic"
      },
      {
        "name": "French fries, from frozen, deep fried",
        "database": "survey_fndds",
        "specificity": "specific"
      },
      {
        "name": "French fries, from frozen, oven baked",
        "database": "survey_fndds",
        "specificity": "specific"
      },
      {
        "name": "French fries, seasoned",
        "database": "survey_fndds",
        "specificity": "specific"
      }
    ],
    "aliases": ["fries", "french fries", "potato fries", "chips"],
    "visual_hints": ["golden", "crispy", "stick shaped", "fried potato"]
  }
}
```

## 🎯 生成対象食品リスト

以下のカテゴリの食品についてマッピングを生成してください：

"""

    # カテゴリごとに食品を追加
    for category, foods in sorted(categories.items()):
        if foods:  # 食品がある場合のみ
            prompt += f"\n### {category}\n"
            prompt += "```\n"
            for food in foods[:50]:  # 各カテゴリ最大50個
                prompt += f"{food}\n"
            if len(foods) > 50:
                prompt += f"... 他 {len(foods)-50}個\n"
            prompt += "```\n"

    prompt += """

## 📌 生成時の注意事項

1. **全ての食品を無理にマッピングしない**
   - 特殊すぎる項目は除外してOK
   - 実用性の低い項目はスキップ

2. **統合を積極的に**
   - 似た食品は1つのキーにまとめる
   - all_usda_mappingsに複数のバリエーションを含める

3. **カテゴリの適切な設定**
   - 既存カテゴリを参考に
   - 新規カテゴリは慎重に

4. **視覚的特徴を重視**
   - visual_hintsは具体的に
   - 写真で識別可能な特徴を列挙

5. **データベース指定**
   - 基本は "survey_fndds"
   - Foundation Foodは特別な場合のみ

生成形式：
- JSON形式で出力
- インデント：2スペース
- 日本語コメント可

マッピング不要と判断した食品は、理由とともに別途リストアップしてください。
"""

    return prompt

def main():
    print("="*80)
    print("未マップ食品プロンプト生成")
    print("="*80)
    print()

    # カテゴリ別食品を抽出
    print("📚 未マップ食品を抽出中...")
    categories = extract_unmapped_categories()

    # 統計表示
    total_foods = sum(len(foods) for foods in categories.values())
    print(f"\n📊 抽出結果:")
    print(f"  カテゴリ数: {len(categories)}")
    print(f"  総食品数: {total_foods}")
    print(f"\n  カテゴリ別:")
    for category, foods in sorted(categories.items()):
        print(f"    {category}: {len(foods)}個")

    # プロンプト生成
    print("\n✍️ プロンプト生成中...")
    prompt = create_enhanced_prompt(categories)

    # ファイル保存
    output_prompt.parent.mkdir(parents=True, exist_ok=True)
    with open(output_prompt, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print(f"\n📁 プロンプト保存: {output_prompt}")
    print(f"   ファイルサイズ: {len(prompt):,} 文字")

    print("\n" + "="*80)
    print("✅ 完了")
    print("="*80)

if __name__ == "__main__":
    main()