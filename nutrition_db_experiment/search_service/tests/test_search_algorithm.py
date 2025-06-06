#!/usr/bin/env python3
"""
Search Algorithm Tests - 検索アルゴリズムの単体・結合テスト

特に単語境界問題（cook vs cookie）の検証を中心とする
"""

import os
import sys
import json
import unittest
from typing import List, Dict, Any

# プロジェクトパスを追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'search_service'))

class TestSearchAlgorithm(unittest.TestCase):
    """検索アルゴリズムのテストケース"""
    
    @classmethod
    def setUpClass(cls):
        """テストセットアップ"""
        try:
            from nlp.query_preprocessor import FoodQueryPreprocessor
            from api.query_builder import NutritionSearchQueryBuilder
            from api.search_handler import NutritionSearchHandler
            
            cls.preprocessor = FoodQueryPreprocessor()
            cls.query_builder = NutritionSearchQueryBuilder()
            cls.search_handler = NutritionSearchHandler()
            
        except Exception as e:
            raise Exception(f"セットアップエラー: {e}")
    
    def test_word_boundary_preprocessing(self):
        """単語境界問題のクエリ前処理テスト"""
        print("\n🔧 単語境界問題のクエリ前処理テスト")
        
        test_cases = [
            # cook関連のテスト
            {
                "input": "cook",
                "expected": "cook",
                "should_match": ["cook", "cooked", "cooking"],
                "should_not_match": ["cookie", "cookies"]
            },
            {
                "input": "cooking",
                "expected": "cook",  # cookにレンマ化される
                "should_match": ["cook", "cooked", "cooking"],
                "should_not_match": ["cookie", "cookies"]
            },
            {
                "input": "cooked",
                "expected": "cooked",  # 保護されてそのまま残る
                "should_match": ["cook", "cooked", "cooking"],
                "should_not_match": ["cookie", "cookies"]
            },
            # cookie関連のテスト
            {
                "input": "cookie",
                "expected": "cookie",  # 保護されてそのまま残る
                "should_match": ["cookie", "cookies"],
                "should_not_match": ["cook", "cooking", "cooked"]
            },
            {
                "input": "cookies",
                "expected": "cookies",  # 保護されてそのまま残る
                "should_match": ["cookie", "cookies"],
                "should_not_match": ["cook", "cooking", "cooked"]
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(input=test_case["input"]):
                result = self.preprocessor.preprocess_query(test_case["input"])
                print(f"📝 '{test_case['input']}' → '{result}'")
                
                # 期待される結果の確認
                self.assertEqual(result, test_case["expected"],
                               f"'{test_case['input']}'の前処理結果が期待値と異なります")
    
    def test_phrase_preprocessing(self):
        """フレーズクエリの前処理テスト"""
        print("\n🔧 フレーズクエリの前処理テスト")
        
        test_cases = [
            {
                "input": "chicken breast",
                "expected": "chicken breast",
                "description": "基本的なフレーズ"
            },
            {
                "input": "chocolate chip cookies",
                "expected": "chocolate chip cookies",
                "description": "cookieが保護されるフレーズ"
            },
            {
                "input": "baking a cake with flour",
                "expected": "baking cake flour",  # "a", "with"がストップワード除去
                "description": "ストップワード除去を含むフレーズ"
            },
            {
                "input": "cooking ground beef",
                "expected": "cook ground beef",  # cookingがcookにレンマ化
                "description": "レンマ化を含むフレーズ"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(input=test_case["input"]):
                result = self.preprocessor.preprocess_query(test_case["input"])
                print(f"📝 '{test_case['input']}' → '{result}' ({test_case['description']})")
                
                self.assertEqual(result, test_case["expected"],
                               f"フレーズ前処理が期待値と異なります: {test_case['description']}")
    
    def test_query_builder_structure(self):
        """クエリビルダー構造テスト"""
        print("\n🔧 クエリビルダー構造テスト")
        
        test_cases = [
            {
                "processed_query": "cook",
                "original_query": "cook",
                "db_type_filter": None,
                "description": "基本的な単語クエリ"
            },
            {
                "processed_query": "cookie",
                "original_query": "cookie",
                "db_type_filter": "branded",
                "description": "フィルタ付きクエリ"
            },
            {
                "processed_query": "chicken breast",
                "original_query": "chicken breast",
                "db_type_filter": "ingredient",
                "description": "フレーズクエリ"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(description=test_case["description"]):
                query = self.query_builder.build_search_query(
                    processed_query=test_case["processed_query"],
                    original_query=test_case["original_query"],
                    db_type_filter=test_case["db_type_filter"]
                )
                
                print(f"📝 {test_case['description']}")
                
                # 基本構造の確認
                self.assertIn("query", query)
                self.assertIn("size", query)
                self.assertIn("_source", query)
                
                # クエリタイプの確認
                query_structure = query["query"]
                if test_case["db_type_filter"]:
                    # フィルタ付きの場合はboolクエリ
                    self.assertIn("bool", query_structure)
                    self.assertIn("must", query_structure["bool"])
                    self.assertIn("filter", query_structure["bool"])
                    
                    # フィルタの確認
                    filter_term = query_structure["bool"]["filter"][0]
                    self.assertEqual(filter_term["term"]["db_type"], test_case["db_type_filter"])
                    
                    # 内部のfunction_scoreの確認
                    inner_query = query_structure["bool"]["must"][0]
                    self.assertIn("function_score", inner_query)
                else:
                    # フィルタなしの場合は直接function_score
                    self.assertIn("function_score", query_structure)
                
                print(f"   ✅ 構造確認完了")
    
    def test_function_score_functions(self):
        """function_score関数の詳細テスト"""
        print("\n🔧 function_score関数の詳細テスト")
        
        query = self.query_builder.build_search_query(
            processed_query="cook chicken",
            original_query="cooking chicken",
            db_type_filter=None
        )
        
        # function_scoreの取得
        function_score = query["query"]["function_score"]
        functions = function_score["functions"]
        
        print(f"📝 関数数: {len(functions)}")
        
        # 関数の種類確認
        function_types = []
        for func in functions:
            filter_query = func["filter"]
            if "match_phrase" in filter_query:
                if "search_name.exact" in filter_query["match_phrase"]:
                    function_types.append("exact_phrase")
                elif "search_name" in filter_query["match_phrase"]:
                    function_types.append("proximity_phrase")
            elif "term" in filter_query:
                function_types.append("exact_word")
            elif "match_phrase_prefix" in filter_query:
                function_types.append("prefix_match")
        
        print(f"📝 関数タイプ: {function_types}")
        
        # 期待される関数タイプが含まれているか確認
        expected_types = ["exact_phrase", "proximity_phrase", "prefix_match"]
        for expected_type in expected_types:
            self.assertIn(expected_type, function_types,
                         f"期待される関数タイプが見つかりません: {expected_type}")
        
        # スコアモードの確認
        self.assertEqual(function_score["score_mode"], "sum")
        self.assertEqual(function_score["boost_mode"], "sum")
        
        print("   ✅ function_score設定確認完了")
    
    def test_search_handler_integration(self):
        """検索ハンドラー統合テスト（モックモード）"""
        print("\n🔧 検索ハンドラー統合テスト")
        
        from api.search_handler import SearchRequest
        
        test_cases = [
            {
                "query": "cook",
                "db_type_filter": None,
                "description": "cook検索（フィルタなし）"
            },
            {
                "query": "cookie",
                "db_type_filter": "branded",
                "description": "cookie検索（brandedフィルタ）"
            },
            {
                "query": "chicken breast",
                "db_type_filter": "ingredient",
                "description": "フレーズ検索（ingredientフィルタ）"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(description=test_case["description"]):
                request = SearchRequest(
                    query=test_case["query"],
                    db_type_filter=test_case["db_type_filter"],
                    size=10
                )
                
                response = self.search_handler.search(request)
                
                print(f"📝 {test_case['description']}")
                print(f"   元クエリ: '{response.query_info['original_query']}'")
                print(f"   処理済み: '{response.query_info['processed_query']}'")
                print(f"   結果数: {response.total_hits}")
                print(f"   処理時間: {response.took_ms}ms")
                
                # 基本的な応答確認
                self.assertIsInstance(response.results, list)
                self.assertGreaterEqual(response.total_hits, 0)
                self.assertGreaterEqual(response.took_ms, 0)
                self.assertIn("original_query", response.query_info)
                self.assertIn("processed_query", response.query_info)
                
                print("   ✅ 統合テスト完了")
    
    def test_word_boundary_test_cases_validation(self):
        """単語境界テストケースの妥当性確認"""
        print("\n🔧 単語境界テストケースの妥当性確認")
        
        # テストケースファイルの読み込み
        test_cases_file = os.path.join(
            os.path.dirname(__file__), 
            "test_data", 
            "word_boundary_test_cases.json"
        )
        
        self.assertTrue(os.path.exists(test_cases_file), 
                       "単語境界テストケースファイルが存在しません")
        
        with open(test_cases_file, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
        
        print(f"📝 テストケース数: {len(test_cases)}")
        
        for i, test_case in enumerate(test_cases):
            with self.subTest(case_index=i):
                # 必須フィールドの確認
                required_fields = ["query", "db_type_filter", "expected_top_results_patterns"]
                for field in required_fields:
                    self.assertIn(field, test_case, 
                                f"テストケース{i}に必須フィールド'{field}'がありません")
                
                # クエリの前処理テスト
                processed = self.preprocessor.preprocess_query(test_case["query"])
                print(f"   ケース{i+1}: '{test_case['query']}' → '{processed}'")
                
                # 検索クエリ構築テスト
                query = self.query_builder.build_search_query(
                    processed_query=processed,
                    original_query=test_case["query"],
                    db_type_filter=test_case["db_type_filter"]
                )
                
                self.assertIsInstance(query, dict)
                self.assertIn("query", query)
        
        print("   ✅ テストケース妥当性確認完了")

class TestProtectedTerms(unittest.TestCase):
    """保護タームの詳細テスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストセットアップ"""
        from nlp.query_preprocessor import FoodQueryPreprocessor
        cls.preprocessor = FoodQueryPreprocessor()
    
    def test_protected_terms_preservation(self):
        """保護タームが正しく保護されるかテスト"""
        print("\n🔧 保護タームの保護テスト")
        
        # 保護されるべき単語
        protected_words = ["cookie", "cookies", "orange", "baked"]
        
        for word in protected_words:
            with self.subTest(word=word):
                analysis = self.preprocessor.analyze_query(word)
                
                # 保護されたタームの存在確認
                protected_tokens = [
                    token for token in analysis["tokens"] 
                    if token["is_protected"]
                ]
                
                self.assertGreater(len(protected_tokens), 0,
                                 f"'{word}'が保護されていません")
                
                print(f"📝 '{word}' → 保護済み: {len(protected_tokens)}個のトークン")
    
    def test_lemma_overrides(self):
        """レンマ上書きの動作テスト"""
        print("\n🔧 レンマ上書き動作テスト")
        
        override_cases = [
            {"input": "cooking", "expected": "cook"},
            {"input": "cooked", "expected": "cooked"},  # 保護される
            {"input": "baking", "expected": "baking"},  # 保護される
        ]
        
        for case in override_cases:
            with self.subTest(input=case["input"]):
                result = self.preprocessor.preprocess_query(case["input"])
                print(f"📝 '{case['input']}' → '{result}'")
                
                # 期待される結果と一致するか確認
                self.assertEqual(result, case["expected"],
                               f"レンマ上書き結果が期待値と異なります")

def run_search_algorithm_tests():
    """検索アルゴリズムテストの実行"""
    print("🧪 検索アルゴリズム単体・結合テスト")
    print("=" * 60)
    
    # テストスイートの作成
    test_suite = unittest.TestSuite()
    
    # テストケースの追加
    test_suite.addTest(unittest.makeSuite(TestSearchAlgorithm))
    test_suite.addTest(unittest.makeSuite(TestProtectedTerms))
    
    # テストランナーの設定
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=False
    )
    
    # テスト実行
    result = runner.run(test_suite)
    
    # 結果サマリー
    print("\n📊 テスト結果サマリー")
    print("=" * 60)
    print(f"実行: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("🎉 全てのテストが成功しました！")
    else:
        print("⚠️  一部のテストが失敗しました。")
        
        if result.failures:
            print("\n失敗:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print("\nエラー:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_search_algorithm_tests() 