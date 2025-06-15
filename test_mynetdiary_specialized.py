#!/usr/bin/env python3
"""
MyNetDiary専用検索システムのテスト
"""
import asyncio
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

from app_v2.pipeline.orchestrator import MealAnalysisPipeline

def setup_environment():
    """環境変数の設定"""
    # .envファイルから環境変数を読み込み
    load_dotenv()
    
    # 既存の設定（.envファイルで設定されていない場合のフォールバック）
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/Users/odasoya/meal_analysis_api_2/service-account-key.json")
    os.environ.setdefault("GEMINI_PROJECT_ID", "recording-diet-ai-3e7cf")
    os.environ.setdefault("GEMINI_LOCATION", "us-central1")
    os.environ.setdefault("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")

def get_image_mime_type(file_path: str) -> str:
    """ファイル拡張子からMIMEタイプを推定"""
    ext = Path(file_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')

async def test_mynetdiary_specialized_analysis():
    """MyNetDiary専用検索システムのテスト"""
    
    # 画像ファイルのパス
    image_path = "test_images/food1.jpg"
    
    # 画像ファイルの存在確認
    if not os.path.exists(image_path):
        print(f"❌ エラー: 画像ファイルが見つかりません: {image_path}")
        return None
    
    # 画像データの読み込み
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    image_mime_type = get_image_mime_type(image_path)
    
    print(f"🚀 MyNetDiary専用検索システムテスト開始")
    print(f"📁 分析対象: {image_path}")
    print(f"📊 画像サイズ: {len(image_bytes):,} bytes")
    print(f"🔍 MIMEタイプ: {image_mime_type}")
    print(f"🔧 検索方法: MyNetDiary Specialized Search (ingredient厳密検索)")
    print("=" * 60)
    
    # 結果保存用ディレクトリを作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_results_dir = f"analysis_results/mynetdiary_test_{timestamp}"
    os.makedirs(main_results_dir, exist_ok=True)
    
    print(f"📁 結果保存ディレクトリ: {main_results_dir}")
    
    # MyNetDiary専用パイプラインの初期化
    pipeline = MealAnalysisPipeline(
        use_elasticsearch_search=True,
        use_mynetdiary_specialized=True  # MyNetDiary専用検索を有効化
    )
    
    try:
        # 完全分析実行
        print(f"\n🔄 MyNetDiary専用分析実行中...")
        analysis_start_time = time.time()
        
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            save_detailed_logs=True,
            test_execution=True,
            test_results_dir=main_results_dir
        )
        
        analysis_end_time = time.time()
        analysis_time = analysis_end_time - analysis_start_time
        
        print(f"✅ MyNetDiary専用分析が完了しました！ ({analysis_time:.2f}秒)")
        
        # 結果の表示
        print_analysis_results(result, analysis_time)
        
        return result
        
    except Exception as e:
        print(f"❌ MyNetDiary専用分析でエラーが発生しました: {e}")
        print(f"   エラータイプ: {type(e).__name__}")
        
        # ingredient検索の厳密性によるエラーの場合
        if "CRITICAL" in str(e) or "Multiple matches" in str(e):
            print(f"   これはMyNetDiary専用検索の厳密性による意図的なエラーです。")
            print(f"   - ingredient名がMyNetDiaryリストに完全一致しない")
            print(f"   - または複数の一致が見つかった")
        
        return None

def print_analysis_results(result: dict, analysis_time: float):
    """分析結果を表示"""
    print(f"\n📋 MyNetDiary専用分析結果サマリー (ID: {result.get('analysis_id', 'N/A')})")
    print("=" * 50)
    
    # Phase1結果
    phase1_result = result.get("phase1_result", {})
    dishes = phase1_result.get("dishes", [])
    
    print(f"🍽️  検出された料理: {len(dishes)}個")
    for i, dish in enumerate(dishes, 1):
        dish_name = dish.get("dish_name", "N/A")
        confidence = dish.get("confidence", 0)
        ingredients = dish.get("ingredients", [])
        print(f"   {i}. {dish_name} (信頼度: {confidence:.2f})")
        print(f"      食材: {[ing.get('ingredient_name', 'N/A') for ing in ingredients]}")
    
    # 栄養検索結果
    nutrition_search_result = result.get("nutrition_search_result", {})
    search_summary = nutrition_search_result.get("search_summary", {})
    
    print(f"\n🔍 MyNetDiary専用検索結果:")
    print(f"   - 検索方法: {search_summary.get('search_method', 'N/A')}")
    print(f"   - 総検索数: {search_summary.get('total_searches', 0)}")
    print(f"   - 成功マッチ: {search_summary.get('successful_matches', 0)}")
    print(f"   - マッチ率: {search_summary.get('match_rate_percent', 0):.1f}%")
    print(f"   - 検索時間: {search_summary.get('search_time_ms', 0)}ms")
    print(f"   - 総結果数: {search_summary.get('total_results', 0)}")
    print(f"   - ingredient厳密検索: {search_summary.get('ingredient_strict_matching', False)}")
    print(f"   - dish柔軟検索: {search_summary.get('dish_flexible_matching', False)}")
    
    # マッチした項目の詳細
    matches = nutrition_search_result.get("matches", {})
    if matches:
        print(f"\n📊 マッチした項目の詳細:")
        for search_term, match_data in matches.items():
            if isinstance(match_data, list):
                print(f"   - {search_term}: {len(match_data)}件")
                for match in match_data[:2]:  # 最初の2件のみ表示
                    print(f"     * {match.get('name', 'N/A')} (DB: {match.get('source_db', 'N/A')}, スコア: {match.get('score', 0):.2f})")
            else:
                print(f"   - {search_term}: {match_data.get('name', 'N/A')} (DB: {match_data.get('source_db', 'N/A')}, スコア: {match_data.get('score', 0):.2f})")
    
    print(f"\n⏱️  総処理時間: {analysis_time:.2f}秒")

def main():
    """メイン関数"""
    setup_environment()
    
    print("🚀 MyNetDiary専用検索システムテスト v1.0")
    print("📝 ingredient厳密検索 + dish柔軟検索")
    print()
    
    # 非同期実行
    result = asyncio.run(test_mynetdiary_specialized_analysis())
    
    if result:
        print("\n✅ MyNetDiary専用検索システムテスト成功！")
    else:
        print("\n❌ MyNetDiary専用検索システムテストが失敗しました。")
        print("   これは意図的な厳密性チェックの結果である可能性があります。")

if __name__ == "__main__":
    main() 