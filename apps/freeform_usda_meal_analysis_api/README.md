# Freeform USDA Meal Analysis API

VLM (Vision Language Model) による画像解析から、USDA FoodData Centralデータベースを用いた栄養素計算までのEnd-to-Endパイプライン。

**Self-contained設計**: `shared/` ディレクトリへの依存を完全に排除し、単一ディレクトリで完結するアーキテクチャ。

**柔軟な設定**: API呼び出し時にVLMモデル、プロンプト、検索パラメータをカスタマイズ可能。

**完全な栄養計算**: USDA FoodData Central の3つのデータソース（Survey, Foundation, SR Legacy）から13,564食材の栄養データを使用。

**単位変換サポート**: 食材ごとの利用可能な単位（カップ、スプーン、枚など）と重量変換情報を提供（96.2%カバレッジ）。

## 🚀 フロントエンドエンジニア向けクイックスタート

### 本番環境URL

```
https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app
```

### API仕様書（Swagger UI）

```
https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/docs
```

### CORS設定

✅ **すべてのオリジンから呼び出し可能**（`Access-Control-Allow-Origin: *`）
フロントエンドから直接APIを呼び出せます。認証不要。

### 主要エンドポイント

| エンドポイント | メソッド | 用途 | レスポンスタイム |
|---------------|---------|------|------------------|
| `/api/v1/meal-analyses/complete` | POST | 画像から食事分析 | 30-50秒 |
| `/api/v1/retrieve` | GET | 食材検索（Hybrid） | 0.2-0.5秒 |
| `/api/v1/metadata` | GET | 全食材メタデータ取得 | 0.1-0.3秒 |
| `/api/v1/metadata/search` | GET | 食材名検索 | 0.05-0.1秒 |
| `/health` | GET | ヘルスチェック | 0.01秒 |

### JavaScript実装例

#### 1. 画像分析（Meal Analysis）

```javascript
// 画像ファイルをアップロードして栄養分析
async function analyzeMealImage(imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('user_context', 'dinner analysis');

  try {
    const response = await fetch(
      'https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/complete',
      {
        method: 'POST',
        body: formData,
        // タイムアウト推奨: 60秒
        signal: AbortSignal.timeout(60000)
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    console.log(`Total Calories: ${result.total_nutrition.calories} kcal`);
    console.log(`Dishes: ${result.total_dishes}`);
    return result;

  } catch (error) {
    if (error.name === 'TimeoutError') {
      console.error('Request timeout (60s)');
    } else {
      console.error('Analysis failed:', error);
    }
    throw error;
  }
}

// 使用例
const fileInput = document.getElementById('imageUpload');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (file) {
    const result = await analyzeMealImage(file);
    displayNutritionInfo(result);
  }
});
```

#### 2. 食材検索（Hybrid Mode）

```javascript
// 食材をセマンティック検索
async function searchFood(query, topK = 10) {
  const url = new URL(
    'https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/api/v1/retrieve'
  );
  url.searchParams.append('q', query);
  url.searchParams.append('mode', 'hybrid');  // BM25 + Vector
  url.searchParams.append('top_k', topK);
  url.searchParams.append('include_nutrition', 'true');

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    return data.results;

  } catch (error) {
    console.error('Search failed:', error);
    throw error;
  }
}

// 使用例
const results = await searchFood('grilled chicken breast', 5);
results.forEach(food => {
  console.log(`${food.name}: ${food.nutrition_per_100g.calories} kcal/100g`);
});
```

#### 3. 全食材メタデータ取得（初回ロード時）

```javascript
// 全13,564食材のメタデータを取得してキャッシュ
async function loadUSDAMetadata() {
  const cacheKey = 'usda_metadata_v1';
  const cacheTimestampKey = 'usda_metadata_timestamp';
  const now = Date.now();
  const cacheExpiry = 86400000; // 24時間

  // キャッシュチェック
  const cachedTimestamp = localStorage.getItem(cacheTimestampKey);
  if (cachedTimestamp && (now - parseInt(cachedTimestamp)) < cacheExpiry) {
    console.log('Using cached metadata');
    return JSON.parse(localStorage.getItem(cacheKey));
  }

  // APIから取得（gzip圧縮版: 0.67MB）
  console.log('Fetching fresh metadata from API...');
  const response = await fetch(
    'https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/api/v1/metadata?compressed=true'
  );

  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  const metadata = await response.json();
  console.log(`Loaded ${metadata.length} foods`);

  // ローカルストレージにキャッシュ
  localStorage.setItem(cacheKey, JSON.stringify(metadata));
  localStorage.setItem(cacheTimestampKey, now.toString());

  return metadata;
}

// クライアント側で食材検索
function searchMetadata(query, metadata) {
  const lowerQuery = query.toLowerCase();
  return metadata.filter(item =>
    item.description.toLowerCase().includes(lowerQuery) ||
    item.main_name.toLowerCase().includes(lowerQuery)
  ).slice(0, 20);
}

// 単位変換機能
function convertToGrams(fdcId, portionDescription, metadata) {
  const food = metadata.find(item => item.fdc_id === fdcId);
  if (!food || !food.portions) return null;

  const portion = food.portions.find(p =>
    p.description.toLowerCase().includes(portionDescription.toLowerCase())
  );

  return portion ? portion.gram_weight : null;
}

// 使用例
const metadata = await loadUSDAMetadata();
const chickenFoods = searchMetadata('chicken', metadata);
const gramsInCup = convertToGrams(746774, 'cup', metadata);
console.log(`1 cup = ${gramsInCup}g`);
```

### エラーレスポンス形式

APIはエラー時に以下の形式でJSONを返します：

```json
{
  "detail": "Error message here"
}
```

**HTTPステータスコード:**
- `400 Bad Request`: パラメータ不正（画像なし、クエリなしなど）
- `404 Not Found`: リソースが存在しない（FDC ID不正など）
- `422 Unprocessable Entity`: バリデーションエラー
- `500 Internal Server Error`: サーバーエラー（DeepInfra API障害など）
- `504 Gateway Timeout`: タイムアウト（VLM処理に60秒以上）

### パフォーマンス指標

| 操作 | 平均レスポンスタイム | 推奨タイムアウト |
|------|---------------------|-----------------|
| 画像分析（VLM処理） | 30-50秒 | 60秒 |
| Hybrid検索 | 0.2-0.5秒 | 5秒 |
| Fast検索 | 0.1-0.2秒 | 3秒 |
| メタデータ取得（gzip） | 0.1-0.3秒 | 5秒 |
| メタデータ検索 | 0.05-0.1秒 | 3秒 |
| ヘルスチェック | 0.01秒 | 1秒 |

**注意:**
- VLM処理はDeepInfra APIの負荷により変動します（20-60秒）
- 初回リクエストはコールドスタート（+3-5秒）が発生する場合があります
- Cloud Run側のタイムアウトは600秒（10分）に設定済み

### ベストプラクティス

1. **メタデータのキャッシュ**: 全食材メタデータは初回ロード時に取得し、localStorageにキャッシュ
2. **タイムアウト設定**: 画像分析は60秒、検索系は5秒のタイムアウトを設定
3. **エラーハンドリング**: HTTPステータスコードとdetailメッセージを表示
4. **プログレス表示**: 画像分析は30-50秒かかるため、ローディングUIを表示
5. **debounce**: リアルタイム検索はdebounce（300ms）を実装してAPI呼び出しを削減

### React実装例

```jsx
import { useState } from 'react';

function MealAnalyzer() {
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setAnalyzing(true);
    setError(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch(
        'https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/complete',
        {
          method: 'POST',
          body: formData,
          signal: AbortSignal.timeout(60000)
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      setResult(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        disabled={analyzing}
      />

      {analyzing && (
        <div className="loading">
          <p>Analyzing image... (30-50 seconds)</p>
          <progress />
        </div>
      )}

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="result">
          <h2>Total: {result.total_nutrition.calories} kcal</h2>
          <ul>
            {result.dishes.map((dish, i) => (
              <li key={i}>
                {dish.dish_name}: {dish.total_nutrition.calories} kcal
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

## アーキテクチャ

```
画像入力 → VLM解析 → クエリ抽出 → USDA検索（Hybrid/Accurate/Fast） → 栄養素計算 → 結果出力
```

### 主要コンポーネント

1. **DeepInfraService**: DeepInfra API との通信を管理（`shared/` に依存せず独立実装）
   - 環境変数から直接設定を取得
   - Thinking モデルのパラメータを自動最適化
2. **VLMService**: DeepInfra の VLM モデルを使用した画像解析
   - **デフォルトモデル**: `Qwen/Qwen3-VL-30B-A3B-Thinking` (30Bパラメータ)
   - **デフォルトプロンプト**: `v7_experimental`
   - API呼び出し時にモデルとプロンプトを動的に変更可能
3. **QueryExtractionService**: VLM レスポンスから検索クエリを抽出
4. **SimplifiedUSDASearcher**: FAISS Full Index を使用した軽量な食材検索
   - 2段階検索: FAISS embedding search → Qwen3 reranking
   - 13,565 ベクトルのインデックス
5. **HybridSearchEngine**: BM25 + Vector Hybrid Search (2025年ベストプラクティス準拠)
   - BM25 (キーワードマッチング) + Vector (セマンティック) の融合
   - RRF (Reciprocal Rank Fusion) で結果を統合
   - 重み付け: BM25=0.4, Vector=0.6, RRF k=60
6. **LocalUSDANutritionService**: `usda_metadata.json` から栄養素データをロード（自己完結型）
   - Survey Foods: 5,431 食材
   - Foundation Foods: 340 食材
   - SR Legacy Foods: 7,793 食材
   - **合計: 13,564 食材**（栄養素データ内蔵、270MBの外部JSONファイル不要）
   - **Portions情報**: 13,046食材（96.2%）に単位変換情報あり
7. **NutritionCalculator**: 100g あたりの栄養素から実重量の栄養素を計算

## ディレクトリ構成

```
apps/freeform_usda_meal_analysis_api/
├── README.md
├── __init__.py
├── main.py                    # FastAPI アプリケーション
├── startup_data_loader.py     # Cloud Storage起動時ダウンロード（Cloud Run用）
├── Dockerfile                 # Docker設定（Cloud Storage最適化版）
├── .gcloudignore              # Cloud Buildから除外するファイル指定
├── deploy.sh                  # デプロイスクリプト
├── requirements.txt           # 依存パッケージ
├── config/
│   ├── __init__.py
│   └── settings.py            # 環境変数と設定管理
├── models/
│   ├── __init__.py
│   ├── request_models.py      # リクエストモデル
│   └── response_models.py     # レスポンスモデル
├── routers/
│   ├── __init__.py
│   ├── analysis.py            # 分析エンドポイント
│   ├── retrieval.py           # 検索エンドポイント（Hybrid/Accurate/Fast）
│   ├── metadata.py            # メタデータ配信エンドポイント（全13,564食材）
│   └── health.py              # ヘルスチェック
├── data/                      # データディレクトリ（ローカル開発用）
│   └── faiss/                 # FAISS インデックスと栄養データ（221MB）
│       ├── usda_index_full.faiss        # ベクトル検索インデックス（13,564 vectors、212MB）
│       ├── usda_bm25_index/             # BM25インデックス（Hybrid Search用、9MB）
│       └── usda_metadata.json           # 栄養素データ統合版（8.4MB、13,564 foods、portions情報含む）
│       # 注意: Cloud Runデプロイ時はこのディレクトリは除外され、
│       #       起動時にgs://new-snap-calorie-faiss-data/faiss/からダウンロードされます
├── scripts/                   # データ生成スクリプト
│   └── build_index_with_nutrition.py    # FAISSインデックス + 栄養データ統合生成
├── prompts/
│   ├── freeform_prompt_usda_format_ver_v7_experimental_20251027.txt  # デフォルト
│   ├── freeform_prompt_usda_format_ver_v7_production_20251027.txt
│   └── ...                    # その他のプロンプトバージョン
├── services/
│   ├── __init__.py
│   ├── deepinfra_service.py   # DeepInfra API通信（shared/から独立）
│   ├── vlm_service.py         # VLM画像解析
│   ├── query_extraction.py    # クエリ抽出
│   ├── usda_search.py         # Simplified USDA Searcher
│   ├── food_search_service.py # USDA検索サービス
│   ├── hybrid_search.py       # Hybrid Search Engine (BM25 + Vector)
│   ├── nutrition_service.py   # 栄養素計算
│   └── pipeline.py            # End-to-End統合
└── test_result_food1.json     # テスト結果サンプル
```

## 環境変数

### ローカル開発環境

```bash
# 必須
DEEPINFRA_API_KEY=<your-api-key>
GOOGLE_CLOUD_PROJECT=new-snap-calorie

# FAISS インデックスディレクトリ（栄養データ統合版を含む）
USDA_INDEX_DIR=/path/to/apps/freeform_usda_meal_analysis_api/data/faiss

# オプション
PORT=8006
PYTHONPATH=/path/to/meal_analysis_api_2
```

### Cloud Run環境

Cloud Run上では、FAISSデータはCloud Storageから起動時に自動ダウンロードされます：

```bash
# 必須（Cloud Runの環境変数として設定）
DEEPINFRA_API_KEY=<your-api-key>

# 自動設定（main.pyで起動時に設定）
USDA_INDEX_DIR=/tmp/faiss                    # 起動時ダウンロード先
USDA_METADATA_FILE=/tmp/faiss/usda_metadata.json
```

**Cloud Storage統合の仕組み：**
- デプロイ時: `data/` ディレクトリは除外（.gcloudignoreで指定）
- 起動時: `gs://new-snap-calorie-faiss-data/faiss/` から `/tmp/faiss` へダウンロード
- メリット: ビルド時間短縮（10分→2分）、イメージサイズ削減（400MB→50MB）、コスト削減（93%減）

### VLMモデルの選択

デフォルトでは **Qwen/Qwen3-VL-30B-A3B-Thinking** を使用します。

**利用可能なThinking models:**
- `Qwen/Qwen3-VL-30B-A3B-Thinking` (**デフォルト**、バランス型)
- `Qwen/Qwen3-VL-235B-A22B-Thinking` (最高精度、高コスト)
- `Qwen/Qwen3-VL-8B-Thinking` (軽量、最安)

**推奨設定:**
- 本番環境（高精度重視）: `Qwen3-VL-235B-A22B-Thinking`
- 本番環境（コストバランス重視）: `Qwen3-VL-30B-A3B-Thinking` (**デフォルト**)
- 開発/テスト: `Qwen3-VL-8B-Thinking`

API呼び出し時にモデルを動的に変更可能:
```bash
curl -X POST "http://localhost:8006/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "model_id=Qwen/Qwen3-VL-235B-A22B-Thinking"
```

## ローカル起動

### 起動スクリプトを使用（推奨）

```bash
# プロジェクトルートに移動
cd /path/to/meal_analysis_api_2

# 環境変数を設定して起動
export USDA_INDEX_DIR="$(pwd)/apps/freeform_usda_meal_analysis_api/data/faiss"
export PYTHONPATH="$(pwd)"
export GOOGLE_CLOUD_PROJECT="new-snap-calorie"
export PORT="8006"

# API 起動
python -m apps.freeform_usda_meal_analysis_api.main
```

### 起動確認

起動ログで以下が表示されることを確認：

```
✅ Loaded 13564 foods with nutrition data
✅ Loaded full index: 13564 vectors
✅ Hybrid search engine initialized
✅ Pipeline initialized successfully
Uvicorn running on http://0.0.0.0:8006
```

起動後、以下の URL でアクセス可能:
- **Swagger UI**: http://localhost:8006/docs (フロントエンドエンジニア向けAPI仕様書)
- **ReDoc**: http://localhost:8006/redoc (読みやすいAPI仕様書)
- **OpenAPI JSON**: http://localhost:8006/openapi.json
- **Health Check**: http://localhost:8006/health
- **API Root**: http://localhost:8006/

## API使用例

### 基本的な画像分析（デフォルト設定使用）

```bash
curl -X POST "http://localhost:8006/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=dinner analysis"
```

### モデルとプロンプトをカスタマイズ

```bash
curl -X POST "http://localhost:8006/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "model_id=Qwen/Qwen2-VL-72B-Instruct" \
  -F "prompt_path=freeform_prompt_usda_format_ver_v7_production_20251027.txt" \
  -F "temperature=0.5" \
  -F "max_tokens=8192"
```

### 検索設定をカスタマイズ

```bash
curl -X POST "http://localhost:8006/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "stage1_top_k=60"
```

### すべてのパラメータを指定

```bash
curl -X POST "http://localhost:8006/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=lunch" \
  -F "model_id=Qwen/Qwen2-VL-72B-Instruct" \
  -F "prompt_path=freeform_prompt_usda_format_ver_v6_enhanced_20251027.txt" \
  -F "temperature=0.7" \
  -F "max_tokens=4096" \
  -F "stage1_top_k=40"
```

### レスポンス例

実際の `test_result_food1.json` からの抜粋（`test_images/images/test_food1.jpg` の解析結果）：

```json
{
  "analysis_id": "94c25b50",
  "input_type": "image",
  "total_dishes": 2,
  "total_ingredients": 5,
  "processing_time_seconds": 58.34,
  "dishes": [
    {
      "dish_name": "fresh, raw, with cherry tomatoes, cucumber slices, salad dressing",
      "confidence": 0.9,
      "ingredients": [
        {
          "ingredient_name": "mixed greens salad",
          "weight_g": 135.0,
          "calculated_nutrition": {
            "calories": 28.4,
            "protein": 1.8,
            "fat": 0.3,
            "carbs": 4.6
          },
          "source_db": "usda_fndds",
          "fdc_id": "2709792"
        }
      ],
      "total_nutrition": {
        "calories": 28.4,
        "protein": 1.8,
        "fat": 0.3,
        "carbs": 4.6
      }
    }
  ],
  "total_nutrition": {
    "calories": 772.9,
    "protein": 68.2,
    "fat": 34.3,
    "carbs": 48.8
  },
  "ai_model_used": "Qwen/Qwen3-VL-30B-A3B-Thinking",
  "prompt_file_used": "freeform_prompt_usda_format_ver_v7_experimental_20251027.txt",
  "match_rate_percent": 100.0
}
```

完全なレスポンスは `test_result_food1.json` を参照してください。

## USDA食材検索API（Retrieve Endpoint）

食材データベースから直接検索を行うAPIエンドポイント。3つの検索モードをサポートします。

### Fast Mode (FAISS検索のみ、高速)

```bash
curl -X GET "http://localhost:8006/api/v1/retrieve?q=chicken&mode=fast&top_k=5"
```

### Accurate Mode (FAISS + Reranking、高精度)

```bash
curl -X GET "http://localhost:8006/api/v1/retrieve?q=beef&mode=accurate&top_k=5"
```

### Hybrid Mode (BM25 + FAISS、最高精度、デフォルト)

```bash
curl -X GET "http://localhost:8006/api/v1/retrieve?q=rice&mode=hybrid&top_k=5&debug=true"
```

### レスポンス例（Hybrid Mode）

**✨ 新機能: Portions（単位変換情報）** を含むレスポンス:

```json
{
  "query": "chicken",
  "mode": "hybrid",
  "results": [
    {
      "fdc_id": 2706085,
      "name": "Chicken feet",
      "main_name": "Chicken feet",
      "descriptors": "",
      "source": "survey",
      "score": 0.9159824474180568,
      "score_type": "hybrid_score",
      "component_scores": {
        "bm25": 0.9056922034159449,
        "vector": 0.8694238066673279,
        "rrf": 0.03205128205128205
      },
      "nutrition_per_100g": {
        "calories": 215.0,
        "protein": 19.4,
        "fat": 14.6,
        "carbs": 0.2
      },
      "portions": [
        {
          "description": "1 cup",
          "gram_weight": 240.0
        },
        {
          "description": "1 tablespoon",
          "gram_weight": 15.0
        }
      ]
    }
  ],
  "metadata": {
    "total_results": 5,
    "search_time_ms": 376,
    "index_type": "FAISS",
    "algorithm": "BM25+Vector_RRF"
  },
  "status": {
    "success": true,
    "message": "Search completed successfully"
  }
}
```

**Portions（単位変換情報）について:**
- **カバレッジ**: 13,564食材中13,046食材（96.2%）にportions情報あり
- **NULL値**: 518食材（3.8%）は `"portions": null` を返す
- **構造**: 各portionは `description`（単位の説明）と `gram_weight`（グラム変換値）を含む
- **用途**: ユーザーが「1カップ」「大さじ1」などの単位で入力した場合に、自動でグラム換算できる

**Portionsの例:**
```json
"portions": [
  {"description": "1 cup", "gram_weight": 240.0},
  {"description": "1 tablespoon", "gram_weight": 15.0},
  {"description": "1 teaspoon", "gram_weight": 5.0},
  {"description": "1 slice", "gram_weight": 28.0}
]
```

Portions情報がない食材の例:
```json
"portions": null
```

### 検索モード比較

| モード | アルゴリズム | 速度 | 精度 | 用途 |
|--------|--------------|------|------|------|
| **fast** | FAISS Vector検索のみ | 最速 | 標準 | プロトタイプ、リアルタイム検索 |
| **accurate** | FAISS + Qwen3-Reranker | 中速 | 高精度 | 本番環境、高精度重視 |
| **hybrid** | BM25 + Vector + RRF | 中速 | 最高精度 | 本番環境、最高品質（デフォルト） |

### パラメータ

- `q` (必須): 検索クエリ（例: "chicken breast grilled"）
- `mode` (オプション): 検索モード（fast/accurate/hybrid、デフォルト: hybrid）
- `top_k` (オプション): 返却する結果数（1-50、デフォルト: 10）
- `include_nutrition` (オプション): 栄養情報を含めるか（true/false、デフォルト: true）
- `debug` (オプション): デバッグ情報を含めるか（true/false、デフォルト: false）

## USDAメタデータAPI（Metadata Endpoint）

フロントエンドアプリケーション向けに、全13,564食材のメタデータを配信するAPIエンドポイント。食材選択UI、栄養表示、単位変換機能の実装に使用します。

### 概要

**主な特徴:**
- **全件取得**: 13,564食材の完全なメタデータ（栄養情報 + portions情報）
- **効率的な配信**: gzip圧縮により 8.4MB → 0.67MB（92%削減）
- **キャッシュ対応**: 24時間のCache-Controlヘッダー
- **高いportionsカバレッジ**: 96.2%（13,046/13,564）の食材に単位変換情報あり
- **フロントエンド最適化**: ローカルストレージへのキャッシュ推奨

**データソース内訳:**
- Survey Foods: 5,431 食材
- Foundation Foods: 340 食材
- SR Legacy Foods: 7,793 食材

### エンドポイント一覧

#### 1. 全メタデータ取得（推奨）

```bash
# gzip圧縮版（推奨、8.4MB → 0.67MB）
curl -X GET "http://localhost:8006/api/v1/metadata?compressed=true" \
  -H "Accept-Encoding: gzip"

# 非圧縮版（開発時のみ、8.4MB）
curl -X GET "http://localhost:8006/api/v1/metadata?compressed=false"
```

**レスポンス構造:**
```json
[
  {
    "fdc_id": 746774,
    "description": "Chicken, breast, grilled",
    "main_name": "Chicken, breast",
    "descriptors": "grilled",
    "source": "survey",
    "nutrition": {
      "calories": 165.0,
      "protein": 31.0,
      "fat": 3.6,
      "carbs": 0.0
    },
    "portions": [
      {
        "description": "1 breast, bone and skin removed",
        "gram_weight": 86.0
      },
      {
        "description": "1 cup, chopped or diced",
        "gram_weight": 140.0
      }
    ]
  }
]
```

**フロントエンド実装例（JavaScript）:**
```javascript
// 初回ロード時にメタデータ取得
async function loadUSDAMetadata() {
  const cacheKey = 'usda_metadata';
  const cacheTimestamp = localStorage.getItem('usda_metadata_timestamp');
  const now = Date.now();

  // 24時間以内のキャッシュがあれば使用
  if (cacheTimestamp && (now - parseInt(cacheTimestamp)) < 86400000) {
    return JSON.parse(localStorage.getItem(cacheKey));
  }

  // APIから取得（gzip圧縮版）
  const response = await fetch('http://localhost:8006/api/v1/metadata?compressed=true');
  const metadata = await response.json();

  // ローカルストレージにキャッシュ
  localStorage.setItem(cacheKey, JSON.stringify(metadata));
  localStorage.setItem('usda_metadata_timestamp', now.toString());

  return metadata;
}

// 食材検索UIの実装
function searchFoods(query, metadata) {
  return metadata.filter(item =>
    item.description.toLowerCase().includes(query.toLowerCase()) ||
    item.main_name.toLowerCase().includes(query.toLowerCase())
  );
}

// 単位変換機能の実装
function convertToGrams(fdc_id, portionDescription, metadata) {
  const food = metadata.find(item => item.fdc_id === fdc_id);
  if (!food || !food.portions) return null;

  const portion = food.portions.find(p =>
    p.description.toLowerCase() === portionDescription.toLowerCase()
  );

  return portion ? portion.gram_weight : null;
}
```

#### 2. メタデータ情報取得

```bash
curl -X GET "http://localhost:8006/api/v1/metadata/info"
```

**レスポンス例:**
```json
{
  "total_items": 13564,
  "file_size_mb": 8.36,
  "compressed_size_mb": 0.67,
  "compression_ratio": 0.08,
  "sources": {
    "survey": 5431,
    "foundation": 340,
    "sr_legacy": 7793
  },
  "portions_coverage_percent": 96.2,
  "items_with_portions": 13046
}
```

#### 3. メタデータ検索（軽量版）

```bash
# 基本検索
curl -X GET "http://localhost:8006/api/v1/metadata/search?q=chicken&limit=20"

# ソースフィルター付き
curl -X GET "http://localhost:8006/api/v1/metadata/search?q=beef&source=survey&limit=10"

# ページネーション
curl -X GET "http://localhost:8006/api/v1/metadata/search?q=rice&limit=20&offset=20"
```

**レスポンス例:**
```json
{
  "query": "chicken",
  "results": [
    {
      "fdc_id": 746774,
      "description": "Chicken, breast, grilled",
      "main_name": "Chicken, breast",
      "descriptors": "grilled",
      "source": "survey",
      "nutrition": {...},
      "portions": [...]
    }
  ],
  "total": 156,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

**パラメータ:**
- `q` (必須): 検索クエリ
- `limit` (オプション): 返却件数（1-100、デフォルト: 20）
- `offset` (オプション): オフセット（ページネーション用、デフォルト: 0）
- `source` (オプション): データソースフィルター（survey/foundation/sr_legacy）

**注意:** この検索はシンプルな部分一致検索です。高度なセマンティック検索が必要な場合は `/api/v1/retrieve` エンドポイント（Hybrid Mode）を使用してください。

#### 4. FDC ID指定取得

```bash
curl -X GET "http://localhost:8006/api/v1/metadata/746774"
```

**レスポンス例:**
```json
{
  "fdc_id": 746774,
  "description": "Chicken, breast, grilled",
  "main_name": "Chicken, breast",
  "descriptors": "grilled",
  "source": "survey",
  "nutrition": {
    "calories": 165.0,
    "protein": 31.0,
    "fat": 3.6,
    "carbs": 0.0
  },
  "portions": [
    {
      "description": "1 breast, bone and skin removed",
      "gram_weight": 86.0
    }
  ]
}
```

### Portions（単位変換情報）の活用

**カバレッジ:**
- 13,564食材中 13,046食材（96.2%）にportions情報あり
- 518食材（3.8%）は `"portions": null`

**一般的な単位の例:**
- 体積: `1 cup`, `1 tablespoon`, `1 teaspoon`, `1 fluid ounce`
- 数量: `1 slice`, `1 piece`, `1 item`, `1 serving`
- 重量: `1 oz`, `1 lb`（既にグラム換算されている）

**実装例（単位変換機能）:**
```javascript
// "2 cups of rice" → グラム換算
function parseAndConvertToGrams(userInput, metadata) {
  const match = userInput.match(/(\d+\.?\d*)\s*(cup|tablespoon|teaspoon|slice)s?\s+of\s+(.+)/i);
  if (!match) return null;

  const [, quantity, unit, foodName] = match;

  // 食材を検索
  const food = metadata.find(item =>
    item.description.toLowerCase().includes(foodName.toLowerCase())
  );
  if (!food || !food.portions) return null;

  // 単位を検索
  const portion = food.portions.find(p =>
    p.description.toLowerCase().includes(unit.toLowerCase())
  );
  if (!portion) return null;

  // グラム換算
  const grams = parseFloat(quantity) * portion.gram_weight;

  return {
    food: food.description,
    fdc_id: food.fdc_id,
    original_input: userInput,
    quantity: parseFloat(quantity),
    unit: unit,
    grams: grams,
    nutrition: calculateNutrition(food.nutrition, grams)
  };
}

// 実際の栄養計算
function calculateNutrition(nutrition_per_100g, grams) {
  const factor = grams / 100.0;
  return {
    calories: nutrition_per_100g.calories * factor,
    protein: nutrition_per_100g.protein * factor,
    fat: nutrition_per_100g.fat * factor,
    carbs: nutrition_per_100g.carbs * factor
  };
}
```

### デプロイ後のアクセス

Cloud Run本番環境では以下のURLでアクセス可能：
```
https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/api/v1/metadata
https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/api/v1/metadata/info
https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/api/v1/metadata/search?q=chicken
https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/api/v1/metadata/746774
```

### パフォーマンスとキャッシュ戦略

**推奨実装:**
1. **初回ロード時**: `/api/v1/metadata?compressed=true` で全データ取得
2. **ローカルストレージ**: 24時間キャッシュ（localStorage推奨）
3. **検索**: キャッシュされたデータをクライアント側でフィルタリング
4. **リアルタイム検索**: 高度な検索が必要な場合のみ `/api/v1/retrieve` 使用

**データサイズ:**
- 非圧縮: 8.4MB（8,767,812 bytes）
- gzip圧縮: 0.67MB（702,565 bytes）
- 圧縮率: 8%（92%削減）

**レスポンスヘッダー:**
- `Content-Type: application/json`
- `Content-Encoding: gzip`（compressed=trueの場合）
- `Cache-Control: public, max-age=86400`（24時間）
- `X-Original-Size: 8767812`
- `X-Compressed-Size: 702565`

## デプロイ（Cloud Run）- Cloud Storage最適化版

### アーキテクチャ概要

本APIは**Cloud Storage統合**により、大規模データ（221MB）のデプロイコストと時間を大幅に削減しています：

**従来方式（v1-v8）:**
- イメージサイズ: 400MB+（FAISSデータ221MB含む）
- ビルド時間: 約10分
- 月額コスト: $0.08/月

**最適化版（v9以降）:**
- イメージサイズ: 50MB（FAISSデータ除外）
- ビルド時間: 約2分（80%削減）
- 月額コスト: $0.005/月（93%削減）
- 起動時: Cloud Storageから自動ダウンロード（5-10秒）

### 前提条件

#### 1. Cloud Storageバケットの準備（初回のみ）

FAISSデータをCloud Storageにアップロード：

```bash
cd /path/to/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api

# バケットが存在しない場合は作成
gcloud storage buckets create gs://new-snap-calorie-faiss-data --location=us-central1

# FAISSデータをアップロード（221MB、約10秒）
gcloud storage cp -r data/faiss/* gs://new-snap-calorie-faiss-data/faiss/
```

**アップロード内容:**
- `usda_index_full.faiss` (212MB) - ベクトル検索インデックス
- `usda_bm25_index/` (約9MB) - BM25キーワード検索インデックス
- `usda_metadata.json` (8.4MB) - 栄養素メタデータ

#### 2. 環境変数設定

```bash
# DEEPINFRA_API_KEYを環境変数に設定
export DEEPINFRA_API_KEY=your-api-key
```

### デプロイ手順

#### オプション1: デプロイスクリプト実行（推奨）

```bash
cd apps/freeform_usda_meal_analysis_api
bash deploy.sh
```

デプロイスクリプトは以下を自動実行します：
1. Dockerイメージのビルド（data/除外、約2分）
2. Google Container Registryへのプッシュ
3. Cloud Runへのデプロイ（環境変数設定含む）

#### オプション2: 手動デプロイ

```bash
cd /path/to/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api

# 1. イメージビルド（data/はビルドから除外）
gcloud builds submit --tag gcr.io/new-snap-calorie/freeform-usda-meal-analysis-api:v9-cloud-storage-optimized . --timeout=900

# 2. Cloud Runにデプロイ
gcloud run deploy freeform-usda-meal-analysis-api \
  --image gcr.io/new-snap-calorie/freeform-usda-meal-analysis-api:v9-cloud-storage-optimized \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 600 \
  --allow-unauthenticated \
  --set-env-vars="DEEPINFRA_API_KEY=${DEEPINFRA_API_KEY}"
```

### データ更新手順

FAISSインデックスや栄養データを更新した場合：

```bash
cd /path/to/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api

# 1. ローカルでFAISSインデックスを再生成
PYTHONPATH=/path/to/meal_analysis_api_2 \
python scripts/build_index_with_nutrition.py

# 2. Cloud Storageを更新
gcloud storage cp -r data/faiss/* gs://new-snap-calorie-faiss-data/faiss/

# 3. Cloud Runを再デプロイ（または再起動）
gcloud run services update freeform-usda-meal-analysis-api --region us-central1
```

**注意:** Cloud Runインスタンスは起動時にCloud Storageからデータをダウンロードするため、データ更新後は既存のインスタンスを再起動する必要があります。

### 起動時の動作

Cloud Run上でのコンテナ起動シーケンス：

1. **コンテナ起動** (main.py実行)
2. **FAISSデータダウンロード** (`startup_data_loader.py`)
   - Cloud Storage: `gs://new-snap-calorie-faiss-data/faiss/`
   - ダウンロード先: `/tmp/faiss`
   - 並列ダウンロード: 最大10ファイル同時
   - 所要時間: 5-10秒
3. **サービス初期化**
   - HybridSearchEngine初期化
   - Pipeline初期化
4. **API稼働開始**

### トラブルシューティング

#### Cloud Storageからのダウンロード失敗

```bash
# Cloud Runログを確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=freeform-usda-meal-analysis-api" --limit=50 --format=json

# バケットの権限を確認
gcloud storage buckets describe gs://new-snap-calorie-faiss-data
```

#### 古いイメージのクリーンアップ

```bash
# 失敗したデプロイイメージを削除してストレージコスト削減
cd apps/freeform_usda_meal_analysis_api
bash scripts/cleanup_old_images.sh
```

## データ生成方法

### FAISSインデックスと栄養データの生成

このAPIは、USDAの3つのデータソース（Survey, Foundation, SR Legacy）から統合されたFAISSインデックスと栄養データを使用します。

#### 前提条件

1. **USDA JSONファイルの配置**:
   - `usda_database/surveyDownload.json` (Survey Foods)
   - `usda_database/FoodData_Central_foundation_food_json_2025-04-24 2.json` (Foundation Foods)
   - `usda_database/FoodData_Central_sr_legacy_food_json_2018-04 2.json` (SR Legacy Foods)

2. **DeepInfra API Key**: 環境変数に設定
   ```bash
   export DEEPINFRA_API_KEY=your-api-key
   ```

#### ビルドスクリプト実行

```bash
cd /path/to/meal_analysis_api_2

# 完全ビルド（FAISSインデックス + 栄養データ + Portions情報）
PYTHONPATH=/path/to/meal_analysis_api_2 \
python apps/freeform_usda_meal_analysis_api/scripts/build_index_with_nutrition.py

# メタデータのみ更新（Portions情報を追加、FAISSインデックスは再構築しない）
PYTHONPATH=/path/to/meal_analysis_api_2 \
python apps/freeform_usda_meal_analysis_api/scripts/build_index_with_nutrition.py --metadata-only
```

#### 生成される出力

実行が成功すると、`apps/freeform_usda_meal_analysis_api/data/faiss/` ディレクトリに以下のファイルが生成されます:

1. **usda_index_full.faiss** (約212MB)
   - 13,564個の食材のベクトルインデックス
   - Qwen3-Embedding-8B (4096次元) を使用

2. **usda_bm25_index/** (約30MB)
   - BM25キーワード検索インデックス（Hybrid Search用）
   - 13,564ドキュメント

3. **usda_metadata.json** (約5.0MB)
   - 13,564個の食材の栄養素データとportions情報を含むメタデータ
   - 各食材に以下を格納:
     - `fdc_id`: USDA Food Data Central ID
     - `description`: 食材名
     - `nutrition`: 100gあたりの栄養素（calories, protein_g, fat_g, carbs_g）
     - `source`: データソース（survey/foundation/sr_legacy）
     - **`portions`**: 単位変換情報（96.2%の食材で利用可能、ない場合はnull）

**Portions情報の例:**
```json
{
  "fdc_id": 2705704,
  "description": "Cheese, NFS",
  "nutrition": {
    "calories": 402.0,
    "protein_g": 24.9,
    "fat_g": 33.1,
    "carbs_g": 1.3
  },
  "portions": [
    {
      "description": "1 cracker-size slice",
      "gram_weight": 9.0
    },
    {
      "description": "1 cubic inch",
      "gram_weight": 17.3
    }
  ]
}
```

#### ビルドプロセスの詳細

スクリプトは以下の処理を自動実行します:

1. **USDA JSONファイルの読み込み** (全3ファイル)
2. **栄養素データの抽出**
   - 4つの主要栄養素: calories (1008), protein (1003), fat (1004), carbs (1005)
   - 栄養素が空配列の食材は自動除外（例: "Milk, human"）
3. **Portions情報の抽出** (新機能)
   - Survey: `portionDescription` + `gramWeight`
   - Foundation: `measureUnit.name` + `value` + `gramWeight`
   - SR Legacy: `modifier` + `amount` + `gramWeight`
   - カバレッジ: 13,046/13,564食材（96.2%）
4. **埋め込みベクトル生成** (DeepInfra API使用)
   - バッチサイズ: 1024アイテム/リクエスト
   - 全13,564アイテムを14バッチで処理
5. **BM25インデックス構築** (Hybrid Search用)
   - bm25s ライブラリ使用（500倍高速）
   - ステミング: English Stemmer
6. **FAISSインデックス構築**
   - IndexFlatIP (Inner Product) を使用
   - 正規化済みベクトル（コサイン類似度計算用）
7. **データ保存**
   - `usda_index_full.faiss`: ベクトルインデックス
   - `usda_bm25_index/`: BM25インデックス
   - `usda_metadata.json`: 栄養素 + portions統合メタデータ

#### メタデータのみ更新モード（--metadata-only）

既存のFAISSインデックスを維持したまま、portions情報だけを追加・更新する場合:

```bash
cd /path/to/meal_analysis_api_2

# メタデータのみ更新（約3秒で完了）
PYTHONPATH=/path/to/meal_analysis_api_2 \
python apps/freeform_usda_meal_analysis_api/scripts/build_index_with_nutrition.py --metadata-only
```

**メリット:**
- **高速**: 3秒で完了（完全ビルドは5-10分）
- **APIコスト不要**: DeepInfra APIを呼ばない
- **FAISSインデックス不変**: 既存のベクトルインデックスをそのまま使用

#### 生成後のクリーンアップ

生成が完了したら、元のUSDA JSONファイル（270MB）は不要になり、削除できます:

```bash
rm -rf usda_database
```

これにより約303MBのディスク容量を節約できます。

#### ビルド時間とコスト

- **処理時間**: 約5-10分（DeepInfra APIの速度に依存）
- **API コスト**: 約$0.05-0.10（Qwen3-Embedding-8Bの料金）
- **生成頻度**: データ更新時のみ実行（通常は年1-2回）

## 設定可能なパラメータ

### VLMモデル設定
- `model_id`: DeepInfra VLMモデルID
  - デフォルト: `Qwen/Qwen3-VL-30B-A3B-Thinking`
- `prompt_path`: プロンプトファイル名（prompts/以下）
  - デフォルト: `freeform_prompt_usda_format_ver_v7_experimental_20251027.txt`
- `thinking_budget`: 思考トークン数（QVQモデル用、1-32768）
- `temperature`: 生成温度（0.0-2.0）
  - デフォルト: 0.6（Qwen公式推奨値）
- `max_tokens`: 最大トークン数（1-32768）
  - デフォルト: 4096

### 検索設定
- `stage1_top_k`: Stage1で取得する候補数（1-200）
  - デフォルト: 50
  - Fullインデックスのみを使用（軽量化）

## 技術スタック

- **FastAPI**: Python Web フレームワーク
- **FAISS**: Facebook AI Similarity Search
  - Full Index: 13,564 vectors
- **BM25S**: 高速BM25実装（Hybrid Search用）
  - 500x faster than rank-bm25
  - インデックスサイズ: 約 13,564 documents
- **DeepInfra API**: VLM ホスティング
  - **Qwen3-VL-30B-A3B-Thinking** (デフォルト、画像解析)
  - Qwen3-Embedding-8B (埋め込み生成)
  - Qwen3-Reranker-8B (リランキング)
- **Hybrid Search**: BM25 + Vector Semantic Search (2025年ベストプラクティス)
  - RRF (Reciprocal Rank Fusion) による結果統合
  - 重み付け: BM25=0.4, Vector=0.6, RRF k=60
- **USDA FoodData Central**: 栄養素データベース（metadata.json統合版）
  - Survey Foods: 5,431 食材（調理済み・加工食品）
  - Foundation Foods: 340 食材（生鮮食品）
  - SR Legacy Foods: 7,793 食材（レガシーデータ）
  - **合計: 13,564 食材**（栄養素データ内蔵、270MB外部ファイル不要）
  - **Portions情報**: 13,046食材（96.2%）に単位変換データあり

### Self-contained アーキテクチャ

- **独立した実装**: `shared/` ディレクトリへの依存を完全に排除
- **DeepInfraService**: 環境変数から直接設定を取得し、Thinking モデルパラメータを自動最適化
- **栄養データ統合**: FAISS metadata.json に栄養素データを内蔵（5.0MB）
  - 従来の270MB外部JSONファイル依存を削除
  - 303MBのディスク容量削減
- **Portions情報統合**: 単位変換データもmetadata.jsonに統合
  - 96.2%の食材でカップ、スプーン、枚などの単位変換が可能
  - 外部API不要でグラム換算が完結
- **単一ディレクトリデプロイ**: `apps/freeform_usda_meal_analysis_api/` だけでデプロイ可能

### Thinking Model について

Thinking model は推論プロセス（`<think>...</think>`）を含むため、以下の点で Instruct model より優れています：
- **高精度な食材認識**: 料理名、調理法、食材の種類をより正確に識別
- **重量推定の改善**: 視覚的な情報から重量をより適切に推定
- **曖昧性の解消**: "chicken"（生/調理済み）等の曖昧なケースを推論で解決

### 検索の最適化

- **2段階検索**: FAISS embedding search → Qwen3-Reranker-8B reranking
- **高精度マッチング**: 13,565 食材から最適な候補を検索
- **柔軟な設定**: `stage1_top_k` パラメータで候補数を調整可能

### 単位変換機能（Portions）

**新機能:** 食材ごとの利用可能な単位と重量変換情報を提供

- **カバレッジ**: 96.2%の食材（13,046/13,564）
- **利用可能な単位例**:
  - 体積: カップ (cup), 大さじ (tablespoon), 小さじ (teaspoon)
  - 個数: 枚 (slice), 個 (piece), 本 (stick)
  - その他: serving, portion, ounce等
- **自動グラム換算**: APIレスポンスの `gram_weight` で変換
- **NULL処理**: 単位情報がない食材は `"portions": null` を返却

**活用例:**
1. ユーザーが「チーズ 1枚」と入力
2. APIが該当食材を検索し、portionsから「1 slice = 28g」を取得
3. 28gの栄養価を自動計算
