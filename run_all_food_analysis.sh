#!/bin/bash

# 食事分析API - 全食品画像一括分析スクリプト
# food1.jpg〜food5.jpgまでの全画像に対してPhase1とPhase2を実行し、結果を1つのtxtファイルに保存

set -e  # エラー時に停止

# カラー出力の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 設定
IMAGE_DIR="test_images"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_FILE="all_food_analysis_results_${TIMESTAMP}.txt"
TEMP_DIR="temp_analysis_${TIMESTAMP}"

# ヘルパー関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
}

# サーバーの起動確認
check_server() {
    log_info "Checking server health..."
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Server is running and healthy"
        return 0
    else
        log_error "Server is not running or not healthy"
        echo -e "${YELLOW}Please start the server with:${NC}"
        echo "export USDA_API_KEY=\"vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg\" && export GOOGLE_APPLICATION_CREDENTIALS=\"/Users/odasoya/meal_analysis_api /service-account-key.json\" && export GEMINI_PROJECT_ID=recording-diet-ai-3e7cf && export GEMINI_LOCATION=us-central1 && export GEMINI_MODEL_NAME=gemini-2.5-flash-preview-05-20 && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
        exit 1
    fi
}

# 画像ファイルの存在確認
check_images() {
    log_info "Checking image files..."
    missing_images=()
    
    for i in {1..5}; do
        image_file="${IMAGE_DIR}/food${i}.jpg"
        if [[ ! -f "$image_file" ]]; then
            missing_images+=("$image_file")
        fi
    done
    
    if [[ ${#missing_images[@]} -gt 0 ]]; then
        log_error "Missing image files:"
        for img in "${missing_images[@]}"; do
            echo "  - $img"
        done
        exit 1
    else
        log_success "All image files (food1.jpg - food5.jpg) found"
    fi
}

# 結果ファイルの初期化
initialize_results_file() {
    log_info "Initializing results file: $RESULTS_FILE"
    
    cat > "$RESULTS_FILE" << EOF
# 食事分析API - 全食品画像一括分析結果
# Generated: $(date)
# Script: run_all_food_analysis.sh
# Images processed: food1.jpg - food5.jpg

================================================================================
ANALYSIS SUMMARY
================================================================================

EOF
}

# 個別画像の分析
analyze_image() {
    local image_num=$1
    local image_file="${IMAGE_DIR}/food${image_num}.jpg"
    
    log_header "ANALYZING FOOD${image_num}.JPG"
    
    # Phase1の実行
    log_info "Running Phase 1 for food${image_num}.jpg..."
    local phase1_start=$(date +%s.%N)
    local phase1_duration="0"
    local phase1_success=false
    
    if python test_english_phase1_v2.py "$image_file" > "${TEMP_DIR}/food${image_num}_phase1.log" 2>&1; then
        local phase1_end=$(date +%s.%N)
        phase1_duration=$(echo "$phase1_end - $phase1_start" | bc -l)
        log_success "Phase 1 completed in ${phase1_duration}s"
        phase1_success=true
        
        # Phase1結果の保存
        if [[ -f "phase1_analysis_result_v2.json" ]]; then
            cp "phase1_analysis_result_v2.json" "${TEMP_DIR}/food${image_num}_phase1.json"
        fi
    else
        local phase1_end=$(date +%s.%N)
        phase1_duration=$(echo "$phase1_end - $phase1_start" | bc -l)
        log_error "Phase 1 failed for food${image_num}.jpg in ${phase1_duration}s"
        
        # エラーログを保存
        echo "Phase 1 FAILED" > "${TEMP_DIR}/food${image_num}_phase1.json"
        echo "Error log:" >> "${TEMP_DIR}/food${image_num}_phase1.json"
        cat "${TEMP_DIR}/food${image_num}_phase1.log" >> "${TEMP_DIR}/food${image_num}_phase1.json"
    fi
    
    # Phase2の実行（Phase1が成功した場合のみ）
    local phase2_duration="0"
    local phase2_success=false
    
    if [[ "$phase1_success" == true ]]; then
        log_info "Running Phase 2 for food${image_num}.jpg..."
        local phase2_start=$(date +%s.%N)
        
        if python test_english_phase2_v2.py "$image_file" > "${TEMP_DIR}/food${image_num}_phase2.log" 2>&1; then
            local phase2_end=$(date +%s.%N)
            phase2_duration=$(echo "$phase2_end - $phase2_start" | bc -l)
            log_success "Phase 2 completed in ${phase2_duration}s"
            phase2_success=true
            
            # Phase2結果の保存
            if [[ -f "phase2_analysis_result_v2.json" ]]; then
                cp "phase2_analysis_result_v2.json" "${TEMP_DIR}/food${image_num}_phase2.json"
            fi
        else
            local phase2_end=$(date +%s.%N)
            phase2_duration=$(echo "$phase2_end - $phase2_start" | bc -l)
            log_error "Phase 2 failed for food${image_num}.jpg in ${phase2_duration}s"
            
            # エラーログを保存
            echo "Phase 2 FAILED" > "${TEMP_DIR}/food${image_num}_phase2.json"
            echo "Error log:" >> "${TEMP_DIR}/food${image_num}_phase2.json"
            cat "${TEMP_DIR}/food${image_num}_phase2.log" >> "${TEMP_DIR}/food${image_num}_phase2.json"
        fi
    else
        log_warning "Skipping Phase 2 for food${image_num}.jpg due to Phase 1 failure"
        echo "Phase 2 SKIPPED (Phase 1 failed)" > "${TEMP_DIR}/food${image_num}_phase2.json"
    fi
    
    # 結果をメインファイルに追記（成功・失敗問わず）
    append_results_to_file "$image_num" "$phase1_duration" "$phase2_duration" "$phase1_success" "$phase2_success"
    
    # 両方成功した場合のみ成功とみなす
    if [[ "$phase1_success" == true && "$phase2_success" == true ]]; then
        return 0
    else
        return 1
    fi
}

# 結果をメインファイルに追記
append_results_to_file() {
    local image_num=$1
    local phase1_duration=$2
    local phase2_duration=$3
    local phase1_success=$4
    local phase2_success=$5
    
    local status="FAILED"
    if [[ "$phase1_success" == true && "$phase2_success" == true ]]; then
        status="SUCCESS"
    fi
    
    cat >> "$RESULTS_FILE" << EOF

================================================================================
FOOD${image_num}.JPG ANALYSIS RESULTS - ${status}
================================================================================
Image: ${IMAGE_DIR}/food${image_num}.jpg
Analysis Time: $(date)
Phase 1 Duration: ${phase1_duration}s (Success: ${phase1_success})
Phase 2 Duration: ${phase2_duration}s (Success: ${phase2_success})

--- PHASE 1 RESULTS ---
EOF
    
    if [[ -f "${TEMP_DIR}/food${image_num}_phase1.json" ]]; then
        cat "${TEMP_DIR}/food${image_num}_phase1.json" >> "$RESULTS_FILE"
    else
        echo "Phase 1 results not available" >> "$RESULTS_FILE"
    fi
    
    cat >> "$RESULTS_FILE" << EOF

--- PHASE 2 RESULTS ---
EOF
    
    if [[ -f "${TEMP_DIR}/food${image_num}_phase2.json" ]]; then
        cat "${TEMP_DIR}/food${image_num}_phase2.json" >> "$RESULTS_FILE"
    else
        echo "Phase 2 results not available" >> "$RESULTS_FILE"
    fi
    
    echo "" >> "$RESULTS_FILE"
}

# 最終サマリーの生成
generate_final_summary() {
    local total_duration=$1
    local successful_analyses=$2
    local failed_analyses=$3
    
    log_info "Generating final summary..."
    
    # サマリーをファイルの先頭に挿入するため、一時ファイルを使用
    local temp_summary_file="${TEMP_DIR}/summary.txt"
    
    cat > "$temp_summary_file" << EOF
Total Images Processed: 5 (food1.jpg - food5.jpg)
Successful Analyses: $successful_analyses
Failed Analyses: $failed_analyses
Total Execution Time: ${total_duration}s
Success Rate: $(echo "scale=1; $successful_analyses * 100 / 5" | bc -l)%

EOF
    
    # 既存のサマリー部分を更新
    sed -i '' "/^Total Images Processed:/,/^$/{
        r $temp_summary_file
        d
    }" "$RESULTS_FILE"
}

# クリーンアップ
cleanup() {
    if [[ -d "$TEMP_DIR" ]]; then
        log_info "Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
    fi
}

# メイン実行
main() {
    local script_start=$(date +%s.%N)
    local successful_analyses=0
    local failed_analyses=0
    
    log_header "MEAL ANALYSIS API - BATCH PROCESSING"
    echo -e "${CYAN}Processing food1.jpg through food5.jpg${NC}"
    echo -e "${CYAN}Results will be saved to: $RESULTS_FILE${NC}"
    echo ""
    
    # 事前チェック
    check_server
    check_images
    
    # 一時ディレクトリの作成
    mkdir -p "$TEMP_DIR"
    
    # 結果ファイルの初期化
    initialize_results_file
    
    # 各画像の分析
    for i in {1..5}; do
        if analyze_image "$i"; then
            ((successful_analyses++))
        else
            ((failed_analyses++))
        fi
        
        # 進捗表示
        echo -e "${CYAN}Progress: $((i)) / 5 images completed${NC}"
        echo ""
    done
    
    # 実行時間の計算
    local script_end=$(date +%s.%N)
    local total_duration=$(echo "$script_end - $script_start" | bc -l)
    
    # 最終サマリーの生成
    generate_final_summary "$total_duration" "$successful_analyses" "$failed_analyses"
    
    # 結果の表示
    log_header "BATCH PROCESSING COMPLETED"
    echo -e "${GREEN}✅ Results saved to: $RESULTS_FILE${NC}"
    echo -e "${GREEN}✅ Total execution time: ${total_duration}s${NC}"
    echo -e "${GREEN}✅ Successful analyses: $successful_analyses / 5${NC}"
    
    if [[ $failed_analyses -gt 0 ]]; then
        echo -e "${RED}⚠️  Failed analyses: $failed_analyses / 5${NC}"
    fi
    
    # ファイルサイズの表示
    local file_size=$(ls -lh "$RESULTS_FILE" | awk '{print $5}')
    echo -e "${BLUE}📄 Results file size: $file_size${NC}"
    
    echo ""
    echo -e "${YELLOW}To view results:${NC} cat $RESULTS_FILE"
    echo -e "${YELLOW}To view summary only:${NC} head -20 $RESULTS_FILE"
    
    # クリーンアップ
    cleanup
}

# エラーハンドリング
trap cleanup EXIT

# スクリプト実行
main "$@" 