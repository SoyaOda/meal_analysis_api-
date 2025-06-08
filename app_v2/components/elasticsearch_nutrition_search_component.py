"""
Elasticsearch強化栄養検索コンポーネント
仕様書に基づく高度なDBクエリフェーズの実装
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import asdict
import math

from .base import BaseComponent
from ..models.nutrition_search_models import (
    NutritionQueryInput, NutritionQueryOutput, NutritionMatch, NutritionNutrient,
    convert_usda_query_input_to_nutrition, convert_nutrition_to_usda_query_output
)
from ..models.usda_models import USDAQueryInput, USDAQueryOutput
from ..elasticsearch.search_service import food_search_service, SearchQuery, NutritionTarget, SearchResult
from ..elasticsearch.client import es_client
from ..elasticsearch.config import es_config

logger = logging.getLogger(__name__)


class ElasticsearchNutritionSearchComponent(BaseComponent[USDAQueryInput, USDAQueryOutput]):
    """
    Elasticsearch強化栄養検索コンポーネント
    
    仕様書のフェーズA（Elasticsearch基盤構築）および
    フェーズB（栄養プロファイル類似性スコアリング）を実装
    
    Local Nutrition Searchと同様に、内部では汎用NutritionQueryモデルを使用し、
    外部インターフェースではUSDAQueryモデルとの互換性を保持します。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__("ElasticsearchNutritionSearchComponent")
        self.component_name = "ElasticsearchNutritionSearchComponent"
        self.logger = logging.getLogger(f"{__name__}.{self.component_name}")
        
        # データベース初期化フラグ
        self._db_initialized = False
        self._initialization_error = None
        
    async def _ensure_elasticsearch_ready(self) -> bool:
        """Elasticsearchの準備ができていることを確認"""
        try:
            if self._initialization_error:
                # 以前の初期化エラーがある場合は再試行しない
                self.logger.error(f"Elasticsearch initialization previously failed: {self._initialization_error}")
                return False
            
            if self._db_initialized:
                return True
            
            # Elasticsearch接続チェック
            health_ok = await es_client.health_check()
            if not health_ok:
                self.logger.error("Elasticsearch health check failed")
                self._initialization_error = "Elasticsearch health check failed"
                return False
            
            # インデックス存在チェック
            if not es_client.client.indices.exists(index=es_config.food_nutrition_index):
                self.logger.warning(f"Elasticsearch index '{es_config.food_nutrition_index}' does not exist")
                self._initialization_error = f"Index '{es_config.food_nutrition_index}' not found"
                return False
            
            self._db_initialized = True
            self.logger.info("Elasticsearch nutrition search system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Elasticsearch: {e}")
            self._initialization_error = str(e)
            return False
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elasticsearch栄養検索の実行（Phase1栄養プロファイル対応）
        
        Args:
            input_data: {
                'ingredient_names': List[str],
                'dish_names': List[str] (optional),
                'target_nutrition_profile': Dict[str, float] (optional) - Phase1からの栄養プロファイル
            }
            
        Returns:
            検索結果
        """
        self.logger.info("Starting Elasticsearch nutrition search with enhanced nutritional similarity")
        
        # 入力データの解析
        ingredient_names = input_data.get('ingredient_names', [])
        dish_names = input_data.get('dish_names', [])
        # 🎯 Phase1からの栄養プロファイルを取得
        target_nutrition_profile = input_data.get('target_nutrition_profile', {})
        
        # 入力ログ
        self.log_processing_detail("input_ingredient_names", ingredient_names)
        self.log_processing_detail("input_dish_names", dish_names)
        self.log_processing_detail("input_target_nutrition_profile", target_nutrition_profile)
        self.log_processing_detail("total_search_terms", len(ingredient_names) + len(dish_names))
        
        # 🎯 栄養プロファイルの詳細ログ
        if target_nutrition_profile:
            self.log_reasoning(
                "nutritional_similarity_enabled",
                f"Using Phase1 nutrition profile for enhanced search: "
                f"{target_nutrition_profile.get('calories', 0):.0f}kcal, "
                f"{target_nutrition_profile.get('protein_g', 0):.1f}g protein, "
                f"{target_nutrition_profile.get('fat_total_g', 0):.1f}g fat, "
                f"{target_nutrition_profile.get('carbohydrate_by_difference_g', 0):.1f}g carbs per 100g"
            )
        else:
            self.log_reasoning(
                "nutritional_similarity_disabled",
                "No nutrition profile provided from Phase1 - using lexical search only"
            )
        
        # 検索実行
        matches = {}
        
        # 🎯 食材名の検索（基本食材を優先）
        for ingredient_name in ingredient_names:
            if not ingredient_name or ingredient_name.strip() == '':
                continue
                
            try:
                self.log_processing_detail(f"searching_ingredient", ingredient_name)
                
                # 🎯 食材専用検索（基本的な食材を優先）
                search_results = await self._perform_ingredient_search(
                    query=ingredient_name,
                    target_nutrition_profile=target_nutrition_profile
                )
                
                if search_results:
                    # 🎯 食材らしい結果を優先選択 - より厳格な基本食材判定
                    ingredient_results = []
                    branded_ingredient_results = []
                    basic_ingredient_results = []  # 🎯 真の基本食材を別途収集
                    
                    for result in search_results:
                        if self._is_basic_ingredient(result, ingredient_name):
                            if result.data_type == "branded":
                                branded_ingredient_results.append(result)
                            else:
                                ingredient_results.append(result)
                        
                        # 🎯 さらに厳格な基本食材判定
                        if self._is_truly_basic_ingredient(result, ingredient_name):
                            basic_ingredient_results.append(result)
                    
                    # 🎯 全結果を優先度スコア順にソート
                    all_results_with_priority = []
                    for result in search_results:
                        priority = self._get_ingredient_priority_score(result, ingredient_name)
                        all_results_with_priority.append((result, priority))
                    
                    # 優先度スコア順（降順）でソート
                    all_results_with_priority.sort(key=lambda x: x[1], reverse=True)
                    prioritized_results = [item[0] for item in all_results_with_priority[:5]]
                    
                    # ログ出力
                    if prioritized_results:
                        top_result = prioritized_results[0]
                        top_priority = all_results_with_priority[0][1]
                        self.log_reasoning(
                            "ingredient_priority_sorting",
                            f"Sorted by priority for '{ingredient_name}'. Top result: {top_result.food_name} "
                            f"(priority: {top_priority}, type: {top_result.data_type})"
                        )
                    
                    nutrition_match = self._convert_to_nutrition_match(prioritized_results[0], ingredient_name, search_type="ingredient")
                    matches[ingredient_name] = nutrition_match
                    
                    # 詳細なマッチング情報をログ
                    self.log_reasoning(
                        f"ingredient_match_found_{ingredient_name}",
                        f"Found ingredient match for '{ingredient_name}': {prioritized_results[0].food_name} "
                        f"(score: {prioritized_results[0].score:.3f}, type: {prioritized_results[0].data_type}, "
                        f"nutrition: {prioritized_results[0].nutrition.get('calories', 0):.0f}kcal/100g)"
                    )
                else:
                    self.log_processing_detail(f"no_ingredient_match_for", ingredient_name)
                    self.log_reasoning(
                        f"no_ingredient_match_{ingredient_name}",
                        f"No suitable ingredient matches found for '{ingredient_name}' in Elasticsearch database"
                    )
                
            except Exception as e:
                self.logger.error(f"Ingredient search failed for '{ingredient_name}': {str(e)}")
                self.log_processing_detail(f"ingredient_search_error_{ingredient_name}", str(e))
        
        # 🎯 料理名の検索（料理を優先）
        for dish_name in dish_names:
            if not dish_name or dish_name.strip() == '':
                continue
                
            try:
                self.log_processing_detail(f"searching_dish", dish_name)
                
                # 🎯 料理専用検索（複合料理を優先）
                search_results = await self._perform_dish_search(
                    query=dish_name,
                    target_nutrition_profile=target_nutrition_profile
                )
                
                if search_results:
                    # 🎯 料理らしい結果を優先選択
                    dish_results = []
                    branded_dish_results = []
                    for result in search_results:
                        if self._is_complex_dish(result, dish_name):
                            if result.data_type == "branded":
                                branded_dish_results.append(result)
                            else:
                                dish_results.append(result)
                    
                    # 料理らしい結果の優先順位：dish > branded > その他
                    prioritized_results = dish_results + branded_dish_results
                    
                    # 料理らしい結果がない場合は、最初の5件を返す
                    if not prioritized_results:
                        prioritized_results = search_results[:5]
                        self.log_reasoning(
                            "dish_fallback",
                            f"No complex dishes found for '{dish_name}', using top general matches"
                        )
                    else:
                        self.log_reasoning(
                            "dish_filtered",
                            f"Found {len(dish_results)} dish matches and {len(branded_dish_results)} branded dish matches for '{dish_name}'"
                        )
                    
                    nutrition_match = self._convert_to_nutrition_match(prioritized_results[0], dish_name, search_type="dish")
                    matches[dish_name] = nutrition_match
                    
                    # 詳細なマッチング情報をログ
                    self.log_reasoning(
                        f"dish_match_found_{dish_name}",
                        f"Found dish match for '{dish_name}': {prioritized_results[0].food_name} "
                        f"(score: {prioritized_results[0].score:.3f}, type: {prioritized_results[0].data_type}, "
                        f"nutrition: {prioritized_results[0].nutrition.get('calories', 0):.0f}kcal/100g)"
                    )
                else:
                    self.log_processing_detail(f"no_dish_match_for", dish_name)
                    self.log_reasoning(
                        f"no_dish_match_{dish_name}",
                        f"No suitable dish matches found for '{dish_name}' in Elasticsearch database"
                    )
                
            except Exception as e:
                self.logger.error(f"Dish search failed for '{dish_name}': {str(e)}")
                self.log_processing_detail(f"dish_search_error_{dish_name}", str(e))
        
        # 結果統計
        total_searches = len(ingredient_names) + len(dish_names)
        successful_matches = len(matches)
        match_rate = (successful_matches / total_searches * 100) if total_searches > 0 else 0
        
        self.log_processing_detail("search_statistics", {
            "total_searches": total_searches,
            "ingredient_searches": len(ingredient_names),
            "dish_searches": len(dish_names),
            "successful_matches": successful_matches,
            "failed_searches": total_searches - successful_matches,
            "match_rate_percent": round(match_rate, 1)
        })
        
        self.logger.info(f"Elasticsearch search completed: {successful_matches}/{total_searches} matches ({match_rate:.1f}%)")
        
        return {
            'matches': {term: match.model_dump() for term, match in matches.items()},
            'statistics': {
                'total_searches': total_searches,
                'successful_matches': successful_matches,
                'match_rate': match_rate
            }
        }
    
    async def _perform_ingredient_search(
        self, 
        query: str, 
        target_nutrition_profile: Dict[str, float]
    ) -> List[SearchResult]:
        """
        食材専用検索（基本的な食材を優先）
        ingredientとbrandedのみを検索対象とする
        
        Args:
            query: 検索クエリ（食材名）
            target_nutrition_profile: 栄養プロファイル
            
        Returns:
            List[SearchResult]: 検索結果（食材優先）
        """
        try:
            self.log_processing_detail("ingredient_search_method", "ingredient_and_branded_only")
            self.log_processing_detail("ingredient_search_term", query)
            
            # 食材優先の検索クエリを構築
            search_query = self._build_ingredient_search_query(query, target_nutrition_profile)
            
            # 🎯 ingredientとbrandedのみを検索対象とする
            data_type_filter = ["ingredient", "branded"]
            
            # Elasticsearch検索実行（食材優先フィルタ付き）
            search_results = await food_search_service.search_foods(
                query=search_query,
                size=20,  # 🎯 食材検索では多めに取得してより良い候補を探す
                enable_nutritional_similarity=True,
                enable_semantic_similarity=False,  # 食材検索では語彙的マッチを重視
                data_type_filter=data_type_filter  # 🎯 タイプフィルター追加
            )
            
            self.log_processing_detail("ingredient_search_raw_results", len(search_results))
            self.log_reasoning(
                "ingredient_search_filter",
                f"Searched for '{query}' with data_type filter: {data_type_filter}"
            )
            
            if not search_results:
                self.logger.warning(f"No ingredient results found for '{query}'")
                return []
            
            # 🎯 ingredient タイプを優先し、brandedを補助として使用
            ingredient_results = []
            branded_ingredient_results = []
            
            for result in search_results:
                if result.data_type == "ingredient":
                    ingredient_results.append(result)
                elif result.data_type == "branded":
                    branded_ingredient_results.append(result)
            
            # 優先順位: ingredient > branded
            prioritized_results = ingredient_results + branded_ingredient_results
            
            # 結果をスコア順にソート（同じタイプ内での順序）
            prioritized_results.sort(key=lambda x: x.score, reverse=True)
            
            # ログ出力
            if prioritized_results:
                top_result = prioritized_results[0]
                self.log_reasoning(
                    "ingredient_type_priority",
                    f"Found ingredient match for '{query}': {top_result.food_name} "
                    f"(type: {top_result.data_type}, score: {top_result.score:.3f})"
                )
                
                # タイプ別の結果数をログ
                self.log_processing_detail(
                    "ingredient_results_breakdown",
                    f"ingredient: {len(ingredient_results)}, branded: {len(branded_ingredient_results)}"
                )
            
            return prioritized_results[:5]  # 上位5件に制限
            
        except Exception as e:
            self.logger.error(f"Ingredient search failed for '{query}': {e}")
            return []

    def _is_reasonable_ingredient_fallback(self, result: SearchResult, query: str) -> bool:
        """
        フォールバック用のより寛容な食材判定
        """
        food_name = result.food_name.lower()
        query_lower = query.lower()
        
        # 絶対に避けるべき複合料理パターン
        absolute_exclusions = [
            "sauce", "soup", "salad", "sandwich", "burger", "pizza", "pie", "cake",
            "parfait", "casserole", "stew", "curry", "pasta", "lasagna", "quesadilla",
            "taco", "enchilada", "wrap", "roll"
        ]
        
        for exclusion in absolute_exclusions:
            if exclusion in food_name:
                return False
        
        # クエリが含まれていて、比較的短い名前（4単語以下）
        if query_lower in food_name and len(food_name.split()) <= 4:
            return True
        
        return False

    async def _perform_dish_search(
        self, 
        query: str, 
        target_nutrition_profile: Dict[str, float]
    ) -> List[SearchResult]:
        """
        料理専用検索（複合料理を優先）
        dishとbrandedのみを検索対象とする
        
        Args:
            query: 検索クエリ（料理名）
            target_nutrition_profile: 栄養プロファイル
            
        Returns:
            List[SearchResult]: 検索結果（料理優先）
        """
        try:
            self.log_processing_detail("dish_search_method", "dish_and_branded_only")
            self.log_processing_detail("dish_search_term", query)
            
            # 料理優先の検索クエリを構築
            search_query = self._build_dish_search_query(query, target_nutrition_profile)
            
            # 🎯 dishとbrandedのみを検索対象とする
            data_type_filter = ["dish", "branded"]
            
            # Elasticsearch検索実行（料理優先）
            search_results = await food_search_service.search_foods(
                query=search_query,
                size=15,  # 料理検索でも多めに取得
                enable_nutritional_similarity=True,
                enable_semantic_similarity=es_config.enable_semantic_search,
                data_type_filter=data_type_filter  # 🎯 タイプフィルター追加
            )
            
            self.log_processing_detail("dish_search_raw_results", len(search_results))
            self.log_reasoning(
                "dish_search_filter",
                f"Searched for '{query}' with data_type filter: {data_type_filter}"
            )
            
            if not search_results:
                self.logger.warning(f"No dish results found for '{query}'")
                return []
            
            # 🎯 dish タイプを優先し、brandedを補助として使用
            dish_results = []
            branded_dish_results = []
            
            for result in search_results:
                if result.data_type == "dish":
                    dish_results.append(result)
                elif result.data_type == "branded":
                    branded_dish_results.append(result)
            
            # 優先順位: dish > branded
            prioritized_results = dish_results + branded_dish_results
            
            # 結果をスコア順にソート（同じタイプ内での順序）
            prioritized_results.sort(key=lambda x: x.score, reverse=True)
            
            # ログ出力
            if prioritized_results:
                top_result = prioritized_results[0]
                self.log_reasoning(
                    "dish_type_priority",
                    f"Found dish match for '{query}': {top_result.food_name} "
                    f"(type: {top_result.data_type}, score: {top_result.score:.3f})"
                )
                
                # タイプ別の結果数をログ
                self.log_processing_detail(
                    "dish_results_breakdown",
                    f"dish: {len(dish_results)}, branded: {len(branded_dish_results)}"
                )
            else:
                self.log_reasoning(
                    "dish_fallback",
                    f"No dish or branded results found for '{query}'"
                )
            
            return prioritized_results[:5]  # 上位5件に制限
            
        except Exception as e:
            self.logger.error(f"Dish search failed for '{query}': {e}")
            return []

    def _build_ingredient_search_query(self, query: str, target_nutrition_profile: Dict[str, float]) -> SearchQuery:
        """
        食材専用検索クエリを構築（厳格な完全一致重視）
        """
        # 🎯 基本クエリ語彙（食材名そのもの）+ 完全一致優先
        # 完全一致を最優先にするため、クエリを厳格に設定
        elasticsearch_query_terms = f'"{query}"^3.0 {query}^2.0'  # 完全一致に高いブースト
        
        # 🎯 食材検索では必ず完全一致を優先
        exact_phrase = query  # 常に完全一致を指定
        
        # 栄養プロファイル目標値の構築
        target_nutrition_vector = None
        if target_nutrition_profile:
            default_nutrition = self._calculate_default_nutrition_values()
            
            target_nutrition_vector = NutritionTarget(
                calories=target_nutrition_profile.get('calories', default_nutrition['calories']),
                protein_g=target_nutrition_profile.get('protein_g', default_nutrition['protein_g']),
                fat_total_g=target_nutrition_profile.get('fat_total_g', default_nutrition['fat_total_g']),
                carbohydrate_by_difference_g=target_nutrition_profile.get('carbohydrate_by_difference_g', default_nutrition['carbohydrate_by_difference_g'])
            )
        
        return SearchQuery(
            elasticsearch_query_terms=elasticsearch_query_terms,
            exact_phrase=exact_phrase,
            target_nutrition_vector=target_nutrition_vector,
            semantic_embedding=None  # 食材検索ではセマンティック検索は使わない
        )

    def _build_dish_search_query(self, query: str, target_nutrition_profile: Dict[str, float]) -> SearchQuery:
        """
        料理専用検索クエリを構築
        """
        # 基本クエリ語彙
        elasticsearch_query_terms = query
        
        # 料理検索では部分一致も許容
        exact_phrase = None
        if " " in query and len(query.split()) <= 4:
            exact_phrase = query
        
        # 栄養プロファイル目標値の構築
        target_nutrition_vector = None
        if target_nutrition_profile:
            default_nutrition = self._calculate_default_nutrition_values()
            
            target_nutrition_vector = NutritionTarget(
                calories=target_nutrition_profile.get('calories', default_nutrition['calories']),
                protein_g=target_nutrition_profile.get('protein_g', default_nutrition['protein_g']),
                fat_total_g=target_nutrition_profile.get('fat_total_g', default_nutrition['fat_total_g']),
                carbohydrate_by_difference_g=target_nutrition_profile.get('carbohydrate_by_difference_g', default_nutrition['carbohydrate_by_difference_g'])
            )
        
        # セマンティック埋め込み（料理検索で使用）
        semantic_embedding = None
        if es_config.enable_semantic_search:
            # TODO: 実際のセマンティック埋め込みを生成
            pass
        
        return SearchQuery(
            elasticsearch_query_terms=elasticsearch_query_terms,
            exact_phrase=exact_phrase,
            target_nutrition_vector=target_nutrition_vector,
            semantic_embedding=semantic_embedding
        )

    def _is_basic_ingredient(self, result: SearchResult, query: str) -> bool:
        """
        基本的な食材かどうかを判定（brandedも含む）- より厳格な判定
        """
        food_name = result.food_name.lower()
        query_lower = query.lower()
        data_type = result.data_type or ""
        
        # 🎯 食材データタイプの優先（brandedも含む）
        if data_type in ["ingredient", "branded"]:
            # brandedでも基本的な食材パターンかチェック
            if data_type == "ingredient":
                # ingredientタイプでも複合料理は除外
                return self._is_truly_simple_food(food_name, query_lower)
            elif data_type == "branded":
                # brandedの場合は名前パターンで判定
                return self._is_simple_food_name(food_name, query_lower)
        
        # 🎯 厳格な除外パターン（調理法や複合語が含まれていない）
        # 調理法関連の除外パターンを大幅に拡張
        complex_patterns = [
            # 調理法
            "with", "and", "in", "glazed", "roasted", "fried", "baked", "grilled", "sauce", 
            "soup", "salad", "pie", "cake", "parfait", "wrap", "prepared", "cooked", "steamed",
            "boiled", "sauteed", "braised", "marinated", "seasoned", "spiced", "stuffed",
            
            # 料理タイプ
            "casserole", "stew", "curry", "pasta", "noodle", "bread", "sandwich", "burger",
            "pizza", "taco", "quesadilla", "enchilada", "lasagna", "risotto", "chili",
            
            # 複合表現
            "mixed", "blend", "medley", "combination", "assorted", "variety", "selection",
            "topped", "covered", "layered", "filled", "rolled", "sliced", "diced", "chopped",
            
            # その他の除外語
            "recipe", "homemade", "leftover", "frozen", "fresh", "organic", "raw", "dried",
            "canned", "bottled", "packaged", "instant", "quick", "easy", "traditional"
        ]
        
        # より厳格な複合語チェック
        for pattern in complex_patterns:
            if pattern in food_name:
                return False
        
        # 🎯 追加の厳格チェック：単語数制限
        words = food_name.split()
        if len(words) > 2:  # 2単語を超える場合は複合的と判定
            # 例外：「chicken breast」「ground beef」など許可する基本的なパターン
            allowed_two_word_patterns = [
                f"{query_lower} breast", f"{query_lower} thigh", f"{query_lower} wing",
                f"ground {query_lower}", f"fresh {query_lower}", f"raw {query_lower}",
                f"{query_lower} fillet", f"{query_lower} steak"
            ]
            food_name_simple = " ".join(words[:2])  # 最初の2単語
            if not any(pattern in food_name_simple for pattern in allowed_two_word_patterns):
                return False
        
        # 🎯 クエリ語彙と高い類似性がある場合のみ許可（より厳格）
        if query_lower in food_name:
            # さらに厳格：クエリがfood_nameの最初の単語である場合のみ許可
            first_word = words[0] if words else ""
            return first_word == query_lower or food_name.startswith(query_lower + " ")
        
        # 🎯 基本的な食材パターンの追加チェック
        return self._is_truly_simple_food(food_name, query_lower)

    def _is_truly_basic_ingredient(self, result: SearchResult, query: str) -> bool:
        """
        真の基本食材かどうかを判定（最も厳格な基準）
        """
        food_name = result.food_name.lower()
        query_lower = query.lower()
        data_type = result.data_type or ""
        
        # 🎯 絶対優先：ingredientタイプで基本パターンを含む
        if data_type == "ingredient":
            # 調査で発見した基本食材パターン
            basic_ingredient_patterns = [
                'ground chicken', 'chicken breast', 'chicken thigh', 'chicken wing',
                'chicken drumstick', 'chicken leg', 'chicken meat', 'chicken, raw',
                'chicken, broilers', 'corn, yellow', 'walnuts, nuts', 'lettuce,',
                'tomato,', 'potato,', 'onion,'
            ]
            
            # クエリが含まれ、基本パターンのいずれかにマッチ
            if query_lower in food_name:
                for pattern in basic_ingredient_patterns:
                    if pattern in food_name:
                        return True
                
                # ingredientタイプで2語以下、クエリを含む場合も基本食材
                if len(food_name.split()) <= 2:
                    return True
        
        # 🎯 次優先：brandedでも非常にシンプルな基本食材パターン
        elif data_type == "branded":
            # 例：「Chicken Breast, Safeway」「Iceberg Lettuce, Freshdirect」
            if query_lower in food_name and len(food_name.split()) <= 3:
                # ブランド名やストア名の一般的なパターン
                store_brands = [
                    'safeway', 'freshdirect', 'tesco', 'kirkland', 'signature', 
                    'organic', 'natural', 'whole foods', 'trader joe'
                ]
                # 基本部位パターン
                basic_parts = [
                    'breast', 'thigh', 'wing', 'drumstick', 'leg', 'ground'
                ]
                
                has_store = any(brand in food_name for brand in store_brands)
                has_basic_part = any(part in food_name for part in basic_parts)
                
                if has_store or has_basic_part:
                    return True
        
        return False

    def _get_ingredient_priority_score(self, result: SearchResult, query: str) -> int:
        """
        食材の優先度スコアを計算（高いほど優先）
        """
        food_name = result.food_name.lower()
        query_lower = query.lower()
        data_type = result.data_type or ""
        
        # 🎯 最高優先度：ingredientタイプの基本食材
        if self._is_truly_basic_ingredient(result, query):
            if data_type == "ingredient":
                return 1000  # 最高優先度
            elif data_type == "branded":
                return 900   # 高優先度
        
        # 🎯 高優先度：ingredientタイプ
        if data_type == "ingredient":
            return 800
        
        # 🎯 中優先度：brandedタイプ
        if data_type == "branded":
            return 700
        
        # 🎯 低優先度：dishタイプでも基本的な名前
        if data_type == "dish":
            # 単語数が少なく、複合料理キーワードがない
            complex_keywords = [
                'with', 'and', 'sauce', 'stroganoff', 'curry', 'alfredo',
                'carbonara', 'glazed', 'stuffed', 'casserole', 'pie'
            ]
            
            words = len(food_name.split())
            has_complex = any(keyword in food_name for keyword in complex_keywords)
            
            if not has_complex and words <= 2 and query_lower in food_name:
                return 600  # 中程度優先度
            else:
                return 100  # 低優先度
        
        return 0  # 最低優先度

    def _is_truly_simple_food(self, food_name: str, query_lower: str) -> bool:
        """
        真にシンプルな食品かどうかを厳格に判定
        """
        words = food_name.split()
        
        # 1単語の場合はほぼ確実にシンプル
        if len(words) == 1:
            return query_lower in food_name
        
        # 2単語の場合は基本的なパターンのみ許可
        if len(words) == 2:
            basic_modifiers = [
                "fresh", "raw", "dried", "ground", "whole", "organic", "free range",
                "breast", "thigh", "wing", "fillet", "steak", "chop"
            ]
            second_word = words[1]
            first_word = words[0]
            
            # クエリが最初の単語で、2番目が基本的な修飾語の場合のみ許可
            if first_word == query_lower and second_word in basic_modifiers:
                return True
            # または、クエリが2番目の単語で、1番目が基本的な修飾語の場合
            if second_word == query_lower and first_word in basic_modifiers:
                return True
        
        # 3単語以上は基本的に複合食品と判定
        return False

    def _is_complex_dish(self, result: SearchResult, query: str) -> bool:
        """
        複合料理かどうかを判定（brandedも含む）
        """
        food_name = result.food_name.lower()
        query_lower = query.lower()
        data_type = result.data_type or ""
        
        # 🎯 料理データタイプの優先（brandedも含む）
        if data_type in ["dish", "branded"]:
            if data_type == "dish":
                return True
            elif data_type == "branded":
                # brandedの場合は名前パターンで判定
                return self._is_complex_food_name(food_name, query_lower)
        
        # 🎯 複合的な名前パターン
        # 良いパターン：「with」、「and」、「glazed」、「roasted」などが含まれる
        complex_patterns = ["with", "and", "glazed", "roasted", "fried", "baked", "grilled", "sauce", "soup", "salad", "pie", "cake", "parfait", "wrap", "skillet", "gratin", "prepared", "cooked", "meal", "dinner", "lunch"]
        
        for pattern in complex_patterns:
            if pattern in food_name:
                return True
        
        # 🎯 複数の単語からなる料理名
        if len(food_name.split()) >= 3:
            return True
        
        # 🎯 複合料理パターンの追加チェック
        return self._is_complex_food_name(food_name, query_lower)

    def _is_simple_food_name(self, food_name: str, query_lower: str) -> bool:
        """
        シンプルな食品名かどうかを判定（brandedの基本食材判定用）
        """
        # ブランド名やシンプルな食材名のパターン
        simple_patterns = [
            query_lower,  # クエリそのもの
            f"{query_lower} ",  # クエリで始まる
            f" {query_lower}",  # クエリで終わる
            f" {query_lower} "  # クエリが含まれる
        ]
        
        # クエリが含まれ、かつ短い名前（4単語以下）
        if any(pattern in food_name for pattern in simple_patterns) and len(food_name.split()) <= 4:
            return True
        
        # 一般的な基本食材キーワード
        basic_food_keywords = [
            "milk", "cheese", "butter", "eggs", "chicken", "beef", "pork", "fish", "salmon", "tuna",
            "rice", "bread", "pasta", "noodles", "flour", "sugar", "salt", "oil", "vinegar",
            "apple", "banana", "orange", "tomato", "lettuce", "carrot", "potato", "onion"
        ]
        
        for keyword in basic_food_keywords:
            if keyword in food_name and keyword in query_lower:
                return True
        
        return False

    def _is_complex_food_name(self, food_name: str, query_lower: str) -> bool:
        """
        複合的な食品名かどうかを判定（brandedの料理判定用）
        """
        # 料理らしいキーワード
        dish_keywords = [
            "meal", "dinner", "lunch", "breakfast", "entree", "main", "side", "appetizer",
            "pizza", "burger", "sandwich", "pasta", "salad", "soup", "stew", "curry",
            "casserole", "stir fry", "roast", "grilled", "baked", "fried"
        ]
        
        for keyword in dish_keywords:
            if keyword in food_name:
                return True
        
        # 複数の食材が組み合わされたパターン
        if " and " in food_name or " with " in food_name:
            return True
        
        # 長い名前（5単語以上）は料理の可能性が高い
        if len(food_name.split()) >= 5:
            return True
        
        return False

    async def _perform_enhanced_search(
        self, 
        query: str, 
        target_nutrition_profile: Dict[str, float]
    ) -> List[SearchResult]:
        """
        栄養プロファイル類似性を考慮した検索実行（レガシー互換性のため残す）
        """
        # 新しい食材/料理専用検索にリダイレクト
        return await self._perform_ingredient_search(query, target_nutrition_profile)
    
    def _calculate_default_nutrition_values(self) -> Dict[str, float]:
        """デフォルト栄養値を動的計算"""
        # 平均的な食品の栄養プロファイル（100gあたり）
        base_calories_per_100g = 180.0
        protein_ratio = 0.18  # 18%がタンパク質
        fat_ratio = 0.25      # 25%が脂質
        carb_ratio = 0.57     # 57%が炭水化物
        
        protein_calories = base_calories_per_100g * protein_ratio
        fat_calories = base_calories_per_100g * fat_ratio
        carb_calories = base_calories_per_100g * carb_ratio
        
        return {
            "calories": base_calories_per_100g,
            "protein_g": protein_calories / 4.0,  # 1g protein = 4kcal
            "fat_total_g": fat_calories / 9.0,    # 1g fat = 9kcal
            "carbohydrate_by_difference_g": carb_calories / 4.0  # 1g carb = 4kcal
        }
    
    def _convert_to_nutrition_match(self, search_result, original_search_term: str, search_type: str) -> NutritionMatch:
        """
        Elasticsearch検索結果をNutritionMatchに変換
        """
        # 🎯 修正：スコア正規化方法を改善（対数スケールで0-1範囲に正規化）
        raw_score = search_result.score
        if raw_score > 100:
            confidence_score = 1.0  # 高スコアの場合は最高評価
        elif raw_score > 1:
            # 対数スケールで正規化（1-100 → 0.1-1.0）
            confidence_score = 0.1 + (math.log10(raw_score) / 2.0) * 0.9
        else:
            confidence_score = raw_score / 10.0  # 低スコアはそのまま
        
        confidence_score = min(max(confidence_score, 0.0), 1.0)  # 0-1範囲にクリップ
        
        # 栄養情報の変換（100gあたり）
        nutrients = []
        # 🎯 修正：コア4栄養素のみを使用（fiber_total_dietary, sodium等は削除）
        core_nutrients = {
            "calories": "エネルギー",
            "protein_g": "タンパク質",
            "fat_total_g": "脂質",
            "carbohydrate_by_difference_g": "炭水化物"
        }
        
        for key, display_name in core_nutrients.items():
            value = search_result.nutrition.get(key)
            if value is not None:
                # 🎯 修正：unit_nameフィールドを適切に設定
                unit_name = "g" if key != "calories" else "kcal"
                nutrients.append(NutritionNutrient(
                    name=display_name,
                    amount=value,
                    unit_name=unit_name  # unitではなくunit_nameを使用
                ))
        
        # データタイプの決定（search_typeと組み合わせて判定）
        original_data_type = search_result.data_type or "Unknown"
        
        # 🎯 search_typeを考慮したデータタイプ決定
        if search_type == "ingredient":
            # 食材検索の場合
            if original_data_type == "ingredient":
                data_type = "Local Ingredient"
            elif original_data_type == "branded" and self._is_basic_ingredient(search_result, original_search_term):
                data_type = "Local Branded Ingredient"  # brandedの基本食材
            elif original_data_type == "dish" and self._is_basic_ingredient(search_result, original_search_term):
                data_type = "Local Ingredient"  # 複合料理だが基本的な食材として分類
            elif original_data_type == "branded":
                data_type = "Local Branded (Complex)"  # brandedだが複合的
            else:
                data_type = "Local Ingredient (Complex)"  # 複合的だが食材として検索された
        elif search_type == "dish":
            # 料理検索の場合
            if original_data_type == "dish":
                data_type = "Local Dish"
            elif original_data_type == "branded" and self._is_complex_dish(search_result, original_search_term):
                data_type = "Local Branded Dish"  # brandedの複合料理
            elif original_data_type == "ingredient" and self._is_complex_dish(search_result, original_search_term):
                data_type = "Local Dish"  # 食材だが料理として分類
            elif original_data_type == "branded":
                data_type = "Local Branded (Simple)"  # brandedだがシンプル
            else:
                data_type = "Local Dish (Simple)"  # シンプルだが料理として検索された
        else:
            # 従来の分類
            if original_data_type == "dish":
                data_type = "Local Dish"
            elif original_data_type == "ingredient":
                data_type = "Local Ingredient"
            elif original_data_type == "branded":
                data_type = "Local Branded"
            else:
                data_type = "Local Unknown"
        
        return NutritionMatch(
            id=search_result.food_id,  # idフィールドを使用
            description=search_result.food_name,  # descriptionフィールドを使用
            data_type=data_type,
            source=data_type,  # 🎯 修正："Elasticsearch"から適切なdata_typeに変更
            nutrients=nutrients,
            score=confidence_score,
            original_data={
                "food_id": search_result.food_id,
                "fdc_id": search_result.fdc_id,
                "category": search_result.category,
                "search_method": "nutritional_similarity",
                "original_data_type": original_data_type,
                "score_normalization": f"raw:{raw_score:.4f} -> normalized:{confidence_score:.4f}",
                "search_type": search_type
            }
        ) 