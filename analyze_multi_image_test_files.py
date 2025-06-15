#!/usr/bin/env python3
"""
test_multi_image_analysis.py実行時のアーキテクチャ分析とファイル出力スクリプト

このスクリプトは以下を実行します：
1. test_multi_image_analysis.py実行時に呼び出される全てのファイルを特定
2. MyNetDiary制約付き検索と栄養計算を含む新アーキテクチャの分析
3. 各ファイルの内容をテキストファイルとして保存
4. マルチ画像分析の実行結果サマリーとアーキテクチャ分析レポートの生成
"""

import os
import re
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def get_file_content(file_path: str) -> str:
    """ファイル内容を安全に読み取る"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"ERROR: ファイルを読み取れませんでした: {str(e)}"

def get_latest_multi_image_result_summary() -> Optional[Tuple[str, str]]:
    """最新のtest_multi_image_analysis.py実行結果サマリーを取得"""
    try:
        results_dir = "analysis_results"
        if not os.path.exists(results_dir):
            return None

        # multi_image_analysisディレクトリを検索
        analysis_dirs = [d for d in os.listdir(results_dir) if d.startswith("multi_image_analysis_") and os.path.isdir(os.path.join(results_dir, d))]
        if not analysis_dirs:
            return None

        # 最新のディレクトリを選択
        analysis_dirs.sort(reverse=True)
        latest_dir_path = os.path.join(results_dir, analysis_dirs[0])

        summary_file = os.path.join(latest_dir_path, "comprehensive_analysis_summary.md")
        if os.path.exists(summary_file):
            with open(summary_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # サマリーの主要部分のみを抽出（ここでは最初の20行程度）
            summary_preview = "\n".join(content.splitlines()[:25])
            return analysis_dirs[0], summary_preview
    except Exception as e:
        print(f"Warning: 実行結果サマリーの読み込みに失敗: {e}")
    
    return None

def analyze_multi_image_test_architecture():
    """マルチ画像分析テストのアーキテクチャ構造とファイル分析を実行"""
    
    # test_multi_image_analysis.py実行時の分析対象ファイルのリスト
    files_to_analyze = {
        "Multi-Image Analysis テスト実行ファイル": [
            "test_multi_image_analysis.py"
        ],
        "FastAPI アプリケーション層 (app_v2)": [
            "app_v2/main/app.py",
            "app_v2/api/v1/endpoints/meal_analysis.py"
        ],
        "パイプライン統制層": [
            "app_v2/pipeline/orchestrator.py",
            "app_v2/pipeline/result_manager.py"
        ],
        "コンポーネント層 - Phase1 AI分析": [
            "app_v2/components/base.py",
            "app_v2/components/phase1_component.py"
        ],
        "コンポーネント層 - MyNetDiary制約付き検索": [
            "app_v2/components/mynetdiary_nutrition_search_component.py"
        ],
        "コンポーネント層 - 栄養計算": [
            "app_v2/components/nutrition_calculation_component.py"
        ],
        "データモデル層": [
            "app_v2/models/phase1_models.py",
            "app_v2/models/nutrition_search_models.py",
            "app_v2/models/nutrition_calculation_models.py"
        ],
        "AI サービス層": [
            "app_v2/services/gemini_service.py"
        ],
        "設定管理": [
            "app_v2/config/settings.py"
        ],
        "プロンプト管理（Phase1 - MyNetDiary制約と重量推定）": [
            "app_v2/config/prompts/phase1_prompts.py"
        ],
        "ユーティリティ層 (MyNetDiaryデータハンドリング)": [
            "app_v2/utils/mynetdiary_utils.py"
        ],
        "データファイル (MyNetDiary制約リスト)": [
            "data/mynetdiary_search_names.txt"
        ],
        "テスト画像": [
            "test_images/food1.jpg",
            "test_images/food2.jpg",
            "test_images/food3.jpg",
            "test_images/food4.jpg",
            "test_images/food5.jpg"
        ],
        "依存関係・設定ファイル": [
            "requirements.txt",
            "README.md",
            ".gitignore"
        ]
    }
    
    # 最新の実行結果を取得
    latest_result_info = get_latest_multi_image_result_summary()
    
    # 出力ファイル名（タイムスタンプ付き）
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_multi_image_analysis_architecture_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # ヘッダー情報
        out_f.write("=" * 100 + "\n")
        out_f.write("MEAL ANALYSIS API v2.1 - Multi-Image Analysis System Architecture\n")
        out_f.write("=" * 100 + "\n")
        out_f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write(f"Analysis Target: All files related to test_multi_image_analysis.py execution\n")
        out_f.write("=" * 100 + "\n\n")
        
        # 最新実行結果サマリー
        if latest_result_info:
            dir_name, summary_content = latest_result_info
            out_f.write("🎯 LATEST MULTI-IMAGE ANALYSIS SUMMARY\n")
            out_f.write("-" * 60 + "\n")
            out_f.write(f"📂 Result Directory: {dir_name}\n")
            out_f.write(f"📄 Summary Preview:\n{summary_content}\n")
            out_f.write("\n" + "=" * 100 + "\n\n")
        
        # アーキテクチャ概要
        out_f.write("🚀 MYNETDIARY-CONSTRAINED SEARCH & NUTRITION CALCULATION ARCHITECTURE\n")
        out_f.write("-" * 80 + "\n")
        out_f.write("""
🔄 EXECUTION FLOW:
1.  test_multi_image_analysis.py: Initiates batch processing of multiple JPG images.
2.  FastAPI Endpoint (/api/v1/meal-analyses/complete): Receives each image for full analysis.
    - `use_mynetdiary_specialized=True` flag is set.
3.  Orchestrator: Controls the pipeline execution.
4.  Phase 1 (Gemini Vision Analysis):
    - `phase1_prompts.py`: Uses a prompt now including the 1,142 MyNetDiary ingredients list and a new `weight_g` estimation requirement.
    - `gemini_service.py`: Calls the model and structures the output.
    - `phase1_models.py`: Pydantic model `Ingredient` now requires `weight_g`.
5.  Phase 2 (MyNetDiary-Constrained Search):
    - `mynetdiary_nutrition_search_component.py` is selected by the orchestrator.
    - `_strict_ingredient_search()`: Searches for ingredients with an "exactly one" match rule.
    - `_flexible_dish_search()`: Performs a standard flexible search for dishes.
6.  Phase 3 (Nutrition Calculation):
    - `nutrition_calculation_component.py`:
        - Takes `weight_g` from Phase 1 and nutrition data (per 100g) from Phase 2.
        - Calculates nutrition for the actual ingredient weight.
        - Aggregates nutrition totals for each dish and the entire meal.
7.  Result Manager: Saves all intermediate and final results to the filesystem.

🏗️ KEY ARCHITECTURE COMPONENTS:
├── Test Layer
│   └── test_multi_image_analysis.py
├── FastAPI Application Layer (app_v2)
│   └── pipeline/orchestrator.py (Conditionally selects search component)
├── Component Layer
│   ├── phase1_component.py
│   ├── mynetdiary_nutrition_search_component.py (New: Strict & flexible search)
│   └── nutrition_calculation_component.py (New: Weight-based calculation)
├── AI Service & Prompts
│   ├── services/gemini_service.py
│   └── config/prompts/phase1_prompts.py (Updated with ingredient list & weight estimation)
├── Data Models
│   ├── models/phase1_models.py (Ingredient includes `weight_g`)
│   └── models/nutrition_calculation_models.py (New: For structured nutrition output)
└── Utilities & Data
    ├── utils/mynetdiary_utils.py (New: Handles ingredient list)
    └── data/mynetdiary_search_names.txt (New: 1,142 ingredient constraints)
""")
        out_f.write("\n" + "=" * 100 + "\n\n")

        # 各ファイルの内容を出力
        for category, files in files_to_analyze.items():
            # カテゴリーヘッダー
            out_f.write("\n" + "#" * 80 + "\n")
            out_f.write(f"## CATEGORY: {category}\n")
            out_f.write("#" * 80 + "\n\n")
            
            for file in files:
                if not file: continue # 空のエントリをスキップ
                
                file_path = Path(file)
                # ファイルヘッダー
                out_f.write("-" * 70 + "\n")
                out_f.write(f"### FILE: {file_path}\n")
                out_f.write(f"### FULL PATH: {file_path.resolve()}\n")
                out_f.write("-" * 70 + "\n\n")
                
                # ファイル内容
                if file_path.exists():
                    content = get_file_content(str(file_path))
                    out_f.write(content)
                else:
                    out_f.write("--- FILE NOT FOUND ---\n")
                
                out_f.write("\n\n")

    print(f"✅ アーキテクチャ分析レポートが正常に生成されました: {output_file}")

def main():
    """スクリプトのエントリーポイント"""
    print("🚀 マルチ画像分析システムのアーキテクチャ分析を開始します...")
    analyze_multi_image_test_architecture()
    print("✅ 分析が完了しました。")

if __name__ == '__main__':
    main() 