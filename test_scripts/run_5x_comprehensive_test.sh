#!/bin/bash

# 6つのプロンプトで50画像×5回テストを実行するスクリプト
# プロンプト: v6_corrected, v6_balanced, v7_experimental, v5_streamlined, v7_production, v6_enhanced

# デフォルト値
BATCH_SIZE=${1:-5}  # 第1引数、デフォルトは5
NUM_IMAGES=${2:-50}  # 第2引数、デフォルトは50
NUM_RUNS=${3:-5}    # 第3引数、デフォルトは5
MODEL_ID=${4:-""}  # 第4引数、デフォルトは空（デフォルトモデル使用）

echo "=================================================="
echo "🚀 6プロンプト × ${NUM_IMAGES}画像 × ${NUM_RUNS}回 包括的テスト開始"
echo "=================================================="
echo ""
echo "設定:"
echo "  - バッチサイズ（並列度）: $BATCH_SIZE"
echo "  - 画像数: $NUM_IMAGES"
echo "  - 実行回数: $NUM_RUNS"
if [ -n "$MODEL_ID" ]; then
    echo "  - VLMモデル: $MODEL_ID"
else
    echo "  - VLMモデル: デフォルト (Qwen/Qwen3-VL-235B-A22B-Thinking)"
fi
echo ""
echo "テストプロンプト:"
echo "  - v6_corrected (最良: 22.0%誤差率)"
echo "  - v6_balanced"
echo "  - v7_experimental"
echo "  - v5_streamlined"
echo "  - v7_production"
echo "  - v6_enhanced"
echo ""

# 推定時間の計算（概算）
estimated_time_per_image=$((360 / BATCH_SIZE))  # 1画像あたり約6分、並列度で割る
estimated_time_per_run=$((NUM_IMAGES * estimated_time_per_image / 60))
estimated_total_time=$((estimated_time_per_run * NUM_RUNS))

echo "推定時間:"
echo "  - 1ラン: 約${estimated_time_per_run}分"
echo "  - 合計: 約${estimated_total_time}分 ($(($estimated_total_time / 60))時間$(($estimated_total_time % 60))分)"
echo ""

# 確認プロンプト
read -p "実行しますか？ (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "キャンセルしました"
    exit 1
fi

# タイムスタンプ取得
timestamp=$(date +%Y%m%d_%H%M%S)

# ログディレクトリ作成
log_dir="test_scripts/logs/comprehensive_test_${timestamp}_batch${BATCH_SIZE}"
mkdir -p "$log_dir"

echo ""
echo "ログディレクトリ: $log_dir"
echo ""

# 設定をファイルに保存
cat > "$log_dir/config.txt" << EOF
Test Configuration
==================
Batch Size: $BATCH_SIZE
Number of Images: $NUM_IMAGES
Number of Runs: $NUM_RUNS
Model ID: ${MODEL_ID:-"Default (Qwen/Qwen3-VL-235B-A22B-Thinking)"}
Start Time: $(date)
Prompts: v6_corrected, v6_balanced, v7_experimental, v5_streamlined, v7_production, v6_enhanced
EOF

# 実行開始時刻を記録
start_time=$(date +%s)

# 指定回数実行
for run in $(seq 1 $NUM_RUNS); do
    echo ""
    echo "=================================================="
    echo "📊 Run $run/$NUM_RUNS 開始 - $(date)"
    echo "=================================================="

    # 出力ファイル名にランナンバーを含める
    output_file="$log_dir/run_${run}_output.log"

    # テスト実行
    MODEL_ARG=""
    if [ -n "$MODEL_ID" ]; then
        MODEL_ARG="--model $MODEL_ID"
    fi

    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_scripts/compare_vlm_prompts_nutrition.py \
        --prompts v6_corrected v6_balanced v7_experimental v5_streamlined v7_production v6_enhanced \
        --limit $NUM_IMAGES \
        --concurrency $BATCH_SIZE \
        $MODEL_ARG \
        2>&1 | tee "$output_file"

    # 結果ファイルをログディレクトリにコピー
    latest_json=$(ls -t test_scripts/output/vlm_prompt_nutrition_comparison_*.json | head -1)
    latest_md=$(ls -t test_scripts/output/vlm_prompt_nutrition_comparison_*.md | head -1)

    if [ -f "$latest_json" ]; then
        cp "$latest_json" "$log_dir/run_${run}_results.json"
        echo "✅ Run $run 完了: $log_dir/run_${run}_results.json"
    fi

    if [ -f "$latest_md" ]; then
        cp "$latest_md" "$log_dir/run_${run}_results.md"
    fi

    # 経過時間を表示
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    elapsed_min=$((elapsed / 60))
    echo "⏱️ 経過時間: ${elapsed_min}分"

    # 最後のラン以外は少し待機
    if [ $run -lt $NUM_RUNS ]; then
        echo "⏳ 30秒待機後、次のランを開始..."
        sleep 30
    fi
done

# 実行終了時刻を記録
end_time=$(date +%s)
total_time=$((end_time - start_time))
total_min=$((total_time / 60))

echo ""
echo "=================================================="
echo "✅ 全${NUM_RUNS}ラン完了 - $(date)"
echo "=================================================="
echo ""
echo "総実行時間: ${total_min}分 ($(($total_min / 60))時間$(($total_min % 60))分)"
echo ""
echo "結果ファイル:"
ls -la "$log_dir"/*.json

echo ""
echo "統計分析を実行するには:"
echo "python test_scripts/analyze_5runs_final_stats.py --log_dir $log_dir"

# サマリーファイルの作成
cat >> "$log_dir/config.txt" << EOF

End Time: $(date)
Total Duration: ${total_min} minutes
Files Generated: $(ls "$log_dir"/run_*.json | wc -l) JSON files
EOF

echo ""
echo "📄 設定とサマリー: $log_dir/config.txt"