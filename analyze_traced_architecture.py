#!/usr/bin/env python3
"""
ローカル栄養データベース検索システム アーキテクチャ分析 (依存関係追跡版)

実際にtest_local_nutrition_search_v2.pyから追跡された依存関係に基づいて
正確なファイル分析を実行します。
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

def analyze_traced_dependencies():
    """追跡された依存関係に基づくアーキテクチャ分析"""
    
    # 実際に追跡された依存関係
    traced_dependencies = {'project_python_files': ['test_local_nutrition_search_v2.py', 'venv/lib/python3.9/site-packages/requests/__init__.py'], 'server_files': ['app_v2/__init__.py', 'app_v2/api/__init__.py', 'app_v2/api/v1/__init__.py', 'app_v2/api/v1/endpoints/__init__.py', 'app_v2/api/v1/endpoints/meal_analysis.py', 'app_v2/components/__init__.py', 'app_v2/components/base.py', 'app_v2/components/local_nutrition_search_component.py', 'app_v2/components/phase1_component.py', 'app_v2/components/usda_query_component.py', 'app_v2/config/__init__.py', 'app_v2/config/prompts/__init__.py', 'app_v2/config/prompts/phase1_prompts.py', 'app_v2/config/prompts/phase2_prompts.py', 'app_v2/config/settings.py', 'app_v2/main/app.py', 'app_v2/models/__init__.py', 'app_v2/models/nutrition_models.py', 'app_v2/models/nutrition_search_models.py', 'app_v2/models/phase1_models.py', 'app_v2/models/phase2_models.py', 'app_v2/models/usda_models.py', 'app_v2/pipeline/__init__.py', 'app_v2/pipeline/orchestrator.py', 'app_v2/pipeline/result_manager.py', 'app_v2/services/__init__.py', 'app_v2/services/gemini_service.py', 'app_v2/services/nutrition_calculation_service.py', 'app_v2/services/usda_service.py', 'nutrition_db_experiment/search_service/api/query_builder.py', 'nutrition_db_experiment/search_service/api/search_handler.py', 'nutrition_db_experiment/search_service/nlp/query_preprocessor.py', 'nutrition_db_experiment/search_service/tests/test_search_algorithm.py'], 'data_files': [], 'config_files': ['nutrition_db_experiment/nutrition_database_specification.md'], 'external_files': ['/Users/odasoya/.pyenv/versions/3.9.6/lib/python3.9/datetime.py', '/Users/odasoya/.pyenv/versions/3.9.6/lib/python3.9/json/__init__.py', '/Users/odasoya/.pyenv/versions/3.9.6/lib/python3.9/os.py'], 'missing_files': [], 'import_errors': []}
    
    # ファイルを機能別に分類
    files_to_analyze = {
        "🎯 実行起点ファイル": [
            "test_local_nutrition_search_v2.py"
        ],
        "🏗️ プロジェクト内Pythonファイル": traced_dependencies["project_python_files"],
        "🌐 サーバー側ファイル": traced_dependencies["server_files"],
        "⚙️ 設定ファイル": traced_dependencies["config_files"]
    }
    
    # 出力ファイル名（タイムスタンプ付き）
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"traced_nutrition_architecture_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # ヘッダー情報
        out_f.write("=" * 80 + "\n")
        out_f.write("MEAL ANALYSIS API v2.0 - 依存関係追跡版アーキテクチャ分析\n")
        out_f.write("=" * 80 + "\n")
        out_f.write(f"生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write(f"追跡起点: test_local_nutrition_search_v2.py\n")
        out_f.write(f"総追跡ファイル数: {len(traced_dependencies['project_python_files']) + len(traced_dependencies['server_files']) + len(traced_dependencies['config_files'])}\n")
        out_f.write("=" * 80 + "\n\n")
        
        # 依存関係概要
        out_f.write("📊 DEPENDENCY TRACE SUMMARY\n")
        out_f.write("-" * 40 + "\n")
        out_f.write(f"✅ Project Python Files: {len(traced_dependencies['project_python_files'])}\n")
        out_f.write(f"🌐 Server Files: {len(traced_dependencies['server_files'])}\n")
        out_f.write(f"⚙️ Config Files: {len(traced_dependencies['config_files'])}\n")
        out_f.write(f"🗃️ Data Files (excluded): {len(traced_dependencies['data_files'])}\n")
        out_f.write(f"🌍 External Files: {len(traced_dependencies['external_files'])}\n")
        out_f.write(f"❌ Missing Files: {len(traced_dependencies['missing_files'])}\n")
        if traced_dependencies['import_errors']:
            out_f.write(f"⚠️ Import Errors: {len(traced_dependencies['import_errors'])}\n")
        out_f.write("\n")
        
        # エラーと欠損ファイルの報告
        if traced_dependencies['missing_files']:
            out_f.write("❌ MISSING FILES\n")
            out_f.write("-" * 20 + "\n")
            for missing in traced_dependencies['missing_files']:
                out_f.write(f"- {missing}\n")
            out_f.write("\n")
        
        if traced_dependencies['import_errors']:
            out_f.write("⚠️ IMPORT ERRORS\n")
            out_f.write("-" * 20 + "\n")
            for error in traced_dependencies['import_errors']:
                out_f.write(f"- {error}\n")
            out_f.write("\n")
        
        # 各カテゴリーのファイル分析
        for category, file_list in files_to_analyze.items():
            if not file_list:
                continue
                
            out_f.write(f"{category}\n")
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
                    
                    # ファイル内容（データファイルの場合は制限）
                    if file_path.endswith('.json') and file_size > 1024*1024:  # 1MB以上のJSONは概要のみ
                        out_f.write("CONTENT: (Large JSON file - showing structure only)\n")
                        try:
                            import json
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                            if isinstance(data, list):
                                out_f.write(f"Array with {len(data)} items\n")
                                if data:
                                    out_f.write(f"Sample item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Non-dict items'}\n")
                            elif isinstance(data, dict):
                                out_f.write(f"Object with keys: {list(data.keys())}\n")
                        except:
                            out_f.write("Could not parse JSON structure\n")
                    else:
                        out_f.write("CONTENT:\n")
                        out_f.write("```\n")
                        content = get_file_content(file_path)
                        out_f.write(content)
                        out_f.write("\n```\n")
                    out_f.write("\n")
                else:
                    out_f.write("存在: ❌ ファイルが見つかりません\n\n")
                
                out_f.write("=" * 60 + "\n\n")
        
        # 統計情報
        out_f.write("📊 ANALYSIS STATISTICS\n")
        out_f.write("-" * 40 + "\n")
        total_files = sum(len(files) for files in files_to_analyze.values() if files)
        existing_files = sum(1 for files in files_to_analyze.values() if files for f in files if os.path.exists(f))
        
        out_f.write(f"総ファイル数: {total_files}\n")
        out_f.write(f"存在ファイル数: {existing_files}\n")
        out_f.write(f"分析完了時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write("\nこのファイルには、test_local_nutrition_search_v2.py実行時に\n")
        out_f.write("実際に使用される全ファイルの内容が含まれています。\n")
        
    return output_file, total_files, existing_files

def main():
    """メイン実行関数"""
    print("🔍 依存関係追跡版アーキテクチャ分析開始...")
    print("-" * 60)
    
    try:
        output_file, total_files, existing_files = analyze_traced_dependencies()
        
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
        
        print("\n🎉 依存関係追跡版アーキテクチャ分析が完了しました!")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
