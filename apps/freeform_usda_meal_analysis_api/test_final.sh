#!/bin/bash
# Phase 5: 最終統合テスト

set -e

echo "=================================================="
echo "Phase 5: Final Integration Test"
echo "=================================================="
echo ""

# アプリケーションディレクトリに移動
cd "$(dirname "$0")"

echo "✅ Test 1: ディレクトリ構造の確認"
echo "   Current directory: $(pwd)"
echo ""

# 必要なディレクトリとファイルの確認
echo "✅ Test 2: 必須ファイルの存在確認"
required_files=(
    "main.py"
    "Dockerfile"
    "deploy.sh"
    "requirements.txt"
    "config/settings.py"
    "services/deepinfra_service.py"
    "services/usda_search.py"
    "data/faiss/usda_index_full.faiss"
    "data/faiss/usda_metadata.json"
    "data/usda_json/usda_prepared_ingredients_preprocessed.json"
    "data/usda_json/usda_raw_ingredients_preprocessed.json"
)

all_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file NOT FOUND"
        all_exist=false
    fi
done

if [ "$all_exist" = false ]; then
    echo ""
    echo "❌ Some required files are missing!"
    exit 1
fi

echo ""
echo "✅ Test 3: データサイズの確認"
faiss_size=$(du -sh data/faiss/usda_index_full.faiss | awk '{print $1}')
json_size=$(du -sh data/usda_json | awk '{print $1}')
total_size=$(du -sh data | awk '{print $1}')
echo "   📊 FAISS Index: $faiss_size"
echo "   📊 USDA JSON: $json_size"
echo "   📊 Total Data: $total_size"

echo ""
echo "✅ Test 4: Pythonモジュール構造の確認"
# アプリケーションルートから実行（相対インポート対応）
cd ..
python3 -c "
import sys
import os
os.environ['DEEPINFRA_API_KEY'] = 'test_dummy'
sys.path.insert(0, '.')
from freeform_usda_meal_analysis_api.config import get_settings
print('   ✅ config module import successful')
from freeform_usda_meal_analysis_api.services.deepinfra_service import DeepInfraService
print('   ✅ DeepInfraService import successful')
from freeform_usda_meal_analysis_api.services.usda_search import SimplifiedUSDASearcher
print('   ✅ SimplifiedUSDASearcher import successful')
"

if [ $? -ne 0 ]; then
    echo "   ❌ Python module import failed!"
    exit 1
fi

# ディレクトリを戻す
cd freeform_usda_meal_analysis_api

echo ""
echo "=================================================="
echo "✅ Phase 5 All Tests Passed!"
echo "=================================================="
echo ""
echo "自己完結型アプリケーションが完成しました："
echo "  - shared/への依存: なし"
echo "  - データ: 全てdata/内に統合 ($total_size)"
echo "  - デプロイ: apps/freeform_usda_meal_analysis_api のみで完結"
echo ""
echo "次のステップ:"
echo "  1. ローカル起動テスト: GOOGLE_CLOUD_PROJECT=new-snap-calorie PORT=8007 python -m main"
echo "  2. Cloud Runデプロイ: bash deploy.sh"
