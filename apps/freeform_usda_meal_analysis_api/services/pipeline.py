#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
End-to-End Meal Analysis Pipeline

VLM画像解析 → クエリ抽出 → USDA検索 → 栄養素計算 の統合パイプライン
"""

import logging
import statistics
import time
from typing import Dict, List, Any, Optional
import asyncio

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
        use_lazy_loading: bool = True,
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

        # 設定を取得 - ConfigManagerから動的設定
        from ..admin.config_manager import get_config_manager

        config_manager = get_config_manager()
        config = config_manager.get_config()

        # stage1_top_kが指定されていない場合はConfigManagerから取得
        if stage1_top_k is None:
            stage1_top_k = config.search.stage1_top_k

        # インスタンス変数として保存（_parallel_searchで使用）
        self.stage1_top_k = stage1_top_k

        # VLMサービス初期化
        self.vlm_service = VLMService(
            model_id=vlm_model_id, prompt_file=vlm_prompt_file
        )

        # クエリ抽出サービス初期化
        self.query_extraction = QueryExtractionService()

        # USDA検索サービス初期化（Fullインデックスのみ使用）
        self.food_search_service = USDAFoodSearchService(
            index_dir=index_dir,
            stage1_top_k=stage1_top_k,
            device=device,
            hybrid_engine=hybrid_engine,
            use_lazy_loading=use_lazy_loading,
        )

        # 栄養素サービス初期化
        self.nutrition_service = LocalUSDANutritionService(
            metadata_file=usda_metadata_file
        )

        self.nutrition_calculator = NutritionCalculator(self.nutrition_service)

        # コスト計算サービス初期化
        from .cost_calculator import CostCalculator

        self.cost_calculator = CostCalculator()

        # 後段カロリーキャリブレーション（既定OFF。外部held-outでfitしたときのみ有効化）
        from ..core.calorie_calibration import load_calibration

        self.calorie_calibration = load_calibration()

        logger.info("✅ Meal Analysis Pipeline initialized successfully")

    async def analyze_image(
        self,
        image_bytes: bytes,
        image_mime_type: str = "image/jpeg",
        vlm_temperature: Optional[float] = None,
        vlm_seed: Optional[int] = None,
        vlm_max_tokens: Optional[int] = None,
        vlm_reasoning_effort: Optional[str] = None,
        vlm_use_cache: bool = True,
        enable_self_verification: bool = False,
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
        include_debug_info: bool = False,
        # E8 (F1-a): ユーザー提供コンテキスト（皿径/食べ残し/店名/大盛り等）
        user_context: Optional[str] = None,
        # F2: request-local な VLM prompt / model（共有 vlm_service を mutate しない）
        vlm_prompt: Optional[str] = None,
        vlm_model_id: Optional[str] = None,
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
            vlm_use_cache: VLMキャッシュを利用するか
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
                reasoning_effort=vlm_reasoning_effort,
                use_cache=vlm_use_cache,
                user_context=user_context,
                prompt=vlm_prompt,
                model_id=vlm_model_id,
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

        # Step 1.5: Self-verification (opt-in 2nd pass) — re-show the image with the
        # candidate list and DROP items the model cannot actually see (precision lever
        # against invented items). Single-pass behavior is unchanged when disabled.
        if enable_self_verification and dishes:
            from .vlm_service import apply_verification

            candidate_names = []
            for dish in dishes:
                main_food = dish.get("main_food")
                if main_food and main_food.get("search_name"):
                    candidate_names.append(main_food["search_name"])
                for extra in dish.get("extras") or []:
                    if extra.get("search_name"):
                        candidate_names.append(extra["search_name"])
            logger.info(
                f"\n🔎 Step 1.5/4: Self-verification of {len(candidate_names)} items"
            )
            verify_result = await self.vlm_service.verify_items(
                image_bytes=image_bytes,
                candidate_names=candidate_names,
                image_mime_type=image_mime_type,
                temperature=vlm_temperature,
                seed=vlm_seed,
                max_tokens=vlm_max_tokens,
                reasoning_effort=vlm_reasoning_effort,
                model_id=vlm_model_id,
            )
            vlm_response, n_dropped = apply_verification(
                vlm_response, verify_result["verdicts"]
            )
            dishes = vlm_response.get("dishes", [])
            logger.info(
                f"✅ Self-verification dropped {n_dropped} item(s); "
                f"{len(dishes)} dishes, {len(verify_result['missing'])} flagged missing"
            )

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
                include_debug_info=include_debug_info,
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
                include_debug_info=include_debug_info,
            )

        logger.info(f"✅ USDA search complete: {len(search_results)} results")

        # Step 4: 栄養素計算
        logger.info("\n🔄 Step 4/4: Nutrition Calculation")

        # クエリに検索結果を付与
        for i, query in enumerate(queries):
            query["usda_match"] = search_results[i]

        # dish構造を再構築
        enriched_dishes = self._build_enriched_dishes(dishes, queries)

        # 全体の栄養素を計算
        total_nutrition = self._calculate_total_nutrition(enriched_dishes)
        enriched_dishes, total_nutrition = self._apply_calorie_calibration(
            enriched_dishes, total_nutrition
        )

        logger.info("✅ Nutrition calculation complete")
        logger.info(
            f"   Total: {total_nutrition['calories']} kcal, "
            f"{total_nutrition['protein_g']}g protein, "
            f"{total_nutrition['fat_g']}g fat, "
            f"{total_nutrition['carbs_g']}g carbs"
        )

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
                "end_time": end_time,
            },
        }

    @staticmethod
    def _result_calories(result: Dict[str, Any]) -> float:
        """結果dictから総カロリーを取得（total_nutrition は NutritionInfo か dict）。"""
        total = result.get("total_nutrition")
        cal = getattr(total, "calories", None)
        if cal is None and isinstance(total, dict):
            cal = total.get("calories")
        return float(cal or 0.0)

    @classmethod
    def _select_median_calorie_result(
        cls, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """K個の結果から総カロリーが median のものを返す。

        奇数Kなら中央サンプルそのものを返すため、foods/macros/total が自己整合する。
        """
        if not results:
            raise ValueError("self-consistency: no results to select from")
        med = statistics.median(cls._result_calories(r) for r in results)
        return min(results, key=lambda r: abs(cls._result_calories(r) - med))

    async def analyze_meal_from_image(
        self,
        image_bytes: bytes,
        user_context: Optional[str] = None,
        model_config_override: Optional[Any] = None,
        search_config_override: Optional[Any] = None,
        include_debug_info: bool = False,
        enable_self_verification: bool = False,
    ) -> Dict[str, Any]:
        """画像分析エンドポイント（self-consistency 対応のディスパッチャ）。

        `self_consistency_k`（override > ConfigManager > 1）が >1 のとき、K回（seed違い）
        解析して総カロリーが median の結果を返す（分散低減。検証: evals/lessons/
        20260604_self_consistency_median_ensemble_significant_calorie_win.md）。K=1（既定）は
        単一解析で挙動不変。F2(stateless VLM)後は K 回を並列実行（latency ~Kx → ~1x）。
        """
        k = None
        if model_config_override is not None:
            k = getattr(model_config_override, "self_consistency_k", None)
        if k is None:
            k = getattr(get_config_manager().get_config().vlm, "self_consistency_k", 1)
        k = int(k or 1)

        if k <= 1:
            return await self._analyze_meal_once(
                image_bytes=image_bytes,
                user_context=user_context,
                model_config_override=model_config_override,
                search_config_override=search_config_override,
                include_debug_info=include_debug_info,
                enable_self_verification=enable_self_verification,
            )

        base_seed = None
        if model_config_override is not None:
            base_seed = getattr(model_config_override, "seed", None)
        if base_seed is None:
            base_seed = get_config_manager().get_config().vlm.seed
        base_seed = int(base_seed)

        logger.info(
            "🎲 [Self-Consistency] K=%d samples (seeds %d..%d), median-total-calorie",
            k,
            base_seed,
            base_seed + k - 1,
        )

        from ..models.request_models import ModelConfig

        async def _one_sample(i: int) -> Dict[str, Any]:
            iter_seed = base_seed + i
            if model_config_override is None:
                iter_override = ModelConfig(seed=iter_seed, self_consistency_k=1)
            else:
                iter_override = model_config_override.model_copy(
                    update={"seed": iter_seed, "self_consistency_k": 1}
                )
            return await self._analyze_meal_once(
                image_bytes=image_bytes,
                user_context=user_context,
                model_config_override=iter_override,
                search_config_override=search_config_override,
                include_debug_info=include_debug_info,
                enable_self_verification=enable_self_verification,
            )

        # F2(stateless VLM)後は vlm_service を mutate しないため K 回を並列実行できる
        # （seed 違いの独立サンプル。latency ~Kx → ~1x）。
        results: List[Dict[str, Any]] = await asyncio.gather(
            *[_one_sample(i) for i in range(k)]
        )

        selected = self._select_median_calorie_result(results)
        logger.info(
            "🎲 [Self-Consistency] sample calories=%s -> selected median=%.1f",
            [round(self._result_calories(r), 1) for r in results],
            self._result_calories(selected),
        )
        return selected

    async def _analyze_meal_once(
        self,
        image_bytes: bytes,
        user_context: Optional[str] = None,
        model_config_override: Optional[Any] = None,
        search_config_override: Optional[Any] = None,
        include_debug_info: bool = False,
        enable_self_verification: bool = False,
    ) -> Dict[str, Any]:
        """
        API用の画像分析エンドポイント(パラメータオーバーライド対応・単一サンプル)

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

        # デバッグログ: キャッシュ状態とprompt_text確認
        prompt_text_len = len(config.vlm.prompt_text) if config.vlm.prompt_text else 0
        logger.info(
            f"🔧 [Config Debug] cache_valid={config_manager._is_cache_valid()}, "
            f"cache_ttl={config_manager.cache_ttl_seconds}s, "
            f"prompt_text_len={prompt_text_len}, "
            f"prompt_text_truthy={bool(config.vlm.prompt_text)}, "
            f"prompt_text_type={type(config.vlm.prompt_text).__name__}, "
            f"prompt_file={config.vlm.prompt_file}"
        )

        # モデル設定の適用（オーバーライド > ConfigManager）
        vlm_kwargs = {
            "vlm_temperature": config.vlm.temperature,
            "vlm_seed": config.vlm.seed,
            "vlm_max_tokens": config.vlm.max_tokens,
            "vlm_reasoning_effort": config.vlm.reasoning_effort,
            "vlm_use_cache": config.vlm.use_cache,
        }
        if model_config_override:
            if model_config_override.temperature is not None:
                vlm_kwargs["vlm_temperature"] = model_config_override.temperature
            if model_config_override.seed is not None:
                vlm_kwargs["vlm_seed"] = model_config_override.seed
            if model_config_override.max_tokens is not None:
                vlm_kwargs["vlm_max_tokens"] = model_config_override.max_tokens
            if model_config_override.reasoning_effort is not None:
                vlm_kwargs["vlm_reasoning_effort"] = (
                    model_config_override.reasoning_effort
                )
            if model_config_override.use_vlm_cache is not None:
                vlm_kwargs["vlm_use_cache"] = model_config_override.use_vlm_cache
        logger.info(
            "🔧 [VLM Runtime Params] temperature=%s seed=%s max_tokens=%s reasoning_effort=%s use_cache=%s",
            vlm_kwargs.get("vlm_temperature"),
            vlm_kwargs.get("vlm_seed"),
            vlm_kwargs.get("vlm_max_tokens"),
            vlm_kwargs.get("vlm_reasoning_effort"),
            vlm_kwargs.get("vlm_use_cache"),
        )

        # 検索設定の適用
        search_kwargs = {}
        if search_config_override:
            if search_config_override.stage1_top_k is not None:
                search_kwargs["search_stage1_top_k"] = (
                    search_config_override.stage1_top_k
                )
            if search_config_override.bm25_weight is not None:
                search_kwargs["search_bm25_weight"] = search_config_override.bm25_weight
            if search_config_override.vector_weight is not None:
                search_kwargs["search_vector_weight"] = (
                    search_config_override.vector_weight
                )
            if search_config_override.rrf_k is not None:
                search_kwargs["search_rrf_k"] = search_config_override.rrf_k
            if search_config_override.rrf_weight is not None:
                search_kwargs["search_rrf_weight"] = search_config_override.rrf_weight
            if search_config_override.reranker_model is not None:
                search_kwargs["search_reranker_model"] = (
                    search_config_override.reranker_model
                )
            if search_config_override.reranker_instruction is not None:
                search_kwargs["search_reranker_instruction"] = (
                    search_config_override.reranker_instruction
                )
            if search_config_override.reranker_top_n is not None:
                search_kwargs["search_reranker_top_n"] = (
                    search_config_override.reranker_top_n
                )

        # プロンプトのオーバーライド（F2: 共有 vlm_service を mutate せず request-local に解決）
        # 優先順位: override.prompt_text > override.prompt_path > ConfigManager.prompt_text > ConfigManager.prompt_file > 初期設定
        effective_prompt = self.vlm_service.prompt  # 既定 = 初期ロード済みプロンプト
        if model_config_override and (
            model_config_override.prompt_text or model_config_override.prompt_path
        ):
            if model_config_override.prompt_text:
                effective_prompt = model_config_override.prompt_text
            elif model_config_override.prompt_path:
                from ..config import get_settings

                settings = get_settings()
                effective_prompt = self.vlm_service._load_prompt(
                    settings.get_prompt_path(model_config_override.prompt_path)
                )
        elif config.vlm.prompt_text:
            effective_prompt = config.vlm.prompt_text
        elif config.vlm.prompt_file:
            from ..config import get_settings

            settings = get_settings()
            effective_prompt = self.vlm_service._load_prompt(
                settings.get_prompt_path(config.vlm.prompt_file)
            )

        # モデルIDのオーバーライド（F2: request-local。provider は vlm_service._provider_for で解決）
        # 優先順位: override.vlm_model_id > ConfigManager > 初期設定
        effective_model_id = self.vlm_service.model_id
        if model_config_override and model_config_override.vlm_model_id:
            effective_model_id = model_config_override.vlm_model_id
        elif config.vlm.model_id:
            effective_model_id = config.vlm.model_id

        # F2: prompt/model を request-local に渡す（singleton 不変＝同時/並列リクエスト安全）。
        vlm_kwargs["vlm_prompt"] = effective_prompt
        vlm_kwargs["vlm_model_id"] = effective_model_id

        try:
            # 分析実行
            result = await self.analyze_image(
                image_bytes=image_bytes,
                image_mime_type="image/jpeg",
                include_debug_info=include_debug_info,
                enable_self_verification=enable_self_verification,
                user_context=user_context,
                **vlm_kwargs,
                **search_kwargs,
            )

            # API用のレスポンス形式に変換
            from ..models.response_models import (
                IngredientDetail,
                DishDetail,
                NutritionInfo,
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
                            logger.error("❌ main_food is missing 'search_name' field")
                            logger.error(f"   main_food content: {main_food}")
                            # raise HTTPException を Exception に変更
                            raise Exception(
                                "VLM returned a dish with main_food but no search_name field. "
                                "This indicates a VLM response format error."
                            )
                        else:
                            logger.error(
                                f"❌ USDA search failed for main_food: '{search_name}'"
                            )
                            logger.error(f"   main_food: {main_food}")
                            # raise HTTPException を Exception に変更
                            raise Exception(
                                f"USDA food database search failed for ingredient: '{search_name}'. "
                                f"The food item could not be matched in the USDA database."
                            )

                    # 正常にUSDA検索できた場合の処理
                    main_fdc_id = usda_match.get("fdc_id")
                    main_nutrition_per_100g = (
                        self.nutrition_service.get_nutrition_per_100g(main_fdc_id)
                        if main_fdc_id
                        else None
                    )

                    # デバッグ情報を抽出（新しい _debug_info フィールドを優先）
                    debug_info = None
                    if include_debug_info:
                        hybrid_debug = usda_match.get("_debug_info")
                        if hybrid_debug:
                            debug_info = hybrid_debug
                        else:
                            # 旧形式のデバッグ情報へのフォールバック
                            debug_info = {
                                "retriever_candidates": usda_match.get(
                                    "retriever_candidates", []
                                ),
                                "reranker_results": usda_match.get(
                                    "reranker_results", []
                                ),
                                "retry_count": usda_match.get("retry_count", 0),
                            }

                    ingredients.append(
                        IngredientDetail(
                            ingredient_name=main_food.get(
                                "matched_description", main_food.get("search_name", "")
                            ),
                            vlm_query=main_food.get("search_name", ""),
                            matched_db_description=main_food.get(
                                "matched_description", ""
                            ),
                            weight_g=main_food.get("weight_g", 0.0),
                            nutrition_per_100g=NutritionInfo(
                                calories=main_nutrition_per_100g.get("calories", 0.0)
                                if main_nutrition_per_100g
                                else 0.0,
                                protein=main_nutrition_per_100g.get("protein_g", 0.0)
                                if main_nutrition_per_100g
                                else 0.0,
                                fat=main_nutrition_per_100g.get("fat_g", 0.0)
                                if main_nutrition_per_100g
                                else 0.0,
                                carbs=main_nutrition_per_100g.get("carbs_g", 0.0)
                                if main_nutrition_per_100g
                                else 0.0,
                            ),
                            calculated_nutrition=NutritionInfo(
                                calories=nutrition.get("calories", 0.0)
                                if nutrition
                                else 0.0,
                                protein=nutrition.get("protein_g", 0.0)
                                if nutrition
                                else 0.0,
                                fat=nutrition.get("fat_g", 0.0) if nutrition else 0.0,
                                carbs=nutrition.get("carbs_g", 0.0)
                                if nutrition
                                else 0.0,
                            ),
                            source_db="usda_fndds",
                            fdc_id=str(usda_match.get("fdc_id", "")),
                            calculation_notes=[
                                f"Weight: {main_food.get('weight_g', 0)}g"
                            ],
                            debug_info=debug_info,
                        )
                    )

                # Extrasを追加
                for extra in dish.get("extras", []):
                    extra_nutrition = extra.get("nutrition", {})
                    extra_usda = extra.get("usda_match", {})

                    # fdc_idから100gあたりの栄養素を取得
                    extra_fdc_id = extra_usda.get("fdc_id")
                    extra_nutrition_per_100g = (
                        self.nutrition_service.get_nutrition_per_100g(extra_fdc_id)
                        if extra_fdc_id
                        else None
                    )

                    # extraのデバッグ情報を抽出（新しい _debug_info フィールドを優先）
                    extra_debug_info = None
                    if include_debug_info:
                        extra_hybrid_debug = extra_usda.get("_debug_info")
                        if extra_hybrid_debug:
                            extra_debug_info = extra_hybrid_debug
                        else:
                            # 旧形式のデバッグ情報へのフォールバック
                            extra_debug_info = {
                                "retriever_candidates": extra_usda.get(
                                    "retriever_candidates", []
                                ),
                                "reranker_results": extra_usda.get(
                                    "reranker_results", []
                                ),
                                "retry_count": extra_usda.get("retry_count", 0),
                            }

                    ingredients.append(
                        IngredientDetail(
                            ingredient_name=extra.get(
                                "matched_description",
                                extra.get("search_name", "Unknown"),
                            ),
                            vlm_query=extra.get("search_name", ""),
                            matched_db_description=extra.get("matched_description", ""),
                            weight_g=extra.get("weight_g", 0.0),
                            nutrition_per_100g=NutritionInfo(
                                calories=extra_nutrition_per_100g.get("calories", 0.0)
                                if extra_nutrition_per_100g
                                else 0.0,
                                protein=extra_nutrition_per_100g.get("protein_g", 0.0)
                                if extra_nutrition_per_100g
                                else 0.0,
                                fat=extra_nutrition_per_100g.get("fat_g", 0.0)
                                if extra_nutrition_per_100g
                                else 0.0,
                                carbs=extra_nutrition_per_100g.get("carbs_g", 0.0)
                                if extra_nutrition_per_100g
                                else 0.0,
                            ),
                            calculated_nutrition=NutritionInfo(
                                calories=extra_nutrition.get("calories", 0.0)
                                if extra_nutrition
                                else 0.0,
                                protein=extra_nutrition.get("protein_g", 0.0)
                                if extra_nutrition
                                else 0.0,
                                fat=extra_nutrition.get("fat_g", 0.0)
                                if extra_nutrition
                                else 0.0,
                                carbs=extra_nutrition.get("carbs_g", 0.0)
                                if extra_nutrition
                                else 0.0,
                            ),
                            source_db="usda_fndds",
                            fdc_id=str(extra_usda.get("fdc_id", "")),
                            calculation_notes=[f"Weight: {extra.get('weight_g', 0)}g"],
                            debug_info=extra_debug_info,
                        )
                    )

                # 料理の総栄養を計算
                dish_nutrition = NutritionInfo(
                    calories=sum(
                        ing.calculated_nutrition.calories for ing in ingredients
                    ),
                    protein=sum(
                        ing.calculated_nutrition.protein for ing in ingredients
                    ),
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
                        },
                    )
                )

            # 全体の栄養
            total_nutrition = NutritionInfo(
                calories=result["total_nutrition"]["calories"],
                protein=result["total_nutrition"]["protein_g"],
                fat=result["total_nutrition"]["fat_g"],
                carbs=result["total_nutrition"]["carbs_g"],
            )

            # モデル情報（F2: request-local に解決した実際の値を報告）
            ai_model_used = effective_model_id
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
            match_rate = (
                (matched_queries / total_queries * 100) if total_queries > 0 else 0.0
            )

            # Usage情報とコスト計算
            from ..models.response_models import UsageInfo

            # プロンプト内容を取得（F2: request-local に解決した実際のプロンプト）
            prompt_content = effective_prompt
            usage_info = None
            if result.get("usage"):
                usage_data = result["usage"]
                cost_data = self.cost_calculator.calculate_cost(
                    model_id=ai_model_used,
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
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
                        prompt_content=prompt_content,
                    )
                else:
                    usage_info = UsageInfo(
                        prompt_tokens=cost_data["prompt_tokens"],
                        completion_tokens=cost_data["completion_tokens"],
                        total_tokens=cost_data["total_tokens"],
                        estimated_cost_usd=cost_data["estimated_cost_usd"],
                        model_pricing=cost_data["model_pricing"],
                        raw_vlm_output=usage_data.get("raw_vlm_output"),
                        prompt_content=prompt_content,
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
            logger.error(f"❌ analyze_meal_from_image failed: {str(e)}", exc_info=True)
            raise

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
        include_debug_info: bool = False,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        USDA検索を並列実行（2フェーズ最適化）

        Phase 1: 全クエリのBM25 + FAISS + RRF融合（CPU-bound、順次実行）
        Phase 2: 全Reranker API呼び出しを一括並列実行（I/O-bound）

        これにより、Rerankerの真の並列実行を実現し、
        8クエリで8秒 → 約1秒に短縮する。
        """
        import time as time_module

        # パラメータがNoneの場合はConfigManager（動的設定）から取得
        config_manager = get_config_manager()
        config = config_manager.get_config()

        effective_stage1_top_k = (
            stage1_top_k if stage1_top_k is not None else config.search.stage1_top_k
        )
        effective_bm25_weight = (
            bm25_weight if bm25_weight is not None else config.search.bm25_weight
        )
        effective_vector_weight = (
            vector_weight if vector_weight is not None else config.search.vector_weight
        )
        effective_rrf_k = rrf_k if rrf_k is not None else config.search.rrf_k
        effective_rrf_weight = (
            rrf_weight if rrf_weight is not None else config.search.rrf_weight
        )
        effective_reranker_model = (
            reranker_model if reranker_model is not None else config.reranker.model
        )
        effective_reranker_instruction = (
            reranker_instruction
            if reranker_instruction is not None
            else config.reranker.instruction
        )
        effective_reranker_top_n = (
            reranker_top_n if reranker_top_n is not None else config.reranker.top_n
        )

        # クエリ文字列のリストを抽出
        query_texts = [q["search_name"] for q in queries]

        try:
            # ===== Phase 1a: バッチembedding生成（1回のAPI呼び出し） =====
            phase1_start = time_module.time()
            logger.info(
                f"🔄 Phase 1: Batch embedding generation for {len(query_texts)} queries..."
            )
            embeddings = await self.food_search_service.batch_generate_embeddings(
                query_texts
            )
            embedding_time = time_module.time() - phase1_start
            logger.info(f"✅ Embedding completed in {embedding_time:.2f}s")

            # ===== Phase 1b: 全クエリのBM25 + FAISS + RRF融合（CPU-bound） =====
            # Rerankerなしで候補リストのみ取得
            candidates_start = time_module.time()
            logger.info(
                f"🔄 Phase 1b: BM25 + FAISS + RRF fusion for {len(query_texts)} queries..."
            )

            queries_and_candidates = []
            for i, query in enumerate(queries):
                candidates = self.food_search_service.get_candidates_only_sync(
                    query=query["search_name"],
                    query_embedding=embeddings[i],
                    stage1_top_k=effective_stage1_top_k,
                    bm25_weight=effective_bm25_weight,
                    vector_weight=effective_vector_weight,
                    rrf_k=effective_rrf_k,
                    rrf_weight=effective_rrf_weight,
                )
                queries_and_candidates.append(
                    {"query": query["search_name"], "candidates": candidates}
                )

            candidates_time = time_module.time() - candidates_start
            logger.info(f"✅ BM25/FAISS/RRF completed in {candidates_time:.2f}s")

            # ===== Phase 2: 全Reranker呼び出しを一括並列実行（I/O-bound） =====
            reranker_start = time_module.time()
            logger.info(
                f"🔄 Phase 2: Parallel reranker for {len(queries_and_candidates)} queries..."
            )

            reranked_results = await self.food_search_service.batch_rerank_candidates(
                queries_and_candidates=queries_and_candidates,
                reranker_model=effective_reranker_model,
                reranker_instruction=effective_reranker_instruction,
                # E7/F1-b: top_n>1 で top-k 候補を density-mixture 用に保持（既定 1=top-1 不変）
                top_k=effective_reranker_top_n or 1,
            )

            reranker_time = time_module.time() - reranker_start
            logger.info(f"✅ Parallel reranker completed in {reranker_time:.2f}s")

            total_time = time_module.time() - phase1_start
            logger.info(
                f"📊 Total search time: {total_time:.2f}s (embedding: {embedding_time:.2f}s, BM25/FAISS: {candidates_time:.2f}s, reranker: {reranker_time:.2f}s)"
            )

            # 結果を処理
            processed_results = []
            for result in reranked_results:
                if result:
                    result["score"] = result.get("rerank_score", 0)
                processed_results.append(result)

            return processed_results

        except Exception as e:
            # 2フェーズ方式に失敗した場合は従来方式にフォールバック
            logger.warning(
                f"⚠️ Two-phase search failed, falling back to sequential calls: {e}"
            )
            import traceback

            traceback.print_exc()

            tasks = []
            for query in queries:
                task = self.food_search_service.search(
                    query=query["search_name"],
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
                    include_debug_info=include_debug_info,
                )
                tasks.append(task)
            results = await asyncio.gather(*tasks)

            # 新しいレスポンス形式に対応 {"result": ..., "debug_info": ...}
            processed_results = []
            for response in results:
                if isinstance(response, dict) and "result" in response:
                    result = response.get("result")
                    debug_info = response.get("debug_info")
                    if result:
                        result["_debug_info"] = debug_info
                    processed_results.append(result)
                elif isinstance(response, dict) and "results" in response:
                    results_list = response.get("results", [])
                    debug_info = response.get("debug_info")
                    if results_list:
                        result = results_list[0]
                        result["_debug_info"] = debug_info
                        processed_results.append(result)
                    else:
                        processed_results.append(None)
                elif isinstance(response, list) and len(response) > 0:
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
        include_debug_info: bool = False,
    ) -> List[Optional[Dict[str, Any]]]:
        """USDA検索を逐次実行"""
        # パラメータがNoneの場合はConfigManager（動的設定）から取得
        config_manager = get_config_manager()
        config = config_manager.get_config()

        effective_stage1_top_k = (
            stage1_top_k if stage1_top_k is not None else config.search.stage1_top_k
        )
        effective_bm25_weight = (
            bm25_weight if bm25_weight is not None else config.search.bm25_weight
        )
        effective_vector_weight = (
            vector_weight if vector_weight is not None else config.search.vector_weight
        )
        effective_rrf_k = rrf_k if rrf_k is not None else config.search.rrf_k
        effective_rrf_weight = (
            rrf_weight if rrf_weight is not None else config.search.rrf_weight
        )
        effective_reranker_model = (
            reranker_model if reranker_model is not None else config.reranker.model
        )
        effective_reranker_instruction = (
            reranker_instruction
            if reranker_instruction is not None
            else config.reranker.instruction
        )
        effective_reranker_top_n = (
            reranker_top_n if reranker_top_n is not None else config.reranker.top_n
        )

        results = []
        for query in queries:
            response = await self.food_search_service.search(
                query=query["search_name"],
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
                include_debug_info=include_debug_info,
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
        self, original_dishes: List[Dict], enriched_queries: List[Dict]
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
            enriched_dish["dish_name"] = dish.get("dish_name")

            # main_food処理
            main_food_queries = [
                q for q in grouped_queries[dish_index] if q.get("is_main_food", False)
            ]

            if main_food_queries:
                main_query = main_food_queries[0]  # main_foodは1つ
                enriched_main = self._enrich_food_item(
                    original_food=dish.get("main_food", {}), query=main_query
                )
                enriched_dish["main_food"] = enriched_main
            else:
                # main_foodがnullの場合は明示的にNoneを設定（extrasのみの料理）
                enriched_dish["main_food"] = None

            # extras処理
            extras_queries = [
                q
                for q in grouped_queries[dish_index]
                if not q.get("is_main_food", False)
            ]

            enriched_extras = []
            for extra_query in extras_queries:
                enriched_extra = self._enrich_food_item(
                    original_food={},  # extrasは元の情報が必要ならqueryから復元
                    query=extra_query,
                )
                enriched_extras.append(enriched_extra)

            enriched_dish["extras"] = enriched_extras

            enriched_dishes.append(enriched_dish)

        return enriched_dishes

    def _enrich_food_item(self, original_food: Dict, query: Dict) -> Dict:
        """
        食材アイテムにUSDA matchと栄養素を付与
        """
        # 元の情報をコピー
        enriched = {
            "search_name": query["search_name"],
            "description": query["description"],
            "weight_g": query["weight_g"],
            "confidence": query.get("confidence", 0.0),
        }

        # USDA match情報を追加
        usda_match = query.get("usda_match")
        if usda_match:
            enriched["usda_match"] = usda_match
            # DBから選ばれた名前を保存（VLMクエリとの比較用）
            enriched["matched_description"] = usda_match.get("description", "")

            # 栄養素計算
            fdc_id = usda_match["fdc_id"]
            weight_g = query["weight_g"]

            # E7: top-k 候補があれば density-mixture（E[kcal/100g]×weight）、無ければ top-1。
            topk = usda_match.get("topk_candidates")
            if topk and len(topk) > 1:
                import os

                temp = float(os.getenv("E7_DENSITY_TEMP", "1.0"))
                nutrition = self.nutrition_calculator.calculate_mixture(
                    topk, weight_g, temperature=temp
                )
            else:
                nutrition = self.nutrition_calculator.calculate(fdc_id, weight_g)
            enriched["nutrition"] = nutrition
        else:
            enriched["usda_match"] = None
            enriched["matched_description"] = ""
            enriched["nutrition"] = None

        return enriched

    def _calculate_total_nutrition(self, dishes: List[Dict]) -> Dict[str, float]:
        """全dishの栄養素を合計"""
        total = {"calories": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0}

        for dish in dishes:
            # main_food処理
            main_food = dish.get("main_food")

            if main_food is None:
                # extras-onlyの料理（正常ケース）
                logger.debug(
                    "📝 Dish has no main_food (extras-only), skipping main_food nutrition"
                )
            elif isinstance(main_food, dict):
                # main_foodが辞書の場合（正常ケース）
                main_nutrition = main_food.get("nutrition")
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
            extras = dish.get("extras")
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
                extra_nutrition = extra.get("nutrition")
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

    def _apply_calorie_calibration(
        self, dishes: List[Dict], total_nutrition: Dict[str, float]
    ) -> tuple:
        """後段カロリーキャリブレーションを一貫して適用（既定OFFならno-op）。

        系統的なカロリー過小推定（計測 calibration slope ~0.47）を補正する affine map
        を、total・dish・ingredient の栄養素と weight_g に同一 factor で掛けて応答の
        整合性を保つ。factor は guard rail でクランプ済み。
        """
        cal = getattr(self, "calorie_calibration", None)
        if cal is None or not cal.enabled:
            return dishes, total_nutrition

        raw_cal = float(total_nutrition.get("calories", 0.0) or 0.0)
        factor = cal.scale_factor(raw_cal)
        if factor == 1.0:
            return dishes, total_nutrition

        def _scale_entry(entry: Optional[Dict]) -> None:
            if not isinstance(entry, dict):
                return
            nutrition = entry.get("nutrition")
            if isinstance(nutrition, dict):
                for key in ("calories", "protein_g", "fat_g", "carbs_g"):
                    if nutrition.get(key) is not None:
                        nutrition[key] = round(nutrition[key] * factor, 1)
            if entry.get("weight_g") is not None:
                entry["weight_g"] = round(entry["weight_g"] * factor, 1)

        for dish in dishes:
            _scale_entry(dish.get("main_food"))
            for extra in dish.get("extras") or []:
                _scale_entry(extra)

        scaled_total = {k: round(v * factor, 1) for k, v in total_nutrition.items()}
        logger.info(
            "Applied calorie calibration: factor=%.3f (raw=%.0f -> %.0f kcal)",
            factor,
            raw_cal,
            scaled_total.get("calories", 0.0),
        )
        return dishes, scaled_total

    async def analyze_meal_from_voice(
        self,
        audio_bytes: bytes,
        user_context: Optional[str] = None,
        model_config_override: Optional[Any] = None,
        search_config_override: Optional[Any] = None,
        voice_model_id: Optional[str] = None,
        voice_prompt_file: Optional[str] = None,
        voice_prompt_text: Optional[str] = None,
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
            voice_prompt_text: Voice解析用カスタムプロンプトテキスト（prompt_fileより優先）
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
            IngredientDetail,
            DishDetail,
            NutritionInfo,
            VoiceMetadata,
        )
        from ..admin.config_manager import get_config_manager

        logger.info("=" * 80)
        logger.info("Starting Voice-based Meal Analysis")
        logger.info("=" * 80)

        start_time = time.time()

        # Admin Panel設定を取得
        config_manager = get_config_manager()
        admin_config = config_manager.get_config()
        voice_config = admin_config.voice

        # パラメータ優先順位: API引数 > Admin Panel設定 > デフォルト
        actual_voice_model_id = voice_model_id or voice_config.model_id
        actual_voice_prompt_file = voice_prompt_file or voice_config.prompt_file
        actual_voice_prompt_text = voice_prompt_text or voice_config.prompt_text
        actual_whisper_model = whisper_model or voice_config.whisper_model
        actual_temperature = (
            model_config_override.temperature
            if model_config_override and model_config_override.temperature is not None
            else voice_config.temperature
        )
        actual_max_tokens = (
            model_config_override.max_tokens
            if model_config_override and model_config_override.max_tokens is not None
            else voice_config.max_tokens
        )

        # 設定情報をログに記録（Firestoreで確認可能）
        logger.info("📋 Voice Analysis Configuration:")
        logger.info(f"   Voice Model ID: {actual_voice_model_id}")
        logger.info(f"   Voice Prompt File: {actual_voice_prompt_file}")
        logger.info(
            f"   Voice Prompt Text: {'[Custom text provided]' if actual_voice_prompt_text else '[Not set]'}"
        )
        logger.info(f"   Whisper Model: {actual_whisper_model}")
        logger.info(f"   Temperature: {actual_temperature}")
        logger.info(f"   Max Tokens: {actual_max_tokens}")
        logger.info(f"   Language: {language}")
        logger.info(
            "   Config Source: Admin Panel (Firestore)"
            if config_manager.use_firestore
            else "   Config Source: In-Memory"
        )

        # Step 1: 音声認識 (STT)
        logger.info("\n🔄 Step 1/4: Speech-to-Text (Whisper)")

        speech_service = SpeechService()
        try:
            transcript, stt_metadata = await speech_service.transcribe_audio(
                audio_data=audio_bytes, language=language, model=actual_whisper_model
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
            model_id=actual_voice_model_id,
            prompt_file=actual_voice_prompt_file,
            prompt_text=actual_voice_prompt_text,
        )

        try:
            llm_result, llm_usage = await text_analysis_service.analyze_text(
                text=transcript,
                temperature=actual_temperature,
                max_tokens=actual_max_tokens,
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
                search_kwargs["reranker_instruction"] = (
                    search_config_override.reranker_instruction
                )
            if search_config_override.reranker_top_n is not None:
                search_kwargs["reranker_top_n"] = search_config_override.reranker_top_n

        # 並列検索
        search_results = await self._parallel_search(
            queries, include_debug_info=include_debug_info, **search_kwargs
        )
        logger.info(f"✅ USDA search complete: {len(search_results)} results")

        # クエリに検索結果を付与
        for i, query in enumerate(queries):
            query["usda_match"] = search_results[i]

        # Step 4: 栄養素計算
        logger.info("\n🔄 Step 4/4: Nutrition Calculation")

        enriched_dishes = self._build_enriched_dishes(dishes, queries)
        total_nutrition = self._calculate_total_nutrition(enriched_dishes)
        enriched_dishes, total_nutrition = self._apply_calorie_calibration(
            enriched_dishes, total_nutrition
        )

        logger.info("✅ Nutrition calculation complete")
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
                    main_nutrition_per_100g = (
                        self.nutrition_service.get_nutrition_per_100g(main_fdc_id)
                        if main_fdc_id
                        else None
                    )

                    debug_info = None
                    if include_debug_info:
                        debug_info = usda_match.get("_debug_info")

                    ingredients.append(
                        IngredientDetail(
                            ingredient_name=main_food.get(
                                "matched_description", main_food.get("search_name", "")
                            ),
                            vlm_query=main_food.get("search_name", ""),
                            matched_db_description=main_food.get(
                                "matched_description", ""
                            ),
                            weight_g=main_food.get("weight_g", 0.0),
                            nutrition_per_100g=NutritionInfo(
                                calories=main_nutrition_per_100g.get("calories", 0.0)
                                if main_nutrition_per_100g
                                else 0.0,
                                protein=main_nutrition_per_100g.get("protein_g", 0.0)
                                if main_nutrition_per_100g
                                else 0.0,
                                fat=main_nutrition_per_100g.get("fat_g", 0.0)
                                if main_nutrition_per_100g
                                else 0.0,
                                carbs=main_nutrition_per_100g.get("carbs_g", 0.0)
                                if main_nutrition_per_100g
                                else 0.0,
                            ),
                            calculated_nutrition=NutritionInfo(
                                calories=nutrition.get("calories", 0.0)
                                if nutrition
                                else 0.0,
                                protein=nutrition.get("protein_g", 0.0)
                                if nutrition
                                else 0.0,
                                fat=nutrition.get("fat_g", 0.0) if nutrition else 0.0,
                                carbs=nutrition.get("carbs_g", 0.0)
                                if nutrition
                                else 0.0,
                            ),
                            source_db="usda_fndds",
                            fdc_id=str(usda_match.get("fdc_id", "")),
                            calculation_notes=[
                                f"Weight: {main_food.get('weight_g', 0)}g"
                            ],
                            debug_info=debug_info,
                        )
                    )

            # Extrasを追加
            for extra in dish.get("extras", []):
                extra_nutrition = extra.get("nutrition", {})
                extra_usda = extra.get("usda_match", {})
                extra_fdc_id = extra_usda.get("fdc_id")
                extra_nutrition_per_100g = (
                    self.nutrition_service.get_nutrition_per_100g(extra_fdc_id)
                    if extra_fdc_id
                    else None
                )

                extra_debug_info = None
                if include_debug_info:
                    extra_debug_info = extra_usda.get("_debug_info")

                ingredients.append(
                    IngredientDetail(
                        ingredient_name=extra.get(
                            "matched_description", extra.get("search_name", "Unknown")
                        ),
                        vlm_query=extra.get("search_name", ""),
                        matched_db_description=extra.get("matched_description", ""),
                        weight_g=extra.get("weight_g", 0.0),
                        nutrition_per_100g=NutritionInfo(
                            calories=extra_nutrition_per_100g.get("calories", 0.0)
                            if extra_nutrition_per_100g
                            else 0.0,
                            protein=extra_nutrition_per_100g.get("protein_g", 0.0)
                            if extra_nutrition_per_100g
                            else 0.0,
                            fat=extra_nutrition_per_100g.get("fat_g", 0.0)
                            if extra_nutrition_per_100g
                            else 0.0,
                            carbs=extra_nutrition_per_100g.get("carbs_g", 0.0)
                            if extra_nutrition_per_100g
                            else 0.0,
                        ),
                        calculated_nutrition=NutritionInfo(
                            calories=extra_nutrition.get("calories", 0.0)
                            if extra_nutrition
                            else 0.0,
                            protein=extra_nutrition.get("protein_g", 0.0)
                            if extra_nutrition
                            else 0.0,
                            fat=extra_nutrition.get("fat_g", 0.0)
                            if extra_nutrition
                            else 0.0,
                            carbs=extra_nutrition.get("carbs_g", 0.0)
                            if extra_nutrition
                            else 0.0,
                        ),
                        source_db="usda_fndds",
                        fdc_id=str(extra_usda.get("fdc_id", "")),
                        calculation_notes=[f"Weight: {extra.get('weight_g', 0)}g"],
                        debug_info=extra_debug_info,
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
                    },
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

        # モデル情報（実際に使用された設定を返す）
        ai_model_used = actual_voice_model_id
        prompt_file_used = (
            actual_voice_prompt_file
            if not actual_voice_prompt_text
            else "[custom_prompt_text]"
        )

        # マッチ率計算
        total_queries_count = len(api_dishes)
        matched_queries = sum(1 for dish in api_dishes if len(dish.ingredients) > 0)
        match_rate = (
            (matched_queries / total_queries_count * 100)
            if total_queries_count > 0
            else 0.0
        )

        # Usage情報とコスト計算
        from ..models.response_models import UsageInfo

        usage_info = None
        if llm_usage:
            cost_data = self.cost_calculator.calculate_cost(
                model_id=ai_model_used,
                prompt_tokens=llm_usage.get("prompt_tokens", 0),
                completion_tokens=llm_usage.get("completion_tokens", 0),
            )

            if cost_data is None:
                usage_info = UsageInfo(
                    prompt_tokens=llm_usage.get("prompt_tokens", 0),
                    completion_tokens=llm_usage.get("completion_tokens", 0),
                    total_tokens=llm_usage.get("total_tokens", 0),
                    estimated_cost_usd=None,
                    model_pricing=None,
                    raw_vlm_output=llm_usage.get("raw_vlm_output"),
                )
            else:
                usage_info = UsageInfo(
                    prompt_tokens=cost_data["prompt_tokens"],
                    completion_tokens=cost_data["completion_tokens"],
                    total_tokens=cost_data["total_tokens"],
                    estimated_cost_usd=cost_data["estimated_cost_usd"],
                    model_pricing=cost_data["model_pricing"],
                    raw_vlm_output=llm_usage.get("raw_vlm_output"),
                )

        # VoiceMetadata
        voice_metadata = VoiceMetadata(
            whisper_model=stt_metadata.get("whisper_model", ""),
            audio_duration_seconds=stt_metadata.get("audio_duration_seconds"),
            audio_size_bytes=stt_metadata.get("audio_size_bytes", len(audio_bytes)),
            language_detected=stt_metadata.get("language_detected"),
            stt_processing_time_seconds=stt_metadata.get("stt_processing_time_seconds"),
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
