"""
高度食品検索サービス
仕様書に基づくElasticsearch検索機能の実装
"""
import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from .client import es_client
from .config import es_config

logger = logging.getLogger(__name__)


@dataclass
class NutritionTarget:
    """栄養プロファイル目標値"""
    calories: float
    protein_g: float
    fat_total_g: float
    carbohydrate_by_difference_g: float
    # 追加栄養素（必要に応じて）
    fiber_total_dietary_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    
    def to_dict(self) -> Dict[str, float]:
        """辞書形式に変換"""
        result = {
            "calories": self.calories,
            "protein_g": self.protein_g,
            "fat_total_g": self.fat_total_g,
            "carbohydrate_by_difference_g": self.carbohydrate_by_difference_g
        }
        
        if self.fiber_total_dietary_g is not None:
            result["fiber_total_dietary_g"] = self.fiber_total_dietary_g
        if self.sodium_mg is not None:
            result["sodium_mg"] = self.sodium_mg
            
        return result


@dataclass
class SearchQuery:
    """検索クエリ情報"""
    elasticsearch_query_terms: str
    exact_phrase: Optional[str] = None
    target_nutrition_vector: Optional[NutritionTarget] = None
    semantic_embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    """検索結果アイテム"""
    food_id: str
    fdc_id: Optional[int]
    food_name: str
    description: Optional[str]
    brand_name: Optional[str]
    category: Optional[str]
    data_type: Optional[str]  # 追加：元のデータタイプを保持
    num_favorites: Optional[int]  # 🎯 人気度指標を追加
    nutrition: Dict[str, float]
    score: float
    explanation: Dict[str, Any]


class FoodSearchService:
    """食品検索サービス"""
    
    def __init__(self):
        """初期化"""
        # 🎯 configから設定を読み込み（ハードコード値を排除）
        self.nutrition_normalization = es_config.get_nutrition_normalization_factors()
        self.nutrition_weights = es_config.get_nutrition_weights()
        self.field_boosts = es_config.get_field_boosts()
    
    async def search_foods(
        self, 
        query: SearchQuery, 
        size: int = 10,
        enable_nutritional_similarity: bool = True,
        enable_semantic_similarity: bool = False,
        data_type_filter: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        高度食品検索を実行
        
        Args:
            query: 検索クエリ情報
            size: 結果件数
            enable_nutritional_similarity: 栄養プロファイル類似性を有効にするか
            enable_semantic_similarity: セマンティック類似性を有効にするか
            data_type_filter: 検索対象のデータタイプ (例: ["ingredient", "branded"])
        
        Returns:
            検索結果リスト
        """
        try:
            # Elasticsearchクエリを構築
            es_query = self._build_elasticsearch_query(
                query, 
                enable_nutritional_similarity,
                enable_semantic_similarity,
                data_type_filter
            )
            
            # ログ出力を改善
            query_desc = f"'{query.elasticsearch_query_terms}'"
            if data_type_filter:
                query_desc += f" (filtered to: {', '.join(data_type_filter)})"
            
            logger.info(f"Executing advanced food search for: {query_desc}")
            logger.debug(f"Elasticsearch query: {es_query}")
            
            # 検索実行
            response = await es_client.search(
                index_name=es_config.food_nutrition_index,
                query=es_query,
                size=size
            )
            
            if not response:
                logger.warning("Search response is empty")
                return []
            
            # 結果を解析
            results = self._parse_search_results(response)
            
            logger.info(f"Search completed: {len(results)} results found")
            return results
            
        except Exception as e:
            logger.error(f"Food search failed: {e}")
            return []
    
    def _build_elasticsearch_query(
        self, 
        query: SearchQuery,
        enable_nutritional_similarity: bool,
        enable_semantic_similarity: bool,
        data_type_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        仕様書に基づくElasticsearchクエリを構築
        """
        # ベース語彙的検索クエリ
        base_query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query.elasticsearch_query_terms,
                            "fields": [
                                f"food_name^{self.field_boosts['food_name']}",
                                f"description^{self.field_boosts['description']}",
                                f"brand_name^{self.field_boosts['brand_name']}",
                                f"ingredients_text^{self.field_boosts['ingredients_text']}",
                                f"food_name.phonetic^{self.field_boosts['food_name.phonetic']}"
                            ],
                            "type": "most_fields",
                            "fuzziness": "AUTO"  # typo許容
                        }
                    }
                ],
                "should": [],  # 加点要素
                "filter": []   # フィルタ条件
            }
        }
        
        # データタイプフィルタを追加
        if data_type_filter:
            base_query["bool"]["filter"].append({
                "terms": {
                    "data_type": data_type_filter
                }
            })
        
        # フレーズ一致ブーストを追加
        if query.exact_phrase:
            base_query["bool"]["should"].append({
                "match_phrase": {
                    "food_name": {
                        "query": query.exact_phrase,
                        "boost": es_config.phrase_match_boost
                    }
                }
            })
        
        # 🎯 configベースでfunction_scoreを制御
        functions = []
        
        # 人気度ブースト（configで制御）
        if es_config.enable_popularity_boost:
            popularity_function = self._build_popularity_boost_function()
            functions.append(popularity_function)
            logger.info("🎯 Popularity boost enabled via config")
        
        # 栄養プロファイル類似性（configで制御）
        if (es_config.enable_nutritional_similarity and 
            enable_nutritional_similarity and 
            query.target_nutrition_vector):
            nutrition_function = self._build_nutrition_similarity_function(query.target_nutrition_vector)
            functions.append(nutrition_function)
            logger.info("🎯 Nutritional similarity scoring enabled via config")
        
        # function_scoreを適用するかベースクエリのみにするか決定
        if functions:
            function_score_query = {
                "function_score": {
                    "query": base_query,
                    "functions": functions,
                    "score_mode": "sum",     # 各スコアを合計
                    "boost_mode": "multiply" # 元のクエリスコアに関数スコアを乗算
                }
            }
            return {"query": function_score_query}
        else:
            # function_scoreが無効の場合はベースクエリのみ
            logger.info("🎯 Using pure lexical search (no function_score)")
            return {"query": base_query}
    
    def _build_nutrition_similarity_function(self, target: NutritionTarget) -> Dict[str, Any]:
        """
        栄養プロファイル類似性スコアリング関数を構築
        """
        target_dict = target.to_dict()
        
        # 必須栄養素フィールドの存在チェック用フィルタ
        nutrition_filter = {
            "bool": {
                "must": [
                    {"exists": {"field": "nutrition.calories"}},
                    {"exists": {"field": "nutrition.protein_g"}},
                    {"exists": {"field": "nutrition.fat_total_g"}},
                    {"exists": {"field": "nutrition.carbohydrate_by_difference_g"}}
                ]
            }
        }
        
        # Painlessスクリプト：正規化重み付け逆ユークリッド距離
        nutrition_script = """
            // Target values from Gemini Phase 1
            double target_cal = params.target_nutrition_vector.calories;
            double target_pro = params.target_nutrition_vector.protein_g;
            double target_fat = params.target_nutrition_vector.fat_total_g;
            double target_carb = params.target_nutrition_vector.carbohydrate_by_difference_g;
            
            // Normalization factors
            double norm_cal = params.normalization_factors.calories;
            double norm_pro = params.normalization_factors.protein_g;
            double norm_fat = params.normalization_factors.fat_total_g;
            double norm_carb = params.normalization_factors.carbohydrate_by_difference_g;
            
            // Weights
            double w_cal = params.weights.calories;
            double w_pro = params.weights.protein_g;
            double w_fat = params.weights.fat_total_g;
            double w_carb = params.weights.carbohydrate_by_difference_g;
            
            // Calculate normalized differences
            double cal_diff = (doc['nutrition.calories'].value - target_cal) / norm_cal;
            double pro_diff = (doc['nutrition.protein_g'].value - target_pro) / norm_pro;
            double fat_diff = (doc['nutrition.fat_total_g'].value - target_fat) / norm_fat;
            double carb_diff = (doc['nutrition.carbohydrate_by_difference_g'].value - target_carb) / norm_carb;
            
            // Calculate weighted squared distance
            double dist_sq = w_cal * cal_diff * cal_diff +
                             w_pro * pro_diff * pro_diff +
                             w_fat * fat_diff * fat_diff +
                             w_carb * carb_diff * carb_diff;
            
            // Return inverse similarity score
            return 1.0 / (1.0 + Math.sqrt(dist_sq));
        """
        
        return {
            "filter": nutrition_filter,
            "script_score": {
                "script": {
                    "source": nutrition_script,
                    "params": {
                        "target_nutrition_vector": target_dict,
                        "normalization_factors": self.nutrition_normalization,
                        "weights": self.nutrition_weights
                    }
                }
            },
            "weight": es_config.nutritional_similarity_weight
        }
    
    def _build_popularity_boost_function(self) -> Dict[str, Any]:
        """
        人気度（num_favorites）によるブースト関数を構築
        
        Returns:
            人気度ブースト関数
        """
        # 🎯 より安全でシンプルな人気度ブースト
        popularity_script = """
            // num_favoritesフィールドの存在確認と安全なアクセス
            if (!doc.containsKey('num_favorites') || doc['num_favorites'].empty) {
                return 1.0; // デフォルト（ブーストなし）
            }
            
            // 安全に値を取得
            long favorites = doc['num_favorites'].value;
            
            // シンプルな段階的ブースト
            if (favorites >= 1000) {
                return 1.2; // 高人気
            } else if (favorites >= 100) {
                return 1.1; // 中人気  
            } else if (favorites >= 10) {
                return 1.05; // 低人気
            } else {
                return 1.0; // ブーストなし
            }
        """
        
        return {
            "script_score": {
                "script": {
                    "source": popularity_script
                }
            },
            "weight": es_config.popularity_boost_weight
        }
    
    def _parse_search_results(self, response: Dict[str, Any]) -> List[SearchResult]:
        """
        Elasticsearch検索結果を解析してSearchResultオブジェクトに変換
        """
        results = []
        
        for hit in response.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            
            # 栄養情報を取得
            nutrition = source.get("nutrition", {})
            
            # 検索結果を構築
            result = SearchResult(
                food_id=source.get("food_id", ""),
                fdc_id=source.get("fdc_id"),
                food_name=source.get("food_name", ""),
                description=source.get("description"),
                brand_name=source.get("brand_name"),
                category=source.get("category"),
                data_type=source.get("data_type"),
                num_favorites=source.get("num_favorites"),
                nutrition=nutrition,
                score=hit.get("_score", 0.0),
                explanation={
                    "total_score": hit.get("_score", 0.0),
                    "elasticsearch_score": hit.get("_score", 0.0)
                }
            )
            
            results.append(result)
        
        return results
    
    async def analyze_query_terms(self, query_text: str) -> List[str]:
        """
        食品名クエリをカスタムアナライザーで分析
        """
        try:
            tokens = await es_client.analyze_text(
                index_name=es_config.food_nutrition_index,
                analyzer="food_item_analyzer", 
                text=query_text
            )
            
            logger.debug(f"Query analysis: '{query_text}' -> {tokens}")
            return tokens or []
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return []


# グローバル検索サービスインスタンス
food_search_service = FoodSearchService() 