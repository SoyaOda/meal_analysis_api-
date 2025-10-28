# Freeform USDA Meal Analysis API

VLM (Vision Language Model) による画像解析から、USDA FoodData Centralデータベースを用いた栄養素計算までのEnd-to-Endパイプライン。

**Self-contained設計**: `shared/` ディレクトリへの依存を完全に排除し、単一ディレクトリで完結するアーキテクチャ。

**柔軟な設定**: API呼び出し時にVLMモデル、プロンプト、検索パラメータをカスタマイズ可能。

**完全な栄養計算**: USDA FoodData Central の3つのデータソース（Survey, Foundation, SR Legacy）から13,564食材の栄養データを使用。

**単位変換サポート**: 食材ごとの利用可能な単位（カップ、スプーン、枚など）と重量変換情報を提供（96.2%カバレッジ）。

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
├── Dockerfile                 # Docker設定
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
│   └── health.py              # ヘルスチェック
├── data/                      # データディレクトリ（self-contained）
│   └── faiss/                 # FAISS インデックスと栄養データ
│       ├── usda_index_full.faiss        # ベクトル検索インデックス（13,564 vectors）
│       ├── usda_bm25_index/             # BM25インデックス（Hybrid Search用）
│       └── usda_metadata.json           # 栄養素データ統合版（5.0MB、13,564 foods、portions情報含む）
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

## デプロイ（Cloud Run）

### 前提条件

```bash
# DEEPINFRA_API_KEYを環境変数に設定
export DEEPINFRA_API_KEY=your-api-key
```

### デプロイスクリプト実行

```bash
cd apps/freeform_usda_meal_analysis_api
bash deploy.sh
```

デプロイスクリプトは以下を自動実行します：
1. Dockerイメージのビルド（USDA Full Index 212MB含む）
2. Google Container Registryへのプッシュ
3. Cloud Runへのデプロイ（環境変数設定含む）

### 手動デプロイ

```bash
# イメージビルド（USDA data含む）
gcloud builds submit --tag gcr.io/new-snap-calorie/freeform-usda-meal-analysis-api:latest \
  -f apps/freeform_usda_meal_analysis_api/Dockerfile .

# Cloud Runにデプロイ
gcloud run deploy freeform-usda-meal-analysis-api \
  --image gcr.io/new-snap-calorie/freeform-usda-meal-analysis-api:latest \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 600 \
  --allow-unauthenticated \
  --set-env-vars="DEEPINFRA_API_KEY=${DEEPINFRA_API_KEY}"
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
  - デフォルト: 0.7
- `max_tokens`: 最大トークン数（1-32768）
  - デフォルト: 4096

### 検索設定
- `stage1_top_k`: Stage1で取得する候補数（1-200）
  - デフォルト: 40
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
