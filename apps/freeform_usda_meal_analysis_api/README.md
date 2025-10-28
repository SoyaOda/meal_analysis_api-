# Freeform USDA Meal Analysis API

VLM (Vision Language Model) による画像解析から、USDA FoodData Centralデータベースを用いた栄養素計算までのEnd-to-Endパイプライン。

**柔軟な設定**: API呼び出し時にVLMモデル、プロンプト、検索パラメータをカスタマイズ可能。

**軽量設計**: FAISSのFullインデックス（212MB）のみを使用し、デプロイを最適化。

## アーキテクチャ

```
画像入力 → VLM解析 → クエリ抽出 → USDA検索（Full Index） → 栄養素計算 → 結果出力
```

### 主要コンポーネント

1. **VLMService**: DeepInfraのVLMモデルを使用した画像解析
   - **デフォルトモデル**: `Qwen/Qwen3-VL-30B-A3B-Thinking` (30Bパラメータ)
   - **デフォルトプロンプト**: `v7_experimental`
   - API呼び出し時にモデルとプロンプトを動的に変更可能
2. **QueryExtractionService**: VLMレスポンスから検索クエリを抽出
3. **SimplifiedUSDASearcher**: FAISS Full Indexを使用した軽量な食材検索
   - Fullインデックスのみ使用（212MB）
   - 2段階検索: FAISS embedding search → Qwen3 reranking
4. **LocalUSDANutritionService**: ローカルUSDA JSONファイルから栄養素データをロード
5. **NutritionCalculator**: 100gあたりの栄養素から実重量の栄養素を計算

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
│   └── health.py              # ヘルスチェック
├── prompts/
│   ├── freeform_prompt_usda_format_ver_v7_experimental_20251027.txt  # デフォルト
│   ├── freeform_prompt_usda_format_ver_v7_production_20251027.txt
│   └── ...                    # その他のプロンプトバージョン
└── services/
    ├── __init__.py
    ├── vlm_service.py         # VLM画像解析
    ├── query_extraction.py    # クエリ抽出
    ├── food_search_service.py # USDA検索
    ├── nutrition_service.py   # 栄養素計算
    └── pipeline.py            # End-to-End統合
```

## 環境変数

```bash
# 必須
DEEPINFRA_API_KEY=<your-api-key>
GOOGLE_CLOUD_PROJECT=new-snap-calorie

# オプション
PORT=8005
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

```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
GOOGLE_CLOUD_PROJECT=new-snap-calorie \
PORT=8006 \
python -m apps.freeform_usda_meal_analysis_api.main
```

起動後、以下のURLでアクセス可能:
- **Swagger UI**: http://localhost:8006/docs
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

```json
{
  "dishes": [
    {
      "main_food": {
        "search_name": "chicken",
        "description": "grilled",
        "weight_g": 150,
        "confidence": 0.9,
        "fdc_id": 2706189,
        "matched_description": "Chicken, grilled",
        "nutrition": {
          "weight_g": 150,
          "calories": 246.0,
          "protein_g": 27.3,
          "fat_g": 14.1,
          "carbs_g": 0.0
        }
      },
      "extras": [...]
    }
  ],
  "total_nutrition": {
    "calories": 638.0,
    "protein_g": 42.2,
    "fat_g": 46.0,
    "carbs_g": 12.9
  }
}
```

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

- **FastAPI**: Python Webフレームワーク
- **FAISS**: Facebook AI Similarity Search (Full Index: 212MB)
- **DeepInfra API**: VLMホスティング
  - **Qwen3-VL-30B-A3B-Thinking** (デフォルト、画像解析)
  - BGE-M3 (埋め込み生成)
  - Qwen3-Reranker-8B (リランキング)
- **USDA FoodData Central**: 栄養素データベース（5,772食材）

### Thinking Model について

Thinking modelは推論プロセス（`<think>...</think>`）を含むため、以下の点でInstruct modelより優れています：
- **高精度な食材認識**: 料理名、調理法、食材の種類をより正確に識別
- **重量推定の改善**: 視覚的な情報から重量をより適切に推定
- **曖昧性の解消**: "chicken"（生/調理済み）等の曖昧なケースを推論で解決

### 軽量設計

- **Fullインデックスのみ**: 212MBのFAISSインデックス1つのみでデプロイ
- **コンテナ埋め込み**: インデックスデータをDockerイメージに含めることで起動を高速化
- **最適化された検索**: 2段階検索（FAISS → Reranker）で高精度を維持
