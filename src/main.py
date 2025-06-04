"""
メインエントリポイント

統合された栄養推定APIのメインスクリプト
test_english_phase1_v2.py と test_english_phase2_v2.py を置き換え
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional

from .common.config_loader import ConfigLoader
from .common.exceptions import NutrientEstimationError
from .orchestration.workflow_manager import NutrientEstimationWorkflow


async def main():
    """メイン関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="食事画像から栄養素を推定する統合API",
        epilog="例: python -m src.main images/food.jpg --config configs/main_config.yaml"
    )
    parser.add_argument(
        "image_path", 
        type=str, 
        help="分析する食事画像のパス"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default=None,
        help="設定ファイルのパス（デフォルト: configs/main_config.yaml）"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="結果出力ファイルパス（JSONファイル）"
    )
    parser.add_argument(
        "--text", 
        type=str, 
        default=None,
        help="補助テキスト情報"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="デバッグモードで実行"
    )
    parser.add_argument(
        "--quiet",
        action="store_true", 
        help="クワイエットモード（エラーのみ表示）"
    )
    parser.add_argument(
        "--save-phases",
        action="store_true",
        help="各フェーズの入出力をJSONファイルに保存"
    )
    parser.add_argument(
        "--no-save-phases", 
        action="store_true",
        help="フェーズ出力保存を無効化"
    )
    
    args = parser.parse_args()
    
    try:
        # 設定のロード
        print("🔧 設定をロード中...")
        config = ConfigLoader.load_config(args.config)
        
        # デバッグモード設定
        if args.debug:
            config["DEBUG"] = True
            config["LOGGING_LEVEL"] = "DEBUG"
        
        if args.quiet:
            config["LOGGING_LEVEL"] = "ERROR"
        
        # フェーズ出力保存設定の調整
        if args.save_phases:
            config["SAVE_PHASE_OUTPUTS"] = True
        elif args.no_save_phases:
            config["SAVE_PHASE_OUTPUTS"] = False
        
        # ログ設定
        ConfigLoader.setup_logging(config)
        
        # 画像ファイルの存在確認
        image_path = Path(args.image_path)
        if not image_path.exists():
            print(f"❌ エラー: 画像ファイルが見つかりません: {image_path}")
            sys.exit(1)
        
        print(f"📸 画像を分析中: {image_path}")
        
        # ワークフローの初期化
        print("🚀 栄養推定ワークフローを初期化中...")
        workflow = NutrientEstimationWorkflow(config)
        
        # Geminiサービスの統合（既存サービスクラスが存在する場合）
        gemini_service = await _setup_gemini_service(config)
        if gemini_service:
            workflow.set_gemini_service(gemini_service)
        else:
            print("⚠️  警告: Geminiサービスが設定されていません")
        
        # 栄養推定の実行
        print("🔍 栄養推定を実行中...")
        nutrition_report = await workflow.process_image_to_nutrition(
            str(image_path), 
            args.text
        )
        
        # 結果の表示
        print("\n" + "="*50)
        print("🎯 栄養推定結果")
        print("="*50)
        
        if nutrition_report.total_calories:
            print(f"総カロリー: {nutrition_report.total_calories:.1f} kcal")
        
        if nutrition_report.total_nutrients:
            print("\n主要栄養素:")
            major_nutrients = ["PROTEIN", "TOTAL_FAT", "CARBOHYDRATE_BY_DIFFERENCE"]
            for nutrient in major_nutrients:
                if nutrient in nutrition_report.total_nutrients:
                    summary = nutrition_report.total_nutrients[nutrient]
                    print(f"  {nutrient}: {summary.total_amount:.1f} {summary.unit}")
        
        print(f"\n解析食品数: {len(nutrition_report.detailed_items)}")
        
        if nutrition_report.nutrition_completeness_score:
            print(f"データ完全性: {nutrition_report.nutrition_completeness_score:.1%}")
        
        # マクロ栄養素内訳
        if nutrition_report.macro_breakdown:
            print(f"\nマクロ栄養素内訳:")
            macro = nutrition_report.macro_breakdown
            print(f"  タンパク質: {macro['protein_percentage']}%")
            print(f"  脂質: {macro['fat_percentage']}%")
            print(f"  炭水化物: {macro['carbohydrate_percentage']}%")
        
        # 詳細情報
        if not args.quiet and nutrition_report.detailed_items:
            print(f"\n詳細な食品情報:")
            for i, item in enumerate(nutrition_report.detailed_items, 1):
                print(f"  {i}. {item.selected_food_description}")
                if item.serving_size_g:
                    print(f"     重量: {item.serving_size_g}g")
        
        # 結果のファイル出力
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(nutrition_report.model_dump_json(indent=2, ensure_ascii=False))
            
            print(f"\n💾 結果を保存しました: {output_path}")
        
        # エラーや警告の表示
        if nutrition_report.metadata.get("has_interpretation_errors"):
            print(f"\n⚠️  解釈エラーが発生しました（件数: {nutrition_report.metadata.get('interpretation_errors_count', 0)}）")
        
        # フェーズ出力ファイルの保存状況を表示
        if config.get("SAVE_PHASE_OUTPUTS", True):
            phase_output_dir = Path(config.get("PHASE_OUTPUT_DIR", "test_results/phase_outputs"))
            image_stem = Path(args.image_path).stem
            
            print(f"\n📁 フェーズ出力ファイル:")
            print(f"   保存先: {phase_output_dir}/")
            
            # 各フェーズのファイルを確認
            phase_files = {
                "Phase 1 (画像処理)": f"phase1_{image_stem}_*.json",
                "USDA DB Query": f"usda_db_query_{image_stem}_*.json", 
                "Phase 2 (データ解釈)": f"phase2_{image_stem}_*.json",
                "Nutrition Calculation": f"nutrition_calculation_{image_stem}_*.json",
                "Workflow Summary": f"workflow_summary_{image_stem}_*.json"
            }
            
            for phase_name, pattern in phase_files.items():
                matching_files = list(phase_output_dir.glob(pattern))
                if matching_files:
                    latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
                    print(f"   ✅ {phase_name}: {latest_file.name}")
                else:
                    print(f"   ❌ {phase_name}: ファイルが見つかりません")
            
            print(f"\n💡 フェーズ詳細を確認するには:")
            print(f"   cat {phase_output_dir}/phase1_{image_stem}_*.json | jq '.output.identified_items'")
            print(f"   cat {phase_output_dir}/usda_db_query_{image_stem}_*.json | jq '.output.retrieved_foods[0]'")
            print(f"   cat {phase_output_dir}/phase2_{image_stem}_*.json | jq '.output.interpreted_foods[0]'")
            print(f"   cat {phase_output_dir}/nutrition_calculation_{image_stem}_*.json | jq '.output.total_nutrients'")
        
        print("\n✅ 栄養推定が完了しました！")
        
    except KeyboardInterrupt:
        print("\n\n🛑 処理が中断されました")
        sys.exit(1)
    except NutrientEstimationError as e:
        print(f"\n❌ 栄養推定エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 予期しないエラーが発生しました: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


async def _setup_gemini_service(config: dict) -> Optional[object]:
    """Geminiサービスをセットアップ（既存サービスとの統合）"""
    try:
        # 既存のGeminiサービスクラスをインポート
        import sys
        import os
        from pathlib import Path
        
        # プロジェクトルートを追加
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # 既存のGeminiサービスをインポート
        try:
            from app.services.gemini_service import GeminiMealAnalyzer
            
            # 環境変数から設定を取得
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-05-20")
            
            if not project_id:
                print("⚠️  警告: GOOGLE_CLOUD_PROJECT環境変数が設定されていません")
                return None
            
            gemini_service = GeminiMealAnalyzer(
                project_id=project_id,
                location=location,
                model_name=model_name
            )
            print("✅ Geminiサービスが正常に初期化されました")
            return gemini_service
            
        except ImportError as e:
            print(f"⚠️  既存のGeminiServiceクラスが見つかりません: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Geminiサービスの初期化に失敗しました: {e}")
        return None


if __name__ == "__main__":
    # Windowsでの非同期処理対応
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # メイン処理を実行
    asyncio.run(main()) 