# 🔗 Manual Templates と Stemmed DB の対応付けシステム

マニュアル入力テンプレートとStemmed DBの食材を対応付け、包括的なマッピング情報を生成するシステム

---

## 📋 概要

このディレクトリには、`manual_input_templates`（手動入力テンプレート）と`db/mynetdiary_converted_tool_calls_list_stemmed.json`（Stemmed DB）の食材を対応付けるためのスクリプトと、生成された対応表が含まれています。

### 目的

1. **対応表の作成**: マニュアルテンプレートの食材とStemmed DBの食材を1対1で対応付け
2. **未対応食材の特定**: どちらか一方にのみ存在する食材を明確化
3. **データ品質の可視化**: カテゴリ別の対応状況を統計化

---

## 📁 ディレクトリ構造

```
web_scraping_2/
├── README.md                                    # このファイル
├── create_manual_stemmed_correspondence.py      # 対応表作成スクリプト
├── manual_input_templates/                      # マニュアル入力テンプレート（19カテゴリ）
│   ├── beans_and_peas_manual_input.txt
│   ├── beverages_manual_input.txt
│   ├── breads_and_rolls_manual_input.txt
│   ├── cheese_manual_input.txt
│   ├── condiments_dressings_and_sauces_manual_input.txt
│   ├── dairy_dairy_substitutes_and_egg_manual_input.txt
│   ├── fats_and_oils_manual_input.txt
│   ├── fish_and_seafood_manual_input.txt
│   ├── fruit_-_canned_dried_or_juice_manual_input.txt
│   ├── fruit_-_raw_or_frozen_manual_input.txt
│   ├── grains_and_grain_products_manual_input.txt
│   ├── meats_manual_input.txt
│   ├── nuts_and_seeds_manual_input.txt
│   ├── poultry_manual_input.txt
│   ├── spices_and_herbs_manual_input.txt
│   ├── stocks_and_gravy_manual_input.txt
│   ├── sweets_and_sweeteners_manual_input.txt
│   ├── vegetables_-_canned_dried_or_juice_manual_input.txt
│   └── vegetables_-_raw_frozen_or_cooked_manual_input.txt
└── output/                                      # 生成ファイル
    ├── manual_to_stemmed_correspondence.json    # 対応表（1,117件）
    ├── manual_only_foods.json                   # マニュアルのみに存在（13件）
    ├── stemmed_only_foods.json                  # Stemmed DBのみに存在（25件）
    ├── correspondence_summary.json              # サマリー統計
    └── category_statistics.json                 # カテゴリ別統計
```

---

## 🚀 使用方法

### スクリプト実行

```bash
cd /Users/odasoya/meal_analysis_api_2/web_scraping_2
python3 create_manual_stemmed_correspondence.py
```

### 出力ファイル

実行すると`output/`ディレクトリに以下のファイルが生成されます：

1. **`manual_to_stemmed_correspondence.json`** (844 KB)
   - 対応成功した1,117件の食材マッピング
   - マニュアル食材情報 + Stemmed DB情報の完全なペア

2. **`manual_only_foods.json`** (4 KB)
   - マニュアルテンプレートにのみ存在する13件の食材
   - Stemmed DBに未登録の新規食材

3. **`stemmed_only_foods.json`** (8 KB)
   - Stemmed DBにのみ存在する25件の食材
   - マニュアルテンプレートに未記載の食材

4. **`correspondence_summary.json`** (2.4 KB)
   - 全体統計とカテゴリ別サマリー

5. **`category_statistics.json`** (51 KB)
   - カテゴリごとの詳細統計（対応/未対応食材リスト含む）

---

## 📊 処理結果サマリー

### 全体統計

| 項目 | 数値 | 割合 |
|------|------|------|
| **マニュアルテンプレート総数** | 1,130件 | - |
| **Stemmed DB総数** | 1,142件 | - |
| **対応成功** | 1,117件 | **98.85%** ✅ |
| **マニュアルのみ** | 13件 | 1.15% |
| **Stemmed DBのみ** | 25件 | 2.19% |

### カテゴリ別対応率

#### ✅ 完全対応（100%）カテゴリ（13カテゴリ）

- Grains & Grain Products (89/89)
- Sweets & Sweeteners (50/50)
- Beans & Peas (47/47)
- Cheese (57/57)
- Stocks and Gravy (23/23)
- Fruit - raw or frozen (71/71)
- Poultry (28/28)
- Beverages (67/67)
- Dairy, Dairy Substitutes & Egg (61/61)
- Nuts & Seeds (68/68)
- Meats (56/56)
- Breads & Rolls (38/38)
- Vegetables - canned, dried, or juice (36/36)

#### ⚠️ 一部未対応カテゴリ（6カテゴリ）

| カテゴリ | 総数 | 対応 | 未対応 | 対応率 |
|----------|------|------|--------|--------|
| Fish & Seafood | 75 | 74 | 1 | 98.7% |
| Vegetables - raw, frozen, or cooked | 159 | 158 | 1 | 99.4% |
| Condiments, Dressings & Sauces | 73 | 69 | 4 | 94.5% |
| Fats & Oils | 21 | 19 | 2 | 90.5% |
| Fruit - canned, dried, or juice | 35 | 32 | 3 | 91.4% |
| Spices & Herbs | 76 | 74 | 2 | 97.4% |

---

## 📝 マニュアルのみに存在する食材（13件）

Stemmed DBに未登録の新規食材リスト：

| # | 食材名 | カテゴリ | カロリー |
|---|--------|----------|----------|
| 1 | Sardines canned in water drained, can | Fish & Seafood | 164cals |
| 2 | Roasted asparagus, serving | Vegetables | 20cals |
| 3 | Allulose granular, tsp | Condiments | 0cals |
| 4 | Allulose liquid, tbsp | Condiments | 0cals |
| 5 | Applesauce unsweetened, cup | Condiments | 102cals |
| 6 | Hot sauce, tsp | Condiments | 6cals |
| 7 | Sunflower oil high oleic content over 70%, tbsp | Fats & Oils | 124cals |
| 8 | Vegetable cooking spray oil, sprays | Fats & Oils | 2cals |
| 9 | Cranberry juice cocktail, cup | Fruit juice | 141cals |
| 10 | Cranberry juice unsweetened, cup | Fruit juice | 61cals |
| 11 | Lime juice canned or bottled unsweetened, cup | Fruit juice | 52cals |
| 12 | Italian seasoning dried, tsp | Spices & Herbs | 0cals |
| 13 | Sea salt non-iodized, tsp | Spices & Herbs | 0cals |

**推奨アクション**: これらの食材をStemmed DBに追加することで、カバレッジを向上

---

## 🗂️ Stemmed DBのみに存在する食材（25件）

マニュアルテンプレートに未記載の食材（一部抜粋）：

| # | ID | 食材名 | カテゴリ推定 |
|---|----|--------|--------------|
| 1 | 10000000638 | Beef brisket flat cut trimmed to 1/8" fat raw | Meats |
| 2 | 10000000356 | Lard or pig fat | Fats & Oils |
| 3 | 10000000697 | Almond butter without salt | Nuts & Seeds |
| 4 | 10000000023 | Kidney beans raw | Beans & Peas |
| 5 | 10000000732 | Peanut butter chunky without salt | Nuts & Seeds |
| 6 | 10000000731 | Peanut butter chunky with salt | Nuts & Seeds |
| 7 | 10000000289 | Butter whipped salted | Dairy |
| 8 | 10000000733 | Peanut butter smooth with salt | Nuts & Seeds |
| 9 | 10000000349 | Chicken fat | Fats & Oils |
| 10 | 10000000352 | Cod liver fish oil | Fats & Oils |

**特徴**: 主に塩分有無やカット方法などの詳細バリエーション

---

## 🔄 データソース

### 入力データ

1. **Manual Input Templates**
   - パス: `web_scraping_2/manual_input_templates/`
   - 形式: カテゴリ別テキストファイル（19ファイル）
   - 総食材数: 1,130件

2. **Stemmed DB**
   - パス: `db/mynetdiary_converted_tool_calls_list_stemmed.json`
   - 形式: JSON配列
   - 総食材数: 1,142件

3. **既存マッピング**
   - パス: `web_scraping/processed_data/complete_mapping_with_14_foods.json`
   - 形式: JSON
   - マッピング数: 1,139件

### 対応ロジック

1. マニュアルテンプレートから食材名とカロリーを抽出
2. `final_food_name`形式（`食材名, unit\nカロリー`）で正規化
3. 既存マッピングJSONを利用して対応付け
4. 対応成功/失敗を分類

---

## 📐 データ構造

### manual_to_stemmed_correspondence.json

```json
{
  "metadata": {
    "timestamp": "2025-10-09T17:58:35.643378",
    "total_correspondences": 1117
  },
  "correspondences": [
    {
      "manual_food": {
        "food_name": "Arrowroot flour, cup",
        "category": "Grains & Grain Products",
        "calories": "457cals",
        "final_food_name": "Arrowroot flour, cup\n457cals",
        "source_file": "grains_and_grain_products_manual_input.txt"
      },
      "stemmed_food": {
        "id": "10000000549",
        "original_name": "Arrowroot flour",
        "search_name": "Arrowroot flour",
        "description": "None",
        "nutrition": {
          "calories": 357.03125,
          "protein": 0.0,
          "fat": 0.078125,
          "carbs": 88.28125
        }
      },
      "mapping_info": {
        "final_food_id": "food_0001",
        "sequence": 1
      }
    }
  ]
}
```

### manual_only_foods.json

```json
{
  "metadata": {
    "timestamp": "2025-10-09T17:58:35.643378",
    "total_foods": 13,
    "description": "マニュアルテンプレートにのみ存在する食材（Stemmed DBに未登録）"
  },
  "foods": [
    {
      "sequence": 55,
      "category": "Fish & Seafood",
      "food_name": "Sardines canned in water drained, can",
      "calories": "164cals",
      "final_food_name": "Sardines canned in water drained, can\n164cals",
      "source_file": "fish_and_seafood_manual_input.txt"
    }
  ]
}
```

### stemmed_only_foods.json

```json
{
  "metadata": {
    "timestamp": "2025-10-09T17:58:35.643378",
    "total_foods": 25,
    "description": "Stemmed DBにのみ存在する食材（マニュアルテンプレートに未登録）"
  },
  "foods": [
    {
      "id": "10000000638",
      "original_name": "Beef brisket flat cut trimmed to 1/8\" fat raw",
      "search_name": "Beef brisket",
      "description": "flat cut, trimmed to 1/8\" fat, raw",
      "nutrition": {
        "calories": 276.99,
        "protein": 17.92,
        "fat": 22.19,
        "carbs": 0.0
      }
    }
  ]
}
```

---

## 🎯 活用例

### Python で対応表を読み込み

```python
import json

# 対応表読み込み
with open('output/manual_to_stemmed_correspondence.json', 'r', encoding='utf-8') as f:
    correspondence = json.load(f)

# 対応成功した食材を走査
for corr in correspondence['correspondences']:
    manual_name = corr['manual_food']['food_name']
    stemmed_name = corr['stemmed_food']['original_name']
    stemmed_id = corr['stemmed_food']['id']

    print(f"{manual_name} -> [{stemmed_id}] {stemmed_name}")
```

### マニュアルのみの食材を確認

```python
import json

with open('output/manual_only_foods.json', 'r', encoding='utf-8') as f:
    manual_only = json.load(f)

print(f"Stemmed DBに未登録の食材: {manual_only['metadata']['total_foods']}件")
for food in manual_only['foods']:
    print(f"  - {food['food_name']} ({food['category']})")
```

### カテゴリ別統計を分析

```python
import json

with open('output/category_statistics.json', 'r', encoding='utf-8') as f:
    stats = json.load(f)

for category, data in stats.items():
    match_rate = (data['matched'] / data['total'] * 100) if data['total'] > 0 else 0
    print(f"{category}: {match_rate:.1f}% ({data['matched']}/{data['total']})")
```

---

## ✅ 品質保証

### 検証済み項目

- ✅ 重複マッチングなし（1対1の完全マッピング）
- ✅ 98.85%の高い対応率
- ✅ カテゴリ情報の完全性
- ✅ 栄養情報の整合性
- ✅ 未対応食材の完全リスト化

### データ信頼性

- **データソース**: MyNetDiary公式データ + 手動入力テンプレート
- **処理日時**: 2025年10月9日
- **検証方法**: 既存マッピングJSONとの照合
- **マッピング精度**: 98.85%

---

## 🔧 今後の改善提案

### 1. 未対応食材の追加

**マニュアルのみに存在する13件をStemmed DBに追加:**
- Allulose関連（granular, liquid）
- Applesauce unsweetened
- Hot sauce
- Italian seasoning dried
- など

### 2. Stemmed DB専用食材の検討

**25件の食材を評価:**
- 使用頻度の確認
- マニュアルテンプレートへの追加検討
- 重複バリエーションの整理（塩分有無など）

### 3. 自動更新システム

- 定期的な対応表更新
- 新規食材の自動検出
- 差分レポート生成

---

## 📞 サポート情報

### ファイル配置

```
meal_analysis_api_2/
├── web_scraping_2/                             # このディレクトリ
│   ├── README.md                               # このファイル
│   ├── create_manual_stemmed_correspondence.py
│   ├── manual_input_templates/
│   └── output/
├── web_scraping/
│   └── processed_data/
│       └── complete_mapping_with_14_foods.json # 既存マッピング
└── db/
    └── mynetdiary_converted_tool_calls_list_stemmed.json  # Stemmed DB
```

### トラブルシューティング

**エラー: マニュアルテンプレートが見つかりません**
```bash
# manual_input_templatesディレクトリが存在するか確認
ls -la web_scraping_2/manual_input_templates/
```

**エラー: Stemmed DBが見つかりません**
```bash
# パスを確認
ls -la db/mynetdiary_converted_tool_calls_list_stemmed.json
```

**エラー: 既存マッピングが見つかりません**
```bash
# パスを確認
ls -la web_scraping/processed_data/complete_mapping_with_14_foods.json
```

---

## 🔬 栄養情報統合プロセス（v2.0）

### 概要

Manual Templatesから抽出した栄養情報をStemmed DBに統合するプロセスを実装しました。

### プロセスフロー

```
Manual Templates (1,154件)
    ↓ ① デフォルト情報抽出
all_foods_default_unit_calories.json
    ↓ ② Unit-to-gramsマッピング追加
all_foods_with_unit_grams.json
    ↓ ③ 栄養素情報追加
all_foods_with_nutrition.json (1,152件)
    ↓ ④ マッピングファイル更新
complete_mapping_with_15_additional_foods_updated.json (1,154件)
    ↓ ⑤ Stemmed DBに統合
mynetdiary_converted_tool_calls_list_stemmed_with_nutrition.json (1,157件)
```

### ① デフォルト情報抽出

**スクリプト:** `scripts/extract_all_foods_default_info.py`

Manual Templatesから以下を抽出：
- `food_name`: 食材名
- `default_unit`: デフォルト単位（cup, tbsp, olives等）
- `default_calories`: デフォルトカロリー（小数点対応）
- `title_full_name`: 完全なタイトル名
- `title_calories`: カロリー表記

**特記事項:**
- 小数点カロリー対応: `[\d,.]+cals`パターンで8.75cals等に対応
- 複合食材名の正しい抽出: "Nougat, homemade, piece" → "Nougat homemade"

**出力:** `output/all_foods_default_unit_calories.json` (1,154件)

### ② Unit-to-gramsマッピング追加

**スクリプト:** `scripts/add_unit_to_grams.py`

【Serving情報】セクションから単位→グラム変換を抽出：
```json
"unit_to_grams": {
  "cup": 254.0,
  "gram": 1.0,
  "oz": 28.3,
  "lb": 453.6
}
```

**出力:** `output/all_foods_with_unit_grams.json` (1,154件)

### ③ 栄養素情報追加

**スクリプト:** `scripts/add_nutrition_data.py`

【栄養情報】セクションから栄養素を抽出：
```json
"default_nutrition": {
  "calorie": 239.0,
  "Total_Fat_g": 0.9,
  "Saturated_Fat_g": 0.2,
  "Total_Carbs_g": 54.6,
  "Protein_g": 12.2,
  ...
}
```

**抽出される栄養素（35種類）:**
- Calories（calorie）
- Total Fat, Saturated Fat, Trans Fat, Monounsaturated Fat, Polyunsaturated Fat
- Total Carbs, Net Carbs, Dietary Fiber, Total Sugars, Added Sugars
- Protein, Cholesterol, Sodium
- Vitamins: A, C, D, E, K
- Minerals: Calcium, Iron, Potassium, Magnesium, Zinc, etc.

**栄養情報なし（2件）:**
- Ice cubes（栄養情報が"None"）
- Sea salt non-iodized（栄養情報が"None"）

**出力:** `output/all_foods_with_nutrition.json` (1,152件)

### ④ マッピングファイル更新

**問題:** 手動修正により2件のカロリーがマッピングファイルと不一致
- Mint fresh or raw herb: 3cals → 2cals
- Olives kalamata pitted: 9cals → 8.75cals（4 olives → 1 oliveに修正）

**解決策:** マッピングファイルの`final_food_name`を更新

**更新スクリプト:**
```python
# complete_mapping_with_15_additional_foods.json を複製して更新
mapping['final_food_name'] = 'Mint fresh or raw herb, tbsp\n2cals'
mapping['final_food_name'] = 'Olives kalamata pitted, olives\n8.75cals'
```

**出力:** `web_scraping/processed_data/complete_mapping_with_15_additional_foods_updated.json`

**検証結果:**
- マッピング成功: 1,152件 / 1,152件（100%）
- マッピング失敗: 0件

### ⑤ Stemmed DBに栄養情報統合

**統合スクリプト:**
```python
# マッピングを使用してStemmed DBに情報追加
for stemmed_food in stemmed_db:
    if stemmed_id in mapping:
        stemmed_food['default_unit'] = all_food['default_unit']
        stemmed_food['default_calories'] = all_food['default_calories']
        stemmed_food['unit_to_grams'] = all_food['unit_to_grams']
        stemmed_food['default_nutrition'] = all_food['default_nutrition']
```

**出力:** `db/mynetdiary_converted_tool_calls_list_stemmed_with_nutrition.json`

**統計:**
- 総食材数: 1,157件
- 栄養情報追加成功: 1,152件
- 栄養情報なし: 5件
  - Kidney beans raw（Stemmed-only）
  - Tofu crumbles（Stemmed-only）
  - Ice cubes（栄養情報None）
  - Sea salt non-iodized × 2（栄養情報None + Stemmed-only）

### ⑥ 完全版データベース作成（栄養情報完全な1,152件のみ）

**目的:** 栄養情報が不足している5件を除外し、完全なデータのみを抽出

**処理:**
```python
# default_nutritionがあり、Noneでないものを抽出
complete_foods = [f for f in stemmed_db
                  if 'default_nutrition' in f and f['default_nutrition'] is not None]
```

**出力:** `db/mynetdiary_converted_tool_calls_list_stemmed_with_nutrition_complete.json`

**統計:**
- **栄養情報完全:** 1,152件
- **除外:** 5件

**これが最終的な完成版データベースです！** 🎉

各食材には以下のフィールドが完全に揃っています:
- `id`: 食材ID
- `original_name`: 食材名
- `search_name`: 検索用名前
- `description`: 説明
- `nutrition`: 元のMyNetDiary栄養情報（calories, protein, fat, carbs）
- `default_unit`: デフォルト単位（cup, tbsp, olives等）
- `default_calories`: デフォルトカロリー（小数点対応）
- `unit_to_grams`: 単位→グラム変換マッピング
- `default_nutrition`: 詳細栄養素情報（35種類）

### データ構造

**追加されたフィールド:**

```json
{
  "id": 10000000958,
  "original_name": "Olives kalamata pitted",
  "search_name": "Olives kalamata pitted",
  "description": "None",
  "nutrition": {
    "calories": 35.0,
    "protein": 0.0,
    "fat": 4.0,
    "carbs": 1.0
  },
  "data_type": "unified",
  "source": "MyNetDiary",
  "stemmed_search_name": "oliv kalamata pit",
  "stemmed_description": "none",
  "category": null,

  // ↓↓↓ 新規追加フィールド ↓↓↓
  "default_unit": "olives",
  "default_calories": 8.75,
  "unit_to_grams": {},
  "default_nutrition": {
    "calorie": 8.75,
    "Total_Fat_g": 1.0,
    "Saturated_Fat_g": 0.125,
    "Trans_Fat_g": 0.0,
    "Total_Carbs_g": 0.25,
    "Net_Carbs_g": 0.0,
    "Protein_g": 0.0,
    "Cholesterol_mg": 0.0,
    "Sodium_mg": 62.5,
    ...
  }
}
```

### スクリプト一覧

| スクリプト | 機能 | 入力 | 出力 |
|-----------|------|------|------|
| `scripts/extract_all_foods_default_info.py` | デフォルト情報抽出 | manual_input_templates/*.txt | all_foods_default_unit_calories.json |
| `scripts/add_unit_to_grams.py` | Unit-to-grams追加 | all_foods_default_unit_calories.json | all_foods_with_unit_grams.json |
| `scripts/add_nutrition_data.py` | 栄養素情報追加 | all_foods_with_unit_grams.json | all_foods_with_nutrition.json |
| `scripts/verify_nutrition_values.py` | 栄養素検証 | manual_input_templates/*.txt | NUTRITION_VALUES_VERIFICATION_REPORT.md |
| `scripts/compare_database_and_mappings.py` | DB/マッピング照合 | all_foods_with_nutrition.json + mapping | - |

### 出力ファイル一覧

| ファイル | 説明 | 件数 |
|---------|------|------|
| `output/all_foods_default_unit_calories.json` | デフォルト情報 | 1,154件 |
| `output/all_foods_with_unit_grams.json` | + Unit-to-gramsマッピング | 1,154件 |
| `output/all_foods_with_nutrition.json` | + 栄養素情報 | 1,152件 |
| `web_scraping/processed_data/complete_mapping_with_15_additional_foods_updated.json` | 更新版マッピング | 1,154件 |
| `db/mynetdiary_converted_tool_calls_list_stemmed_with_nutrition.json` | Stemmed DB + 栄養情報 | 1,157件 |
| **`db/mynetdiary_converted_tool_calls_list_stemmed_with_nutrition_complete.json`** | **完全版（最終）** | **1,152件** |

### パイプライン実行方法

```bash
cd /Users/odasoya/meal_analysis_api_2/web_scraping_2

# ① デフォルト情報抽出
python scripts/extract_all_foods_default_info.py

# ② Unit-to-grams追加
python scripts/add_unit_to_grams.py

# ③ 栄養素情報追加
python scripts/add_nutrition_data.py

# ④ 栄養素検証（オプション）
python scripts/verify_nutrition_values.py

# ⑤ マッピングファイル更新（必要に応じて手動）
# complete_mapping_with_15_additional_foods.json を編集

# ⑥ Stemmed DBに統合（Pythonスクリプトで実行）
```

### 重要な修正内容

**1. 小数点カロリー対応**
```python
# 修正前: [\d,]+cals
# 修正後: [\d,.]+cals  # 8.75cals等に対応
```

**2. 複合食材名の正しい抽出**
```python
# "Nougat, homemade, piece" の場合
if ', ' in rest_part:
    rest_parts = rest_part.rsplit(', ', 1)
    food_name_suffix = rest_parts[0]  # "homemade"
    default_unit = rest_parts[1]      # "piece"
    food_name = f"{first_part} {food_name_suffix}"  # "Nougat homemade"
```

**3. Calories_kcal → calorie に変更**
```python
nutrition_dict['calorie'] = value  # キー名を統一
```

### 品質保証

**カロリー一致検証:**
- 全1,152件で `default_calories == calorie` を確認
- 不一致: 0件

**栄養素形式検証:**
- 35種類の栄養素を標準化
- 単位の不一致: 0件

**マッピング検証:**
- 1,152件 / 1,152件（100%）がStemmed DBにマッピング成功

---

## 📝 変更履歴

### v2.0 (2025-10-10)
- ✅ Manual Templatesから栄養情報を抽出（1,152件）
- ✅ Unit-to-gramsマッピング追加
- ✅ 35種類の栄養素を標準化して追加
- ✅ マッピングファイル更新（2件のカロリー修正）
- ✅ Stemmed DBに栄養情報統合（1,157件中1,152件）
- ✅ 100%のマッピング成功率達成
- ✅ **完全版データベース作成（栄養情報完全な1,152件のみ）**
  - ファイル: `db/mynetdiary_converted_tool_calls_list_stemmed_with_nutrition_complete.json`

### v1.0 (2025-10-09)
- 初版リリース
- Manual Templates と Stemmed DB の対応表作成
- 1,117件の対応成功（98.85%）
- 未対応食材リストの生成
- カテゴリ別統計の出力

---

**最終更新:** 2025年10月10日
**データバージョン:** v2.0
**栄養情報統合:** 1,152件 / 1,152件（100%）
**完全版データベース:** `db/mynetdiary_converted_tool_calls_list_stemmed_with_nutrition_complete.json` (1,152件)
**Stemmed DB総数:** 1,157件（完全版: 1,152件）
