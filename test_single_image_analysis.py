#!/usr/bin/env python3
"""
単一画像分析テスト - Deep Infra Gemma 3専用
Gemini依存関係を完全に削除したバージョンでの動作確認
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """環境変数の設定"""
    # .envファイルから環境変数を読み込み
    load_dotenv()
    
    # Deep Infra設定（必須）
    if not os.environ.get("DEEPINFRA_API_KEY"):
        print("❌ DEEPINFRA_API_KEY が設定されていません")
        sys.exit(1)
    
    # Elasticsearch設定
    os.environ.setdefault("USE_ELASTICSEARCH_SEARCH", "true")
    os.environ.setdefault("elasticsearch_url", "http://localhost:9200")
    os.environ.setdefault("elasticsearch_index_name", "nutrition_fuzzy_search")
    
    print("✅ 環境変数設定完了")
    print(f"   DEEPINFRA_API_KEY: {'設定済み' if os.environ.get('DEEPINFRA_API_KEY') else '未設定'}")
    print(f"   DEEPINFRA_MODEL_ID: {os.environ.get('DEEPINFRA_MODEL_ID', 'google/gemma-3-27b-it')}")

async def test_single_image_analysis():
    """単一画像の分析テスト"""
    from app_v2.pipeline.orchestrator import MealAnalysisPipeline
    
    # テスト画像のパス
    test_image_path = "test_images/food1.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"❌ テスト画像が見つかりません: {test_image_path}")
        return False
    
    print(f"\n🔍 単一画像分析テスト開始")
    print(f"   画像: {test_image_path}")
    
    try:
        # パイプラインの初期化
        pipeline = MealAnalysisPipeline()
        
        # 画像ファイルを読み込み
        with open(test_image_path, "rb") as f:
            image_bytes = f.read()
        
        # 分析実行
        start_time = time.time()
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_bytes,
            image_mime_type="image/jpeg",
            optional_text="食事の画像です"
        )
        end_time = time.time()
        
        # 結果の表示
        processing_time = end_time - start_time
        print(f"\n✅ 分析完了 (処理時間: {processing_time:.1f}秒)")
        
        # 基本統計
        final_result = result.get("final_nutrition_result", {})
        total_dishes = len(final_result.get("dishes", []))
        total_calories = final_result.get("total_nutrition", {}).get("calories", 0)
        
        print(f"\n📊 分析結果サマリー:")
        print(f"   料理数: {total_dishes}")
        print(f"   総カロリー: {total_calories:.1f} kcal")
        
        # 料理詳細
        print(f"\n🍽️ 検出された料理:")
        for i, dish in enumerate(final_result.get("dishes", []), 1):
            dish_name = dish.get("dish_name", "不明")
            dish_calories = dish.get("total_nutrition", {}).get("calories", 0)
            ingredient_count = len(dish.get("ingredients", []))
            
            print(f"   {i}. {dish_name}")
            print(f"      カロリー: {dish_calories:.1f} kcal")
            print(f"      食材数: {ingredient_count}個")
        
        # マッチング統計
        processing_summary = result.get("processing_summary", {})
        if "nutrition_search_match_rate" in processing_summary:
            print(f"\n🎯 食材マッチング: {processing_summary['nutrition_search_match_rate']}")
        
        # ファイル保存
        result_file = f"single_image_analysis_result.json"
        import json
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 結果を保存: {result_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン処理"""
    print("🚀 単一画像分析テスト - Deep Infra Gemma 3専用")
    print("=" * 60)
    
    # 環境設定
    setup_environment()
    
    # 単一画像テスト実行
    success = await test_single_image_analysis()
    
    if success:
        print("\n🎉 テスト完了！")
        print("   Deep Infra Gemma 3による単一画像分析が正常に動作しました")
    else:
        print("\n❌ テスト失敗")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 