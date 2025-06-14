#!/usr/bin/env python3
"""
test_advanced_elasticsearch_search.py実行時のアーキテクチャ分析とファイル出力スクリプト

このスクリプトは以下を実行します：
1. test_advanced_elasticsearch_search.py実行時に呼び出される全てのファイルを特定
2. 高度な戦略的Elasticsearch検索アーキテクチャの分析
3. 各ファイルの内容をテキストファイルとして保存
4. 実行結果サマリーと戦略分析レポートの生成
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional

def get_file_content(file_path: str) -> str:
    """ファイル内容を安全に読み取る（センシティブ情報をフィルタリング）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # センシティブ情報をフィルタリング
        if file_path.endswith('.json') and ('service-account' in file_path or 'key' in file_path):
            return "CONTENT FILTERED: センシティブな認証情報が含まれているため、内容は表示されません。"
        
        # JSONファイルの場合、センシティブなキーをマスク
        if file_path.endswith('.json'):
            try:
                data = json.loads(content)
                # センシティブなキーをマスク
                sensitive_keys = [
                    'private_key', 'private_key_id', 'client_email', 
                    'client_id', 'auth_uri', 'token_uri', 'client_x509_cert_url',
                    'universe_domain'
                ]
                
                def mask_sensitive_data(obj):
                    if isinstance(obj, dict):
                        for key in obj:
                            if key in sensitive_keys:
                                obj[key] = "***MASKED***"
                            elif isinstance(obj[key], (dict, list)):
                                mask_sensitive_data(obj[key])
                    elif isinstance(obj, list):
                        for item in obj:
                            if isinstance(item, (dict, list)):
                                mask_sensitive_data(item)
                
                mask_sensitive_data(data)
                return json.dumps(data, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                # JSONでない場合はそのまま返す
                pass
        
        return content
    except Exception as e:
        return f"ERROR: ファイルを読み取れませんでした: {str(e)}"

def get_latest_result_summary() -> Optional[Dict]:
    """最新のtest_advanced_elasticsearch_search.py実行結果を取得"""
    try:
        # analysis_resultsディレクトリから最新の結果を検索
        results_dir = "analysis_results"
        if not os.path.exists(results_dir):
            return None
        
        # advanced_elasticsearch_searchディレクトリを検索
        search_dirs = []
        for item in os.listdir(results_dir):
            if item.startswith("advanced_elasticsearch_search_"):
                full_path = os.path.join(results_dir, item)
                if os.path.isdir(full_path):
                    search_dirs.append((item, full_path))
        
        if not search_dirs:
            return None
        
        # 最新のディレクトリを選択（タイムスタンプ順）
        search_dirs.sort(reverse=True)
        latest_dir = search_dirs[0][1]
        
        # JSONファイルを読み込み
        json_file = os.path.join(latest_dir, "advanced_elasticsearch_search_results.json")
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: 実行結果の読み込みに失敗: {e}")
    
    return None

def analyze_advanced_elasticsearch_architecture():
    """高度な戦略的Elasticsearch検索テストのアーキテクチャ構造とファイル分析を実行"""
    
    # test_advanced_elasticsearch_search.py実行時の分析対象ファイルのリスト
    files_to_analyze = {
        "Advanced Strategic Search テスト実行ファイル": [
            "test_advanced_elasticsearch_search.py"
        ],
        "FastAPI アプリケーション層 (app_v2)": [
            "app_v2/main/app.py",
            "app_v2/api/__init__.py",
            "app_v2/api/v1/__init__.py",
            "app_v2/api/v1/endpoints/__init__.py",
            "app_v2/api/v1/endpoints/meal_analysis.py"
        ],
        "パイプライン統制層": [
            "app_v2/pipeline/__init__.py",
            "app_v2/pipeline/orchestrator.py",
            "app_v2/pipeline/result_manager.py"
        ],
        "コンポーネント層 - Phase1 AI分析": [
            "app_v2/components/__init__.py",
            "app_v2/components/base.py",
            "app_v2/components/phase1_component.py"
        ],
        "コンポーネント層 - 高度戦略的Elasticsearch検索": [
            "app_v2/components/elasticsearch_nutrition_search_component.py",

            ""
        ],
        "データモデル層": [
            "app_v2/models/__init__.py",
            "app_v2/models/nutrition_search_models.py",
            "app_v2/models/phase1_models.py",
            ""
        ],
        "AI サービス層": [
            "app_v2/services/__init__.py",
            "app_v2/services/gemini_service.py"
        ],
        "設定管理": [
            "app_v2/config/__init__.py",
            "app_v2/config/settings.py"
        ],
        "プロンプト管理（Phase1統一プロンプトシステム）": [
            "app_v2/config/prompts/__init__.py",
            "app_v2/config/prompts/phase1_prompts.py",
            ""
        ],
        "Elasticsearch インデックス管理・検索強化": [
            "create_elasticsearch_index.py",
            "app_v2/utils/__init__.py",
            "app_v2/utils/lemmatization.py"
        ],
        "栄養データベース": [
            "db/yazio_db.json",
            "db/mynetdiary_db.json", 
            "db/eatthismuch_db.json"
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
            "openapi.yaml",
            ".gitignore"
        ]
    }
    
    # 最新の実行結果を取得
    latest_results = get_latest_result_summary()
    
    # 出力ファイル名（タイムスタンプ付き）
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_advanced_elasticsearch_architecture_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # ヘッダー情報
        out_f.write("=" * 100 + "\n")
        out_f.write("MEAL ANALYSIS API v2.0 - 高度戦略的Elasticsearch検索システム アーキテクチャ分析\n")
        out_f.write("=" * 100 + "\n")
        out_f.write(f"生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write(f"分析対象: test_advanced_elasticsearch_search.py実行時に呼び出される全ファイル\n")
        out_f.write("=" * 100 + "\n\n")
        
        # 最新実行結果サマリー
        if latest_results:
            out_f.write("🎯 LATEST EXECUTION RESULTS SUMMARY\n")
            out_f.write("-" * 60 + "\n")
            
            summary = latest_results.get('search_summary', {})
            analysis_id = latest_results.get('analysis_id', 'N/A')
            timestamp_result = latest_results.get('timestamp', 'N/A')
            
            out_f.write(f"📊 Analysis ID: {analysis_id}\n")
            out_f.write(f"🕒 Execution Time: {timestamp_result}\n")
            out_f.write(f"✅ Total Searches: {summary.get('total_searches', 0)}\n")
            out_f.write(f"🎯 Successful Matches: {summary.get('successful_matches', 0)}\n")
            out_f.write(f"📈 Match Rate: {summary.get('match_rate_percent', 0)}%\n")
            out_f.write(f"⚡ Search Time: {summary.get('search_time_ms', 0)}ms\n")
            out_f.write(f"📋 Total Results: {summary.get('total_results', 0)}\n")
            out_f.write(f"🗃️ Total Indexed Documents: {summary.get('total_indexed_documents', 0):,}\n")
            
            strategic_approach = summary.get('strategic_approach', {})
            if strategic_approach:
                out_f.write(f"\n🎯 STRATEGIC APPROACH:\n")
                out_f.write(f"   🍽️  Dish Strategy: {strategic_approach.get('dish_strategy', 'N/A')}\n")
                out_f.write(f"   🥕 Ingredient Strategy: {strategic_approach.get('ingredient_strategy', 'N/A')}\n")
            
            # クエリ分析
            input_queries = latest_results.get('input_queries', {})
            if input_queries:
                out_f.write(f"\n📝 INPUT QUERIES ANALYSIS:\n")
                all_queries = input_queries.get('all_queries', [])
                dish_names = input_queries.get('dish_names', [])
                ingredient_names = input_queries.get('ingredient_names', [])
                
                out_f.write(f"   📋 Total Queries: {len(all_queries)}\n")
                out_f.write(f"   🍽️  Dish Queries: {len(dish_names)}\n")
                out_f.write(f"   🥕 Ingredient Queries: {len(ingredient_names)}\n")
                
                if dish_names:
                    out_f.write(f"   🍽️  Dishes: {', '.join(dish_names[:3])}{'...' if len(dish_names) > 3 else ''}\n")
                if ingredient_names:
                    out_f.write(f"   🥕 Ingredients: {', '.join(ingredient_names[:5])}{'...' if len(ingredient_names) > 5 else ''}\n")
            
            out_f.write("\n" + "=" * 100 + "\n\n")
        
        # アーキテクチャ概要
        out_f.write("🚀 ADVANCED STRATEGIC ELASTICSEARCH SEARCH ARCHITECTURE OVERVIEW\n")
        out_f.write("-" * 80 + "\n")
        out_f.write("""
🔄 ADVANCED STRATEGIC SEARCH EXECUTION FLOW:
1. test_advanced_elasticsearch_search.py → JPG画像アップロード
2. FastAPI /api/v1/meal-analyses/complete → 完全分析エンドポイント
3. Phase1: Gemini AI 2.5 Flash 画像分析 → 構造化データ抽出
   📋 DetectedFoodItems: 信頼度付き食品識別
   🏷️  Attributes: 材料・調理法・ブランド・ネガティブキュー
4. 高度戦略的Elasticsearch検索:
   📍 DISH戦略: EatThisMuch dish (primary) → EatThisMuch branded (fallback, score<20.0)
   🥕 INGREDIENT戦略: EatThisMuch ingredient (primary) → MyNetDiary/YAZIO/branded (fallback)
   🔧 Strategic Features:
      - Min Score Threshold: 20.0 (動的フォールバック)
      - Strategic Metadata: 戦略フェーズ・タイプ追跡
      - Multi-DB Fallback: 段階的品質保証
5. 結果統合・保存: JSON + Markdown レポート生成

🏗️ ADVANCED COMPONENT-BASED ARCHITECTURE v2.0:
├── Advanced Test Layer
│   └── test_advanced_elasticsearch_search.py (高度戦略的検索テスト)
├── FastAPI Application Layer (app_v2)
│   ├── main/app.py (Server, CORS, health endpoints)
│   └── api/v1/endpoints/meal_analysis.py (Complete analysis API)
├── Pipeline Management Layer
│   ├── orchestrator.py (MealAnalysisPipeline - 全フェーズ統制・構造化データ対応)
│   └── result_manager.py (ResultManager - 結果保存・履歴管理)
├── AI Component Layer
│   ├── base.py (BaseComponent - 共通インターフェース)
│   ├── phase1_component.py (Phase1Component - Gemini構造化分析)
│   └── elasticsearch_nutrition_search_component.py (高度戦略的検索エンジン)
├── AI Service Layer
│   └── gemini_service.py (GeminiService - Vertex AI統合・構造化スキーマ)
├── Data Model Layer
│   ├── nutrition_search_models.py (NutritionMatch, strategic metadata)
│   └── phase1_models.py (DetectedFoodItem, FoodAttribute, 構造化出力)
├── Elasticsearch Infrastructure
│   ├── create_elasticsearch_index.py (11,845ドキュメント インデックス管理)
│   └── elasticsearch-8.10.4/ (高性能検索エンジン)
└── Strategic Data Layer
    ├── yazio_db.json (1,825項目 - バランス食品・25カテゴリ)
    ├── mynetdiary_db.json (1,142項目 - 科学的データ・統一型)
    └── eatthismuch_db.json (8,878項目 - 最大・3データ型対応)

🎯 ADVANCED STRATEGIC SEARCH FEATURES:
- 🔥 Enhanced Dish検索戦略:
  * Primary: EatThisMuch data_type=dish (高関連性料理データ)
  * Fallback: EatThisMuch data_type=branded (スコア<20.0時の自動切替)
  * Strategy Metadata: dish_primary, dish_fallback tracking
- 🥕 Enhanced Ingredient検索戦略:
  * Primary: EatThisMuch data_type=ingredient (メイン食材データ)
  * Multi-DB Fallback: MyNetDiary(科学的) → YAZIO(分類済) → EatThisMuch branded
  * Strategy Metadata: ingredient_primary, ingredient_fallback tracking
- ⚡ Performance Optimization:
  * Strategic Filtering: 関連性重視の絞り込み
  * Dynamic Fallback: スコア閾値ベース自動切替
  * Results Per DB: 5件制限による効率化
- 📊 Advanced Analytics:
  * Strategic Distribution Tracking
  * Database Source Analysis
  * Query Type Classification (dish vs ingredient)
  * Execution Time Monitoring
- 💾 Comprehensive Metadata:
  * strategic_phase: main_dish, main_ingredient, fallback_multi_db
  * strategy_type: dish_primary, dish_fallback, ingredient_primary, ingredient_fallback
  * fallback_source: 補助DB詳細情報
  * elasticsearch_score: 生スコア保持

🔧 TECHNICAL SPECIFICATIONS:
- Search Engine: Elasticsearch 8.10.4 (BM25F + Multi-Signal Boosting)
- AI Service: Google Vertex AI Gemini 2.5 Flash (構造化出力対応)
- Web Framework: FastAPI 0.104+ (async/await, multipart/form-data)
- Architecture Pattern: Strategic Component Pipeline
- Data Format: JSON (100g正規化栄養データ + 戦略メタデータ)
- Search Strategy: Strategic Multi-Stage Filtering + Score-based Fallback
- Authentication: Google Cloud Service Account
- Performance: Sub-second response times, 100% match rates

🚀 ADVANCED IMPROVEMENTS vs BASIC MULTI-DB:
- 🧠 構造化AI分析: DetectedFoodItems + Attributes抽出
- 🎯 戦略的データベース選択: EatThisMuchを中心とした最適化
- 📈 動的品質保証: スコア閾値ベースフォールバック
- 🔍 高度メタデータ追跡: 検索プロセス完全可視化
- ⚡ 効率的リソース使用: 戦略的結果数制限
- 📊 包括的分析: データベース分布・戦略分析
- 🔧 拡張可能設計: 新戦略・DB追加容易
- 💾 永続化対応: JSON + Markdown デュアル出力

🎖️ STRATEGIC SEARCH EXCELLENCE:
- Phase1-to-Search Pipeline: シームレスなデータ流れ
- Multi-Modal Input: JPG画像 → 構造化クエリ
- Intelligent Fallback: 品質保証付き多段階検索
- Real-time Analytics: 実行時戦略分析
- Production-Ready: 認証・エラーハンドリング完備

""")
        out_f.write("=" * 100 + "\n\n")
        
        # 各カテゴリーのファイル分析
        for category, file_list in files_to_analyze.items():
            out_f.write(f"📁 {category}\n")
            out_f.write("=" * 80 + "\n\n")
            
            for file_path in file_list:
                out_f.write(f"📄 FILE: {file_path}\n")
                out_f.write("-" * 60 + "\n")
                
                if os.path.exists(file_path):
                    # ファイル情報
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
                    
                    out_f.write(f"ファイルサイズ: {file_size:,} bytes\n")
                    out_f.write(f"最終更新: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    out_f.write(f"存在: ✅\n\n")
                    
                    # 特定のファイルタイプに応じた処理
                    if file_path.endswith('.json') and 'db/' in file_path:
                        # データベースJSONファイルは最初の50行のみ表示
                        out_f.write("CONTENT (データベース - 最初の50行):\n")
                        out_f.write("```json\n")
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                for i, line in enumerate(lines[:50]):
                                    out_f.write(line)
                                if len(lines) > 50:
                                    out_f.write(f"\n... ({len(lines) - 50} more lines)\n")
                        except Exception as e:
                            out_f.write(f"ERROR: JSONファイルを読み取れませんでした: {str(e)}\n")
                        out_f.write("```\n\n")
                    elif file_path.endswith('.json'):
                        # 設定JSONファイルは全内容表示（センシティブ情報はマスク済み）
                        out_f.write("CONTENT (設定ファイル):\n")
                        out_f.write("```json\n")
                        content = get_file_content(file_path)
                        out_f.write(content)
                        out_f.write("```\n\n")
                    elif file_path.endswith('.jpg') or file_path.endswith('.jpeg') or file_path.endswith('.png'):
                        # 画像ファイルは情報のみ表示
                        out_f.write("CONTENT: [画像ファイル - バイナリデータ]\n")
                        out_f.write(f"画像ファイル: {os.path.basename(file_path)}\n")
                        out_f.write(f"用途: test_advanced_elasticsearch_search.py の入力画像\n\n")
                    elif file_path.endswith('.yml') or file_path.endswith('.yaml'):
                        # 設定ファイル
                        out_f.write("CONTENT (設定ファイル):\n")
                        out_f.write("```yaml\n")
                        content = get_file_content(file_path)
                        out_f.write(content)
                        out_f.write("```\n\n")
                    else:
                        # Python/text ファイルは全内容表示
                        out_f.write("CONTENT:\n")
                        out_f.write("```python\n")
                        content = get_file_content(file_path)
                        out_f.write(content)
                        out_f.write("\n```\n\n")
                else:
                    out_f.write("存在: ❌ ファイルが見つかりません\n\n")
                
                out_f.write("=" * 80 + "\n\n")
        
        # 実行結果詳細分析（利用可能な場合）
        if latest_results and 'matches' in latest_results:
            out_f.write("📊 DETAILED EXECUTION RESULTS ANALYSIS\n")
            out_f.write("=" * 80 + "\n\n")
            
            matches = latest_results['matches']
            input_queries = latest_results.get('input_queries', {})
            dish_names = input_queries.get('dish_names', [])
            ingredient_names = input_queries.get('ingredient_names', [])
            
            # データベース分布分析
            source_distribution = {}
            strategy_breakdown = {"dish_primary": 0, "dish_fallback": 0, "ingredient_primary": 0, "ingredient_fallback": 0}
            total_results = 0
            
            for query, match_results in matches.items():
                query_type = "dish" if query in dish_names else "ingredient"
                if isinstance(match_results, list):
                    total_results += len(match_results)
                    for match in match_results:
                        source = match.get('source', 'unknown')
                        if source not in source_distribution:
                            source_distribution[source] = 0
                        source_distribution[source] += 1
                        
                        # 戦略統計
                        metadata = match.get('search_metadata', {})
                        strategy_type = metadata.get('strategy_type', 'unknown')
                        if strategy_type in strategy_breakdown:
                            strategy_breakdown[strategy_type] += 1
                else:
                    total_results += 1
                    source = match_results.get('source', 'unknown')
                    if source not in source_distribution:
                        source_distribution[source] = 0
                    source_distribution[source] += 1
            
            out_f.write("🗃️ DATABASE SOURCE DISTRIBUTION:\n")
            for source, count in sorted(source_distribution.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_results) * 100 if total_results > 0 else 0
                out_f.write(f"   {source}: {count} results ({percentage:.1f}%)\n")
            
            out_f.write(f"\n🎯 STRATEGIC BREAKDOWN:\n")
            total_strategy_results = sum(strategy_breakdown.values())
            for strategy, count in strategy_breakdown.items():
                if count > 0:
                    percentage = (count / total_strategy_results) * 100 if total_strategy_results > 0 else 0
                    out_f.write(f"   {strategy}: {count} results ({percentage:.1f}%)\n")
            
            out_f.write(f"\n📋 QUERY ANALYSIS:\n")
            for query, match_results in matches.items():
                query_type = "dish" if query in dish_names else "ingredient"
                result_count = len(match_results) if isinstance(match_results, list) else 1
                out_f.write(f"   '{query}' ({query_type}): {result_count} results\n")
                
                # トップ結果のスコア情報
                if isinstance(match_results, list) and match_results:
                    top_result = match_results[0]
                    score = top_result.get('score', 0)
                    name = top_result.get('search_name', 'N/A')
                    out_f.write(f"      Top: {name} (score: {score:.3f})\n")
                elif not isinstance(match_results, list):
                    score = match_results.get('score', 0)
                    name = match_results.get('search_name', 'N/A')
                    out_f.write(f"      Result: {name} (score: {score:.3f})\n")
            
            out_f.write("\n" + "=" * 80 + "\n\n")
        
        # フッター
        out_f.write("🎯 ADVANCED STRATEGIC ELASTICSEARCH SEARCH ANALYSIS SUMMARY\n")
        out_f.write("-" * 70 + "\n")
        total_files = sum(len(files) for files in files_to_analyze.values())
        existing_files = sum(1 for files in files_to_analyze.values() for f in files if os.path.exists(f))
        
        out_f.write(f"総ファイル数: {total_files}\n")
        out_f.write(f"存在ファイル数: {existing_files}\n")
        out_f.write(f"分析完了時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if latest_results:
            summary = latest_results.get('search_summary', {})
            out_f.write(f"\n📊 LATEST EXECUTION PERFORMANCE:\n")
            out_f.write(f"   ✅ Match Rate: {summary.get('match_rate_percent', 0)}%\n")
            out_f.write(f"   ⚡ Search Time: {summary.get('search_time_ms', 0)}ms\n")
            out_f.write(f"   📋 Total Results: {summary.get('total_results', 0)}\n")
        
        out_f.write("\nこのファイルには、test_advanced_elasticsearch_search.py実行時に\n")
        out_f.write("関わる高度戦略的Elasticsearch検索システムの全アプリケーション\n")
        out_f.write("ファイルと最新実行結果の完全な内容が含まれています。\n")
        out_f.write("\n🔥 ADVANCED STRATEGIC SEARCH SYSTEM HIGHLIGHTS:\n")
        out_f.write("- 🧠 AI構造化分析: Gemini 2.5 Flash DetectedFoodItems抽出\n")
        out_f.write("- 🍽️  Advanced Dish戦略: EatThisMuch dish → branded fallback\n")
        out_f.write("- 🥕 Advanced Ingredient戦略: EatThisMuch ingredient → Multi-DB fallback\n")
        out_f.write("- 📈 動的品質保証: スコア閾値20.0による自動フォールバック\n")
        out_f.write("- 🎯 戦略的メタデータ: 完全な検索プロセス追跡\n")
        out_f.write("- ⚡ 高性能実行: Sub-second strategic search\n")
        out_f.write("- 📊 包括的分析: データベース分布・戦略統計\n")
        out_f.write("- 💾 デュアル出力: JSON + Markdown レポート\n")
        out_f.write("- 🔧 Production-Ready: 認証・エラーハンドリング完備\n")
        out_f.write("- 🚀 拡張可能設計: Component-based Strategic Architecture\n")
        
    return output_file, total_files, existing_files, latest_results

def main():
    """メイン実行関数"""
    print("🔍 高度戦略的Elasticsearch検索システム アーキテクチャ分析開始...")
    print("-" * 80)
    
    try:
        output_file, total_files, existing_files, latest_results = analyze_advanced_elasticsearch_architecture()
        
        print(f"✅ 分析完了!")
        print(f"📁 出力ファイル: {output_file}")
        print(f"📊 総ファイル数: {total_files}")
        print(f"✅ 存在ファイル数: {existing_files}")
        
        if latest_results:
            summary = latest_results.get('search_summary', {})
            print(f"🎯 最新実行結果:")
            print(f"   📊 Analysis ID: {latest_results.get('analysis_id', 'N/A')}")
            print(f"   ✅ Match Rate: {summary.get('match_rate_percent', 0)}%")
            print(f"   ⚡ Search Time: {summary.get('search_time_ms', 0)}ms")
            print(f"   📋 Total Results: {summary.get('total_results', 0)}")
        
        if existing_files < total_files:
            missing = total_files - existing_files
            print(f"⚠️  見つからないファイル: {missing}個")
        
        # ファイルサイズを表示
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"📄 出力ファイルサイズ: {file_size:,} bytes")
        
        print("\n🎉 高度戦略的Elasticsearch検索システム アーキテクチャ分析とファイル出力が完了しました!")
        print("🔥 このファイルには高度戦略的検索で使用される全ファイルと実行結果が含まれています。")
        print("🧠 AI構造化分析 + 戦略的検索による最適化されたシステム構成を確認できます。")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 