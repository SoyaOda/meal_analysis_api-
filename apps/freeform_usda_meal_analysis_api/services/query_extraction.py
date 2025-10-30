#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Query Extraction Service

VLMレスポンスから検索クエリを抽出する。
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class QueryExtractionService:
    """
    VLMレスポンスからUSDA検索用のクエリを抽出するサービス
    """

    def extract_queries(self, vlm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        VLMレスポンスからクエリリストを抽出

        Args:
            vlm_response: VLMの解析結果（dishes配列を含む）

        Returns:
            クエリリスト: [
                {
                    "search_name": str,
                    "description": str,
                    "weight_g": float,
                    "confidence": float,
                    "dish_index": int,  # どのdishに属するか
                    "is_main_food": bool  # main_food or extras
                },
                ...
            ]
        """
        all_queries = []

        dishes = vlm_response.get("dishes", [])

        for dish_index, dish in enumerate(dishes):
            # Main food を抽出
            main_food = dish.get("main_food")
            if main_food:
                query = self._create_query_from_food_item(
                    food_item=main_food,
                    dish_index=dish_index,
                    is_main_food=True
                )
                if query:
                    all_queries.append(query)

            # Extras を抽出
            extras = dish.get("extras", [])
            for extra in extras:
                query = self._create_query_from_food_item(
                    food_item=extra,
                    dish_index=dish_index,
                    is_main_food=False
                )
                if query:
                    all_queries.append(query)

        logger.info(f"Extracted {len(all_queries)} queries from {len(dishes)} dishes")

        return all_queries

    def _create_query_from_food_item(
        self,
        food_item: Dict[str, Any],
        dish_index: int,
        is_main_food: bool
    ) -> Dict[str, Any]:
        """
        食材アイテムからクエリを作成
        V2プロンプト対応: VLMからweight_gを直接取得し、なければフォールバック

        Args:
            food_item: VLMレスポンスの食材オブジェクト
            dish_index: どのdishに属するか
            is_main_food: main_foodかextrasか

        Returns:
            クエリオブジェクト（Noneの場合は無効な食材）
        """
        search_name = food_item.get("search_name", "").strip()

        if not search_name:
            logger.warning(f"Empty search_name in dish {dish_index} (is_main={is_main_food})")
            return None

        description = (food_item.get("description") or "").strip()
        confidence = food_item.get("confidence", 0.0)
        
        # V2プロンプト: VLMから直接weight_gを取得
        weight_g = food_item.get("weight_g")
        
        # 後方互換性: weight_gがない場合は体積×密度で計算（V3対応）
        if weight_g is None:
            volume_cm3 = food_item.get("volume_cm3")
            density_category = food_item.get("density_category")
            estimation_method = food_item.get("estimation_method", "direct")
            
            # 密度カテゴリーごとの密度値（g/cm³）
            density_map = {
                "HIGH": 1.5,      # 肉類、チーズ等
                "MEDIUM": 1.0,    # パスタ、米等
                "LIQUID": 1.0,    # 液体
                "LOW": 0.5,       # 葉物野菜等
                "VERY_LOW": 0.15  # ポップコーン等
            }
            
            if volume_cm3 and density_category and (is_main_food or estimation_method == "volume_density"):
                # 体積×密度から重量を計算
                density = density_map.get(density_category, 1.0)
                weight_g = round(volume_cm3 * density)
                logger.info(f"Calculated weight from volume×density: {weight_g}g "
                           f"(volume={volume_cm3}cm³, density_cat={density_category})")
            elif estimation_method == "direct" and not is_main_food:
                # extras で direct estimation の場合、典型的な分量を使用
                typical_weights = {
                    "cheese": 10,
                    "parmesan": 5,
                    "dressing": 30,
                    "sauce": 25,
                    "ketchup": 20,
                    "mayo": 15,
                    "croutons": 10,
                    "nuts": 15,
                    "bacon": 10,
                }

                # typical weightsから検索
                found_weight = None
                for key, typical_weight in typical_weights.items():
                    if key in search_name.lower():
                        found_weight = typical_weight
                        break

                if found_weight is not None:
                    weight_g = found_weight
                    logger.info(f"Using typical weight for direct estimation: {weight_g}g for '{search_name}'")
                else:
                    # typical weightsに該当しない場合はエラー
                    logger.error(f"No typical weight found for '{search_name}' in direct estimation mode")
                    raise ValueError(
                        f"[Query Extractor] No typical weight found for '{search_name}' "
                        f"in direct estimation mode. VLM should provide weight_g or use volume-based estimation."
                    )
            else:
                # VLMが重量情報を提供していない場合はエラー
                logger.error(
                    f"VLM did not provide weight info for '{search_name}'. "
                    f"volume_cm3={volume_cm3}, density_category={density_category}, "
                    f"estimation_method={estimation_method}, is_main_food={is_main_food}"
                )
                raise ValueError(
                    f"[Query Extractor] VLM did not provide sufficient weight information for '{search_name}'. "
                    f"VLM must provide either weight_g or (volume_cm3 + density_category) for main foods, "
                    f"or use estimation_method='direct' with recognizable ingredient names for extras."
                )
        
        return {
            "search_name": search_name,
            "description": description,
            "weight_g": weight_g,
            "confidence": confidence,
            "dish_index": dish_index,
            "is_main_food": is_main_food
        }

    def group_queries_by_dish(
        self,
        queries: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        クエリをdish_indexでグループ化

        Args:
            queries: クエリリスト

        Returns:
            dish_indexごとにグループ化されたクエリリスト
            [[dish0のクエリ], [dish1のクエリ], ...]
        """
        # dish_indexの最大値を取得
        if not queries:
            return []

        max_dish_index = max(q["dish_index"] for q in queries)

        # dish_indexごとにグループ化
        grouped = [[] for _ in range(max_dish_index + 1)]

        for query in queries:
            dish_index = query["dish_index"]
            grouped[dish_index].append(query)

        return grouped
