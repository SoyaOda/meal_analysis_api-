#!/usr/bin/env python3
"""
検索コンポーネント動作確認テスト

各コンポーネントの動作を段階的に確認
"""

import os
import sys
import json
from typing import Dict, Any

# プロジェクトパスを追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_root, 'search_service'))

def test_component_imports():
    """コンポーネントのインポートテスト"""
    print("🔧 1. コンポーネントインポートテスト")
    print("-" * 50)
    
    try:
        from search_service.nlp.query_preprocessor import preprocess_query, analyze_query
        print("✅ query_preprocessor インポート成功")
    except Exception as e:
        print(f"❌ query_preprocessor インポート失敗: {e}")
        return False
    
    try:
        from search_service.api.query_builder import build_nutrition_search_query
        print("✅ query_builder インポート成功")
    except Exception as e:
        print(f"❌ query_builder インポート失敗: {e}")
        return False
    
    try:
        from search_service.api.search_handler import SearchRequest, search_nutrition_db
        print("✅ search_handler インポート成功")
    except Exception as e:
        print(f"❌ search_handler インポート失敗: {e}")
        return False
    
    print()
    return True

def test_spacy_setup():
    """spaCyセットアップテスト"""
    print("🔧 2. spaCyセットアップテスト")
    print("-" * 50)
    
    try:
        import spacy
        print("✅ spaCy インポート成功")
        
        # 言語モデルの確認
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✅ en_core_web_sm モデル読み込み成功")
            
            # 簡単なテスト
            doc = nlp("cooking chicken")
            tokens = [token.text for token in doc]
            print(f"   テストトークン化: {tokens}")
            
            return True
        except OSError:
            print("❌ en_core_web_sm モデルが見つかりません")
            print("   インストール方法: python -m spacy download en_core_web_sm")
            return False
    except ImportError:
        print("❌ spaCy がインストールされていません")
        print("   インストール方法: pip install spacy")
        return False
    
    except Exception as e:
        print(f"❌ spaCy セットアップエラー: {e}")
        return False

def test_query_preprocessor():
    """クエリ前処理テスト"""
    print("🔧 3. クエリ前処理テスト")
    print("-" * 50)
    
    try:
        from search_service.nlp.query_preprocessor import preprocess_query, analyze_query
        
        # テストケース
        test_queries = [
            "cook",
            "cooking chicken",
            "cookie",
            "chocolate chip cookies",
            "baking a cake",
            "ground beef"
        ]
        
        for query in test_queries:
            try:
                processed = preprocess_query(query)
                analysis = analyze_query(query)
                
                print(f"📝 クエリ: '{query}'")
                print(f"   処理後: '{processed}'")
                print(f"   統計: {analysis['statistics']}")
                print()
                
            except Exception as e:
                print(f"❌ クエリ処理エラー '{query}': {e}")
                return False
        
        print("✅ クエリ前処理テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ クエリ前処理テスト失敗: {e}")
        return False

def test_query_builder():
    """クエリビルダーテスト"""
    print("🔧 4. クエリビルダーテスト")
    print("-" * 50)
    
    try:
        from search_service.api.query_builder import build_nutrition_search_query
        
        # テストケース
        test_cases = [
            {
                "processed_query": "cook chicken",
                "original_query": "cooking chicken",
                "db_type_filter": None
            },
            {
                "processed_query": "cookie",
                "original_query": "cookie",
                "db_type_filter": "branded"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                query = build_nutrition_search_query(**test_case)
                
                print(f"📝 テストケース {i}:")
                print(f"   元クエリ: {test_case['original_query']}")
                print(f"   処理後: {test_case['processed_query']}")
                print(f"   フィルタ: {test_case['db_type_filter']}")
                
                # クエリ構造の詳細確認
                query_structure = query['query']
                if 'function_score' in query_structure:
                    print(f"   クエリタイプ: function_score")
                    print(f"   関数数: {len(query_structure['function_score']['functions'])}")
                    base_query = query_structure['function_score']['query']
                    print(f"   ベースクエリタイプ: {list(base_query.keys())[0]}")
                    
                    if 'multi_match' in base_query:
                        print(f"   フィールド: {base_query['multi_match']['fields']}")
                elif 'bool' in query_structure:
                    print(f"   クエリタイプ: bool (フィルタ適用)")
                    inner_query = query_structure['bool']['must'][0]
                    if 'function_score' in inner_query:
                        print(f"   内部クエリ: function_score")
                        print(f"   関数数: {len(inner_query['function_score']['functions'])}")
                else:
                    print(f"   クエリタイプ: {list(query_structure.keys())[0]}")
                
                print()
                
            except Exception as e:
                print(f"❌ クエリ構築エラー: {e}")
                print(f"   詳細: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                return False
        
        print("✅ クエリビルダーテスト成功")
        return True
        
    except Exception as e:
        print(f"❌ クエリビルダーテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_search_handler():
    """検索ハンドラーテスト（モックモード）"""
    print("🔧 5. 検索ハンドラーテスト")
    print("-" * 50)
    
    try:
        from search_service.api.search_handler import search_nutrition_db
        
        # テストクエリ
        test_queries = [
            {"query": "cook", "db_type_filter": None},
            {"query": "cookie", "db_type_filter": "branded"},
            {"query": "chicken breast", "db_type_filter": "ingredient"}
        ]
        
        for test_query in test_queries:
            try:
                response = search_nutrition_db(**test_query)
                
                print(f"📝 検索: '{test_query['query']}'")
                print(f"   フィルタ: {test_query['db_type_filter']}")
                print(f"   結果数: {response.total_hits}")
                print(f"   処理時間: {response.took_ms}ms")
                print(f"   処理済みクエリ: '{response.query_info['processed_query']}'")
                
                # 結果の詳細
                for i, result in enumerate(response.results[:2], 1):
                    print(f"   結果{i}: {result['search_name']} (スコア: {result['_score']})")
                
                print()
                
            except Exception as e:
                print(f"❌ 検索エラー '{test_query['query']}': {e}")
                return False
        
        print("✅ 検索ハンドラーテスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 検索ハンドラーテスト失敗: {e}")
        return False

def test_word_boundary_examples():
    """単語境界問題のテスト例"""
    print("🔧 6. 単語境界問題テスト")
    print("-" * 50)
    
    try:
        from search_service.nlp.query_preprocessor import preprocess_query, analyze_query
        
        # cook vs cookie のテストケース
        boundary_tests = [
            "cook",
            "cooked", 
            "cooking",
            "cookie",
            "cookies",
            "chocolate chip cookie"
        ]
        
        print("単語境界問題のクエリ前処理結果:")
        print()
        
        for query in boundary_tests:
            processed = preprocess_query(query)
            analysis = analyze_query(query)
            
            # 保護されたタームの確認
            protected_count = analysis['statistics']['protected_terms']
            overridden_count = analysis['statistics']['overridden_terms']
            
            print(f"📝 '{query}' → '{processed}'")
            print(f"   保護ターム: {protected_count}, 上書き: {overridden_count}")
            
            # トークン詳細
            for token in analysis['tokens']:
                if token['is_protected'] or token['custom_lemma']:
                    print(f"   → {token['text']}: 保護={token['is_protected']}, カスタム={token['custom_lemma']}")
            
            print()
        
        print("✅ 単語境界問題テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ 単語境界問題テスト失敗: {e}")
        return False

def run_all_tests():
    """全テストを実行"""
    print("🚀 栄養データベース検索システム動作確認テスト")
    print("=" * 60)
    print()
    
    tests = [
        test_component_imports,
        test_spacy_setup,
        test_query_preprocessor,
        test_query_builder,
        test_search_handler,
        test_word_boundary_examples
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            results.append(False)
        
        print()
    
    # 結果サマリー
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"成功: {passed}/{total}")
    
    if passed == total:
        print("🎉 全てのテストが成功しました！")
        print("\n次のステップ:")
        print("1. Elasticsearchサーバーを起動")
        print("2. 栄養データベースをインデックス化")
        print("3. 実際の検索テストを実行")
    else:
        print("⚠️  一部のテストが失敗しました。エラーメッセージを確認してください。")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests() 