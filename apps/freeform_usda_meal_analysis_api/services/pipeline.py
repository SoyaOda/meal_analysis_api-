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
from ..admin import get_config_manager

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
        
        # インスタンス変数として保存（_parallel_searchで使用）
        self.stage1_top_k = stage1_top_k

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
        vlm_reasoning_effort: Optional[str] = None,
        parallel_search: bool = True,
        # 検索設定パラメータ
        search_stage1_top_k: Optional[int] = None,
        search_bm25_weight: Optional[float] = None,
        search_vector_weight: Optional[float] = None,
        search_rrf_k: Optional[int] = None,
        search_rrf_weight: Optional[float] = None,
        search_reranker_model: Optional[str] = None,
        search_reranker_instruction: Optional[str] = None,
        search_reranker_top_n: Optional[int] = None,
        # デバッグオプション
        include_debug_info: bool = False
    ) -> Dict[str, Any]:
        """
        画像から栄養素計算までのEnd-to-End処理

        Args:
            image_bytes: 画像データ
            image_mime_type: 画像MIMEタイプ
            vlm_temperature: VLM temperature（Noneの場合はconfig設定値を使用）
            vlm_seed: VLM seed（Noneの場合はconfig設定値を使用）
            vlm_max_tokens: VLM max tokens（Noneの場合はconfig設定値を使用）
            vlm_reasoning_effort: Reasoning effort レベル（minimal/low/medium/high/xhigh）
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
                reasoning_effort=vlm_reasoning_effort
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
            search_results = await self._parallel_search(
                queries,
                stage1_top_k=search_stage1_top_k,
                bm25_weight=search_bm25_weight,
                vector_weight=search_vector_weight,
                rrf_k=search_rrf_k,
                rrf_weight=search_rrf_weight,
                reranker_model=search_reranker_model,
                reranker_instruction=search_reranker_instruction,
                reranker_top_n=search_reranker_top_n,
                include_debug_info=include_debug_info
            )
        else:
            # 逐次検索
            search_results = await self._sequential_search(
                queries,
                stage1_top_k=search_stage1_top_k,
                bm25_weight=search_bm25_weight,
                vector_weight=search_vector_weight,
                rrf_k=search_rrf_k,
                rrf_weight=search_rrf_weight,
                reranker_model=search_reranker_model,
                reranker_instruction=search_reranker_instruction,
                reranker_top_n=search_reranker_top_n,
                include_debug_info=include_debug_info
            )

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
        include_debug_info: bool = False,
    ) -> Dict[str, Any]:
        """
        API用の画像分析エンドポイント(パラメータオーバーライド対応)

        Args:
            image_bytes: 画像データ
            user_context: ユーザーコンテキスト
            model_config_override: モデル設定のオーバーライド(ModelConfigオブジェクト)
            search_config_override: 検索設定のオーバーライド(SearchConfigオブジェクト)
            include_debug_info: デバッグ情報を含めるか

        Returns:
            API用にフォーマットされた分析結果
        """
        # ConfigManagerから動的設定を取得
        config_manager = get_config_manager()
        config = config_manager.get_config()

        # モデル設定の適用（オーバーライド > ConfigManager）
        vlm_kwargs = {}
        if model_config_override:
            if model_config_override.temperature is not None:
                vlm_kwargs["vlm_temperature"] = model_config_override.temperature
            if model_config_override.max_tokens is not None:
                vlm_kwargs["vlm_max_tokens"] = model_config_override.max_tokens
            if model_config_override.reasoning_effort is not None:
                vlm_kwargs["vlm_reasoning_effort"] = model_config_override.reasoning_effort
        else:
            # ConfigManagerからデフォルト値を適用
            vlm_kwargs["vlm_temperature"] = config.vlm.temperature
            vlm_kwargs["vlm_max_tokens"] = config.vlm.max_tokens
            vlm_kwargs["vlm_reasoning_effort"] = config.vlm.reasoning_effort

        # 検索設定の適用
        search_kwargs = {}
        if search_config_override:
            if search_config_override.stage1_top_k is not None:
                search_kwargs["search_stage1_top_k"] = search_config_override.stage1_top_k
            if search_config_override.bm25_weight is not None:
                search_kwargs["search_bm25_weight"] = search_config_override.bm25_weight
            if search_config_override.vector_weight is not None:
                search_kwargs["search_vector_weight"] = search_config_override.vector_weight
            if search_config_override.rrf_k is not None:
                search_kwargs["search_rrf_k"] = search_config_override.rrf_k
            if search_config_override.rrf_weight is not None:
                search_kwargs["search_rrf_weight"] = search_config_override.rrf_weight
            if search_config_override.reranker_model is not None:
                search_kwargs["search_reranker_model"] = search_config_override.reranker_model
            if search_config_override.reranker_instruction is not None:
                search_kwargs["search_reranker_instruction"] = search_config_override.reranker_instruction
            if search_config_override.reranker_top_n is not None:
                search_kwargs["search_reranker_top_n"] = search_config_override.reranker_top_n

        # プロンプトのオーバーライド(一時的に変更)
        # 優先順位: override.prompt_text > override.prompt_path > ConfigManager.prompt_text > ConfigManager.prompt_file > 初期設定
        original_prompt = None
        if model_config_override and (model_config_override.prompt_text or model_config_override.prompt_path):
            original_prompt = self.vlm_service.prompt
            # prompt_textが指定されている場合はそちらを優先
            if model_config_override.prompt_text:
                self.vlm_service.prompt = model_config_override.prompt_text
            elif model_config_override.prompt_path:
                from ..config import get_settings
                settings = get_settings()
                prompt_full_path = settings.get_prompt_path(model_config_override.prompt_path)
                self.vlm_service.prompt = self.vlm_service._load_prompt(prompt_full_path)
        elif config.vlm.prompt_text:
            # ConfigManagerからプロンプトテキストを取得（prompt_fileより優先）
            original_prompt = self.vlm_service.prompt
            self.vlm_service.prompt = config.vlm.prompt_text
        elif config.vlm.prompt_file:
            # ConfigManagerからプロンプトファイルを取得
            original_prompt = self.vlm_service.prompt
            from ..config import get_settings
            settings = get_settings()
            prompt_full_path = settings.get_prompt_path(config.vlm.prompt_file)
            self.vlm_service.prompt = self.vlm_service._load_prompt(prompt_full_path)

        # モデルIDのオーバーライド(一時的に変更)
        # 優先順位: override.model_id > ConfigManager > 初期設定
        original_model_id = None
        effective_model_id = None
        if model_config_override and model_config_override.model_id:
            effective_model_id = model_config_override.model_id
        elif config.vlm.model_id:
            effective_model_id = config.vlm.model_id

        if effective_model_id and effective_model_id != self.vlm_service.model_id:
            original_model_id = self.vlm_service.model_id
            self.vlm_service.model_id = effective_model_id
            # プロバイダーも更新（VLMProviderFactoryを使用）
            from .providers import VLMProviderFactory
            self.vlm_service.provider = VLMProviderFactory.create_provider(
                model_id=effective_model_id
            )
            # 後方互換性のため
            self.vlm_service.deepinfra_service = self.vlm_service.provider

        try:
            # 分析実行
            result = await self.analyze_image(
                image_bytes=image_bytes,
                image_mime_type="image/jpeg",
                include_debug_info=include_debug_info,
                **vlm_kwargs,
                **search_kwargs
            )

            # API用のレスポンス形式に変換
            from ..models.response_models import (
                IngredientDetail, DishDetail, NutritionInfo
            )

            # VLMレスポンスからmeal_titleを取得
            vlm_output = result.get("vlm_output", {})
            meal_title = vlm_output.get("meal_title")

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

                    # デバッグ情報を抽出（新しい _debug_info フィールドを優先）
                    debug_info = None
                    if include_debug_info:
                        hybrid_debug = usda_match.get("_debug_info")
                        if hybrid_debug:
                            debug_info = hybrid_debug
                        else:
                            # 旧形式のデバッグ情報へのフォールバック
                            debug_info = {
                                "retriever_candidates": usda_match.get("retriever_candidates", []),
                                "reranker_results": usda_match.get("reranker_results", []),
                                "retry_count": usda_match.get("retry_count", 0)
                            }

                    ingredients.append(
                        IngredientDetail(
                            ingredient_name=main_food.get("matched_description", main_food.get("search_name", "")),
                            vlm_query=main_food.get("search_name", ""),
                            matched_db_description=main_food.get("matched_description", ""),
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

                    # extraのデバッグ情報を抽出（新しい _debug_info フィールドを優先）
                    extra_debug_info = None
                    if include_debug_info:
                        extra_hybrid_debug = extra_usda.get("_debug_info")
                        if extra_hybrid_debug:
                            extra_debug_info = extra_hybrid_debug
                        else:
                            # 旧形式のデバッグ情報へのフォールバック
                            extra_debug_info = {
                                "retriever_candidates": extra_usda.get("retriever_candidates", []),
                                "reranker_results": extra_usda.get("reranker_results", []),
                                "retry_count": extra_usda.get("retry_count", 0)
                            }

                    ingredients.append(
                        IngredientDetail(
                            ingredient_name=extra.get("matched_description", extra.get("search_name", "Unknown")),
                            vlm_query=extra.get("search_name", ""),
                            matched_db_description=extra.get("matched_description", ""),
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

                # VLMレスポンスからdish_nameを取得
                dish_name = dish.get("dish_name")

                api_dishes.append(
                    DishDetail(
                        dish_name=dish_name,
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

            # モデル情報（使用された実際の値を報告）
            ai_model_used = self.vlm_service.model_id  # 一時的にオーバーライドされた値
            # プロンプト情報を取得
            if model_config_override and model_config_override.prompt_text:
                prompt_file_used = "[Custom Prompt Text (API Override)]"
            elif model_config_override and model_config_override.prompt_path:
                prompt_file_used = model_config_override.prompt_path
            elif config.vlm.prompt_text:
                prompt_file_used = "[Custom Prompt Text (Admin Config)]"
            else:
                # ConfigManagerからのプロンプトファイル名を使用
                prompt_file_used = config.vlm.prompt_file

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
                "meal_title": meal_title,
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

    async def _parallel_search(
        self,
        queries: List[Dict[str, Any]],
        stage1_top_k: Optional[int] = None,
        bm25_weight: Optional[float] = None,
        vector_weight: Optional[float] = None,
        rrf_k: Optional[int] = None,
        rrf_weight: Optional[float] = None,
        reranker_model: Optional[str] = None,
        reranker_instruction: Optional[str] = None,
        reranker_top_n: Optional[int] = None,
        include_debug_info: bool = False
    ) -> List[Optional[Dict[str, Any]]]:
        """USDA検索を並列実行（バッチembedding最適化）"""
        # パラメータがNoneの場合はConfigManager（動的設定）から取得
        config_manager = get_config_manager()
        config = config_manager.get_config()

        effective_stage1_top_k = stage1_top_k if stage1_top_k is not None else config.search.stage1_top_k
        effective_bm25_weight = bm25_weight if bm25_weight is not None else config.search.bm25_weight
        effective_vector_weight = vector_weight if vector_weight is not None else config.search.vector_weight
        effective_rrf_k = rrf_k if rrf_k is not None else config.search.rrf_k
        effective_rrf_weight = rrf_weight if rrf_weight is not None else config.search.rrf_weight
        effective_reranker_model = reranker_model if reranker_model is not None else config.reranker.model
        effective_reranker_instruction = reranker_instruction if reranker_instruction is not None else config.reranker.instruction
        effective_reranker_top_n = reranker_top_n if reranker_top_n is not None else config.reranker.top_n

        # クエリ文字列のリストを抽出
        query_texts = [q['search_name'] for q in queries]

        # ===== バッチembedding最適化 =====
        # 全クエリのembeddingを1回のAPI呼び出しで一括生成（N回→1回に削減）
        try:
            logger.info(f"🔄 Batch embedding generation for {len(query_texts)} queries...")
            embeddings = await self.food_search_service.batch_generate_embeddings(query_texts)
            logger.info(f"✅ Batch embedding completed")

            # 事前計算済みembeddingを使用した検索を並列実行
            tasks = []
            for i, query in enumerate(queries):
                task = self.food_search_service.search_with_precomputed_embedding(
                    query=query['search_name'],
                    query_embedding=embeddings[i],
                    stage1_top_k=effective_stage1_top_k,
                    bm25_weight=effective_bm25_weight,
                    vector_weight=effective_vector_weight,
                    rrf_k=effective_rrf_k,
                    rrf_weight=effective_rrf_weight,
                    reranker_instruction=effective_reranker_instruction,
                    include_debug_info=include_debug_info
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)

        except Exception as e:
            # バッチembeddingに失敗した場合は従来方式にフォールバック
            logger.warning(f"⚠️ Batch embedding failed, falling back to individual calls: {e}")
            tasks = []
            for query in queries:
                task = self.food_search_service.search(
                    query=query['search_name'],
                    search_mode="full_index_only",
                    stage1_top_k=effective_stage1_top_k,
                    use_hybrid=True,
                    bm25_weight=effective_bm25_weight,
                    vector_weight=effective_vector_weight,
                    rrf_k=effective_rrf_k,
                    rrf_weight=effective_rrf_weight,
                    reranker_model=effective_reranker_model,
                    reranker_instruction=effective_reranker_instruction,
                    reranker_top_n=effective_reranker_top_n,
                    include_debug_info=include_debug_info
                )
                tasks.append(task)
            results = await asyncio.gather(*tasks)
        # 新しいレスポンス形式に対応 {"result": ..., "debug_info": ...}
        processed_results = []
        for response in results:
            if isinstance(response, dict) and "result" in response:
                # 新しい形式: {"result": ..., "debug_info": ...}
                result = response.get("result")
                debug_info = response.get("debug_info")
                if result:
                    result["_debug_info"] = debug_info  # デバッグ情報を結果に付与
                processed_results.append(result)
            elif isinstance(response, dict) and "results" in response:
                # 複数結果の形式: {"results": [...], "debug_info": ...}
                results_list = response.get("results", [])
                debug_info = response.get("debug_info")
                if results_list:
                    result = results_list[0]
                    result["_debug_info"] = debug_info
                    processed_results.append(result)
                else:
                    processed_results.append(None)
            elif isinstance(response, list) and len(response) > 0:
                # 旧形式（リスト）
                processed_results.append(response[0])
            else:
                processed_results.append(response)
        return processed_results

    async def _sequential_search(
        self,
        queries: List[Dict[str, Any]],
        stage1_top_k: Optional[int] = None,
        bm25_weight: Optional[float] = None,
        vector_weight: Optional[float] = None,
        rrf_k: Optional[int] = None,
        rrf_weight: Optional[float] = None,
        reranker_model: Optional[str] = None,
        reranker_instruction: Optional[str] = None,
        reranker_top_n: Optional[int] = None,
        include_debug_info: bool = False
    ) -> List[Optional[Dict[str, Any]]]:
        """USDA検索を逐次実行"""
        # パラメータがNoneの場合はConfigManager（動的設定）から取得
        config_manager = get_config_manager()
        config = config_manager.get_config()

        effective_stage1_top_k = stage1_top_k if stage1_top_k is not None else config.search.stage1_top_k
        effective_bm25_weight = bm25_weight if bm25_weight is not None else config.search.bm25_weight
        effective_vector_weight = vector_weight if vector_weight is not None else config.search.vector_weight
        effective_rrf_k = rrf_k if rrf_k is not None else config.search.rrf_k
        effective_rrf_weight = rrf_weight if rrf_weight is not None else config.search.rrf_weight
        effective_reranker_model = reranker_model if reranker_model is not None else config.reranker.model
        effective_reranker_instruction = reranker_instruction if reranker_instruction is not None else config.reranker.instruction
        effective_reranker_top_n = reranker_top_n if reranker_top_n is not None else config.reranker.top_n

        results = []
        for query in queries:
            response = await self.food_search_service.search(
                query=query['search_name'],
                search_mode="full_index_only",
                stage1_top_k=effective_stage1_top_k,
                use_hybrid=True,  # 画像分析APIはHybrid search + Reranker を使用
                bm25_weight=effective_bm25_weight,
                vector_weight=effective_vector_weight,
                rrf_k=effective_rrf_k,
                rrf_weight=effective_rrf_weight,
                reranker_model=effective_reranker_model,
                reranker_instruction=effective_reranker_instruction,
                reranker_top_n=effective_reranker_top_n,
                include_debug_info=include_debug_info
            )
            # 新しいレスポンス形式に対応 {"result": ..., "debug_info": ...}
            if isinstance(response, dict) and "result" in response:
                # 新しい形式: {"result": ..., "debug_info": ...}
                result = response.get("result")
                debug_info = response.get("debug_info")
                if result:
                    result["_debug_info"] = debug_info  # デバッグ情報を結果に付与
                results.append(result)
            elif isinstance(response, dict) and "results" in response:
                # 複数結果の形式: {"results": [...], "debug_info": ...}
                results_list = response.get("results", [])
                debug_info = response.get("debug_info")
                if results_list:
                    result = results_list[0]
                    result["_debug_info"] = debug_info
                    results.append(result)
                else:
                    results.append(None)
            elif isinstance(response, list) and len(response) > 0:
                # 旧形式（リスト）
                results.append(response[0])
            else:
                results.append(response)

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

            # dish_nameを保持（VLMレスポンスから）
            enriched_dish['dish_name'] = dish.get('dish_name')

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
            # DBから選ばれた名前を保存（VLMクエリとの比較用）
            enriched['matched_description'] = usda_match.get('description', '')

            # 栄養素計算
            fdc_id = usda_match['fdc_id']
            weight_g = query['weight_g']

            nutrition = self.nutrition_calculator.calculate(fdc_id, weight_g)
            enriched['nutrition'] = nutrition
        else:
            enriched['usda_match'] = None
            enriched['matched_description'] = ''
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

    async def analyze_meal_from_voice(
        self,
        audio_bytes: bytes,
        user_context: Optional[str] = None,
        model_config_override: Optional[Any] = None,
        search_config_override: Optional[Any] = None,
        voice_model_id: Optional[str] = None,
        voice_prompt_file: Optional[str] = None,
        whisper_model: Optional[str] = None,
        language: str = "en",
        include_debug_info: bool = False,
    ) -> Dict[str, Any]:
        """
        API用の音声分析エンドポイント

        処理フロー:
        1. 音声 → Whisper STT → テキスト変換
        2. テキスト → LLM → 食事情報抽出（USDA形式JSON）
        3. USDA検索 → 栄養価計算

        Args:
            audio_bytes: 音声データ（バイト列）
            user_context: ユーザーコンテキスト
            model_config_override: モデル設定のオーバーライド
            search_config_override: 検索設定のオーバーライド
            voice_model_id: Voice解析用LLM/VLMモデルID
            voice_prompt_file: Voice解析用プロンプトファイル
            whisper_model: Whisperモデル（STT用）
            language: 言語コード（en, ja等）
            include_debug_info: デバッグ情報を含めるか

        Returns:
            - dishes: 検出された料理リスト
            - total_nutrition: 総栄養価
            - transcript: 音声認識テキスト
            - voice_metadata: 音声メタデータ
            - usage: Token使用量
        """
        import time
        from .speech_service import SpeechService
        from .text_analysis_service import TextAnalysisService
        from ..models.response_models import (
            IngredientDetail, DishDetail, NutritionInfo, VoiceMetadata
        )

        logger.info("=" * 80)
        logger.info("Starting Voice-based Meal Analysis")
        logger.info("=" * 80)

        start_time = time.time()

        # Step 1: 音声認識 (STT)
        logger.info("\n🔄 Step 1/4: Speech-to-Text (Whisper)")

        speech_service = SpeechService()
        try:
            transcript, stt_metadata = await speech_service.transcribe_audio(
                audio_data=audio_bytes,
                language=language,
                model=whisper_model
            )
        except Exception as e:
            logger.error(f"STT failed: {e}")
            raise RuntimeError(f"[Pipeline] Speech-to-text failed: {e}") from e

        if not transcript or not transcript.strip():
            raise ValueError("[Pipeline] Speech recognition returned empty text")

        logger.info(f"✅ Transcript: '{transcript[:100]}...'")

        # Step 2: テキスト分析 (LLM)
        logger.info("\n🔄 Step 2/4: Text Analysis (LLM)")

        text_analysis_service = TextAnalysisService(
            model_id=voice_model_id,
            prompt_file=voice_prompt_file
        )

        try:
            llm_result, llm_usage = await text_analysis_service.analyze_text(
                text=transcript,
                temperature=model_config_override.temperature if model_config_override else None,
                max_tokens=model_config_override.max_tokens if model_config_override else None
            )
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise RuntimeError(f"[Pipeline] LLM text analysis failed: {e}") from e

        dishes = llm_result.get("dishes", [])
        logger.info(f"✅ LLM analysis complete: {len(dishes)} dishes found")

        # Step 3: クエリ抽出 & USDA検索
        logger.info("\n🔄 Step 3/4: Query Extraction & USDA Search")

        queries = self.query_extraction.extract_queries(llm_result)
        logger.info(f"✅ Extracted {len(queries)} queries")

        # 検索設定の適用
        search_kwargs = {}
        if search_config_override:
            if search_config_override.stage1_top_k is not None:
                search_kwargs["stage1_top_k"] = search_config_override.stage1_top_k
            if search_config_override.bm25_weight is not None:
                search_kwargs["bm25_weight"] = search_config_override.bm25_weight
            if search_config_override.vector_weight is not None:
                search_kwargs["vector_weight"] = search_config_override.vector_weight
            if search_config_override.rrf_k is not None:
                search_kwargs["rrf_k"] = search_config_override.rrf_k
            if search_config_override.rrf_weight is not None:
                search_kwargs["rrf_weight"] = search_config_override.rrf_weight
            if search_config_override.reranker_model is not None:
                search_kwargs["reranker_model"] = search_config_override.reranker_model
            if search_config_override.reranker_instruction is not None:
                search_kwargs["reranker_instruction"] = search_config_override.reranker_instruction
            if search_config_override.reranker_top_n is not None:
                search_kwargs["reranker_top_n"] = search_config_override.reranker_top_n

        # 並列検索
        search_results = await self._parallel_search(
            queries,
            include_debug_info=include_debug_info,
            **search_kwargs
        )
        logger.info(f"✅ USDA search complete: {len(search_results)} results")

        # クエリに検索結果を付与
        for i, query in enumerate(queries):
            query['usda_match'] = search_results[i]

        # Step 4: 栄養素計算
        logger.info("\n🔄 Step 4/4: Nutrition Calculation")

        enriched_dishes = self._build_enriched_dishes(dishes, queries)
        total_nutrition = self._calculate_total_nutrition(enriched_dishes)

        logger.info(f"✅ Nutrition calculation complete")
        logger.info(f"   Total: {total_nutrition['calories']} kcal")

        # API用のレスポンス形式に変換
        api_dishes = []
        for dish in enriched_dishes:
            main_food = dish.get("main_food")
            ingredients = []

            if main_food is not None:
                usda_match = main_food.get("usda_match")
                nutrition = main_food.get("nutrition")

                if usda_match:
                    main_fdc_id = usda_match.get("fdc_id")
                    main_nutrition_per_100g = self.nutrition_service.get_nutrition_per_100g(main_fdc_id) if main_fdc_id else None

                    debug_info = None
                    if include_debug_info:
                        debug_info = usda_match.get("_debug_info")

                    ingredients.append(
                        IngredientDetail(
                            ingredient_name=main_food.get("matched_description", main_food.get("search_name", "")),
                            vlm_query=main_food.get("search_name", ""),
                            matched_db_description=main_food.get("matched_description", ""),
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
                extra_fdc_id = extra_usda.get("fdc_id")
                extra_nutrition_per_100g = self.nutrition_service.get_nutrition_per_100g(extra_fdc_id) if extra_fdc_id else None

                extra_debug_info = None
                if include_debug_info:
                    extra_debug_info = extra_usda.get("_debug_info")

                ingredients.append(
                    IngredientDetail(
                        ingredient_name=extra.get("matched_description", extra.get("search_name", "Unknown")),
                        vlm_query=extra.get("search_name", ""),
                        matched_db_description=extra.get("matched_description", ""),
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

            dish_name = dish.get("dish_name")

            api_dishes.append(
                DishDetail(
                    dish_name=dish_name,
                    ingredients=ingredients,
                    total_nutrition=dish_nutrition,
                    calculation_metadata={
                        "ingredient_count": len(ingredients),
                        "total_weight_g": sum(ing.weight_g for ing in ingredients),
                    }
                )
            )

        # 全体の栄養
        total_nutrition_info = NutritionInfo(
            calories=total_nutrition["calories"],
            protein=total_nutrition["protein_g"],
            fat=total_nutrition["fat_g"],
            carbs=total_nutrition["carbs_g"],
        )

        # 終了時刻を記録
        end_time = time.time()
        total_time = end_time - start_time

        # モデル情報
        ai_model_used = voice_model_id or text_analysis_service.model_id
        prompt_file_used = voice_prompt_file or text_analysis_service.prompt_file

        # マッチ率計算
        total_queries_count = len(api_dishes)
        matched_queries = sum(1 for dish in api_dishes if len(dish.ingredients) > 0)
        match_rate = (matched_queries / total_queries_count * 100) if total_queries_count > 0 else 0.0

        # Usage情報とコスト計算
        from ..models.response_models import UsageInfo
        usage_info = None
        if llm_usage:
            cost_data = self.cost_calculator.calculate_cost(
                model_id=ai_model_used,
                prompt_tokens=llm_usage.get("prompt_tokens", 0),
                completion_tokens=llm_usage.get("completion_tokens", 0)
            )

            if cost_data is None:
                usage_info = UsageInfo(
                    prompt_tokens=llm_usage.get("prompt_tokens", 0),
                    completion_tokens=llm_usage.get("completion_tokens", 0),
                    total_tokens=llm_usage.get("total_tokens", 0),
                    estimated_cost_usd=None,
                    model_pricing=None,
                    raw_vlm_output=llm_usage.get("raw_vlm_output")
                )
            else:
                usage_info = UsageInfo(
                    prompt_tokens=cost_data["prompt_tokens"],
                    completion_tokens=cost_data["completion_tokens"],
                    total_tokens=cost_data["total_tokens"],
                    estimated_cost_usd=cost_data["estimated_cost_usd"],
                    model_pricing=cost_data["model_pricing"],
                    raw_vlm_output=llm_usage.get("raw_vlm_output")
                )

        # VoiceMetadata
        voice_metadata = VoiceMetadata(
            whisper_model=stt_metadata.get("whisper_model", ""),
            audio_duration_seconds=stt_metadata.get("audio_duration_seconds"),
            audio_size_bytes=stt_metadata.get("audio_size_bytes", len(audio_bytes)),
            language_detected=stt_metadata.get("language_detected"),
            stt_processing_time_seconds=stt_metadata.get("stt_processing_time_seconds")
        )

        logger.info("\n" + "=" * 80)
        logger.info("✅ Voice-based Analysis Complete")
        logger.info(f"⏱️  Total time: {total_time:.2f} seconds")
        logger.info("=" * 80)

        return {
            "dishes": api_dishes,
            "meal_title": llm_result.get("meal_title"),
            "total_nutrition": total_nutrition_info,
            "ai_model_used": ai_model_used,
            "prompt_file_used": prompt_file_used,
            "match_rate_percent": match_rate,
            "usage": usage_info,
            "transcript": transcript,
            "voice_metadata": voice_metadata,
            "processing_time_seconds": round(total_time, 2),
            "warnings": [],
        }
