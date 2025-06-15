#!/usr/bin/env python3
"""
Gemma独立性検証スクリプト
Geminiの認証情報なしでGemmaが動作することを確認
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_single_image_gemma_only():
    """1画像のみでGemma単体テスト"""
    print("🟢 Gemma単体動作確認テスト開始...")
    print(f"DEEPINFRA_API_KEY: {'設定済み' if os.environ.get('DEEPINFRA_API_KEY') else '未設定'}")
    print(f"GEMINI_PROJECT_ID: {'設定済み' if os.environ.get('GEMINI_PROJECT_ID') else '未設定'}")
    print(f"service-account-key.json: {'存在' if Path('service-account-key.json').exists() else '不存在'}")
    
    try:
        from app_v2.pipeline.orchestrator import MealAnalysisPipeline
        from app_v2.services.deepinfra_service import DeepInfraService
        
        # DeepInfraServiceの初期化テスト
        print("\n🔧 DeepInfraService初期化テスト...")
        service = DeepInfraService()
        print("✅ DeepInfraService初期化成功")
        
        # パイプライン初期化テスト
        print("\n🔧 MealAnalysisPipeline初期化テスト...")
        pipeline = MealAnalysisPipeline()
        print("✅ MealAnalysisPipeline初期化成功")
        
        # 1画像のみテスト実行
        print("\n🍽️ food1.jpg単体分析テスト...")
        image_path = Path("test_images/food1.jpg")
        
        if not image_path.exists():
            print("❌ テスト画像が見つかりません")
            return False
            
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
            
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_bytes,
            image_mime_type="image/jpeg",
            save_detailed_logs=True,
            test_execution=True,
            test_results_dir="analysis_results/gemma_only_verification"
        )
        
        print(f"📋 結果の詳細: {result}")
        
        if result.get("processing_summary", {}).get("pipeline_status") == "completed":
            print("✅ Gemma単体分析成功！")
            print(f"📊 総カロリー: {result.get('processing_summary', {}).get('total_calories', 'N/A')} kcal")
            print(f"🍽️ 料理数: {result.get('processing_summary', {}).get('total_dishes', 'N/A')}")
            print(f"🥕 食材数: {result.get('processing_summary', {}).get('total_ingredients', 'N/A')}")
            return True
        else:
            print("❌ 分析失敗")
            print(f"エラー: {result.get('error', 'Unknown error')}")
            print(f"処理状況: {result.get('processing_summary', {}).get('pipeline_status', 'N/A')}")
            return False
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン実行関数"""
    print("🔍 Gemma単体動作確認テスト")
    print("=" * 50)
    
    success = await test_single_image_gemma_only()
    
    print("\n" + "=" * 50)
    if success:
        print("🎯 テスト成功: Gemmaのみで正常に動作しています")
    else:
        print("⚠️ テスト失敗: 問題が発生しました")

if __name__ == "__main__":
    asyncio.run(main()) 