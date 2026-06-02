# API Quickstart（起動コマンド & エンドポイント例）

各 API の起動方法と代表的な呼び出し例。全コマンドは `PYTHONPATH=/Users/odasoya/meal_analysis_api_2` 前提。詳細は各アプリの `README.md` を参照。

## サーバー起動

### Word Query API (8002)
```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8002 python -m apps.word_query_api.main
```

### Meal Analysis API (8001)
```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 GOOGLE_CLOUD_PROJECT=new-snap-calorie PORT=8001 python -m apps.meal_analysis_api.main
```

### Barcode API (8003)
```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8003 python -m apps.barcode_api.main
```

### USDA Word Query API (8004)
```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8004 python -m apps.usda_word_query_api.main
```

### USDA Meal Analysis API (8005)
```bash
# USDA Word Query API (8004) の起動が必須
WORD_QUERY_API_URL=http://localhost:8004 \
INGREDIENT_ELASTICSEARCH_INDEX=usda_unified_nutrition_db \
NUTRITION_DATA_SOURCE=usda_api \
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
GOOGLE_CLOUD_PROJECT=new-snap-calorie \
PORT=8005 \
python -m apps.usda_meal_analysis_api.main
```

### Freeform USDA Meal Analysis API (8006)
```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8006 python -m apps.freeform_usda_meal_analysis_api.main
```

## エンドポイント例

### Meal Analysis API (http://localhost:8001)
```bash
# 音声入力
curl -X POST "http://localhost:8001/api/v1/meal-analyses/voice" \
  -F "audio_file=@test-audio/lunch_detailed.wav" \
  -F "user_context=lunch analysis"

# 画像入力
curl -X POST "http://localhost:8001/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=dinner analysis"
```

### Barcode API (http://localhost:8003)
```bash
curl -X POST "http://localhost:8003/api/v1/barcode/lookup" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "000000016872"}'

curl -X GET "http://localhost:8003/api/v1/barcode/cache-stats"
curl -X DELETE "http://localhost:8003/api/v1/barcode/cache"
```

### USDA Word Query API (http://localhost:8004)
```bash
curl -X GET "http://localhost:8004/api/v1/usda/suggest?q=chicken&limit=5"
curl -X GET "http://localhost:8004/health"
```

### USDA Meal Analysis API (http://localhost:8005)
```bash
curl -X POST "http://localhost:8005/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=USDA analysis"

curl -X POST "http://localhost:8005/api/v1/meal-analyses/voice" \
  -F "audio_file=@test-audio/lunch_detailed.wav" \
  -F "user_context=USDA lunch analysis"

curl -X GET "http://localhost:8005/health"
```

### Freeform USDA Meal Analysis API (http://localhost:8006)
```bash
curl -X POST "http://localhost:8006/api/v1/meal-analyses/complete" \
  -F "image=@apps/freeform_usda_meal_analysis_api/test_images/food1.jpg" \
  -F "user_context=freeform analysis"
```

## Apps 一覧
- `apps/word_query_api` — MyNetDiary版 単語検索
- `apps/meal_analysis_api` — MyNetDiary版 食事分析
- `apps/barcode_api` — バーコード検索
- `apps/usda_word_query_api` — USDA FNDDS版 単語検索
- `apps/usda_meal_analysis_api` — USDA FNDDS版 食事分析
- `apps/freeform_usda_meal_analysis_api` — USDA版 自由形式・写真カロリー推定（PDCA運用あり）
