#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
End-to-End Meal Analysis Pipeline

VLM画像解析 → クエリ抽出 → USDA検索 → 栄養素計算 の統合パイプライン
"""

import logging
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncio

from .vlm_service import VLMService
from .query_extraction import QueryExtractionService
from .food_search_service import USDAFoodSearchService
from .nutrition_service import LocalUSDANutritionService, NutritionCalculator

logger = logging.getLogger(__name__)


class MealAnalysisPipeline:
    """
    画像から栄養素計算までのEnd-to-Endパイプライン
    """

    def __init__(
        self,
        vlm_model_id: Optional[str] = None,
        vlm_prompt_file: Optional[str] = None,
        index_dir: str = None,
        usda_survey_file: str = None,
        usda_foundation_file: str = None,
        usda_sr_legacy_file: Optional[str] = None,
        stage1_top_k: int = 40,
        device: str = "cpu"
    ):
        """
        Args:
            vlm_model_id: DeepInfra VLMモデルID（Noneの場合はconfig設定値を使用）
            vlm_prompt_file: VLMプロンプトファイルのパス
            index_dir: FAISSインデックスディレクトリのパス
            usda_survey_file: USDA Survey JSONファイルのパス
            usda_foundation_file: USDA Foundation JSONファイルのパス
            usda_sr_legacy_file: USDA SR Legacy JSONファイルのパス（オプション）
            stage1_top_k: Stage1で取得する候補数
            device: 計算デバイス
        """
        logger.info("Initializing Meal Analysis Pipeline (Full Index Only)...")

        # VLMサービス初期化
        self.vlm_service = VLMService(
            model_id=vlm_model_id,
            prompt_file=vlm_prompt_file
        )

        # クエリ抽出サービス初期化
        self.query_extraction = QueryExtractionService()

        # USDA検索サービス初期化（Fullインデックスのみ使用）
        self.food_search_service = USDAFoodSearchService(
            index_dir=index_dir,
            stage1_top_k=stage1_top_k,
            device=device
        )

        # 栄養素サービス初期化
        self.nutrition_service = LocalUSDANutritionService(
            survey_file=usda_survey_file,
            foundation_file=usda_foundation_file,
            sr_legacy_file=usda_sr_legacy_file
        )

        self.nutrition_calculator = NutritionCalculator(self.nutrition_service)

        logger.info("✅ Meal Analysis Pipeline initialized successfully")

    async def analyze_image(
        self,
        image_bytes: bytes,
        image_mime_type: str = "image/jpeg",
        vlm_temperature: Optional[float] = None,
        vlm_seed: Optional[int] = None,
        vlm_max_tokens: Optional[int] = None,
        vlm_thinking_budget: Optional[int] = None,
        parallel_search: bool = True
    ) -> Dict[str, Any]:
        """
        画像から栄養素計算までのEnd-to-End処理

        Args:
            image_bytes: 画像データ
            image_mime_type: 画像MIMEタイプ
            vlm_temperature: VLM temperature（Noneの場合はconfig設定値を使用）
            vlm_seed: VLM seed（Noneの場合はconfig設定値を使用）
            vlm_max_tokens: VLM max tokens（Noneの場合はconfig設定値を使用）
            vlm_thinking_budget: VLM thinking budget（Noneの場合はconfig設定値を使用）
            parallel_search: USDA検索を並列実行するか

        Returns:
            {
                "vlm_output": {...},  # VLMの生出力
                "dishes": [
                    {
                        "main_food": {
                            "search_name": str,
                            "description": str,
                            "weight_g": float,
                            "confidence": float,
                            "usda_match": {
                                "fdc_id": int,
                                "matched_description": str,
                                "rerank_score": float,
                                ...
                            },
                            "nutrition": {
                                "weight_g": float,
                                "calories": float,
                                "protein_g": float,
                                "fat_g": float,
                                "carbs_g": float
                            }
                        },
                        "extras": [...]
                    }
                ],
                "total_nutrition": {
                    "calories": float,
                    "protein_g": float,
                    "fat_g": float,
                    "carbs_g": float
                }
            }
        """
        logger.info("=" * 80)
        logger.info("Starting End-to-End Meal Analysis")
        logger.info("=" * 80)

        # 開始時刻を記録
        start_time = time.time()

        # Step 1: VLM解析
        logger.info("\n🔄 Step 1/4: VLM Image Analysis")
        vlm_response, usage = await self.vlm_service.analyze_image(
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            temperature=vlm_temperature,
            seed=vlm_seed,
            max_tokens=vlm_max_tokens,
            thinking_budget=vlm_thinking_budget
        )

        dishes = vlm_response.get("dishes", [])
        logger.info(f"✅ VLM analysis complete: {len(dishes)} dishes found")

        # Step 2: クエリ抽出
        logger.info("\n🔄 Step 2/4: Query Extraction")
        queries = self.query_extraction.extract_queries(vlm_response)
        logger.info(f"✅ Extracted {len(queries)} queries")

        # Step 3: USDA検索（並列実行）
        logger.info("\n🔄 Step 3/4: USDA Food Search")

        if parallel_search:
            # 並列検索
            search_results = await self._parallel_search(queries)
        else:
            # 逐次検索
            search_results = self._sequential_search(queries)

        logger.info(f"✅ USDA search complete: {len(search_results)} results")

        # Step 4: 栄養素計算
        logger.info("\n🔄 Step 4/4: Nutrition Calculation")

        # クエリに検索結果を付与
        for i, query in enumerate(queries):
            query['usda_match'] = search_results[i]

        # dish構造を再構築
        enriched_dishes = self._build_enriched_dishes(dishes, queries)

        # 全体の栄養素を計算
        total_nutrition = self._calculate_total_nutrition(enriched_dishes)

        logger.info(f"✅ Nutrition calculation complete")
        logger.info(f"   Total: {total_nutrition['calories']} kcal, "
                   f"{total_nutrition['protein_g']}g protein, "
                   f"{total_nutrition['fat_g']}g fat, "
                   f"{total_nutrition['carbs_g']}g carbs")

        # 終了時刻を記録
        end_time = time.time()
        total_time = end_time - start_time

        logger.info("\n" + "=" * 80)
        logger.info("✅ End-to-End Analysis Complete")
        logger.info(f"⏱️  Total time: {total_time:.2f} seconds")
        logger.info("=" * 80)

        return {
            "vlm_output": vlm_response,
            "dishes": enriched_dishes,
            "total_nutrition": total_nutrition,
            "usage": usage,  # VLM usage情報
            "performance": {
                "total_time_seconds": round(total_time, 2),
                "start_time": start_time,
                "end_time": end_time
            }
        }

    async def analyze_meal_from_image(
        self,
        image_bytes: bytes,
        user_context: Optional[str] = None,
        model_config_override: Optional[Any] = None,
        search_config_override: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        API用の画像分析エンドポイント（パラメータオーバーライド対応）

        Args:
            image_bytes: 画像データ
            user_context: ユーザーコンテキスト
            model_config_override: モデル設定のオーバーライド（ModelConfigオブジェクト）
            search_config_override: 検索設定のオーバーライド（SearchConfigオブジェクト）

        Returns:
            API用にフォーマットされた分析結果
        """
        # モデル設定の適用
        vlm_kwargs = {}
        if model_config_override:
            if model_config_override.temperature is not None:
                vlm_kwargs["vlm_temperature"] = model_config_override.temperature
            if model_config_override.max_tokens is not None:
                vlm_kwargs["vlm_max_tokens"] = model_config_override.max_tokens
            if model_config_override.thinking_budget is not None:
                vlm_kwargs["vlm_thinking_budget"] = model_config_override.thinking_budget

        # プロンプトのオーバーライド（一時的に変更）
        original_prompt = None
        if model_config_override and model_config_override.prompt_path:
            from ..config import get_settings
            settings = get_settings()
            prompt_full_path = settings.get_prompt_path(model_config_override.prompt_path)
            original_prompt = self.vlm_service.prompt
            self.vlm_service.prompt = self.vlm_service._load_prompt(prompt_full_path)

        # モデルIDのオーバーライド（一時的に変更）
        original_model_id = None
        if model_config_override and model_config_override.model_id:
            original_model_id = self.vlm_service.model_id
            self.vlm_service.model_id = model_config_override.model_id
            # DeepInfraサービスも更新
            from shared.services.deepinfra_service import DeepInfraService
            self.vlm_service.deepinfra_service = DeepInfraService(
                model_id=model_config_override.model_id
            )

        try:
            # 分析実行
            result = await self.analyze_image(
                image_bytes=image_bytes,
                image_mime_type="image/jpeg",
                **vlm_kwargs
            )

            # API用のレスポンス形式に変換
            from ..models.response_models import (
                IngredientDetail, DishDetail, NutritionInfo
            )

            api_dishes = []
            for dish in result["dishes"]:
                # メインフードを処理
                main_food = dish.get("main_food", {})
                usda_match = main_food.get("usda_match", {})
                nutrition = main_food.get("nutrition", {})

                ingredients = [
                    IngredientDetail(
                        ingredient_name=main_food.get("matched_description", main_food.get("search_name", "Unknown")),
                        weight_g=main_food.get("weight_g", 0.0),
                        nutrition_per_100g=NutritionInfo(
                            calories=usda_match.get("calories_per_100g", 0.0),
                            protein=usda_match.get("protein_per_100g", 0.0),
                            fat=usda_match.get("fat_per_100g", 0.0),
                            carbs=usda_match.get("carbs_per_100g", 0.0),
                        ),
                        calculated_nutrition=NutritionInfo(
                            calories=nutrition.get("calories", 0.0),
                            protein=nutrition.get("protein_g", 0.0),
                            fat=nutrition.get("fat_g", 0.0),
                            carbs=nutrition.get("carbs_g", 0.0),
                        ),
                        source_db="usda_fndds",
                        fdc_id=str(usda_match.get("fdc_id", "")),
                        calculation_notes=[f"Weight: {main_food.get('weight_g', 0)}g"]
                    )
                ]

                # Extrasを追加
                for extra in dish.get("extras", []):
                    extra_nutrition = extra.get("nutrition", {})
                    extra_usda = extra.get("usda_match", {})
                    ingredients.append(
                        IngredientDetail(
                            ingredient_name=extra.get("matched_description", extra.get("search_name", "Unknown")),
                            weight_g=extra.get("weight_g", 0.0),
                            nutrition_per_100g=NutritionInfo(
                                calories=extra_usda.get("calories_per_100g", 0.0),
                                protein=extra_usda.get("protein_per_100g", 0.0),
                                fat=extra_usda.get("fat_per_100g", 0.0),
                                carbs=extra_usda.get("carbs_per_100g", 0.0),
                            ),
                            calculated_nutrition=NutritionInfo(
                                calories=extra_nutrition.get("calories", 0.0),
                                protein=extra_nutrition.get("protein_g", 0.0),
                                fat=extra_nutrition.get("fat_g", 0.0),
                                carbs=extra_nutrition.get("carbs_g", 0.0),
                            ),
                            source_db="usda_fndds",
                            fdc_id=str(extra_usda.get("fdc_id", "")),
                            calculation_notes=[f"Weight: {extra.get('weight_g', 0)}g"]
                        )
                    )

                # 料理の総栄養を計算
                dish_nutrition = NutritionInfo(
                    calories=sum(ing.calculated_nutrition.calories for ing in ingredients),
                    protein=sum(ing.calculated_nutrition.protein for ing in ingredients),
                    fat=sum(ing.calculated_nutrition.fat for ing in ingredients),
                    carbs=sum(ing.calculated_nutrition.carbs for ing in ingredients),
                )

                api_dishes.append(
                    DishDetail(
                        dish_name=main_food.get("description", "Unknown Dish"),
                        confidence=main_food.get("confidence", 0.0),
                        ingredients=ingredients,
                        total_nutrition=dish_nutrition,
                        calculation_metadata={
                            "ingredient_count": len(ingredients),
                            "total_weight_g": sum(ing.weight_g for ing in ingredients),
                        }
                    )
                )

            # 全体の栄養
            total_nutrition = NutritionInfo(
                calories=result["total_nutrition"]["calories"],
                protein=result["total_nutrition"]["protein_g"],
                fat=result["total_nutrition"]["fat_g"],
                carbs=result["total_nutrition"]["carbs_g"],
            )

            # モデル情報
            ai_model_used = model_config_override.model_id if model_config_override and model_config_override.model_id else self.vlm_service.model_id
            prompt_file_used = model_config_override.prompt_path if model_config_override and model_config_override.prompt_path else "freeform_prompt_usda_format_ver_v7_experimental_20251027.txt"

            # マッチ率計算
            total_queries = len(api_dishes)
            matched_queries = sum(1 for dish in api_dishes if len(dish.ingredients) > 0)
            match_rate = (matched_queries / total_queries * 100) if total_queries > 0 else 0.0

            return {
                "dishes": api_dishes,
                "total_nutrition": total_nutrition,
                "ai_model_used": ai_model_used,
                "prompt_file_used": prompt_file_used,
                "match_rate_percent": match_rate,
                "warnings": [],
            }

        finally:
            # プロンプトを元に戻す
            if original_prompt is not None:
                self.vlm_service.prompt = original_prompt
            # モデルIDを元に戻す
            if original_model_id is not None:
                self.vlm_service.model_id = original_model_id
                from shared.services.deepinfra_service import DeepInfraService
                self.vlm_service.deepinfra_service = DeepInfraService(
                    model_id=original_model_id
                )

    async def _parallel_search(self, queries: List[Dict[str, Any]]) -> List[Optional[Dict[str, Any]]]:
        """USDA検索を並列実行"""
        # ThreadPoolExecutorで並列実行（FAISSはGILに影響されにくい）
        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for query in queries:
                future = loop.run_in_executor(
                    executor,
                    self.food_search_service.search,
                    query['search_name'],
                    query['description']
                )
                futures.append(future)

            results = await asyncio.gather(*futures)

        return list(results)

    def _sequential_search(self, queries: List[Dict[str, Any]]) -> List[Optional[Dict[str, Any]]]:
        """USDA検索を逐次実行"""
        results = []
        for query in queries:
            result = self.food_search_service.search(
                search_name=query['search_name'],
                description=query['description']
            )
            results.append(result)

        return results

    def _build_enriched_dishes(
        self,
        original_dishes: List[Dict],
        enriched_queries: List[Dict]
    ) -> List[Dict]:
        """
        元のdish構造にUSDA matchと栄養素を付与

        Args:
            original_dishes: VLMの元のdishes配列
            enriched_queries: USDA matchが付与されたクエリリスト

        Returns:
            栄養素情報が付与されたdishes配列
        """
        # dish_indexでクエリをグループ化
        grouped_queries = self.query_extraction.group_queries_by_dish(enriched_queries)

        enriched_dishes = []

        for dish_index, dish in enumerate(original_dishes):
            enriched_dish = {}

            # main_food処理
            main_food_queries = [
                q for q in grouped_queries[dish_index]
                if q.get('is_main_food', False)
            ]

            if main_food_queries:
                main_query = main_food_queries[0]  # main_foodは1つ
                enriched_main = self._enrich_food_item(
                    original_food=dish.get('main_food', {}),
                    query=main_query
                )
                enriched_dish['main_food'] = enriched_main

            # extras処理
            extras_queries = [
                q for q in grouped_queries[dish_index]
                if not q.get('is_main_food', False)
            ]

            enriched_extras = []
            for extra_query in extras_queries:
                enriched_extra = self._enrich_food_item(
                    original_food={},  # extrasは元の情報が必要ならqueryから復元
                    query=extra_query
                )
                enriched_extras.append(enriched_extra)

            enriched_dish['extras'] = enriched_extras

            enriched_dishes.append(enriched_dish)

        return enriched_dishes

    def _enrich_food_item(
        self,
        original_food: Dict,
        query: Dict
    ) -> Dict:
        """
        食材アイテムにUSDA matchと栄養素を付与
        """
        # 元の情報をコピー
        enriched = {
            "search_name": query['search_name'],
            "description": query['description'],
            "weight_g": query['weight_g'],
            "confidence": query.get('confidence', 0.0)
        }

        # USDA match情報を追加
        usda_match = query.get('usda_match')
        if usda_match:
            enriched['usda_match'] = usda_match

            # 栄養素計算
            fdc_id = usda_match['fdc_id']
            weight_g = query['weight_g']

            nutrition = self.nutrition_calculator.calculate(fdc_id, weight_g)
            enriched['nutrition'] = nutrition
        else:
            enriched['usda_match'] = None
            enriched['nutrition'] = None

        return enriched

    def _calculate_total_nutrition(self, dishes: List[Dict]) -> Dict[str, float]:
        """全dishの栄養素を合計"""
        total = {
            "calories": 0.0,
            "protein_g": 0.0,
            "fat_g": 0.0,
            "carbs_g": 0.0
        }

        for dish in dishes:
            # main_food
            main_food = dish.get('main_food', {})
            main_nutrition = main_food.get('nutrition')
            if main_nutrition:
                for key in total:
                    total[key] += main_nutrition.get(key, 0.0)

            # extras
            for extra in dish.get('extras', []):
                extra_nutrition = extra.get('nutrition')
                if extra_nutrition:
                    for key in total:
                        total[key] += extra_nutrition.get(key, 0.0)

        # 丸め処理
        return {k: round(v, 1) for k, v in total.items()}
