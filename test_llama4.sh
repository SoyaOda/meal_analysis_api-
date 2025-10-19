#!/bin/bash

MODEL="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
IMAGES=("food1" "food2" "food3" "food4" "food5")
API_URL="http://localhost:8005/api/v1/meal-analyses/complete"
OUTPUT_DIR="/tmp/llama4_test_results"

mkdir -p "$OUTPUT_DIR"

echo "==================================="
echo "🦙 Llama-4 テスト開始"
echo "==================================="
echo ""

# プロセスクリーンアップ
echo "既存プロセスをクリーンアップ中..."
lsof -ti:8004,8005 | xargs kill -9 2>/dev/null
sleep 2

# Word Query API起動
echo "Word Query APIを起動中（ポート8004）..."
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
PORT=8004 \
python -m apps.usda_word_query_api.main > /tmp/word_query_api_llama4.log 2>&1 &

sleep 8

if ! curl -s http://localhost:8004/health > /dev/null 2>&1; then
  echo "❌ Word Query APIの起動に失敗"
  exit 1
fi
echo "✅ Word Query API起動完了"
echo ""

# Llama-4でMeal Analysis API起動
echo "🦙 Llama-4 Meal Analysis API起動中（ポート8005）..."
DEEPINFRA_MODEL_ID="$MODEL" \
WORD_QUERY_API_URL=http://localhost:8004 \
INGREDIENT_ELASTICSEARCH_INDEX=usda_unified_nutrition_db \
NUTRITION_DATA_SOURCE=usda_api \
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
GOOGLE_CLOUD_PROJECT=new-snap-calorie \
PORT=8005 \
python -m apps.usda_meal_analysis_api.main > "/tmp/llama4_api.log" 2>&1 &

sleep 10

if ! curl -s http://localhost:8005/health > /dev/null 2>&1; then
  echo "❌ Meal Analysis APIの起動に失敗"
  exit 1
fi

echo "✅ Llama-4 API起動完了"
echo ""

# 各画像をテスト
for img in "${IMAGES[@]}"; do
  echo "  処理中: $img.jpg"
  output_file="$OUTPUT_DIR/Llama-4_${img}.json"

  curl -s -X POST "$API_URL" \
    -F "image=@test_images/${img}.jpg" \
    -F "user_context=Llama-4 test" \
    > "$output_file"

  if [ $? -eq 0 ] && [ -s "$output_file" ]; then
    if grep -q '"detail".*"failed"' "$output_file"; then
      echo "    ❌ APIエラー"
    else
      echo "    ✅ 完了"
    fi
  else
    echo "    ❌ リクエストエラー"
  fi

  sleep 2
done

echo ""
echo "==================================="
echo "🦙 Llama-4 テスト完了"
echo "結果: $OUTPUT_DIR"
echo "==================================="
