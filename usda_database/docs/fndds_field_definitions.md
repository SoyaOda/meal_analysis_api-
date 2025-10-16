# FNDDS (surveyDownload.json) 全フィールド定義書

## 📅 更新日
2025-10-12

## 📊 概要

**総食品数**: 5,432件
**トップレベルフィールド数**: 14個

---

## 🔍 トップレベルフィールド一覧

| # | フィールド名 | データ型 | カバレッジ | 説明 |
|---|------------|---------|-----------|------|
| 1 | `dataType` | string | 100% | データタイプ識別子 |
| 2 | `description` | string | 100% | 食品の説明（食品名） |
| 3 | `endDate` | string | 100% | データの終了日 |
| 4 | `fdcId` | integer | 100% | FoodData Central ID（一意識別子） |
| 5 | `foodAttributes` | list | 100% | 食品属性データ（WWEIAカテゴリー等） |
| 6 | `foodClass` | string | 100% | 食品クラス |
| 7 | `foodCode` | string | 100% | 8桁の食品コード |
| 8 | `foodNutrients` | list | 100% | 栄養素データ（最大65種類） |
| 9 | `foodPortions` | list | 100% | 単位変換データ |
| 10 | `footnote` | string | 0.02% | 脚注（特殊な場合のみ） |
| 11 | `inputFoods` | list | 100% | レシピ・材料データ |
| 12 | `publicationDate` | string | 100% | 公開日 |
| 13 | `startDate` | string | 100% | データの開始日 |
| 14 | `wweiaFoodCategory` | dict | 100% | WWEIAカテゴリー情報 |

---

## 📝 各フィールドの詳細定義

### 1. `dataType` (string)

**説明**: データタイプ識別子
**カバレッジ**: 100% (5,432/5,432)
**データ型**: string

**値の例**:
```
"Survey (FNDDS)"
```

**意味**: すべての食品が「Survey (FNDDS)」として分類される。これはFNDDS（Food and Nutrient Database for Dietary Studies）のサーベイデータであることを示す。

**用途**:
- データソースの識別
- 他のFoodData Centralデータベース（SR Legacy, Branded Food等）との区別

---

### 2. `description` (string)

**説明**: 食品の説明（食品名）
**カバレッジ**: 100% (5,432/5,432)
**データ型**: string

**値の例**:
```
"Milk, human"
"Milk, NFS"
"Milk, whole"
"Milk, reduced fat (2%)"
"Milk, low fat (1%)"
```

**意味**: 食品の公式名称。調理方法、脂肪含有量、その他の修飾語を含む詳細な説明。

**用途**:
- 食品の識別
- **search_name/descriptionの生成元**
- ユーザー向けの表示名

**注意事項**:
- 非常に詳細で長い記述が多い
- ルールベースでのsearch_name生成は困難（→ LLMベース推奨）

---

### 3. `endDate` (string)

**説明**: データの終了日
**カバレッジ**: 100% (5,432/5,432)
**データ型**: string (MM/DD/YYYY形式)

**値の例**:
```
"12/31/2023"
```

**意味**: このFNDDSバージョン（2021-2023）のデータ有効終了日

**用途**:
- データのバージョン管理
- 有効期間の確認

---

### 4. `fdcId` (integer)

**説明**: FoodData Central ID（一意識別子）
**カバレッジ**: 100% (5,432/5,432)
**データ型**: integer

**値の例**:
```
2705383
2705384
2705385
2705386
2705387
```

**意味**: 各食品を一意に識別するID。FoodData Centralデータベース全体で一意。

**用途**:
- 食品の一意識別
- データベース間のリンク
- APIでの検索・参照

**重要性**: ⭐⭐⭐ (最重要)

---

### 5. `foodAttributes` (list)

**説明**: 食品属性データ（WWEIAカテゴリー番号・説明等）
**カバレッジ**: 100% (5,432/5,432)
**データ型**: list of dict

**構造**:
```json
[
  {
    "id": 3298313,
    "name": "WWEIA Category number",
    "value": "9602",
    "foodAttributeType": {
      "id": 999,
      "name": "Attribute",
      "description": "Generic attributes"
    }
  },
  {
    "id": 3298314,
    "name": "WWEIA Category description",
    "value": "Human milk",
    "foodAttributeType": {
      "id": 999,
      "name": "Attribute",
      "description": "Generic attributes"
    }
  }
]
```

**含まれる情報**:
- **WWEIA Category number**: カテゴリー番号
- **WWEIA Category description**: カテゴリー説明（例: "Human milk", "Milk, whole"）
- **Additional Description**: 追加説明（一部の食品のみ）
- **Adjustments**: 水分量変更等の調整情報（例: "Moisture change: 0%"）

**用途**:
- カテゴリー別のフィルタリング
- 食品分類
- 検索の補助情報

---

### 6. `foodClass` (string)

**説明**: 食品クラス
**カバレッジ**: 100% (5,432/5,432)
**データ型**: string

**値の例**:
```
"Survey"
```

**意味**: すべての食品が「Survey」クラスに分類される。これはFNDDSがサーベイベースのデータベースであることを示す。

**用途**:
- データベースタイプの識別

---

### 7. `foodCode` (string)

**説明**: 8桁の食品コード
**カバレッジ**: 100% (5,432/5,432)
**データ型**: string

**値の例**:
```
"11000000"
"11100000"
"11111000"
"11112110"
"11112210"
```

**意味**: FNDDSの8桁食品コード。カテゴリーや食品グループを示す階層構造を持つ。

**構造**:
- 上位桁: 大カテゴリー（例: "11" = 乳製品）
- 下位桁: 詳細分類

**用途**:
- 食品の階層的分類
- カテゴリー別検索
- レガシーシステムとの互換性

---

### 8. `foodNutrients` (list) ⭐⭐⭐

**説明**: 栄養素データ（最大65種類の栄養素）
**カバレッジ**: 100% (5,432/5,432)
**データ型**: list of dict

**構造**:
```json
[
  {
    "type": "FoodNutrient",
    "id": 34136159,
    "nutrient": {
      "id": 1003,
      "number": "203",
      "name": "Protein",
      "rank": 600,
      "unitName": "g"
    },
    "amount": 3.33
  },
  {
    "type": "FoodNutrient",
    "id": 34136160,
    "nutrient": {
      "id": 1004,
      "number": "204",
      "name": "Total lipid (fat)",
      "rank": 800,
      "unitName": "g"
    },
    "amount": 2.14
  }
]
```

**含まれる主要栄養素**:
1. **Energy (kcal)** - カロリー
2. **Protein (g)** - タンパク質
3. **Total lipid (fat) (g)** - 脂質
4. **Carbohydrate, by difference (g)** - 炭水化物
5. **Fiber, total dietary (g)** - 食物繊維
6. **Sugars, total (g)** - 糖質
7. **Calcium (mg)** - カルシウム
8. **Iron (mg)** - 鉄
9. **Sodium (mg)** - ナトリウム
10. **Vitamin C (mg)** - ビタミンC
... 他55種類

**重要フィールド**:
- `amount`: 100gあたりの栄養素量
- `nutrient.name`: 栄養素名
- `nutrient.unitName`: 単位（g, mg, µg, kcal等）
- `nutrient.rank`: 表示順序

**用途**:
- **栄養計算の基礎データ**
- 栄養表示
- 健康管理アプリでの利用

**重要性**: ⭐⭐⭐ (最重要)

**注意事項**:
- すべての食品に65種類の栄養素があるわけではない（一部は0または欠損）
- **100gあたりの値**であることに注意

---

### 9. `foodPortions` (list) ⭐⭐⭐

**説明**: 単位変換データ（serving size情報）
**カバレッジ**: 100% (5,432/5,432)
**データ型**: list of dict

**構造**:
```json
[
  {
    "id": 290506,
    "measureUnit": {
      "id": 9999,
      "name": "undetermined",
      "abbreviation": "undetermined"
    },
    "modifier": 10205,
    "gramWeight": 246,
    "portionDescription": "1 cup",
    "sequenceNumber": 1
  },
  {
    "id": 290508,
    "measureUnit": {
      "id": 9999,
      "name": "undetermined",
      "abbreviation": "undetermined"
    },
    "modifier": 30000,
    "gramWeight": 30.8,
    "portionDescription": "1 fl oz",
    "sequenceNumber": 3
  }
]
```

**重要フィールド**:
- **`portionDescription`**: 単位の説明（例: "1 cup", "1 fl oz", "1 piece"）
- **`gramWeight`**: その単位の重量（グラム）
- **`sequenceNumber`**: 表示順序

**用途**:
- **単位変換**（cup → グラム、oz → グラム等）
- **default_unit / unit_to_grams の生成元**
- ユーザー入力の量をグラムに変換

**変換例**:
```
1 cup = 246g
1 fl oz = 30.8g
```

**重要性**: ⭐⭐⭐ (最重要)

**注意事項**:
- `gramWeight: 0` の場合は「Quantity not specified」（量未指定）
- 1つの食品に複数の単位が定義されている

---

### 10. `footnote` (string)

**説明**: 脚注（特殊な場合のみ）
**カバレッジ**: 0.02% (1/5,432)
**データ型**: string

**値の例**:
```
"FNDDS 2021-2023 includes the food code 11000000 Milk, human;
it does not provide any nutrient values. The data were 50 years old,
the source was unverifiable, and some values were based on cow's milk..."
```

**意味**: データに関する特殊な注記や警告。ほとんどの食品には存在しない。

**用途**:
- データ品質に関する注意事項の表示
- 特殊なケースの説明

**重要性**: ⭐ (低)

---

### 11. `inputFoods` (list) ⭐⭐

**説明**: レシピ・材料データ
**カバレッジ**: 100% (5,432/5,432)
**データ型**: list of dict

**構造**:
```json
[
  {
    "id": 124268,
    "unit": "GM",
    "portionDescription": "NONE",
    "portionCode": 0,
    "foodDescription": "Milk, whole, 3.25% milkfat, with added vitamin D",
    "retentionCode": 0,
    "ingredientWeight": 40,
    "ingredientCode": 1077,
    "ingredientDescription": "Milk, whole, 3.25% milkfat, with added vitamin D",
    "amount": 40,
    "sequenceNumber": 1
  }
]
```

**重要フィールド**:
- **`ingredientDescription`**: 材料の説明
- **`ingredientWeight`** / **`amount`**: 材料の重量（グラム）
- **`unit`**: 単位（通常は"GM"=グラム）
- **`sequenceNumber`**: 材料の順序

**用途**:
- **複合料理の材料リスト**
- 料理の構成を理解
- 材料数による食品分類（複合料理 vs 基本食材）

**重要な特徴**:
- **空リスト `[]`**: 基本食材（レシピなし）
- **1要素**: 単一材料（調理済み食材の可能性）
- **2要素以上**: 複合料理

**材料数の分布**:
- 0種類（基本食材）: 1,603件 (29.5%)
- 1種類（調理済み食材）: 170件 (3.1%)
- 2種類以上（複合料理）: 3,829件 (70.5%)

**重要性**: ⭐⭐ (重要)

---

### 12. `publicationDate` (string)

**説明**: 公開日
**カバレッジ**: 100% (5,432/5,432)
**データ型**: string (MM/DD/YYYY形式)

**値の例**:
```
"10/31/2024"
```

**意味**: このデータセットの公開日

**用途**:
- データのバージョン管理
- 更新履歴の追跡

---

### 13. `startDate` (string)

**説明**: データの開始日
**カバレッジ**: 100% (5,432/5,432)
**データ型**: string (MM/DD/YYYY形式)

**値の例**:
```
"1/1/2021"
```

**意味**: このFNDDSバージョン（2021-2023）のデータ有効開始日

**用途**:
- データのバージョン管理
- 有効期間の確認

---

### 14. `wweiaFoodCategory` (dict) ⭐

**説明**: WWEIA（What We Eat In America）カテゴリー情報
**カバレッジ**: 100% (5,432/5,432)
**データ型**: dict

**構造**:
```json
{
  "wweiaFoodCategoryDescription": "Human milk",
  "wweiaFoodCategoryCode": 3298314
}
```

**フィールド**:
- **`wweiaFoodCategoryDescription`**: カテゴリー名（例: "Meat mixed dishes", "Pasta mixed dishes"）
- **`wweiaFoodCategoryCode`**: カテゴリーコード（一意識別子）

**カテゴリー数**: 172種類

**主要カテゴリー（上位10）**:
1. Meat mixed dishes: 233件
2. Pasta mixed dishes: 174件
3. Chicken, whole pieces: 160件
4. Eggs and omelets: 147件
5. Other vegetables and combinations: 147件
6. Poultry mixed dishes: 133件
7. Rice mixed dishes: 132件
8. Yeast breads: 113件
9. Fish: 109件
10. Coffee: 109件

**用途**:
- **カテゴリー別フィルタリング**
- 食品分類
- 優先度付け（頻出カテゴリーの優先処理）

**重要性**: ⭐⭐ (重要)

---

## 📊 データ構造の階層図

```
SurveyFood (食品データ)
│
├─ 基本情報
│  ├─ fdcId (一意ID) ⭐⭐⭐
│  ├─ description (食品名) ⭐⭐⭐
│  ├─ foodCode (8桁コード)
│  ├─ foodClass ("Survey")
│  ├─ dataType ("Survey (FNDDS)")
│  ├─ startDate / endDate (有効期間)
│  ├─ publicationDate (公開日)
│  └─ footnote (脚注、稀)
│
├─ 栄養データ ⭐⭐⭐
│  └─ foodNutrients []
│     └─ nutrient
│        ├─ name (栄養素名)
│        ├─ amount (100gあたりの量)
│        └─ unitName (単位)
│
├─ 単位変換データ ⭐⭐⭐
│  └─ foodPortions []
│     ├─ portionDescription ("1 cup", "1 oz"等)
│     └─ gramWeight (グラム重量)
│
├─ レシピデータ ⭐⭐
│  └─ inputFoods []
│     ├─ ingredientDescription (材料名)
│     └─ amount (材料の重量)
│
├─ カテゴリー情報 ⭐⭐
│  ├─ wweiaFoodCategory
│  │  ├─ wweiaFoodCategoryDescription
│  │  └─ wweiaFoodCategoryCode
│  │
│  └─ foodAttributes []
│     ├─ WWEIA Category number
│     ├─ WWEIA Category description
│     ├─ Additional Description (任意)
│     └─ Adjustments (任意)
```

---

## 🎯 各フィールドの重要度

| 重要度 | フィールド | 理由 |
|-------|----------|------|
| ⭐⭐⭐ | `fdcId` | 一意識別子（必須） |
| ⭐⭐⭐ | `description` | search_name/description生成元 |
| ⭐⭐⭐ | `foodNutrients` | 栄養計算の基礎データ |
| ⭐⭐⭐ | `foodPortions` | 単位変換（default_unit/unit_to_grams生成元） |
| ⭐⭐ | `inputFoods` | レシピ情報、食品分類 |
| ⭐⭐ | `wweiaFoodCategory` | カテゴリー別フィルタリング |
| ⭐ | `foodCode` | レガシーシステム互換性 |
| ⭐ | `foodAttributes` | 補助情報 |
| ⭐ | その他 | メタデータ（日付、クラス等） |

---

## 💡 データ利用の推奨事項

### 1. **search_name / description生成**
- **元データ**: `description`
- **推奨方法**: LLMベース（DeepInfra API）
- **理由**: ルールベースでは複雑な食品名の処理が困難

### 2. **栄養計算**
- **元データ**: `foodNutrients` (100gあたり)
- **単位変換**: `foodPortions` (gramWeight)
- **計算式**: `栄養素量 = (foodNutrients.amount / 100) × 入力量（g）`

### 3. **単位変換データ生成**
- **元データ**: `foodPortions`
- **生成項目**:
  - `default_unit`: 最初のportionDescription
  - `unit_to_grams`: {portionDescription: gramWeight} のマッピング
  - `default_nutrition`: 1 default_unit あたりの栄養素

### 4. **食品フィルタリング**
- **カテゴリー**: `wweiaFoodCategory.wweiaFoodCategoryDescription`
- **材料数**: `len(inputFoods)`
- **キーワード**: `description`に頻出キーワードを含むか

### 5. **データ品質チェック**
- `foodNutrients`が空でないか
- `foodPortions`が存在するか
- `gramWeight > 0` の単位があるか

---

## 📄 関連ファイル

- **分析スクリプト**: `/tmp/analyze_fndds_all_fields.py`
- **分析結果**: `/tmp/fndds_all_fields_analysis.txt`
- **データソース**: `/Users/odasoya/meal_analysis_api_2/usda_database/surveyDownload.json`

---

## 📚 参考リンク

- [USDA FoodData Central](https://fdc.nal.usda.gov/)
- [FNDDS Documentation](https://www.ars.usda.gov/northeast-area/beltsville-md-bhnrc/beltsville-human-nutrition-research-center/food-surveys-research-group/docs/fndds-download-databases/)
- [WWEIA Food Categories](https://www.ars.usda.gov/northeast-area/beltsville-md-bhnrc/beltsville-human-nutrition-research-center/food-surveys-research-group/docs/wweia-food-categories/)
