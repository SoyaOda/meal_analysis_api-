# 栄養データベース仕様書 (Nutrition Database Specification)

## 概要 (Overview)

このドキュメントは、USDA Food Data Central API から収集した生データを基に構築した統一栄養データベースの仕様を説明します。

## データベース構造 (Database Structure)

### 統一フォーマット (Unified Format)

全てのアイテムは以下の統一フォーマットに従います：

```json
{
  "db_type": "string",        // "dish", "ingredient", "branded"のいずれか
  "id": number,               // USDA Food Data CentralのID
  "search_name": "string",    // 検索用の名前
  "nutrition": {
    "calories": number,       // カロリー (kcal/100g)
    "protein": number,        // タンパク質 (g/100g)
    "fat": number,           // 脂質 (g/100g)
    "carbs": number          // 炭水化物 (g/100g)
  },
  "weight": number            // 基準重量 (g)
}
```

## カテゴリ別詳細 (Category Details)

### 1. Dish (料理・レシピ)

**説明**: 完成された料理やレシピのデータ
**データソース**: USDA Recipe データ
**特徴**: 複数の食材を組み合わせた完成品

#### JSON サンプル:

```json
{
  "db_type": "dish",
  "id": 123456,
  "search_name": "Chicken stir-fry with vegetables",
  "nutrition": {
    "calories": 145.5,
    "protein": 18.2,
    "fat": 6.8,
    "carbs": 4.3
  },
  "weight": 150.0
}
```

#### 元データからの変換プロセス:

- `title` → `search_name`
- `nutrients.servingSize` → `weight` (gram 抽出)
- 栄養素は 100g あたりに正規化

### 2. Ingredient (食材・基本食品)

**説明**: 個別の食材や基本的な食品のデータ
**データソース**: USDA Food データ
**特徴**: 単一食材、調理前の状態

#### JSON サンプル:

```json
{
  "db_type": "ingredient",
  "id": 789012,
  "search_name": "Chicken, breast, boneless, skinless, raw",
  "nutrition": {
    "calories": 165.0,
    "protein": 31.0,
    "fat": 3.6,
    "carbs": 0.0
  },
  "weight": 100.0
}
```

#### 元データからの変換プロセス:

- `name` + `description` → `search_name`
- `units`から`description="grams"`の amount を`weight`として使用
- 栄養素は 100g あたりに正規化

### 3. Branded (ブランド食品)

**説明**: 特定ブランドの商品データ
**データソース**: USDA Branded Food データ
**特徴**: 商用製品、パッケージ食品

#### JSON サンプル:

```json
{
  "db_type": "branded",
  "id": 345678,
  "search_name": "KRAFT, Macaroni & Cheese Dinner Original",
  "nutrition": {
    "calories": 370.0,
    "protein": 11.0,
    "fat": 3.0,
    "carbs": 71.0
  },
  "weight": 70.0
}
```

#### 元データからの変換プロセス:

- `food_name` + `description` → `search_name`
- `unit_weights`から`description="grams"`の amount を`weight`として使用
- 栄養素フィールドは`calories`/`serving_calories`, `proteins`/`serving_proteins`等から取得
- 栄養素は 100g あたりに正規化

## データベースファイル構成 (Database File Structure)

```
nutrition_db/
├── dish_db.json              # 料理データのみ
├── ingredient_db.json        # 食材データのみ
├── branded_db.json           # ブランド食品データのみ
├── unified_nutrition_db.json # 全カテゴリ統合
└── build_stats.json          # 構築統計情報
```

## 検索・利用方法 (Search & Usage)

### 1. カテゴリ別検索

特定のカテゴリのデータのみを検索したい場合は、対応するファイルを使用。

### 2. 統合検索

全カテゴリを横断して検索したい場合は、`unified_nutrition_db.json`を使用。

### 3. 検索キー

- `search_name`フィールドを使用してテキスト検索
- `db_type`でカテゴリフィルタリング
- `id`で特定アイテムの直接アクセス

## 栄養値の正規化 (Nutrition Value Normalization)

- **基準**: 全ての栄養値は 100g あたりで正規化
- **計算方法**: `(元の栄養値 / 元の重量) × 100`
- **利点**: 異なる食品間での栄養価比較が容易

## 検索仕様 (Search Specification)

### 検索対象フィールド詳細

#### search_name フィールド

- **データ型**: string
- **構成**: 元データベースの `name` と `description` を結合
- **フォーマット**: メイン名称 + 修飾語（スペース区切り）
  - 例: `"Onions, Cooked, boiled, drained, with salt"`
  - 例: `"Roasted Cherry Tomatoes with Mint"`
- **長さ**:
  - **通常**: 5 単語以内
  - **最大**: 10 単語程度
- **特徴**: 英語ベース、食材・料理の詳細な説明を含む

### 検索アルゴリズム要件

#### 単語境界問題への対処

検索システムは以下の単語境界問題に対処する必要があります：

**問題例**: `"cook"` でクエリした場合の期待される結果

```
✅ 高スコア（意味的に関連）:
- "cook" (完全一致)
- "cooking" (同じ語幹)
- "cooked" (同じ語幹)

❌ 低スコア（意味的に無関係）:
- "cookie" (文字列的には似ているが意味が異なる)
- "cookies" (文字列的には似ているが意味が異なる)
```

#### 実装推奨事項

1. **語幹処理 (Stemming)**: 語尾変化を正規化
2. **BM25F 検索**: フィールド別重み付き検索
3. **マルチシグナルブースティング**: 複数の関連度指標を組み合わせ
4. **同義語辞書**: 食材・料理固有の同義語対応
5. **部分一致スコアリング**: 文字列類似度 vs 意味的類似度のバランス

### 検索性能指標

- **目標精度**: 90%以上のマッチ率
- **応答時間**: 1 秒以内（8,878 項目対象）
- **フォールバック**: ElasticSearch 利用不可時の直接検索対応
