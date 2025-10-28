# Freeform USDA Meal Analysis API

VLM (Vision Language Model) による画像解析から、USDA FoodData Centralデータベースを用いた栄養素計算までのEnd-to-Endパイプライン。

## アーキテクチャ

```
画像入力 → VLM解析 → クエリ抽出 → USDA検索 → 栄養素計算 → 結果出力
```

### 主要コンポーネント

1. **VLMService**: DeepInfraのVLMモデル（**Qwen3-VL-235B-Thinking**）を使用した画像解析
   - **デフォルトモデル**: `Qwen/Qwen3-VL-235B-A22B-Thinking`
   - Thinking modelは推論プロセスを含むため、Instruct modelより高精度
2. **QueryExtractionService**: VLMレスポンスから検索クエリを抽出
3. **FoodSearchService**: FAISS vector searchによるUSDA食材検索
4. **LocalUSDANutritionService**: ローカルUSDA JSONファイルから栄養素データをロード
5. **NutritionCalculator**: 100gあたりの栄養素から実重量の栄養素を計算

## ディレクトリ構成

```
apps/freeform_usda_meal_analysis_api/
├── README.md
├── __init__.py
├── main.py                    # FastAPI アプリケーション
├── prompts/
│   └── freeform_prompt_usda_format_ver.txt  # VLMプロンプト
├── services/
│   ├── __init__.py
│   ├── vlm_service.py         # VLM画像解析
│   ├── query_extraction.py    # クエリ抽出
│   ├── food_search_service.py # USDA検索
│   ├── nutrition_service.py   # 栄養素計算
│   └── pipeline.py            # End-to-End統合
├── endpoints/
│   ├── __init__.py
│   └── meal_analysis.py       # APIエンドポイント
└── models/
    ├── __init__.py
    └── meal_analysis_models.py # Pydanticモデル
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

デフォルトでは **Qwen/Qwen3-VL-235B-A22B-Thinking** を使用します。

利用可能なThinking models:
- `Qwen/Qwen3-VL-235B-A22B-Thinking` (デフォルト、最高精度)
- `Qwen/Qwen3-VL-30B-A3B-Thinking` (バランス型、低コスト)
- `Qwen/Qwen3-VL-8B-Thinking` (軽量、最安)

⚠️ **Instructモデルは非推奨**: Thinking modelより精度が低いため、使用しないでください。

カスタムモデルを指定する場合は、コード内で明示的に指定:
```python
from apps.freeform_usda_meal_analysis_api.services.vlm_service import VLMService

# 30B Thinking modelを使用
vlm_service = VLMService(model_id="Qwen/Qwen3-VL-30B-A3B-Thinking")
```

## ローカル起動

```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
GOOGLE_CLOUD_PROJECT=new-snap-calorie \
PORT=8005 \
python -m apps.freeform_usda_meal_analysis_api.main
```

## API使用例

### 画像から食事分析

```bash
curl -X POST "http://localhost:8005/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=dinner analysis"
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

### コンテナビルド

```bash
# イメージビルド（USDA data含む）
gcloud builds submit --tag gcr.io/new-snap-calorie/freeform-usda-meal-api:latest .

# Cloud Runにデプロイ
gcloud run deploy freeform-usda-meal-api \
  --image gcr.io/new-snap-calorie/freeform-usda-meal-api:latest \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 600 \
  --allow-unauthenticated
```

## 技術スタック

- **FastAPI**: Python Webフレームワーク
- **FAISS**: Facebook AI Similarity Search (ベクトル検索)
- **DeepInfra API**: VLMホスティング
  - **Qwen3-VL-235B-A22B-Thinking** (画像解析、Thinking model)
  - Qwen3-Embedding-8B (埋め込み生成)
  - Qwen3-Reranker-8B (リランキング)
- **USDA FoodData Central**: 栄養素データベース（5,772食材）

### Thinking Model について

Thinking modelは推論プロセス（`<think>...</think>`）を含むため、以下の点でInstruct modelより優れています：
- **高精度な食材認識**: 料理名、調理法、食材の種類をより正確に識別
- **重量推定の改善**: 視覚的な情報から重量をより適切に推定
- **曖昧性の解消**: "chicken"（生/調理済み）等の曖昧なケースを推論で解決

**推奨設定**:
- 本番環境: `Qwen3-VL-235B-A22B-Thinking` (最高精度)
- 開発/テスト: `Qwen3-VL-30B-A3B-Thinking` (コストとバランス)
- 大量バッチ処理: `Qwen3-VL-8B-Thinking` (低コスト)
