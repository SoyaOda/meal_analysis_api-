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

[Instruction]
apps に 2 つの API が実装されている。詳細を README.md を見て理解すること。

[命令]

[実装の上でのポイント]
・一度に複数の Script を実装しないこと。Script ごとに機能の Test をして実装した内容がきちんと動くことを確認して次の機能の実装に移ること。
・こちらで作業する必要がある部分や必要な情報があれば、その都度どのようにしたらいいか教えて。
