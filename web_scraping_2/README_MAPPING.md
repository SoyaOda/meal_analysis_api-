# 🔗 Manual Templates と Stemmed DB の完全マッピングガイド

Manual Input TemplatesとStemmed DBを完全に1:1でマッピングする方法を説明します。

---

## 📊 概要

### マッピング状況

| 項目 | 件数 |
|------|------|
| **Manual Templates** | 1,154件 |
| **Stemmed DB (with manual)** | 1,157件 |
| **完全マッピング** | 1,154件（100%） |
| **Stemmed DBのみ** | 3件（Kidney beans raw, Tofu crumbles, Sea salt non-iodized） |

### ✅ 完全な1:1対応を実現

- **重複なし**: Manual側、Stemmed側ともに完全にユニーク
- **マッピング成功率**: 100%（1,154/1,154）

---

## 📁 必要なファイル

### 1. Stemmed DB（manual版）

```
db/mynetdiary_converted_tool_calls_list_stemmed_with_manual.json
```

- **総件数**: 1,157件
- **内容**: 元のStemmed DB（1,142件）+ manual-only foods（15件）

### 2. マッピングファイル（完全版）

```
web_scraping/processed_data/complete_mapping_with_15_additional_foods.json
```

- **総マッピング数**: 1,154件
- **構成**:
  - 既存マッピング: 1,139件
  - 追加マッピング: 15件（新しく追加したmanual-only foods）

### 3. Manual Input Templates

```
web_scraping_2/manual_input_templates/
```

- **ファイル数**: 19カテゴリ
- **総食材数**: 1,154件

---

## 🚀 使用方法

### 方法1: マッピングスクリプトを使用

更新されたマッピングファイルを使用するスクリプト：

```python
#!/usr/bin/env python3
import json
import re
from pathlib import Path

# パス設定
base_dir = Path('/Users/odasoya/meal_analysis_api_2/web_scraping_2')
manual_templates_dir = base_dir / "manual_input_templates"
stemmed_db_path = base_dir.parent / "db" / "mynetdiary_converted_tool_calls_list_stemmed_with_manual.json"
mapping_path = base_dir.parent / "web_scraping" / "processed_data" / "complete_mapping_with_15_additional_foods.json"

# データ読み込み
with open(stemmed_db_path, 'r', encoding='utf-8') as f:
    stemmed_db = json.load(f)

with open(mapping_path, 'r', encoding='utf-8') as f:
    mapping_data = json.load(f)

# マッピング辞書を作成
mapping_dict = {}
for mapping in mapping_data['mappings']:
    mapping_dict[mapping['final_food_name']] = mapping

# Manual Templatesから食材を抽出
manual_foods = []
for manual_file in manual_templates_dir.glob("*_manual_input.txt"):
    with open(manual_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 食材抽出（カンマ付きカロリー対応）
    pattern = r'\n(\d+)\. (.+?)\n([\d,]+cals)'
    matches = re.findall(pattern, content)

    for sequence, food_name, calories in matches:
        final_food_name = f"{food_name}\n{calories}"
        manual_foods.append({
            'food_name': food_name,
            'final_food_name': final_food_name
        })

# マッピング実行
stemmed_dict = {str(food['id']): food for food in stemmed_db}

for manual_food in manual_foods:
    final_name = manual_food['final_food_name']

    if final_name in mapping_dict:
        mapping = mapping_dict[final_name]
        stemmed_id = mapping['stemmed_id']
        stemmed_food = stemmed_dict.get(stemmed_id)

        print(f"✅ {manual_food['food_name']}")
        print(f"   → Stemmed ID: {stemmed_id}")
        print(f"   → Stemmed Name: {stemmed_food['original_name']}")
    else:
        print(f"❌ {manual_food['food_name']}: マッピングなし")

print(f"\n総マッピング数: {len(manual_foods)}件")
```

### 方法2: 既存スクリプトを更新

`web_scraping_2/create_manual_stemmed_correspondence.py`を以下のように修正：

```python
# main()関数内で、マッピングファイルのパスを変更
def main():
    # ...
    stemmed_db_path = base_dir.parent / "db" / "mynetdiary_converted_tool_calls_list_stemmed_with_manual.json"
    existing_mapping_path = base_dir.parent / "web_scraping" / "processed_data" / "complete_mapping_with_15_additional_foods.json"
    # ...
```

実行：

```bash
cd /Users/odasoya/meal_analysis_api_2/web_scraping_2
python create_manual_stemmed_correspondence.py
```

**期待される結果**:
```
✅ 対応成功: 1154件 (100.00%)
⚠️  マニュアルのみ: 0件
⚠️  Stemmed DBのみ: 3件
```

---

## 📋 マッピングデータ構造

### マッピングファイルの構造

```json
{
  "total_mappings": 1154,
  "timestamp": "2025-10-09T...",
  "description": "Complete mapping with 15 additional manual foods",
  "statistics": {
    "total_stemmed_foods": 1157,
    "total_final_foods": 1154,
    "mapping_success_rate": "100.00%",
    "original_mappings": 1139,
    "added_mappings": 15
  },
  "unmapped_foods": [],
  "mappings": [
    {
      "stemmed_id": "10000000001",
      "stemmed_name": "Food Name",
      "final_food_id": "food_0001",
      "final_food_name": "Food Name, unit\n123cals",
      "sequence": 1,
      "category": "Category Name"
    },
    // ... 1154 mappings
  ]
}
```

### Stemmed DBの構造

```json
[
  {
    "id": 10000000001,
    "original_name": "Food Name",
    "search_name": "Search Name",
    "description": "description",
    "nutrition": {
      "calories": 123.0,
      "protein": 10.0,
      "fat": 5.0,
      "carbs": 15.0
    },
    "data_type": "unified",
    "source": "MyNetDiary",
    "stemmed_search_name": "stemmed search",
    "stemmed_description": "stemmed desc",
    "category": "Category Name"
  },
  // ... 1157 foods
]
```

---

## 🔍 マッピング確認方法

### 1. 全体統計の確認

```python
import json

with open('web_scraping/processed_data/complete_mapping_with_15_additional_foods.json') as f:
    data = json.load(f)

print(f"総マッピング数: {data['total_mappings']}")
print(f"マッピング成功率: {data['statistics']['mapping_success_rate']}")
print(f"未マッピング: {len(data['unmapped_foods'])}件")
```

### 2. 1:1対応の検証

```python
from collections import Counter

# 重複チェック
stemmed_ids = [m['stemmed_id'] for m in data['mappings']]
final_names = [m['final_food_name'] for m in data['mappings']]

stemmed_counter = Counter(stemmed_ids)
final_counter = Counter(final_names)

stemmed_dupes = {id: c for id, c in stemmed_counter.items() if c > 1}
final_dupes = {name: c for name, c in final_counter.items() if c > 1}

if not stemmed_dupes and not final_dupes:
    print("✅ 完全な1:1対応です")
else:
    print(f"⚠️ Stemmed側重複: {len(stemmed_dupes)}件")
    print(f"⚠️ Final側重複: {len(final_dupes)}件")
```

### 3. 特定の食材を検索

```python
# Manual名からStemmed食材を検索
def find_mapping(manual_food_name, mappings):
    for m in mappings:
        if manual_food_name in m['final_food_name']:
            return m
    return None

# 使用例
mapping = find_mapping("Lard or pig fat", data['mappings'])
if mapping:
    print(f"Stemmed ID: {mapping['stemmed_id']}")
    print(f"Stemmed Name: {mapping['stemmed_name']}")
    print(f"Category: {mapping['category']}")
```

---

## 📊 追加された15件の詳細

以下の15件が新たにマッピングファイルに追加されました：

| # | 食材名 | Stemmed ID | Category |
|---|--------|-----------|----------|
| 1 | Turkey breast meat only raw, breast | 10000001155 | Poultry |
| 2 | Sardines canned in water drained, can | 10000001142 | Fish & Seafood |
| 3 | Roasted asparagus, serving | 10000001143 | Vegetables |
| 4 | Allulose granular, tsp | 10000001144 | Condiments |
| 5 | Allulose liquid, tbsp | 10000001145 | Condiments |
| 6 | Applesauce unsweetened, cup | 10000001146 | Condiments |
| 7 | Hot sauce, tsp | 10000001147 | Condiments |
| 8 | Safflower oil high linoleic content over 70%, cup | 10000001156 | Fats & Oils |
| 9 | Sunflower oil high oleic content over 70%, tbsp | 10000001148 | Fats & Oils |
| 10 | Vegetable cooking spray oil, sprays | 10000001149 | Fats & Oils |
| 11 | Cranberry juice cocktail, cup | 10000001150 | Fruit |
| 12 | Cranberry juice unsweetened, cup | 10000001151 | Fruit |
| 13 | Lime juice canned or bottled unsweetened, cup | 10000001152 | Fruit |
| 14 | Italian seasoning dried, tsp | 10000001153 | Spices & Herbs |
| 15 | Sea salt non-iodized, tsp | 10000001154 | Spices & Herbs |

---

## ⚙️ 重要な修正内容

### 1. 正規表現パターンの修正

カンマ付きカロリー（1,849cals）に対応：

```python
# 修正前
pattern = r'\n(\d+)\. (.+?)\n(\d+cals)'

# 修正後
pattern = r'\n(\d+)\. (.+?)\n([\d,]+cals)'  # [\d,]+ でカンマを含む数字にマッチ
```

### 2. マッピングファイルの拡張

既存の`complete_mapping_with_14_foods.json`（1,139件）に15件を追加：

- Sequence: 1189-1203
- Final Food ID: food_1189 - food_1203
- 合計: 1,154件（100%マッピング）

---

## 🔗 関連ファイル

### 入力ファイル

- `web_scraping_2/manual_input_templates/*.txt` - 19カテゴリのマニュアルテンプレート
- `db/mynetdiary_converted_tool_calls_list_stemmed_with_manual.json` - 拡張版Stemmed DB
- `web_scraping/processed_data/complete_mapping_with_15_additional_foods.json` - 完全版マッピングファイル

### 出力ファイル（create_manual_stemmed_correspondence.py実行時）

- `web_scraping_2/output/manual_to_stemmed_correspondence.json` - 対応表
- `web_scraping_2/output/manual_only_foods.json` - マニュアルのみ（0件になるはず）
- `web_scraping_2/output/stemmed_only_foods.json` - Stemmedのみ（3件）
- `web_scraping_2/output/correspondence_summary.json` - サマリー統計
- `web_scraping_2/output/category_statistics.json` - カテゴリ別統計

### スクリプト

- `web_scraping_2/create_manual_stemmed_correspondence.py` - メインマッピングスクリプト
- `web_scraping_2/collect_stemmed_only_nutrition.py` - Stemmed-only foods栄養情報収集

### レポート

- `web_scraping_2/ADDED_FOODS_REPORT.md` - 追加食材レポート
- `web_scraping_2/STEMMED_ONLY_FOODS_NUTRITION_REPORT.md` - Stemmed-only foods栄養レポート
- `web_scraping_2/README_MAPPING.md` - このファイル

---

## ✅ 検証チェックリスト

完全マッピングを確認するためのチェックリスト：

- [ ] Stemmed DB（manual版）を使用: `mynetdiary_converted_tool_calls_list_stemmed_with_manual.json` (1,157件)
- [ ] 新しいマッピングファイルを使用: `complete_mapping_with_15_additional_foods.json` (1,154件)
- [ ] 正規表現パターンがカンマ付きカロリーに対応: `[\d,]+cals`
- [ ] 対応成功率が100%: 1,154/1,154
- [ ] Manual-only foodsが0件
- [ ] Stemmed-only foodsが3件（Kidney beans raw, Tofu crumbles, Sea salt non-iodized）
- [ ] 1:1対応が完全（重複なし）

---

## 🎯 使用例

### 例1: 特定の食材のマッピング情報を取得

```python
import json

# データ読み込み
with open('web_scraping/processed_data/complete_mapping_with_15_additional_foods.json') as f:
    mapping_data = json.load(f)

with open('db/mynetdiary_converted_tool_calls_list_stemmed_with_manual.json') as f:
    stemmed_db = json.load(f)

# マッピング辞書とStemmed辞書を作成
mapping_dict = {m['final_food_name']: m for m in mapping_data['mappings']}
stemmed_dict = {str(f['id']): f for f in stemmed_db}

# 特定の食材を検索
food_to_find = "Lard or pig fat, cup\n1,849cals"

if food_to_find in mapping_dict:
    mapping = mapping_dict[food_to_find]
    stemmed_id = mapping['stemmed_id']
    stemmed_food = stemmed_dict[stemmed_id]

    print(f"Manual Food: {food_to_find}")
    print(f"Stemmed ID: {stemmed_id}")
    print(f"Stemmed Name: {stemmed_food['original_name']}")
    print(f"Category: {mapping['category']}")
    print(f"Nutrition: {stemmed_food.get('nutrition')}")
```

### 例2: カテゴリ別にマッピング数を集計

```python
from collections import defaultdict

category_counts = defaultdict(int)

for mapping in mapping_data['mappings']:
    category_counts[mapping['category']] += 1

print("カテゴリ別マッピング数:")
for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {category}: {count}件")
```

---

## 📞 トラブルシューティング

### Q1: マッピング成功率が100%にならない

**A**: 以下を確認してください：
1. Stemmed DBが`mynetdiary_converted_tool_calls_list_stemmed_with_manual.json`（1,157件）であることを確認
2. マッピングファイルが`complete_mapping_with_15_additional_foods.json`（1,154件）であることを確認
3. 正規表現パターンが`[\d,]+cals`であることを確認（カンマ対応）

### Q2: 重複が見つかる

**A**: マッピングファイルの内容を確認：
```python
from collections import Counter

stemmed_ids = [m['stemmed_id'] for m in mapping_data['mappings']]
duplicates = {id: c for id, c in Counter(stemmed_ids).items() if c > 1}

if duplicates:
    print(f"重複ID: {duplicates}")
```

### Q3: Stemmed-only foodsが3件より多い

**A**: Stemmed DBとマッピングファイルのバージョンを確認：
- Stemmed DB: 1,157件（manual版）
- マッピング: 1,154件
- Stemmed-only: 3件（Kidney beans raw, Tofu crumbles, Sea salt non-iodized）

---

**作成日**: 2025-10-09
**バージョン**: v1.0
**総マッピング数**: 1,154件（100%）
**1:1対応**: 完全
