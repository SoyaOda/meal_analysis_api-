#!/usr/bin/env python3
"""
Auto Niche Food Updater

クエリアルゴリズム実行時に検索結果を分析し、
exact matchがないクエリを自動的にJSONファイルに追加する機能
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from app_v2.utils.niche_food_manager import NicheFoodManager
from app_v2.models.nutrition_search_models import NutritionMatch

class AutoNicheFoodUpdater:
    """自動ニッチ食材更新クラス"""
    
    def __init__(self, enable_auto_update: bool = True):
        """
        初期化
        
        Args:
            enable_auto_update: 自動更新を有効にするかどうか
        """
        self.enable_auto_update = enable_auto_update
        self.manager = NicheFoodManager()
        self.update_log = []
    
    def analyze_search_results(self, query_results: Dict[str, List[NutritionMatch]]) -> Dict[str, Any]:
        """
        検索結果を分析してexact matchの状況を確認
        
        Args:
            query_results: クエリごとの検索結果 {query: [NutritionMatch, ...]}
            
        Returns:
            分析結果の辞書
        """
        analysis = {
            "queries_with_exact_match": [],
            "queries_without_exact_match": [],
            "analysis_timestamp": datetime.now().isoformat(),
            "total_queries": len(query_results)
        }
        
        for query, matches in query_results.items():
            if not matches:
                # 結果がない場合は no exact match として扱う
                analysis["queries_without_exact_match"].append({
                    "query": query,
                    "reason": "no_results",
                    "total_results": 0
                })
                continue
            
            # 少なくとも1つのexact matchがあるかチェック
            has_exact_match = any(match.is_exact_match for match in matches)
            
            if has_exact_match:
                analysis["queries_with_exact_match"].append({
                    "query": query,
                    "total_results": len(matches),
                    "exact_match_count": sum(1 for match in matches if match.is_exact_match)
                })
            else:
                analysis["queries_without_exact_match"].append({
                    "query": query,
                    "reason": "no_exact_match_in_results",
                    "total_results": len(matches),
                    "all_partial_matches": True
                })
        
        return analysis
    
    def classify_query_type(self, query: str, context_queries: List[str] = None) -> str:
        """
        クエリが料理(dish)か食材(ingredient)かを分類
        
        Args:
            query: 分類対象のクエリ
            context_queries: 同じ検索セッションの他のクエリ（コンテキスト）
            
        Returns:
            "dish" or "ingredient"
        """
        # 料理を示すキーワード
        dish_keywords = [
            "salad", "soup", "stew", "curry", "pasta", "rice", "sandwich", 
            "burger", "pizza", "taco", "burrito", "wrap", "bowl", "plate",
            "omelet", "pancake", "waffle", "cake", "pie", "bread", "toast"
        ]
        
        # 食材を示すキーワード
        ingredient_keywords = [
            "cheese", "oil", "butter", "milk", "cream", "sauce", "dressing",
            "lettuce", "tomato", "onion", "garlic", "pepper", "salt",
            "chicken", "beef", "pork", "fish", "egg", "flour", "sugar"
        ]
        
        query_lower = query.lower()
        
        # 料理キーワードとのマッチをチェック
        for keyword in dish_keywords:
            if keyword in query_lower:
                return "dish"
        
        # 食材キーワードとのマッチをチェック
        for keyword in ingredient_keywords:
            if keyword in query_lower:
                return "ingredient"
        
        # デフォルトは食材として分類（より一般的）
        return "ingredient"
    
    def auto_update_niche_mappings(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析結果に基づいてニッチ食材マッピングを自動更新
        
        Args:
            analysis: analyze_search_results()の結果
            
        Returns:
            更新結果の詳細
        """
        if not self.enable_auto_update:
            return {"status": "disabled", "message": "Auto update is disabled"}
        
        update_results = {
            "timestamp": datetime.now().isoformat(),
            "updates_made": [],
            "skipped_queries": [],
            "errors": []
        }
        
        # exact matchがないクエリを処理
        for query_info in analysis["queries_without_exact_match"]:
            query = query_info["query"]
            
            try:
                # クエリタイプを分類
                query_type = self.classify_query_type(query)
                
                if query_type == "dish":
                    # 料理として追加
                    success = self.manager.add_dish_mapping(query)
                    if success:
                        update_results["updates_made"].append({
                            "query": query,
                            "type": "dish",
                            "reason": query_info["reason"]
                        })
                        self.update_log.append(f"Added dish: {query}")
                else:
                    # 食材として追加（シンプルなリスト形式）
                    mappings = self.manager.load_mappings()
                    
                    # 既存チェック
                    existing_items = mappings["ingredients"]["no_exact_match_items"]
                    
                    if query.lower() not in [item.lower() for item in existing_items]:
                        # シンプルにリストに追加
                        mappings["ingredients"]["no_exact_match_items"].append(query.lower())
                        mappings["ingredients"]["no_exact_match_items"].sort()
                        
                        if self.manager.save_mappings(mappings):
                            update_results["updates_made"].append({
                                "query": query,
                                "type": "ingredient",
                                "reason": query_info["reason"],
                                "note": "Added as no-exact-match query"
                            })
                            self.update_log.append(f"Added ingredient (no exact match): {query}")
                
            except Exception as e:
                update_results["errors"].append({
                    "query": query,
                    "error": str(e)
                })
                print(f"⚠️  Error updating query '{query}': {e}")
        
        return update_results
    
    def process_search_session(self, query_results: Dict[str, List[NutritionMatch]]) -> Dict[str, Any]:
        """
        検索セッション全体を処理して自動更新を実行
        
        Args:
            query_results: クエリごとの検索結果
            
        Returns:
            処理結果の詳細
        """
        print(f"🔍 Auto-analyzing {len(query_results)} search queries...")
        
        # 1. 検索結果を分析
        analysis = self.analyze_search_results(query_results)
        
        # 2. 分析結果をログ出力
        no_exact_count = len(analysis["queries_without_exact_match"])
        exact_count = len(analysis["queries_with_exact_match"])
        
        print(f"   📊 Queries with exact match: {exact_count}")
        print(f"   📊 Queries without exact match: {no_exact_count}")
        
        if no_exact_count > 0:
            print("   🔍 Queries without exact match:")
            for query_info in analysis["queries_without_exact_match"]:
                print(f"     - {query_info['query']} ({query_info['reason']})")
        
        # 3. 自動更新を実行
        update_results = {"status": "no_updates_needed"}
        if no_exact_count > 0 and self.enable_auto_update:
            update_results = self.auto_update_niche_mappings(analysis)
            
            if update_results["updates_made"]:
                print(f"   ✅ Updated {len(update_results['updates_made'])} niche food mappings")
                for update in update_results["updates_made"]:
                    print(f"     + {update['type']}: {update['query']}")
        
        return {
            "analysis": analysis,
            "updates": update_results,
            "session_timestamp": datetime.now().isoformat()
        }

def analyze_test_results_file(json_file_path: str, dry_run: bool = True) -> Dict[str, Any]:
    """
    テスト結果のJSONファイルを分析してニッチ食材マッピングを更新
    
    Args:
        json_file_path: 分析するJSONファイルのパス
        dry_run: テストモード
        
    Returns:
        分析結果
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # JSON構造からNutritionQueryResultを再構築（簡易版）
        matches = {}
        for query, match_data in data.get("matches", {}).items():
            if isinstance(match_data, list):
                matches[query] = match_data
            else:
                matches[query] = [match_data] if match_data else []
        
        # 簡易的なNutritionQueryResultオブジェクトを作成
        class SimpleQueryResult:
            def __init__(self, matches_dict):
                self.matches = matches_dict
        
        search_results = SimpleQueryResult(matches)
        
        # 分析実行
        updater = AutoNicheFoodUpdater()
        results = updater.auto_update_niche_mappings(search_results, dry_run=dry_run)
        
        return results
        
    except Exception as e:
        print(f"❌ Error analyzing test results file: {e}")
        return {"error": str(e)} 