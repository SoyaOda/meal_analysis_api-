#!/usr/bin/env python3
"""
test_english_phase1_v2.py と test_english_phase2_v2.py 実行時のアーキテクチャ分析とファイル出力スクリプト

このスクリプトは以下を実行します：
1. v2.1テストファイルから呼び出される全てのファイルを特定
2. v2.1仕様のアーキテクチャ構造の分析
3. ログ機能を含む各ファイルの内容をテキストファイルとして保存
"""

import os
import datetime
from pathlib import Path
from typing import Dict, List

def get_file_content(file_path: str) -> str:
    """ファイル内容を安全に読み取る"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"ERROR: ファイルを読み取れませんでした: {str(e)}"

def analyze_architecture_v2():
    """v2.1アーキテクチャ構造とファイル分析を実行"""
    
    # 分析対象ファイルのリスト (v2.1仕様 - Pythonファイルのみ)
    files_to_analyze = {
        "v2.1メインテストファイル": [
            "test_english_phase1_v2.py",
            "test_english_phase2_v2.py"
        ],
        "API エンドポイント層 (v2.1)": [
            "app/main.py",
            "app/api/__init__.py",
            "app/api/v1/__init__.py",
            "app/api/v1/endpoints/__init__.py",
            "app/api/v1/endpoints/meal_analyses.py",      # Phase 1 v2.1エンドポイント
            "app/api/v1/endpoints/meal_analyses_refine.py" # Phase 2 v2.1エンドポイント
        ],
        "サービス層 (v2.1対応)": [
            "app/services/__init__.py",
            "app/services/gemini_service.py",              # v2.1 2フェーズ対応
            "app/services/usda_service.py",                # v2.1 Rich search対応
            "app/services/nutrition_calculation_service.py", # v2.1 新しい栄養計算エンジン
            "app/services/logging_service.py"              # v2.1 新しいログ機能
        ],
        "データモデル層 (v2.1スキーマ)": [
            "app/api/v1/schemas/__init__.py",
            "app/api/v1/schemas/meal.py"                   # v2.1 Phase1/Phase2 レスポンスモデル
        ],
        "プロンプト管理層 (v2.1)": [
            "app/prompts/__init__.py",
            "app/prompts/prompt_loader.py"                 # v2.1 2フェーズ対応
        ]
    }
    
    # 出力ファイル名（タイムスタンプ付き）
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"meal_analysis_architecture_v2.1_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # ヘッダー情報
        out_f.write("=" * 80 + "\n")
        out_f.write("MEAL ANALYSIS API v2.1 - アーキテクチャ構造とファイル分析\n")
        out_f.write("=" * 80 + "\n")
        out_f.write(f"生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write(f"分析対象: test_english_phase1_v2.py & test_english_phase2_v2.py 実行時に呼び出される全Pythonファイル\n")
        out_f.write("=" * 80 + "\n\n")
        
        # v2.1アーキテクチャ概要
        out_f.write("📊 ARCHITECTURE OVERVIEW v2.1\n")
        out_f.write("-" * 40 + "\n")
        out_f.write("""
🔄 EXECUTION FLOW (Advanced 2-Phase Approach):
Phase 1: 画像 → Gemini AI → 料理・食材識別 + USDAクエリ候補生成
Phase 2: Phase1結果 → 並列USDA検索 → 戦略決定AI → FDC ID選択 → 動的栄養計算

🏗️ LAYER STRUCTURE v2.1:
├── API層 (FastAPI)
│   ├── meal_analyses.py (Phase 1 v2.1: USDAクエリ候補生成)
│   └── meal_analyses_refine.py (Phase 2 v2.1: 高度戦略決定 + 栄養計算)
├── サービス層 (Enhanced)
│   ├── gemini_service.py (2フェーズメソッド: analyze_image_phase1, refine_analysis_phase2)
│   ├── usda_service.py (Rich search + 栄養詳細取得)
│   ├── nutrition_calculation_service.py (動的計算エンジン)
│   └── logging_service.py (セッション管理 + 詳細ログ記録)
├── データモデル層 (v2.1 Schemas)
│   └── meal.py (Phase1AnalysisResponse, Phase2GeminiResponse, MealAnalysisRefinementResponse)
└── プロンプト管理層 (2-Phase Templates)
    ├── prompt_loader.py (フェーズ別プロンプト管理)
    └── prompt templates (phase1_*, phase2_*)

🔧 TECHNICAL FEATURES v2.1:
- ✨ 高度戦略決定システム (dish_level vs ingredient_level)
- 🔍 並列USDA検索 (25+候補の同時処理)
- 📊 動的栄養計算 (戦略ベース計算)
- 📈 包括的ログ機能 (セッション追跡 + パフォーマンス分析)
- 🎯 FDC ID選択とソース説明
- 🔄 3層栄養集計 (食材 → 料理 → 食事)
- ⚡ 非同期処理最適化
- 📋 構造化JSON出力 (Gemini response_schema)

🆕 NEW FEATURES v2.1:
- USDAクエリ候補の自動生成
- 戦略理由と選択理由の詳細記録
- リアルタイムログ分析
- CSV/JSONLログエクスポート
- パフォーマンス統計とエラー分析

""")
        out_f.write("=" * 80 + "\n\n")
        
        # 各カテゴリーのファイル分析
        for category, file_list in files_to_analyze.items():
            out_f.write(f"📁 {category}\n")
            out_f.write("=" * 60 + "\n\n")
            
            for file_path in file_list:
                out_f.write(f"📄 FILE: {file_path}\n")
                out_f.write("-" * 50 + "\n")
                
                if os.path.exists(file_path):
                    # ファイル情報
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
                    
                    out_f.write(f"ファイルサイズ: {file_size} bytes\n")
                    out_f.write(f"最終更新: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    out_f.write(f"存在: ✅\n")
                    
                    # 特別なファイルタイプの説明
                    if file_path.endswith('.py'):
                        out_f.write(f"タイプ: 🐍 Python モジュール\n")
                    
                    out_f.write("\n")
                    
                    # ファイル内容（すべてPythonファイル）
                    out_f.write("CONTENT:\n")
                    out_f.write("```\n")
                    content = get_file_content(file_path)
                    out_f.write(content)
                    out_f.write("\n```\n\n")
                else:
                    out_f.write("存在: ❌ ファイルが見つかりません\n\n")
                
                out_f.write("=" * 60 + "\n\n")
        
        # フッター
        out_f.write("🎯 SUMMARY v2.1\n")
        out_f.write("-" * 40 + "\n")
        total_files = sum(len(files) for files in files_to_analyze.values())
        existing_files = sum(1 for files in files_to_analyze.values() for f in files if os.path.exists(f))
        
        out_f.write(f"総ファイル数: {total_files}\n")
        out_f.write(f"存在ファイル数: {existing_files}\n")
        out_f.write(f"分析完了時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        out_f.write("📋 v2.1の主要改善点:\n")
        out_f.write("✅ USDAクエリ候補の自動生成\n")
        out_f.write("✅ 高度な戦略決定システム\n")
        out_f.write("✅ 動的栄養計算エンジン\n")
        out_f.write("✅ 包括的ログ機能\n")
        out_f.write("✅ リアルタイム分析ツール\n\n")
        
        out_f.write("このファイルには、test_english_phase1_v2.py および\n")
        out_f.write("test_english_phase2_v2.py実行時に関わる全ての\n")
        out_f.write("Pythonファイルの完全な内容が含まれています。\n")
        
    return output_file, total_files, existing_files

def main():
    """メイン実行関数"""
    print("🔍 Meal Analysis API v2.1 アーキテクチャ分析開始...")
    print("-" * 60)
    
    try:
        output_file, total_files, existing_files = analyze_architecture_v2()
        
        print(f"✅ v2.1分析完了!")
        print(f"📁 出力ファイル: {output_file}")
        print(f"📊 総ファイル数: {total_files}")
        print(f"✅ 存在ファイル数: {existing_files}")
        
        if existing_files < total_files:
            missing = total_files - existing_files
            print(f"⚠️  見つからないファイル: {missing}個")
        
        # ファイルサイズを表示
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"📄 出力ファイルサイズ: {file_size:,} bytes")
        
        print("\n🎉 v2.1アーキテクチャ分析とファイル出力が完了しました!")
        print("📋 含まれる主要機能:")
        print("   - Phase 1 & Phase 2 v2.1エンドポイント")
        print("   - 高度戦略決定システム")
        print("   - 動的栄養計算エンジン")
        print("   - ログ機能（セッション管理）")
        print("   - プロンプト管理システム")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 