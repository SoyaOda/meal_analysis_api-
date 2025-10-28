# Word Query APIs アーキテクチャ徹底分析

## 概要

`apps/word_query_api` (MyNetDiary版) と `apps/usda_word_query_api` (USDA FNDDS版) の2つのAPIは、どちらも食材・栄養情報の高精度検索を提供する独立したAPIサービスです。

---

## 1. データベース技術

### 共通点: Elasticsearch
両APIは **Elasticsearch 7.x+** を検索エンジンとして使用しています。

#### 接続設定
- **URL**: `http://35.193.16.212:9200` (Production VM)
- **プロトコル**: HTTP REST API
- **タイムアウト**: 5秒 (検索リクエスト)

### 使用しているインデックス

#### word_query_api (MyNetDiary版)
- **インデックス名**: `mynetdiary_converted_tool_calls_list_stemmed_with_nutrition`
- **データソース**: MyNetDiaryデータベース
- **データ数**: 不明（ドキュメントに記載なし）
- **データパス**: 未特定

#### usda_word_query_api (USDA版)
- **インデックス名**: `usda_unified_nutrition_db`
- **データソース**: USDA FNDDS (Food and Nutrient Database for Dietary Studies)
- **データ数**: 1,542件
  - 生食材（raw）: 1,399件
  - 準備済み（prepared）: 143件
- **インデックスサイズ**: 1.47 MB
- **データパス**: `/Users/odasoya/meal_analysis_api_2/usda_data_processing/db/usda_unified_db.json`

### インデックス設定の詳細

両APIは非常に似たインデックス設定を採用しています:

#### 共通の設定要素
1. **Shards**: 1
2. **Replicas**: 1
3. **Custom Analyzer**: `stemmed_analyzer` (Porter Stemmer使用)
4. **Normalizer**: `lowercase_normalizer`

#### フィールドマッピング（USDA版の例）

**検索用フィールド:**
- `original_name` (text + keyword + exact)
- `search_name` (text + keyword)
- `description` (text + keyword)
- **`stemmed_search_name`** (text with stemmed_analyzer + keyword) ← 重要
- **`stemmed_description`** (text with stemmed_analyzer + keyword) ← 重要

**メタデータフィールド:**
- `id` (keyword)
- `ingredient_type` (keyword) - "raw" or "prepared" (USDA版のみ)
- `processing_method` (keyword) - MyNetDiary版のみ
- `brand_name` (keyword) - LLMで生成
- `item_type` (keyword) - LLMで生成

**栄養情報フィールド:**
- `default_unit` (keyword)
- `default_nutrition` (object) - カロリー、タンパク質、脂質、炭水化物
- `unit_to_grams` (object) - 単位変換テーブル

---

## 2. 検索アルゴリズム

### 共通アーキテクチャ: 7層Tierアルゴリズム + 語幹化

両APIは**Porter Stemmer**による語幹化と、**7層のTier検索**アルゴリズムを採用しています。

### 語幹化処理 (Stemming)

#### 実装: NLTK Porter Stemmer

```python
from nltk.stem import PorterStemmer
stemmer = PorterStemmer()

def stem_query(query: str) -> str:
    # 1. 小文字変換
    query = query.lower()
    
    # 2. 特殊文字除去（アルファベットとスペースのみ残す）
    query = re.sub(r'[^a-z\s]', ' ', query)
    
    # 3. 複数スペースを単一スペースに
    query = re.sub(r'\s+', ' ', query).strip()
    
    # 4. トークン化と語幹化
    tokens = query.split()
    stemmed_tokens = [stemmer.stem(token) for token in tokens]
    
    return ' '.join(stemmed_tokens)
```

**例:**
- "chicken" → "chicken"
- "chickens" → "chicken"
- "grilled chicken breast" → "grill chicken breast"

### 7層Tier検索アルゴリズム

両APIで**完全に同じ**アルゴリズムを使用:

| Tier | マッチタイプ | ブーストスコア | Elasticsearchクエリタイプ | 対象フィールド |
|------|------------|-------------|------------------------|--------------|
| **1** | Exact Match (Phrase) | **15** | `match_phrase` | `stemmed_search_name` |
| **2** | Exact Match (Description) | **12** | `match_phrase` | `stemmed_description` |
| **3** | Phrase Match | **10** | `match` | `stemmed_search_name` |
| **4** | Phrase Match (Description) | **8** | `match` | `stemmed_description` |
| **5** | Term Match | **6** | `term` | `stemmed_search_name.keyword` |
| **6** | Multi-field Match | **4** | `multi_match` | 複数フィールド |
| **7** | Fuzzy Match | **2** | `fuzzy` | `stemmed_search_name` |

#### Elasticsearchクエリ構造 (共通)

```json
{
  "query": {
    "bool": {
      "should": [
        {"match_phrase": {"stemmed_search_name": {"query": "語幹化クエリ", "boost": 15}}},
        {"match_phrase": {"stemmed_description": {"query": "語幹化クエリ", "boost": 12}}},
        {"match": {"stemmed_search_name": {"query": "語幹化クエリ", "boost": 10}}},
        {"match": {"stemmed_description": {"query": "語幹化クエリ", "boost": 8}}},
        {"term": {"stemmed_search_name.keyword": {"value": "語幹化クエリ", "boost": 6}}},
        {"multi_match": {
          "query": "語幹化クエリ",
          "fields": ["stemmed_search_name^3", "stemmed_description^2", "original_name"],
          "boost": 4
        }},
        {"fuzzy": {"stemmed_search_name": {"value": "語幹化クエリ", "boost": 2}}}
      ]
    }
  }
}
```

### word_query_api固有の検索戦略

#### Exact Match優先戦略 (2段階検索)

**Step 1: Exact Match First**
```python
def elasticsearch_exact_match_first(query: str, size: int = 10):
    # Step 1: original_name.exact での完全一致（小文字化）
    exact_match_body = {
        "query": {
            "term": {
                "original_name.exact": query.lower()
            }
        }
    }
    
    # Exact matchが見つかれば決定的スコア999.0で返す
    if hits:
        return formatted_result  # score=999.0
    
    # Step 2: Exact match失敗時、Tierアルゴリズムにフォールバック
    return elasticsearch_search_optimized_fallback(query, size)
```

**特徴:**
1. まず `original_name.exact` フィールドで完全一致を探す
2. 見つかれば**決定的スコア999.0**で即座に返す
3. 見つからなければ7層Tierアルゴリズムにフォールバック

#### コンテキスト別検索 (search_context)

word_query_apiは用途別に検索戦略を切り替える:

| search_context | 検索戦略 | デフォルト動作 | 用途 |
|---------------|---------|--------------|-----|
| `meal_analysis` | Exact Match Only | uncooked除外 | 食事分析用 |
| `word_search` | Tier検索 | 全候補表示 | ワード検索用 |

```python
if search_context == "word_search":
    result = elasticsearch_search_optimized_fallback(...)
else:  # meal_analysis
    result = elasticsearch_exact_match_only(...)
```

### usda_word_query_api固有の検索機能

#### ingredient_typeフィルタ

USDA版は食材タイプによるフィルタリングをサポート:

```python
# ingredient_typeフィルタを追加
if ingredient_types:
    search_body["query"]["bool"]["filter"] = [
        {"terms": {"ingredient_type": ingredient_types}}
    ]
```

**使用例:**
- `?ingredient_type=raw` - 生食材のみ
- `?ingredient_type=prepared` - 準備済み食材のみ
- `?ingredient_type=all` or なし - 両方

---

## 3. マッチタイプ判定ロジック

両APIは同じ `determine_match_type()` 関数を使用してマッチタイプを判定します。

### 判定アルゴリズム

```python
def determine_match_type(query: str, explanation: str, original_name: str,
                        search_name_list: list, description: str) -> str:
    q_lower = query.lower()
    stemmed_query = stem_query(query)
    
    # 1. Exact Match（original_nameで完全一致）
    if explanation == "exact_match_original_name_keyword":
        return "exact_match"
    if original_name and original_name.lower() == q_lower:
        return "exact_match"
    
    # 2. Tier 1: stemmed_search_nameでの完全一致
    for name in search_name_list:
        if stem_query(name) == stemmed_query:
            return "tier_1_exact"
    
    # 3. Tier 2: stemmed_descriptionでの完全一致
    if stem_query(description) == stemmed_query:
        return "tier_2_description"
    
    # 4. Tier 3: stemmed_search_nameでのプレフィックスマッチ
    for name in search_name_list:
        if stem_query(name).startswith(stemmed_query):
            return "tier_3_phrase"
    
    # 5-8: 同様のロジック...
    
    # 9. Tier 7: その他（ファジーマッチ）
    return "tier_7_fuzzy"
```

### 返されるマッチタイプ

- `exact_match` - 完全一致（スコア999.0）
- `tier_1_exact` - 語幹化完全一致 (スコア15+)
- `tier_2_description` - 説明完全一致 (スコア12+)
- `tier_3_phrase` - プレフィックスマッチ (スコア10+)
- `tier_4_phrase_desc` - 説明プレフィックス (スコア8+)
- `tier_5_term` - 部分マッチ (スコア6+)
- `tier_6_multi` - 複数フィールド (スコア4+)
- `tier_7_fuzzy` - ファジーマッチ (スコア2+)

---

## 4. データローディング（USDA版）

### load_usda_db.py の処理フロー

```python
# Step 1: Elasticsearch接続確認
check_elasticsearch_connection(ELASTICSEARCH_URL)

# Step 2: 既存インデックス削除
delete_index_if_exists(ELASTICSEARCH_URL, USDA_INDEX_NAME)

# Step 3: 新しいインデックス作成
create_index(ELASTICSEARCH_URL, USDA_INDEX_NAME, index_settings)

# Step 4: USDAデータ読み込み
documents = load_usda_data("usda_unified_db.json")

# Step 5: ドキュメントのバルクインデックス化
bulk_index_documents(ELASTICSEARCH_URL, USDA_INDEX_NAME, documents, batch_size=500)

# Step 6: インデックス検証
verify_index(ELASTICSEARCH_URL, USDA_INDEX_NAME)
```

### バルクインデックス化

- **バッチサイズ**: 500ドキュメント/バッチ
- **API**: Elasticsearch Bulk API (`_bulk`)
- **フォーマット**: NDJSON (Newline Delimited JSON)
- **タイムアウト**: 60秒/バッチ

```python
# Bulk APIフォーマット
bulk_data = []
for doc in batch:
    bulk_data.append(json.dumps({"index": {"_index": index_name, "_id": doc["id"]}}))
    bulk_data.append(json.dumps(doc))

bulk_body = "\n".join(bulk_data) + "\n"
```

---

## 5. パフォーマンス特性

### 検索速度

#### word_query_api
- **平均検索時間**: 変動あり（コンテキスト依存）
  - Exact Match: 高速 (Step 1のみ)
  - Tier Fallback: やや遅い (2段階検索)

#### usda_word_query_api
- **平均検索時間**: 290-330ms
- **同時接続**: サポート (FastAPI非同期処理)

### データサイズ

#### usda_word_query_api
- **インデックスサイズ**: 1.47 MB
- **ドキュメント数**: 1,542件

---

## 6. APIエンドポイント比較

### 共通エンドポイント

| エンドポイント | word_query_api | usda_word_query_api |
|--------------|---------------|-------------------|
| 検索 | `GET /api/v1/nutrition/suggest` | `GET /api/v1/usda/suggest` |
| ヘルスチェック | `GET /api/v1/nutrition/suggest/health` | `GET /api/v1/usda/suggest/health` |

### パラメータ比較

#### word_query_api 検索パラメータ
- `q`: 検索クエリ (必須)
- `limit`: 結果数 (1-50, デフォルト10)
- `debug`: デバッグ情報表示
- **`search_context`**: `meal_analysis` | `word_search`
- **`exclude_uncooked`**: uncooked除外フラグ

#### usda_word_query_api 検索パラメータ
- `q`: 検索クエリ (必須)
- `limit`: 結果数 (1-50, デフォルト10)
- `debug`: デバッグ情報表示
- **`ingredient_type`**: `raw` | `prepared` | `all`

### 固有エンドポイント

#### usda_word_query_api のみ
- `GET /api/v1/usda/stats` - 統計情報取得
  - ドキュメント総数
  - ingredient_type別内訳
  - タイムスタンプ

---

## 7. レスポンスフォーマット

### 共通レスポンス構造

```json
{
  "query_info": {
    "original_query": "chicken",
    "processed_query": "chicken",
    "timestamp": "2025-10-16T14:00:19.663897Z",
    "suggestion_type": "autocomplete"
  },
  "suggestions": [
    {
      "rank": 1,
      "suggestion": "Chicken breast",
      "match_type": "tier_1_exact",
      "confidence_score": 100.0,
      "food_info": {
        "search_name": "Chicken breast",
        "search_name_list": ["Chicken breast", "Breast of chicken"],
        "description": "Chicken breast, grilled",
        "original_name": "Chicken breast, grilled"
      },
      "nutrition_preview": {
        "calories": 165.0,
        "protein": 31.0,
        "carbohydrates": 0.0,
        "fat": 3.6,
        "per_serving": "100g"
      },
      "default_unit": "gram",
      "default_nutrition": {
        "calorie": 1.65,
        "Protein_g": 0.31,
        "Total_Fat_g": 0.036,
        "Total_Carbs_g": 0.0
      },
      "unit_to_grams": {
        "gram": 1.0,
        "oz": 28.35,
        "lb": 453.6
      }
    }
  ],
  "metadata": {
    "total_suggestions": 10,
    "total_hits": 56,
    "search_time_ms": 325,
    "processing_time_ms": 325,
    "elasticsearch_index": "usda_unified_nutrition_db"
  },
  "status": {
    "success": true,
    "message": "USDA suggestions generated successfully"
  }
}
```

### USDA版固有フィールド

```json
{
  "food_info": {
    "ingredient_type": "raw",  // "raw" or "prepared"
    "ai_description": "Lean protein source...",
    "brand_name": "Generic",
    "item_type": "raw_ingredient"
  },
  "category": "Poultry",
  "category_emoji": "🍗",
  "food_specific_emoji": "🐔"
}
```

---

## 8. 主要な違いのまとめ

| 項目 | word_query_api (MyNetDiary版) | usda_word_query_api (USDA版) |
|-----|----------------------------|---------------------------|
| **データソース** | MyNetDiary | USDA FNDDS |
| **インデックス名** | `mynetdiary_converted_tool_calls_list_stemmed_with_nutrition` | `usda_unified_nutrition_db` |
| **データ数** | 不明 | 1,542件 |
| **検索戦略** | 2段階 (Exact Match First → Tier) | Tier検索のみ |
| **コンテキスト別検索** | ✅ あり (`search_context`) | ❌ なし |
| **フィルタ** | `exclude_uncooked` | `ingredient_type` (raw/prepared) |
| **ポート** | 8002 | 8004 |
| **統計API** | ❌ なし | ✅ あり (`/api/v1/usda/stats`) |
| **USDA固有フィールド** | ❌ なし | ✅ あり (`ingredient_type`, `ai_description`) |

---

## 9. 共通点のまとめ

1. **検索エンジン**: Elasticsearch 7.x+ (同じVM)
2. **語幹化**: Porter Stemmer (NLTK)
3. **検索アルゴリズム**: 7層Tierアルゴリズム（完全同一）
4. **マッチタイプ判定**: 同じロジック
5. **レスポンスモデル**: `shared.models.nutrition_search_models` を共有
6. **FastAPI**: 両方ともFastAPIで実装
7. **非同期処理**: 両方ともサポート
8. **デバッグモード**: 両方ともサポート

---

## 10. 技術スタック

### 共通技術
- **Webフレームワーク**: FastAPI
- **検索エンジン**: Elasticsearch 7.x+
- **自然言語処理**: NLTK (Porter Stemmer)
- **HTTPクライアント**: requests
- **データシリアライゼーション**: Pydantic models

### Python依存関係
```python
# 主要ライブラリ
fastapi
requests
nltk
pydantic
```

---

## 結論

両APIは**ほぼ同じアーキテクチャ**を採用しながら、異なるデータソース（MyNetDiary vs USDA FNDDS）に対応しています。

**主要な技術的共通点:**
- Elasticsearchベースの検索
- Porter Stemmerによる語幹化
- 7層Tierアルゴリズム
- FastAPIによる実装

**主要な違い:**
- word_query_api: Exact Match優先の2段階検索、コンテキスト別戦略
- usda_word_query_api: Tier検索のみ、ingredient_typeフィルタ

この設計により、両APIは**独立して動作**しながら、**同じ検索品質**を維持しています。
