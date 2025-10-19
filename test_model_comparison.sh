#!/bin/bash

# 3つのモデルでfood1〜food5をテストして比較
# Usage: ./test_model_comparison.sh

MODELS=(
  "Qwen/Qwen3-VL-4B-Instruct"
  "google/gemma-3-27b-it"
  "mistralai/Mistral-Small-3.2-24B-Instruct-2506"
)

IMAGES=("food1" "food2" "food3" "food4" "food5")
API_URL="http://localhost:8005/api/v1/meal-analyses/complete"
OUTPUT_DIR="/tmp/model_comparison_results"

# 出力ディレクトリを作成
mkdir -p "$OUTPUT_DIR"

echo "==================================="
echo "モデル比較テスト開始"
echo "==================================="
echo ""

# 既存のプロセスをクリーンアップ
echo "既存のプロセスをクリーンアップ中..."
lsof -ti:8004,8005 | xargs kill -9 2>/dev/null
sleep 2

# Word Query APIを起動（テスト全体で1度だけ）
echo "Word Query APIを起動中（ポート8004）..."
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
PORT=8004 \
python -m apps.usda_word_query_api.main > /tmp/word_query_api.log 2>&1 &

WORD_QUERY_PID=$!
echo "Word Query API PID: $WORD_QUERY_PID"
sleep 8

# Word Query APIが起動したか確認
if ! curl -s http://localhost:8004/health > /dev/null 2>&1; then
  echo "❌ Word Query APIの起動に失敗しました"
  exit 1
fi
echo "✅ Word Query API起動完了"
echo ""

# 各モデルでテスト
for model in "${MODELS[@]}"; do
  model_name=$(basename "$model")
  echo "--- モデル: $model_name ---"

  # 既存のMeal Analysis APIを停止（ポート8005のみ）
  echo "Meal Analysis APIを再起動中..."
  lsof -ti:8005 | xargs kill -9 2>/dev/null
  sleep 2

  # 新しいモデルでMeal Analysis APIを起動
  DEEPINFRA_MODEL_ID="$model" \
  WORD_QUERY_API_URL=http://localhost:8004 \
  INGREDIENT_ELASTICSEARCH_INDEX=usda_unified_nutrition_db \
  NUTRITION_DATA_SOURCE=usda_api \
  PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
  GOOGLE_CLOUD_PROJECT=new-snap-calorie \
  PORT=8005 \
  python -m apps.usda_meal_analysis_api.main > "/tmp/meal_analysis_${model_name}.log" 2>&1 &

  MEAL_API_PID=$!
  echo "Meal Analysis API PID: $MEAL_API_PID"
  sleep 10

  # Meal Analysis APIが起動したか確認
  if ! curl -s http://localhost:8005/health > /dev/null 2>&1; then
    echo "❌ Meal Analysis APIの起動に失敗しました"
    continue
  fi

  # 各画像をテスト
  for img in "${IMAGES[@]}"; do
    echo "  処理中: $img.jpg"
    output_file="$OUTPUT_DIR/${model_name}_${img}.json"

    curl -s -X POST "$API_URL" \
      -F "image=@test_images/${img}.jpg" \
      -F "user_context=model comparison test" \
      > "$output_file"

    if [ $? -eq 0 ] && [ -s "$output_file" ]; then
      # エラーレスポンスかチェック
      if grep -q '"detail".*"failed"' "$output_file"; then
        echo "    ❌ APIエラー"
      else
        echo "    ✅ 完了"
      fi
    else
      echo "    ❌ リクエストエラー"
    fi

    # APIに負荷をかけすぎないよう待機
    sleep 2
  done

  echo ""
done

# クリーンアップ
echo "==================================="
echo "全テスト完了 - クリーンアップ中..."
lsof -ti:8004,8005 | xargs kill -9 2>/dev/null
echo "結果ディレクトリ: $OUTPUT_DIR"
echo "==================================="
