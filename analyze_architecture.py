#!/usr/bin/env python3
"""
test_english_phase2.py実行時のアーキテクチャ分析とファイル出力スクリプト

このスクリプトは以下を実行します：
1. test_english_phase2.pyから呼び出される全てのファイルを特定
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
    
    # 分析対象ファイルのリスト
    files_to_analyze = {
        "メインテストファイル": [
            "test_english_phase2.py"
        ],
        "API エンドポイント層": [
            "app/main.py",
            "app/api/v1/endpoints/meal_analyses.py",
            "app/api/v1/endpoints/meal_analyses_refine.py"
        ],
        "サービス層": [
            "app/services/gemini_service.py",
            "app/services/usda_service.py"
        ],
        "データモデル層": [
            "app/api/v1/schemas/meal.py"
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
        ]
    }
    
    # 出力ファイル名（タイムスタンプ付き）
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"meal_analysis_architecture_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # ヘッダー情報
        out_f.write("=" * 80 + "\n")
        out_f.write("MEAL ANALYSIS API - アーキテクチャ構造とファイル分析\n")
        out_f.write("=" * 80 + "\n")
        out_f.write(f"生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write(f"分析対象: test_english_phase2.py 実行時に呼び出される全ファイル\n")
        out_f.write("=" * 80 + "\n\n")
        
        # アーキテクチャ概要
        out_f.write("📊 ARCHITECTURE OVERVIEW\n")
        out_f.write("-" * 40 + "\n")
        out_f.write("""
🔄 EXECUTION FLOW (2-Phase Approach):
Phase 1: 画像 → Gemini AI → 料理・食材識別 (英語名)
Phase 2: Phase1結果 + 画像 → USDA検索 → Gemini再分析 → 栄養成分精緻化

🏗️ LAYER STRUCTURE:
├── API層 (FastAPI)
│   ├── meal_analyses.py (Phase 1 endpoint)
│   └── meal_analyses_refine.py (Phase 2 endpoint)
├── サービス層
│   ├── gemini_service.py (Vertex AI Gemini連携)
│   └── usda_service.py (USDA FoodData Central API連携)
├── データモデル層
│   └── meal.py (Pydantic schemas)
├── プロンプト管理層
│   ├── prompt_loader.py (Template management)
│   └── prompt templates (*.txt)
└── 設定層
    └── config.py (Environment configuration)

🔧 TECHNICAL FEATURES:
- 非同期処理 (async/await)
- 構造化JSON出力 (Gemini response_schema)
- USDA栄養データベース連携
- キャッシュ機能
- 包括的エラーハンドリング

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
        out_f.write("🎯 SUMMARY\n")
        out_f.write("-" * 40 + "\n")
        total_files = sum(len(files) for files in files_to_analyze.values())
        existing_files = sum(1 for files in files_to_analyze.values() for f in files if os.path.exists(f))
        
        out_f.write(f"総ファイル数: {total_files}\n")
        out_f.write(f"存在ファイル数: {existing_files}\n")
        out_f.write(f"分析完了時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write("\nこのファイルには、test_english_phase2.py実行時に関わる全ての\n")
        out_f.write("アプリケーションファイルの完全な内容が含まれています。\n")
        
    return output_file, total_files, existing_files

def main():
    """メイン実行関数"""
    print("🔍 Meal Analysis API アーキテクチャ分析開始...")
    print("-" * 50)
    
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
        
        print("\n🎉 アーキテクチャ分析とファイル出力が完了しました!")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 