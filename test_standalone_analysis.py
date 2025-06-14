#!/usr/bin/env python3
"""
食事分析スタンドアロン実行テスト
APIサーバーを使わずに直接MealAnalysisPipelineでfood1.jpgを分析します。
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app_v2.pipeline import MealAnalysisPipeline

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def setup_environment():
    """環境変数の設定"""
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


async def analyze_food1_image():
    """food1.jpgの分析を実行"""
    
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
    
    print(f"🚀 スタンドアロン食事分析テスト開始")
    print(f"📁 分析対象: {image_path}")
    print(f"📊 画像サイズ: {len(image_bytes):,} bytes")
    print(f"🔍 MIMEタイプ: {image_mime_type}")
    print(f"🔧 検索方法: Elasticsearch (高性能)")
    print("=" * 60)
    
    # パイプラインの初期化（Elasticsearch検索を使用）
    pipeline = MealAnalysisPipeline(
        use_elasticsearch_search=True,
        use_local_nutrition_search=False
    )
    
    try:
        # 分析実行
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            save_results=True,
            save_detailed_logs=False  # 簡単なテストなので詳細ログは無効
        )
        
        print("✅ 分析が完了しました！")
        print("=" * 60)
        
        # 結果の表示
        print_analysis_summary(result)
        
        return result
        
    except Exception as e:
        print(f"❌ 分析中にエラーが発生しました: {e}")
        logger.error(f"分析エラー: {e}", exc_info=True)
        return None


def print_analysis_summary(result: dict):
    """分析結果のサマリーを表示"""
    if not result or 'error' in result:
        print(f"❌ エラー: {result.get('error', '不明なエラー')}")
        return
    
    print(f"📋 分析結果サマリー (ID: {result.get('analysis_id', 'N/A')})")
    print("-" * 40)
    
    # Phase1結果
    phase1 = result.get('phase1_result', {})
    dishes = phase1.get('dishes', [])
    detected_items = phase1.get('detected_food_items', [])
    
    print(f"🍽️  検出された料理: {len(dishes)}個")
    for i, dish in enumerate(dishes, 1):
        confidence = dish.get('confidence', 0)
        print(f"   {i}. {dish.get('dish_name', 'N/A')} (信頼度: {confidence:.2f})")
    
    print(f"\n🥕 検出された食材: {len(detected_items)}個")
    for i, item in enumerate(detected_items, 1):
        confidence = item.get('confidence', 0)
        print(f"   {i}. {item.get('item_name', 'N/A')} (信頼度: {confidence:.2f})")
    
    # 栄養検索結果
    nutrition_search = result.get('nutrition_search_result', {})
    match_rate = nutrition_search.get('match_rate', 0)
    matches_count = nutrition_search.get('matches_count', 0)
    
    print(f"\n🔍 栄養データベース照合結果:")
    print(f"   - マッチ件数: {matches_count}件")
    print(f"   - 成功率: {match_rate:.1%}")
    print(f"   - 検索方法: {nutrition_search.get('search_summary', {}).get('search_method', 'elasticsearch')}")
    
    # 処理時間
    processing = result.get('processing_summary', {})
    processing_time = processing.get('processing_time_seconds', 0)
    total_dishes = processing.get('total_dishes', 0)
    total_ingredients = processing.get('total_ingredients', 0)
    
    print(f"\n⏱️  処理統計:")
    print(f"   - 処理時間: {processing_time:.2f}秒")
    print(f"   - 総料理数: {total_dishes}個")
    print(f"   - 総食材数: {total_ingredients}個")
    
    # 暫定栄養価
    nutrition = result.get('final_nutrition_result', {}).get('total_meal_nutrients', {})
    if nutrition:
        print(f"\n🍎 暫定栄養価 (概算):")
        print(f"   - カロリー: {nutrition.get('calories_kcal', 0):.0f} kcal")
        print(f"   - タンパク質: {nutrition.get('protein_g', 0):.1f} g")
        print(f"   - 炭水化物: {nutrition.get('carbohydrates_g', 0):.1f} g")
        print(f"   - 脂質: {nutrition.get('fat_g', 0):.1f} g")
    
    # 保存先
    if 'legacy_saved_to' in result:
        print(f"\n💾 結果保存先: {result['legacy_saved_to']}")
    
    print("\n" + "=" * 60)
    print("🎯 スタンドアロン分析テスト完了！")


def main():
    """メイン関数"""
    print("🚀 食事分析スタンドアロンテスト v2.0")
    print("📝 APIサーバー不要の直接パイプライン実行")
    print()
    
    # 環境設定
    setup_environment()
    
    try:
        # 分析実行
        result = asyncio.run(analyze_food1_image())
        
        if result:
            print("✅ テスト成功！")
            return 0
        else:
            print("❌ テスト失敗")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ ユーザーによって中断されました")
        return 1
    except Exception as e:
        print(f"❌ 実行中にエラーが発生しました: {e}")
        logger.error(f"メイン実行エラー: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 