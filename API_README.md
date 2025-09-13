# 食事分析API (Meal Analysis API) v2.0

Deep Infra AI とElasticsearchを活用した高精度な食事画像分析システム

## 📋 概要

このAPIは食事の画像を解析し、料理の識別、食材の特定、重量推定、栄養価計算を行います。

### 🔧 技術スタック
- **AI分析**: Deep Infra (Qwen2.5-VL-32B-Instruct / Gemma 3)
- **栄養データベース**: Elasticsearch + MyNetDiary統合DB (1,142件)
- **API Framework**: FastAPI + Pydantic
- **デプロイ**: Google Cloud Run + GCP Compute Engine VM

### 🌟 主な機能
- 複数料理の同時識別
- 食材重量の自動推定
- 高精度栄養価計算
- model_id外部指定対応
- 詳細分析ログ保存

## 🚀 APIエンドポイント

### Base URL
- **本番環境**: `https://meal-analysis-api-1077966746907.us-central1.run.app`
- **ローカル**: `http://localhost:8000`

### 主要エンドポイント

#### POST `/api/v1/meal-analyses/complete`
完全な食事分析を実行

**パラメーター:**
- `image` (必須): 分析対象の画像ファイル
- `model_id` (オプション): Deep Infra Model ID 
  - デフォルト: `Qwen/Qwen2.5-VL-32B-Instruct`
  - 選択可能: `google/gemma-3-27b-it`
- `optional_text` (オプション): AIへのテキストプロンプト
- `save_detailed_logs` (オプション): 詳細ログ保存 (デフォルト: true)

**サポート画像形式:**
- JPEG (.jpg, .jpeg)
- PNG (.png) 
- WebP (.webp)
- BMP (.bmp)
- TIFF (.tiff)

#### GET `/health`
ヘルスチェック

#### GET `/docs`
Swagger UI API仕様書

## 📊 パフォーマンス指標

### 本番環境 (Cloud Run + VM Elasticsearch)
- **処理時間**: 約9.8秒
- **栄養マッチング率**: 88.9% (8/9)
- **AI分析精度**: 95%信頼度
- **データベース**: 1,142件の栄養データ

### ローカル環境
- **処理時間**: 約11秒  
- **栄養マッチング率**: 100% (10/10)
- **データベース**: 同じ1,142件

## 🔥 使用例

### cURL
```bash
# 基本的な分析
curl -X POST "https://meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/complete" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food1.jpg"

# モデル指定
curl -X POST "https://meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/complete" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food1.jpg" \
  -F "model_id=google/gemma-3-27b-it" \
  -F "optional_text=この料理の栄養成分を詳しく分析してください"
```

### Python
```python
import requests

url = "https://meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/complete"

with open("test_images/food1.jpg", "rb") as f:
    files = {"image": f}
    data = {
        "model_id": "Qwen/Qwen2.5-VL-32B-Instruct",
        "optional_text": "食事の画像です",
        "save_detailed_logs": True
    }
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
    
print(f"総カロリー: {result['final_nutrition_result']['total_nutrition']['calories']:.1f} kcal")
print(f"処理時間: {result['processing_summary']['processing_time_seconds']:.1f}秒")
```

## 📈 レスポンス例

```json
{
  "analysis_id": "f1f92d07",
  "phase1_result": {
    "dishes": [
      {
        "dish_name": "Pasta with Tomato and Cheese",
        "confidence": 0.95,
        "ingredients": [
          {
            "ingredient_name": "pasta penne cooked",
            "weight_g": 250.0
          },
          {
            "ingredient_name": "tomatoes, chopped", 
            "weight_g": 50.0
          }
        ]
      }
    ]
  },
  "processing_summary": {
    "total_dishes": 2,
    "total_ingredients": 9,
    "nutrition_search_match_rate": "8/9 (88.9%)",
    "total_calories": 820.78,
    "processing_time_seconds": 9.85
  },
  "final_nutrition_result": {
    "total_nutrition": {
      "calories": 820.78,
      "protein": 26.26,
      "fat": 32.13,
      "carbs": 106.52
    }
  }
}
```

## 🔧 開発・デプロイ情報

### 環境変数
```bash
# Deep Infra API設定
DEEPINFRA_API_KEY=your_api_key_here
DEEPINFRA_MODEL_ID=Qwen/Qwen2.5-VL-32B-Instruct
DEEPINFRA_BASE_URL=https://api.deepinfra.com/v1/openai

# Elasticsearch設定  
USE_ELASTICSEARCH_SEARCH=true
elasticsearch_url=http://35.193.16.212:9200
elasticsearch_index_name=mynetdiary_list_support_db

# API設定
API_LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### ローカル実行
```bash
# 依存関係インストール
pip install -r requirements.txt

# API起動
python -m app_v2.main.app

# テスト実行
python test_single_image_analysis.py
```

### Cloud Run デプロイ
```bash
# ビルド & デプロイ
gcloud builds submit --tag gcr.io/new-snap-calorie/meal-analysis-api:latest .
gcloud run deploy meal-analysis-api \
  --image gcr.io/new-snap-calorie/meal-analysis-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 900s
```

## 🐛 トラブルシューティング

### よくある問題
1. **画像アップロードエラー**: サポートされている形式 (JPEG, PNG等) を使用
2. **タイムアウト**: 大きな画像は圧縮してから送信
3. **栄養データ不一致**: Elasticsearch接続状況を確認

### エラーコード
- `INVALID_IMAGE_FORMAT`: 無効な画像形式
- `FILE_TOO_LARGE`: ファイルサイズ超過 (最大10MB)
- `ANALYSIS_ERROR`: AI分析処理エラー
- `INTERNAL_SERVER_ERROR`: 内部サーバーエラー

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/your-org/meal-analysis-api/issues)
- **Documentation**: `/docs` エンドポイント
- **Status**: `/health` エンドポイント

## 📄 ライセンス

MIT License

---

**最終更新**: 2025-09-12  
**バージョン**: v2.0  
**API URL**: https://meal-analysis-api-1077966746907.us-central1.run.app