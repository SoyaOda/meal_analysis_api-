#!/usr/bin/env python3
"""
完全分析エンドポイント(/complete)実行時のアーキテクチャ分析とファイル出力スクリプト

このスクリプトは以下を実行します：
1. /api/v1/meal-analyses/complete エンドポイント実行時に呼び出される全てのファイルを特定
2. アーキテクチャ構造の分析
3. 各ファイルの内容をテキストファイルとして保存
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

def analyze_architecture():
    """アーキテクチャ構造とファイル分析を実行"""
    
    # 完全分析(/complete)エンドポイント実行時の分析対象ファイルのリスト
    files_to_analyze = {
        "FastAPIアプリケーション層": [
            "app/main.py"
        ],
        "完全分析API エンドポイント層": [
            "app/api/v1/endpoints/meal_analyses_complete.py"
        ],
        "サービス層": [
            "app/services/gemini_service.py",
            "app/services/usda_service.py",
            "app/services/nutrition_calculation_service.py"
        ],
        "設定管理": [
            "app/core/config.py"
        ],
        "プロンプト管理": [
            "app/prompts/__init__.py",
            "app/prompts/prompt_loader.py"
        ],
        "プロンプトテンプレート": [
            "app/prompts/phase1_system_prompt.txt",
            "app/prompts/phase1_user_prompt_template.txt", 
            "app/prompts/phase2_system_prompt.txt",
            "app/prompts/phase2_user_prompt_template.txt"
        ],
        "テスト・実行ファイル": [
            "test_complete_analysis.py"
        ]
    }
    
    # 出力ファイル名（タイムスタンプ付き）
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"complete_analysis_architecture_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # ヘッダー情報
        out_f.write("=" * 80 + "\n")
        out_f.write("MEAL ANALYSIS API - 完全分析パイプライン アーキテクチャ構造とファイル分析\n")
        out_f.write("=" * 80 + "\n")
        out_f.write(f"生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write(f"分析対象: /api/v1/meal-analyses/complete エンドポイント実行時に呼び出される全ファイル\n")
        out_f.write("=" * 80 + "\n\n")
        
        # アーキテクチャ概要
        out_f.write("📊 COMPLETE ANALYSIS ARCHITECTURE OVERVIEW\n")
        out_f.write("-" * 40 + "\n")
        out_f.write("""
🔄 COMPLETE EXECUTION FLOW (4-Phase Integrated Pipeline):
Phase 1: 画像 → Gemini AI → 料理・食材識別 (英語名)
USDA Query: 全食材 → USDA データベース照合 → FDC ID 取得  
Phase 2: Phase1結果 + USDA候補 + 画像 → Gemini AI → 計算戦略決定・栄養精緻化
Nutrition Calculation: 実重量 × USDA栄養データ → 最終栄養価計算・集計

🏗️ INTEGRATED LAYER STRUCTURE:
├── FastAPI Application Layer
│   └── main.py (Server, routing, CORS, error handling)
├── Complete Analysis API Layer  
│   └── meal_analyses_complete.py (Unified endpoint for all phases)
├── Service Layer
│   ├── gemini_service.py (Vertex AI Gemini連携 - Phase1&2)
│   ├── usda_service.py (USDA FoodData Central API連携)
│   └── nutrition_calculation_service.py (Nutrition computation engine)
├── Prompt Management Layer
│   ├── prompt_loader.py (Template loading & management)
│   └── prompt templates (Phase1&2 system/user prompts)
└── Configuration Layer
    └── config.py (Environment variables, settings)

🔧 COMPLETE ANALYSIS TECHNICAL FEATURES:
- 🔗 Unified API Endpoint (/complete): All phases in single request
- 🧠 AI-Driven Strategy Selection: dish_level vs ingredient_level
- 📊 3-Tier Nutrition Aggregation: ingredient → dish → meal  
- 💾 Automatic Result Saving: JSON files with analysis_id
- 🔍 100% USDA Integration: Real nutrition data retrieval
- ⚡ Async Processing: Non-blocking operations throughout
- 🛡️ Comprehensive Error Handling: Per-phase error isolation
- 📈 Real-time Logging: Detailed execution tracking

🎯 KEY IMPROVEMENTS OVER PHASE-BY-PHASE APPROACH:
- Single API call instead of multiple requests
- Automatic data flow between phases  
- Integrated error handling across all phases
- Built-in result persistence and retrieval
- Optimized resource usage with service caching

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
                    
                    out_f.write(f"ファイルサイズ: {file_size:,} bytes\n")
                    out_f.write(f"最終更新: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    out_f.write(f"存在: ✅\n\n")
                    
                    # ファイル内容
                    out_f.write("CONTENT:\n")
                    out_f.write("```\n")
                    content = get_file_content(file_path)
                    out_f.write(content)
                    out_f.write("\n```\n\n")
                else:
                    out_f.write("存在: ❌ ファイルが見つかりません\n\n")
                
                out_f.write("=" * 60 + "\n\n")
        
        # フッター
        out_f.write("🎯 COMPLETE ANALYSIS SUMMARY\n")
        out_f.write("-" * 40 + "\n")
        total_files = sum(len(files) for files in files_to_analyze.values())
        existing_files = sum(1 for files in files_to_analyze.values() for f in files if os.path.exists(f))
        
        out_f.write(f"総ファイル数: {total_files}\n")
        out_f.write(f"存在ファイル数: {existing_files}\n")
        out_f.write(f"分析完了時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write("\nこのファイルには、/api/v1/meal-analyses/complete エンドポイント\n")
        out_f.write("実行時に関わる完全分析パイプラインの全アプリケーションファイルの\n")
        out_f.write("完全な内容が含まれています。\n")
        out_f.write("\n🔥 COMPLETE ANALYSIS FEATURES:\n")
        out_f.write("- Phase 1: Gemini AI image analysis\n")
        out_f.write("- USDA Query: Database ingredient matching  \n")
        out_f.write("- Phase 2: Strategy determination & refinement\n")
        out_f.write("- Nutrition Calculation: Weight-based macro computation\n")
        out_f.write("- Result Management: Automatic save/retrieve functionality\n")
        
    return output_file, total_files, existing_files

def main():
    """メイン実行関数"""
    print("🔍 Complete Analysis Pipeline アーキテクチャ分析開始...")
    print("-" * 60)
    
    try:
        output_file, total_files, existing_files = analyze_architecture()
        
        print(f"✅ 分析完了!")
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
        
        print("\n🎉 Complete Analysis Pipeline アーキテクチャ分析とファイル出力が完了しました!")
        print("🔥 このファイルには完全分析(/complete)で使用される全ファイルが含まれています。")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 