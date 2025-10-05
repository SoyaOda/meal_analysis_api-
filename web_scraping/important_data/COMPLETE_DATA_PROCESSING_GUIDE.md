# 完全食材データベース - データ処理ガイド

最終更新: 2025-10-05
データバージョン: v2.0

---

## 📊 最終成果物

### 主要ファイル

1. **`complete_food_database.json`** (2.75 MB) 【最終版・推奨】
   - **1,152食材**の完全データベース
   - Nutrition情報 + Serving変換情報の両方完備
   - 重複除外済み

2. **`complete_nutrition_1185_foods.json`** (1.18 MB)
   - 1,185食材の栄養情報
   - 20種類の栄養素を網羅
   - 重複33件含む

3. **`serving_conversions_1188_foods.json`** (1.46 MB)
   - 1,188食材のServing変換情報
   - 397種類のunit変換データ

4. **`complete_scraping_data_1188_foods_final.json`** (68 MB)
   - 元の生データ（参照用）

---

## 🔄 データ処理フロー全体

### Phase 1: 初期スクレイピング

```
元データ収集
├─ comprehensive_food_collection_all_20251001_124446.json (1,588食材)
└─ フィルタリング（navigation_success=true AND data_collection_success=true）
   └─ complete_scraping_data_1188_foods.json (1,188食材)
```

### Phase 2: 品質検証と再収集

**問題発見:**
- 63食材で'Select Serving'データ不在
- 原因: `PlaywrightFoodDataCollector._extract_serving_options`の抽出条件バグ

**再収集:**
```
retry_select_serving_foods.py
├─ 63食材を再スクレイピング
├─ 成功: 63/63食材
└─ 結果: retry_select_serving_results.json
```

**データ統合:**
```
merge_retry_results.py
├─ 再収集データを統合
├─ 49食材を更新（重複除く）
└─ complete_scraping_data_1188_foods_final.json
```

### Phase 3: Nutrition情報抽出

```
extract_complete_nutrition_data.py
├─ 元データ: complete_scraping_data_1188_foods_final.json (1,188食材)
├─ 自動抽出: 1,141食材
├─ マニュアル補完: 44食材（nutrition_failure_foods.txt）
├─ 抽出成功: 1,185食材（重複33件含む）
├─ 抽出失敗: 3食材
│   ├─ Olives kalamata pitted
│   └─ Sea salt non-iodized (×2 重複)
└─ 出力: complete_nutrition_1185_foods.json
```

**重複詳細:**
- 28種類の食材が重複（33レコード）
- 例: Cornstarch (×3), Baker's yeast (×3), Cardamom (×3)

### Phase 4: Serving変換情報抽出

```
extract_serving_conversions.py
├─ 元データ: complete_scraping_data_1188_foods_final.json (1,188食材)
├─ 自動抽出: 1,174食材
├─ マニュアル補完: 14食材（serving_conversion_failure_foods.txt）
├─ 抽出成功: 1,188食材（全成功）
└─ 出力: serving_conversions_1188_foods.json
```

**マニュアル補完:**
- 6種類の食材（14レコード、重複含む）
- Baker's yeast compressed, Cardamom, Sea bass, Jellies, Walnuts (×2)

### Phase 5: 最終統合

```
create_complete_food_database.py
├─ Nutrition: 1,185食材（重複33件含む） → ユニーク: 1,152食材
├─ Serving: 1,188食材 → ユニーク: 1,154食材
├─ 統合（両方あり）: 1,152食材
├─ 除外（Servingのみ）: 2食材
│   ├─ Olives kalamata pitted（Nutrition抽出失敗）
│   └─ Sea salt non-iodized（Nutrition抽出失敗）
└─ 出力: complete_food_database.json
```

**重複自動除外:**
- 食材名をキーとした辞書で統合 → 重複自動除外
- 1,185レコード → 1,152ユニーク食材

---

## 📈 データ品質指標

### 最終データベース（complete_food_database.json）

- **総食材数:** 1,152食材（重複除外済み）
- **Nutrition情報完備率:** 100%
- **Serving変換情報完備率:** 100%
- **除外食材:** 2食材（0.17%）

### データソース内訳

**Nutrition情報:**
- 自動抽出: 1,109食材 (96.3%)
- マニュアル補完: 43食材 (3.7%)

**Serving変換情報:**
- 自動抽出: 1,146食材 (99.5%)
- マニュアル補完: 6食材 (0.5%)

### 栄養素カバレッジ（20種類）

| # | 栄養素 | カバレッジ | 単位 |
|---|--------|-----------|------|
| 1 | Total Fat | 1,152/1,152 (100.0%) | g |
| 2 | Total Carbs | 1,152/1,152 (100.0%) | g |
| 3 | Net Carbs | 1,152/1,152 (100.0%) | g |
| 4 | Protein | 1,152/1,152 (100.0%) | g |
| 5 | Dietary Fiber | 1,145/1,152 (99.4%) | g |
| 6 | Saturated Fat | 1,139/1,152 (98.9%) | g |
| 7 | Cholesterol | 1,137/1,152 (98.7%) | mg |
| 8 | Added Sugars | 1,130/1,152 (98.1%) | g |
| 9 | Iron | 1,126/1,152 (97.7%) | mg |
| 10 | Calcium | 1,122/1,152 (97.4%) | mg |
| 11 | Total Sugars | 1,108/1,152 (96.2%) | g |
| 12 | Caffeine | 1,098/1,152 (95.3%) | mg |
| 13 | Vitamin A | 1,091/1,152 (94.7%) | mcg |
| 14 | Vitamin C | 1,088/1,152 (94.4%) | mg |
| 15 | Monounsaturated Fat | 1,076/1,152 (93.4%) | g |
| 16 | Polyunsaturated Fat | 1,076/1,152 (93.4%) | g |
| 17 | Sodium | 1,051/1,152 (91.2%) | mg |
| 18 | Alcohol | 1,039/1,152 (90.2%) | g |
| 19 | Trans Fat | 1,023/1,152 (88.8%) | g |
| 20 | Potassium | 998/1,152 (86.6%) | mg |

**統計:**
- 平均栄養素数/食材: 19.1種類
- 最小カバレッジ: Potassium 86.6%
- 最大カバレッジ: 必須4栄養素 100%

### Serving変換統計

- **Unit種類:** 396種類
- **平均変換数:** 6.9種類/食材
- **変換数の分布:**
  - 3種類: 35食材
  - 4種類: 225食材
  - 5種類: 163食材
  - 8種類: 450食材（最多）

---

## 📋 データ構造

### complete_food_database.json

```json
{
  "database_summary": {
    "timestamp": "2025-10-05T...",
    "total_foods": 1152,
    "data_quality": {
      "complete_foods": 1152,
      "nutrition_only": 0,
      "serving_only": 2
    },
    "data_sources": {
      "nutrition": {"auto": 1109, "manual": 43},
      "serving_conversions": {"auto": 1146, "manual": 6}
    },
    "statistics": {
      "total_nutrients_found": 20,
      "avg_nutrients_per_food": 19.1,
      "total_units_found": 396,
      "avg_conversions_per_food": 6.9
    }
  },
  "foods": [
    {
      "sequence": 1,
      "food_name": "Arrowroot flour, cup\n457cals",
      "catalog_category": "Grains & Grain Products",

      "serving_info": {
        "unit": "cup",
        "grams_per_unit": 128.0,
        "calories_per_unit": 457.0,
        "source": "auto"
      },

      "nutrition": {
        "essential_nutrients": {
          "calories": 457.0,
          "total_fat": 0.1,
          "total_carbs": 113.0,
          "protein": 0.0
        },
        "all_nutrients": {
          "total_fat": 0.1,
          "saturated_fat": 0.0,
          "dietary_fiber": 4.0,
          "sodium": 3.0,
          ...
        },
        "total_nutrients_found": 20
      },

      "serving_conversions": {
        "base_unit": "cup",
        "conversions": [
          {"unit": "tablespoon", "calories": 29.0, "grams": 8.0},
          {"unit": "teaspoon", "calories": 10.0, "grams": 2.7},
          {"unit": "gram", "calories": 4.0, "grams": 1.0},
          {"unit": "cup", "calories": 457.0, "grams": 128.0},
          ...
        ],
        "total_conversions": 8,
        "source": "auto"
      },

      "data_sources": {
        "nutrition_source": "auto",
        "serving_conversion_source": "auto"
      }
    }
  ],
  "excluded_foods": {
    "nutrition_only": [],
    "serving_only": [
      {
        "sequence": 378,
        "food_name": "Olives kalamata pitted, olives\n9cals",
        "catalog_category": "Vegetables - canned, dried, or juice",
        "reason": "No nutrition data available (failed nutrition extraction)",
        "has_nutrition": false,
        "has_serving_conversion": true,
        "serving_conversion_info": {...}
      },
      {
        "sequence": 1184,
        "food_name": "Sea salt non-iodized, tsp\n0cals",
        "catalog_category": "Spices & Herbs",
        "reason": "No nutrition data available (failed nutrition extraction)",
        "has_nutrition": false,
        "has_serving_conversion": true,
        "serving_conversion_info": {...}
      }
    ],
    "total_excluded": 2
  }
}
```

---

## 🔧 使用方法

### Python で完全データベースを使用

```python
import json
from pathlib import Path

# 完全データベース読み込み
with open('important_data/complete_food_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

# サマリー情報
summary = db['database_summary']
print(f"総食材数: {summary['total_foods']}")
print(f"除外食材: {summary['data_quality']['serving_only']}")

# 各食材の情報にアクセス
for food in db['foods']:
    food_name = food['food_name']

    # Serving情報
    serving = food['serving_info']
    print(f"\n{food_name}")
    print(f"  1 {serving['unit']} = {serving['grams_per_unit']}g ({serving['calories_per_unit']} kcal)")

    # 必須栄養素
    nutrients = food['nutrition']['essential_nutrients']
    print(f"  Fat: {nutrients['total_fat']}g, Carbs: {nutrients['total_carbs']}g, Protein: {nutrients['protein']}g")

    # Serving変換（最初の3つ）
    conversions = food['serving_conversions']['conversions'][:3]
    print(f"  変換: {', '.join([f'{c['unit']}={c['grams']}g' for c in conversions])}")
```

### カテゴリ別分析

```python
from collections import defaultdict

categories = defaultdict(list)
for food in db['foods']:
    categories[food['catalog_category']].append(food)

# カテゴリ別統計
for category, foods in sorted(categories.items()):
    avg_nutrients = sum(f['nutrition']['total_nutrients_found'] for f in foods) / len(foods)
    avg_conversions = sum(f['serving_conversions']['total_conversions'] for f in foods) / len(foods)
    print(f"{category}: {len(foods)}食材")
    print(f"  平均栄養素数: {avg_nutrients:.1f}")
    print(f"  平均変換数: {avg_conversions:.1f}")
```

### 特定条件でフィルタリング

```python
# 高タンパク質食材（20g以上）
high_protein = [
    food for food in db['foods']
    if food['nutrition']['essential_nutrients']['protein'] >= 20
]

# 低カロリー食材（100kcal未満）
low_cal = [
    food for food in db['foods']
    if food['serving_info']['calories_per_unit'] < 100
]

# 特定unitを持つ食材
cup_foods = [
    food for food in db['foods']
    if any(c['unit'] == 'cup' for c in food['serving_conversions']['conversions'])
]
```

---

## 🐛 発見された問題と解決

### 問題1: 'Select Serving'抽出漏れ（63食材）

**根本原因:**
`playwright_food_data_collector.py`の`_extract_serving_options`メソッド

```python
# 抽出条件が不十分（修正前）
is_complete_serving = has_unit and has_cals and has_grams and has_number
is_unit_only = has_unit and len(text) < 20 and not has_cals

if is_complete_serving or is_unit_only:
    all_serving_texts.append(text)
```

**問題点:**
- "Select Serving"は`has_unit=True`だが、`has_cals=False`のため除外
- `is_unit_only`条件でも漏れる可能性

**解決策（推奨）:**
```python
# "Select Serving"を明示的に含める
is_select_serving = 'select' in text_lower and 'serving' in text_lower
is_complete_serving = has_unit and has_cals and has_grams and has_number
is_unit_only = has_unit and len(text) < 20 and not has_cals

if is_complete_serving or is_unit_only or is_select_serving:
    all_serving_texts.append(text)
```

**実施した対処:**
- 63食材を手動で再スクレイピング
- データ統合により問題解決

### 問題2: 重複データ（33レコード）

**詳細:**
- 28種類の食材が重複
- Cornstarch, Baker's yeast (×3)
- Salt, Sea salt, Za'atar (×2)
- 合計33の余分なレコード

**解決:**
- 統合時に食材名をキーとした辞書使用
- 自動的に重複除外
- 1,185レコード → 1,152ユニーク食材

### 問題3: マニュアルデータ管理

**課題:**
- 自動抽出失敗時の手動補完が必要
- Nutrition: 43食材
- Serving変換: 6食材

**実装:**
```python
# ManualServingDataLoader - nutrition_failure_foods.txt
class ManualServingDataLoader:
    def get_serving_info(self, food_name: str) -> dict:
        # マニュアルデータから取得

# ManualServingConversionLoader - serving_conversion_failure_foods.txt
class ManualServingConversionLoader:
    def get_conversion_info(self, food_name: str) -> list:
        # マニュアル変換データから取得
```

---

## 📁 重要ファイル一覧

### 最終データファイル

1. **`complete_food_database.json`** (2.75 MB) ⭐推奨
   - 完全データベース（1,152食材）

2. **`complete_nutrition_1185_foods.json`** (1.18 MB)
   - 栄養情報のみ

3. **`serving_conversions_1188_foods.json`** (1.46 MB)
   - Serving変換情報のみ

4. **`complete_scraping_data_1188_foods_final.json`** (68 MB)
   - 元データ（参照用）

### マニュアルデータ

- **`nutrition_failure_foods.txt`**
  - 43食材のマニュアルServing情報

- **`serving_conversion_failure_foods.txt`**
  - 6食材のマニュアルServing変換情報

### 補助ファイル

- **`retry_select_serving_results.json`**
  - 63食材の再収集結果

- **`retry_select_serving_log.txt`**
  - 再収集実行ログ

### 処理スクリプト

#### データ抽出
- `scripts/extract_complete_nutrition_data.py` - Nutrition情報抽出
- `scripts/extract_serving_conversions.py` - Serving変換抽出
- `scripts/create_complete_food_database.py` - 最終統合

#### 検証スクリプト
- `scripts/verify_select_serving.py` - 'Select Serving'確認
- `scripts/verify_essential_nutrients.py` - 必須栄養素検証
- `scripts/final_verification.py` - 最終検証

#### 再収集
- `scripts/retry_select_serving_foods.py` - 63食材再スクレイピング
- `scripts/merge_retry_results.py` - データ統合

#### コアコンポーネント
- `scripts/src/nutrition_facts_extractor.py`
  - NutritionFactsExtractor: Serving Size抽出
  - NutrientExtractor: 20栄養素抽出

- `scripts/src/manual_serving_data_loader.py`
  - ManualServingDataLoader: マニュアルServing情報
  - ManualServingConversionLoader: マニュアル変換情報

---

## ✅ データ品質保証

### 検証済み項目

- ✅ 全1,152食材でServing Size情報完備
- ✅ 全1,152食材で必須4栄養素完備
- ✅ 平均19.1種類/食材の栄養素データ
- ✅ 平均6.9種類/食材のServing変換データ
- ✅ 最低86.6%のカバレッジ（Potassium）
- ✅ 重複データ自動除外
- ✅ マニュアル補完システム完備

### 信頼性

- **データソース:** MyNetDiary公式サイト
- **スクレイピング期間:** 2025年10月
- **検証回数:** 5回（元データ、再収集、Nutrition、Serving、最終統合）
- **自動抽出率:** 96%以上
- **マニュアル補完率:** 4%以下

---

## 🎯 用途

このデータベースは以下の用途に最適:

1. **栄養分析アプリケーション**
   - 食事記録の栄養計算
   - カロリー・マクロ栄養素トラッキング
   - Unit変換機能

2. **レシピ分析**
   - 料理の栄養価計算
   - 栄養バランス評価
   - 材料の単位変換

3. **食事プランニング**
   - 栄養目標に基づく食材選択
   - マクロ栄養素バランス調整
   - カロリー計算

4. **機械学習**
   - 食材推奨システム
   - 栄養価予測モデル
   - レシピ生成

5. **データ分析**
   - 栄養素間の相関分析
   - カテゴリ別栄養特性分析
   - Unit使用傾向分析

---

## 📊 カテゴリ分布

19種類のカテゴリに分類:

- Grains & Grain Products
- Meats
- Vegetables
- Dairy & Eggs
- Fruits
- Fats & Oils
- Beans, Nuts & Seeds
- Condiments & Spices
- Beverages
- Fish & Seafood
- Baked Goods
- Sweets & Snacks
- その他

---

## ⚠️ 注意事項と制限

### 除外された食材（2個、0.17%）

1. **Olives kalamata pitted, olives 9cals**
   - カテゴリ: Vegetables - canned, dried, or juice
   - 理由: Nutrition抽出失敗（Serving情報なし）
   - Serving変換データ: あり

2. **Sea salt non-iodized, tsp 0cals**
   - カテゴリ: Spices & Herbs
   - 理由: Nutrition抽出失敗（Serving情報なし）
   - Serving変換データ: あり

### データ制限

- 一部食材で特定栄養素が欠損（最低86.6%カバレッジ）
- ビタミン類はA、Cのみ（B群等は未収集）
- ミネラル類は主要なもののみ（Calcium, Iron, Sodium, Potassium）
- アレルゲン情報は含まれない
- 原材料情報は限定的

---

## 🔧 今後の改善提案

### 1. コード修正

`playwright_food_data_collector.py`の抽出条件を修正:
```python
# "Select Serving"を確実に取得
is_select_serving = 'select' in text_lower and 'serving' in text_lower
```

### 2. データクリーニング

- ✅ 重複エントリ除外済み（統合時に自動処理）
- 0カロリー食材の適切な処理検討
- カテゴリの標準化

### 3. 自動化

- 定期的なデータ更新フロー構築
- 'Select Serving'存在チェック自動実行
- 失敗時の自動リトライ機能
- マニュアルデータの自動統合

### 4. データ拡張

- ビタミンB群の追加
- 微量ミネラルの追加
- アレルゲン情報
- GI値データ

---

## 📝 バージョン履歴

### v2.0 (2025-10-05) - 完全データベース版
- 完全データベース作成（1,152食材）
- Nutrition + Serving変換統合
- 重複自動除外
- 除外食材詳細情報追加

### v1.1 (2025-10-05) - Serving変換追加
- Serving変換情報抽出（1,188食材）
- マニュアル補完（6食材）
- 397種類のunit対応

### v1.0 (2025-10-05) - Nutrition抽出版
- Nutrition情報抽出（1,185食材）
- 20種類の栄養素対応
- マニュアル補完（43食材）

### v0.9 (2025-10-05) - 再収集版
- 'Select Serving'再収集（63食材）
- データ統合
- 最終検証

### v0.1 (2025-10-01) - 初期版
- 初期スクレイピング（1,188食材）

---

## 📞 サポート情報

### データに関する問い合わせ

- データ品質に関する質問
- 使用方法のサポート
- バグ報告

### ファイル構成

```
web_scraping/
├── important_data/
│   ├── complete_food_database.json          # 最終版（推奨）
│   ├── complete_nutrition_1185_foods.json   # Nutritionのみ
│   ├── serving_conversions_1188_foods.json  # Serving変換のみ
│   ├── complete_scraping_data_1188_foods_final.json  # 元データ
│   ├── nutrition_failure_foods.txt          # マニュアルNutrition
│   ├── serving_conversion_failure_foods.txt # マニュアルServing変換
│   └── COMPLETE_DATA_PROCESSING_GUIDE.md    # このファイル
│
└── scripts/
    ├── extract_complete_nutrition_data.py
    ├── extract_serving_conversions.py
    ├── create_complete_food_database.py
    └── src/
        ├── nutrition_facts_extractor.py
        └── manual_serving_data_loader.py
```

---

**最終更新:** 2025-10-05
**データバージョン:** v2.0
**総食材数:** 1,152食材
**ファイルサイズ:** 2.75 MB
**処理時間合計:** 約3時間
