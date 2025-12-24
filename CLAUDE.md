# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

必ず serena MCP が日本語で対応すること！
日本語で応答すること！

### 3. API サーバーの起動

#### Word Query API (ポート 8002)

```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8002 python -m apps.word_query_api.main
```

#### Meal Analysis API (ポート 8001)

```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 GOOGLE_CLOUD_PROJECT=new-snap-calorie PORT=8001 python -m apps.meal_analysis_api.main
```

#### Barcode API (ポート 8003)

```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8003 python -m apps.barcode_api.main
```

#### USDA Word Query API (ポート 8004)

```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8004 python -m apps.usda_word_query_api.main
```

#### USDA Meal Analysis API (ポート 8005)

```bash
# USDA Word Query APIが起動していることが必須（ポート8004）
WORD_QUERY_API_URL=http://localhost:8004 \
INGREDIENT_ELASTICSEARCH_INDEX=usda_unified_nutrition_db \
NUTRITION_DATA_SOURCE=usda_api \
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
GOOGLE_CLOUD_PROJECT=new-snap-calorie \
PORT=8005 \
python -m apps.usda_meal_analysis_api.main
```

## 📚 API エンドポイント

### Meal Analysis API (http://localhost:8001)

#### 音声入力による食事分析

```bash
curl -X POST "http://localhost:8001/api/v1/meal-analyses/voice" \
  -F "audio_file=@test-audio/lunch_detailed.wav" \
  -F "user_context=lunch analysis"
```

#### 画像入力による食事分析

```bash
curl -X POST "http://localhost:8001/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=dinner analysis"
```

### Barcode API (http://localhost:8003)

#### バーコード検索

```bash
curl -X POST "http://localhost:8003/api/v1/barcode/lookup" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "000000016872"}'
```

#### キャッシュ統計確認

```bash
curl -X GET "http://localhost:8003/api/v1/barcode/cache-stats"
```

#### キャッシュクリア

```bash
curl -X DELETE "http://localhost:8003/api/v1/barcode/cache"
```

### USDA Word Query API (http://localhost:8004)

#### 食材検索

```bash
curl -X GET "http://localhost:8004/api/v1/usda/suggest?q=chicken&limit=5"
```

#### ヘルスチェック

```bash
curl -X GET "http://localhost:8004/health"
```

### USDA Meal Analysis API (http://localhost:8005)

#### 画像入力による食事分析（USDA版）

```bash
curl -X POST "http://localhost:8005/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=USDA analysis"
```

#### 音声入力による食事分析（USDA版）

```bash
curl -X POST "http://localhost:8005/api/v1/meal-analyses/voice" \
  -F "audio_file=@test-audio/lunch_detailed.wav" \
  -F "user_context=USDA lunch analysis"
```

#### ヘルスチェック

```bash
curl -X GET "http://localhost:8005/health"
```

[Instruction]
apps に 5 つの API が実装されている。詳細を各 README.md を見て理解すること。
- apps/word_query_api (MyNetDiary版)
- apps/meal_analysis_api (MyNetDiary版)
- apps/barcode_api
- apps/usda_word_query_api (USDA FNDDS版)
- apps/usda_meal_analysis_api (USDA FNDDS版)

[命令]

[実装の上でのポイント]
・一度に複数の Script を実装しないこと。Script ごとに機能の Test をして実装した内容がきちんと動くことを確認して次の機能の実装に移ること。
・・Fallbackのような実装はせずきちんとエラーを出して止めるように実装すること
・こちらで作業する必要がある部分や必要な情報があれば、その都度どのようにしたらいいか教えて。
・修正したらpython -m py_compileで構文エラーは確かめてね
