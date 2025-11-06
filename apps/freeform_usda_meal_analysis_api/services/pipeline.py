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
from fastapi import HTTPException

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
        usda_metadata_file: str = None,
        stage1_top_k: int = None,
        device: str = "cpu",
        hybrid_engine=None,
        use_lazy_loading: bool = True
    ):
        """
        Args:
            vlm_model_id: DeepInfra VLMモデルID（Noneの場合はconfig設定値を使用）
            vlm_prompt_file: VLMプロンプトファイルのパス
            index_dir: FAISSインデックスディレクトリのパス
            usda_metadata_file: USDA Metadataファイルのパス (栄養素データを含む)
            stage1_top_k: Stage1で取得する候補数（Noneの場合はsettingsから取得）
            device: 計算デバイス
            hybrid_engine: HybridSearchEngineインスタンス（オプション）
        """
        logger.info("Initializing Meal Analysis Pipeline (Full Index Only)...")

        # 設定を取得
        from ..config.settings import get_settings
        settings = get_settings()

        # stage1_top_kが指定されていない場合は設定から取得
        if stage1_top_k is None:
            stage1_top_k = settings.DEFAULT_STAGE1_TOP_K

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
            device=device,
            hybrid_engine=hybrid_engine,
            use_lazy_loading=use_lazy_loading
        )

        # 栄養素サービス初期化
        self.nutrition_service = LocalUSDANutritionService(
            metadata_file=usda_metadata_file
        )

        self.nutrition_calculator = NutritionCalculator(self.nutrition_service)

        # コスト計算サービス初期化
        from .cost_calculator import CostCalculator
        self.cost_calculator = CostCalculator()

        logger.info("✅ Meal Analysis Pipeline initialized successfully")

    async def analyze_image(
        self,
        image_bytes: bytes,
        image_mime_type: str = "image/jpeg",
        vlm_temperature: Optional[float] = None,
        vlm_seed: Optional[int] = None,
        vlm_max_tokens: Optional[int] = None,
        vlm_thinking_budget: Optional[int] = None,
        vlm_enable_thinking: Optional[bool] = None,
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
        try:
            vlm_response, usage = await self.vlm_service.analyze_image(
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                temperature=vlm_temperature,
                seed=vlm_seed,
                max_tokens=vlm_max_tokens,
                thinking_budget=vlm_thinking_budget,
                enable_thinking=vlm_enable_thinking
            )
        except Exception as e:
            logger.error(f"VLM analysis failed: {e}")
            raise RuntimeError(f"[Pipeline] VLM image analysis failed: {e}") from e

        # vlm_responseのNullチェック
        if vlm_response is None:
            logger.error("VLM returned None response")
            raise ValueError("[Pipeline] VLM returned None response")

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
            search_results = await self._sequential_search(queries)

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
        API用の画像分析エンドポイント(パラメータオーバーライド対応)

        Args:
            image_bytes: 画像データ
            user_context: ユーザーコンテキスト
            model_config_override: モデル設定のオーバーライド(ModelConfigオブジェクト)
            search_config_override: 検索設定のオーバーライド(SearchConfigオブジェクト)

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
            if model_config_override.enable_thinking is not None:
                vlm_kwargs["vlm_enable_thinking"] = model_config_override.enable_thinking

        # プロンプトのオーバーライド(一時的に変更)
        original_prompt = None
        if model_config_override and model_config_override.prompt_path:
            from ..config import get_settings
            settings = get_settings()
            prompt_full_path = settings.get_prompt_path(model_config_override.prompt_path)
            original_prompt = self.vlm_service.prompt
            self.vlm_service.prompt = self.vlm_service._load_prompt(prompt_full_path)

        # モデルIDのオーバーライド(一時的に変更)
        original_model_id = None
        if model_config_override and model_config_override.model_id:
            original_model_id = self.vlm_service.model_id
            self.vlm_service.model_id = model_config_override.model_id
            # プロバイダーも更新（VLMProviderFactoryを使用）
            from .providers import VLMProviderFactory
            self.vlm_service.provider = VLMProviderFactory.create_provider(
                model_id=model_config_override.model_id
            )
            # 後方互換性のため
            self.vlm_service.deepinfra_service = self.vlm_service.provider

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
                main_food = dish.get("main_food")

                ingredients = []

                # main_foodがNoneの場合はextrasのみの料理として扱う（正常ケース）
                if main_food is None:
                    logger.info("📝 Dish has no main_food (extras-only dish)")
                else:
                    # main_foodが存在する場合はUSDA検索結果を確認
                    usda_match = main_food.get("usda_match")
                    nutrition = main_food.get("nutrition")

                    # USDA検索が失敗した場合は明確なエラー
                    if not usda_match:
                        search_name = main_food.get("search_name")
                        if not search_name:
                            logger.error(f"❌ main_food is missing 'search_name' field")
                            logger.error(f"   main_food content: {main_food}")
                            # raise HTTPException を Exception に変更
                            raise Exception(
                                "VLM returned a dish with main_food but no search_name field. "
                                "This indicates a VLM response format error."
                            )
                        else:
                            logger.error(f"❌ USDA search failed for main_food: '{search_name}'")
                            logger.error(f"   main_food: {main_food}")
                            # raise HTTPException を Exception に変更
                            raise Exception(
                                f"USDA food database search failed for ingredient: '{search_name}'. "
                                f"The food item could not be matched in the USDA database."
                            )

                    # 正常にUSDA検索できた場合の処理
                    main_fdc_id = usda_match.get("fdc_id")
                    main_nutrition_per_100g = self.nutrition_service.get_nutrition_per_100g(main_fdc_id) if main_fdc_id else None

                    # デバッグ情報を抽出
                    debug_info = {
                        "retriever_candidates": usda_match.get("retriever_candidates", []),
                        "reranker_results": usda_match.get("reranker_results", []),
                        "retry_count": usda_match.get("retry_count", 0)
                    }

                    ingredients.append(
                        IngredientDetail(
                            ingredient_name=main_food.get("matched_description", main_food.get("search_name", "")),
                            weight_g=main_food.get("weight_g", 0.0),
                            nutrition_per_100g=NutritionInfo(
                                calories=main_nutrition_per_100g.get("calories", 0.0) if main_nutrition_per_100g else 0.0,
                                protein=main_nutrition_per_100g.get("protein_g", 0.0) if main_nutrition_per_100g else 0.0,
                                fat=main_nutrition_per_100g.get("fat_g", 0.0) if main_nutrition_per_100g else 0.0,
                                carbs=main_nutrition_per_100g.get("carbs_g", 0.0) if main_nutrition_per_100g else 0.0,
                            ),
                            calculated_nutrition=NutritionInfo(
                                calories=nutrition.get("calories", 0.0) if nutrition else 0.0,
                                protein=nutrition.get("protein_g", 0.0) if nutrition else 0.0,
                                fat=nutrition.get("fat_g", 0.0) if nutrition else 0.0,
                                carbs=nutrition.get("carbs_g", 0.0) if nutrition else 0.0,
                            ),
                            source_db="usda_fndds",
                            fdc_id=str(usda_match.get("fdc_id", "")),
                            calculation_notes=[f"Weight: {main_food.get('weight_g', 0)}g"],
                            debug_info=debug_info
                        )
                    )

                # Extrasを追加
                for extra in dish.get("extras", []):
                    extra_nutrition = extra.get("nutrition", {})
                    extra_usda = extra.get("usda_match", {})

                    # fdc_idから100gあたりの栄養素を取得
                    extra_fdc_id = extra_usda.get("fdc_id")
                    extra_nutrition_per_100g = self.nutrition_service.get_nutrition_per_100g(extra_fdc_id) if extra_fdc_id else None

                    # extraのデバッグ情報を抽出
                    extra_debug_info = {
                        "retriever_candidates": extra_usda.get("retriever_candidates", []),
                        "reranker_results": extra_usda.get("reranker_results", []),
                        "retry_count": extra_usda.get("retry_count", 0)
                    }

                    ingredients.append(
                        IngredientDetail(
                            ingredient_name=extra.get("matched_description", extra.get("search_name", "Unknown")),
                            weight_g=extra.get("weight_g", 0.0),
                            nutrition_per_100g=NutritionInfo(
                                calories=extra_nutrition_per_100g.get("calories", 0.0) if extra_nutrition_per_100g else 0.0,
                                protein=extra_nutrition_per_100g.get("protein_g", 0.0) if extra_nutrition_per_100g else 0.0,
                                fat=extra_nutrition_per_100g.get("fat_g", 0.0) if extra_nutrition_per_100g else 0.0,
                                carbs=extra_nutrition_per_100g.get("carbs_g", 0.0) if extra_nutrition_per_100g else 0.0,
                            ),
                            calculated_nutrition=NutritionInfo(
                                calories=extra_nutrition.get("calories", 0.0) if extra_nutrition else 0.0,
                                protein=extra_nutrition.get("protein_g", 0.0) if extra_nutrition else 0.0,
                                fat=extra_nutrition.get("fat_g", 0.0) if extra_nutrition else 0.0,
                                carbs=extra_nutrition.get("carbs_g", 0.0) if extra_nutrition else 0.0,
                            ),
                            source_db="usda_fndds",
                            fdc_id=str(extra_usda.get("fdc_id", "")),
                            calculation_notes=[f"Weight: {extra.get('weight_g', 0)}g"],
                            debug_info=extra_debug_info
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

            # Usage情報とコスト計算
            from ..models.response_models import UsageInfo
            # プロンプト内容を取得（デバッグ用）
            prompt_content = self.vlm_service.prompt if hasattr(self.vlm_service, 'prompt') else None
            usage_info = None
            if result.get("usage"):
                usage_data = result["usage"]
                cost_data = self.cost_calculator.calculate_cost(
                    model_id=ai_model_used,
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0)
                )

                # cost_dataがNoneの場合（pricing情報がないモデル）はtoken情報のみ
                if cost_data is None:
                    usage_info = UsageInfo(
                        prompt_tokens=usage_data.get("prompt_tokens", 0),
                        completion_tokens=usage_data.get("completion_tokens", 0),
                        total_tokens=usage_data.get("total_tokens", 0),
                        estimated_cost_usd=None,
                        model_pricing=None,
                        raw_vlm_output=usage_data.get("raw_vlm_output"),
                        prompt_content=prompt_content
                    )
                else:
                    usage_info = UsageInfo(
                        prompt_tokens=cost_data["prompt_tokens"],
                        completion_tokens=cost_data["completion_tokens"],
                        total_tokens=cost_data["total_tokens"],
                        estimated_cost_usd=cost_data["estimated_cost_usd"],
                        model_pricing=cost_data["model_pricing"],
                        raw_vlm_output=usage_data.get("raw_vlm_output"),
                        prompt_content=prompt_content
                    )

            return {
                "dishes": api_dishes,
                "total_nutrition": total_nutrition,
                "ai_model_used": ai_model_used,
                "prompt_file_used": prompt_file_used,
                "match_rate_percent": match_rate,
                "usage": usage_info,
                "warnings": [],
            }

        except Exception as e:
            # エラー詳細をログ出力（元のエラーメッセージを保持）
            logger.error(f"❌ analyze_meal_from_image failed: {str(e)}", exc_info=True)
            # エラーを再発生（元のエラーメッセージを保持）
            raise

        finally:
            # プロンプトを元に戻す
            if original_prompt is not None:
                self.vlm_service.prompt = original_prompt
            # モデルIDを元に戻す
            if original_model_id is not None:
                self.vlm_service.model_id = original_model_id
                # プロバイダーも元に戻す（VLMProviderFactoryを使用）
                from .providers import VLMProviderFactory
                self.vlm_service.provider = VLMProviderFactory.create_provider(
                    model_id=original_model_id
                )
                # 後方互換性のため
                self.vlm_service.deepinfra_service = self.vlm_service.provider

    async def _parallel_search(self, queries: List[Dict[str, Any]]) -> List[Optional[Dict[str, Any]]]:
        """USDA検索を並列実行"""
        # 非同期関数を直接並列実行
        tasks = []
        for query in queries:
            task = self.food_search_service.search(
                query=query['search_name'],
                search_mode="full_index_only",
                stage1_top_k=1
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return list(results)

    async def _sequential_search(self, queries: List[Dict[str, Any]]) -> List[Optional[Dict[str, Any]]]:
        """USDA検索を逐次実行"""
        results = []
        for query in queries:
            result = await self.food_search_service.search(
                query=query['search_name'],
                search_mode="full_index_only",
                stage1_top_k=1
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
            else:
                # main_foodがnullの場合は明示的にNoneを設定（extrasのみの料理）
                enriched_dish['main_food'] = None

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
            # main_food処理
            main_food = dish.get('main_food')

            if main_food is None:
                # extras-onlyの料理（正常ケース）
                logger.debug("📝 Dish has no main_food (extras-only), skipping main_food nutrition")
            elif isinstance(main_food, dict):
                # main_foodが辞書の場合（正常ケース）
                main_nutrition = main_food.get('nutrition')
                if main_nutrition:
                    if not isinstance(main_nutrition, dict):
                        raise ValueError(
                            f"❌ Invalid main_food.nutrition type: expected dict, got {type(main_nutrition).__name__}. "
                            f"Value: {main_nutrition}"
                        )
                    for key in total:
                        total[key] += main_nutrition.get(key, 0.0)
            else:
                # main_foodがNoneでも辞書でもない（異常ケース）
                raise ValueError(
                    f"❌ Invalid main_food type: expected dict or None, got {type(main_food).__name__}. "
                    f"main_food value: {main_food}"
                )

            # extras処理
            extras = dish.get('extras')
            if extras is None:
                extras = []
            elif not isinstance(extras, list):
                raise ValueError(
                    f"❌ Invalid extras type: expected list or None, got {type(extras).__name__}. "
                    f"extras value: {extras}"
                )

            for extra in extras:
                if not isinstance(extra, dict):
                    raise ValueError(
                        f"❌ Invalid extra item type: expected dict, got {type(extra).__name__}. "
                        f"extra value: {extra}"
                    )
                extra_nutrition = extra.get('nutrition')
                if extra_nutrition:
                    if not isinstance(extra_nutrition, dict):
                        raise ValueError(
                            f"❌ Invalid extra.nutrition type: expected dict, got {type(extra_nutrition).__name__}. "
                            f"Value: {extra_nutrition}"
                        )
                    for key in total:
                        total[key] += extra_nutrition.get(key, 0.0)

        # 丸め処理
        return {k: round(v, 1) for k, v in total.items()}
