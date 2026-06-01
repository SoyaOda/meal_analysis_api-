"""
SSE Streaming router for real-time progress updates

Provides Server-Sent Events (SSE) endpoint for meal analysis with live progress updates.
"""

import uuid
import time
import json
import logging
import asyncio
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from ..models.request_models import ModelConfig, SearchConfig
from ..models.response_models import AnalysisResponse
from .analysis import get_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/meal-analyses", tags=["Streaming"])


# Progress stage definitions for image analysis
IMAGE_STAGES = {
    "upload": {
        "progress": 5,
        "message_en": "Receiving image...",
        "message_ja": "画像を受信中...",
    },
    "vlm_start": {
        "progress": 10,
        "message_en": "Analyzing image with AI...",
        "message_ja": "AIが画像を解析中...",
    },
    "vlm_complete": {
        "progress": 40,
        "message_en": "Image analysis complete",
        "message_ja": "画像解析完了",
    },
    "query_extraction": {
        "progress": 45,
        "message_en": "Extracting food items...",
        "message_ja": "食材を抽出中...",
    },
    "embedding_start": {
        "progress": 50,
        "message_en": "Generating embeddings...",
        "message_ja": "埋め込みを生成中...",
    },
    "embedding_complete": {
        "progress": 55,
        "message_en": "Embeddings generated",
        "message_ja": "埋め込み生成完了",
    },
    "search_start": {
        "progress": 60,
        "message_en": "Searching food database...",
        "message_ja": "食品データベースを検索中...",
    },
    "search_complete": {
        "progress": 70,
        "message_en": "Database search complete",
        "message_ja": "データベース検索完了",
    },
    "rerank_start": {
        "progress": 75,
        "message_en": "Ranking results...",
        "message_ja": "結果をランキング中...",
    },
    "rerank_complete": {
        "progress": 85,
        "message_en": "Ranking complete",
        "message_ja": "ランキング完了",
    },
    "nutrition_start": {
        "progress": 90,
        "message_en": "Calculating nutrition...",
        "message_ja": "栄養価を計算中...",
    },
    "nutrition_complete": {
        "progress": 95,
        "message_en": "Nutrition calculated",
        "message_ja": "栄養価計算完了",
    },
    "complete": {
        "progress": 100,
        "message_en": "Analysis complete!",
        "message_ja": "分析完了！",
    },
}

# Progress stage definitions for voice analysis
VOICE_STAGES = {
    "upload": {
        "progress": 5,
        "message_en": "Receiving audio...",
        "message_ja": "音声を受信中...",
    },
    "stt_start": {
        "progress": 10,
        "message_en": "Converting speech to text...",
        "message_ja": "音声をテキストに変換中...",
    },
    "stt_complete": {
        "progress": 30,
        "message_en": "Speech recognition complete",
        "message_ja": "音声認識完了",
    },
    "llm_start": {
        "progress": 35,
        "message_en": "Analyzing text with AI...",
        "message_ja": "AIがテキストを解析中...",
    },
    "llm_complete": {
        "progress": 50,
        "message_en": "Text analysis complete",
        "message_ja": "テキスト解析完了",
    },
    "query_extraction": {
        "progress": 55,
        "message_en": "Extracting food items...",
        "message_ja": "食材を抽出中...",
    },
    "embedding_start": {
        "progress": 60,
        "message_en": "Generating embeddings...",
        "message_ja": "埋め込みを生成中...",
    },
    "embedding_complete": {
        "progress": 65,
        "message_en": "Embeddings generated",
        "message_ja": "埋め込み生成完了",
    },
    "search_start": {
        "progress": 70,
        "message_en": "Searching food database...",
        "message_ja": "食品データベースを検索中...",
    },
    "search_complete": {
        "progress": 77,
        "message_en": "Database search complete",
        "message_ja": "データベース検索完了",
    },
    "rerank_start": {
        "progress": 80,
        "message_en": "Ranking results...",
        "message_ja": "結果をランキング中...",
    },
    "rerank_complete": {
        "progress": 88,
        "message_en": "Ranking complete",
        "message_ja": "ランキング完了",
    },
    "nutrition_start": {
        "progress": 92,
        "message_en": "Calculating nutrition...",
        "message_ja": "栄養価を計算中...",
    },
    "nutrition_complete": {
        "progress": 97,
        "message_en": "Nutrition calculated",
        "message_ja": "栄養価計算完了",
    },
    "complete": {
        "progress": 100,
        "message_en": "Analysis complete!",
        "message_ja": "分析完了！",
    },
}

# Backward compatibility
STAGES = IMAGE_STAGES


def create_progress_event(
    stage: str, details: Optional[dict] = None, stages: dict = None
) -> dict:
    """Create a progress event payload"""
    if stages is None:
        stages = STAGES
    stage_info = stages.get(
        stage, {"progress": 0, "message_en": stage, "message_ja": stage}
    )
    event = {
        "stage": stage,
        "progress": stage_info["progress"],
        "message": stage_info["message_en"],
        "message_ja": stage_info["message_ja"],
        "timestamp": time.time(),
    }
    if details:
        event["details"] = details
    return event


@router.post("/stream")
async def analyze_meal_stream(
    request: Request,
    image: UploadFile = File(..., description="食事画像ファイル"),
    user_context: Optional[str] = Form(None, description="ユーザーコンテキスト"),
    # Model config overrides
    vlm_model_id: Optional[str] = Form(None, description="VLMモデルID"),
    prompt_path: Optional[str] = Form(None, description="プロンプトファイルパス"),
    reasoning_effort: Optional[str] = Form(None, description="Reasoning effortレベル"),
    temperature: Optional[float] = Form(None, description="生成温度"),
    max_tokens: Optional[int] = Form(None, description="最大トークン数"),
    # Search config overrides
    stage1_top_k: Optional[int] = Form(None, description="Stage1候補数"),
    reranker_model: Optional[str] = Form(None, description="Rerankerモデル名"),
    # Options
    debug: bool = Form(False, description="デバッグ情報を含める"),
    language: str = Form("en", description="言語 (en/ja)"),
):
    """
    SSE streaming endpoint for meal analysis with real-time progress updates.

    ## Event Types

    - **progress**: Processing stage updates with progress percentage
    - **result**: Final analysis result (same format as /complete endpoint)
    - **error**: Error information if analysis fails

    ## Progress Stages

    1. upload (5%) - Image received
    2. vlm_start (10%) - VLM analysis starting
    3. vlm_complete (40%) - VLM analysis complete
    4. query_extraction (45%) - Extracting food queries
    5. embedding_start (50%) - Generating embeddings
    6. embedding_complete (55%) - Embeddings generated
    7. search_start (60%) - Database search starting
    8. search_complete (70%) - Database search complete
    9. rerank_start (75%) - Reranking results
    10. rerank_complete (85%) - Reranking complete
    11. nutrition_start (90%) - Calculating nutrition
    12. nutrition_complete (95%) - Nutrition calculated
    13. complete (100%) - Analysis complete

    ## Usage (JavaScript)

    ```javascript
    const formData = new FormData();
    formData.append('image', file);

    const eventSource = new EventSource('/api/v1/meal-analyses/stream', {
        method: 'POST',
        body: formData
    });

    eventSource.addEventListener('progress', (e) => {
        const data = JSON.parse(e.data);
        console.log(`${data.progress}%: ${data.message}`);
    });

    eventSource.addEventListener('result', (e) => {
        const result = JSON.parse(e.data);
        console.log('Analysis complete:', result);
        eventSource.close();
    });
    ```

    ## Usage (Swift/iOS)

    Use EventSource library (e.g., mattt/EventSource) to consume SSE events.
    """
    analysis_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # Read image data BEFORE entering the generator (required for SSE)
    # FastAPI closes the file after the request handler returns
    image_bytes = await image.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Image file is empty")

    # File size limit (20MB)
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail="Image file too large. Maximum size is 20MB."
        )

    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            # Stage: Upload received
            yield {
                "event": "progress",
                "data": json.dumps(create_progress_event("upload")),
            }

            # image_bytes is already read above

            # Get pipeline
            pipeline = get_pipeline()

            # Build config overrides
            model_config_override = None
            if any(
                [vlm_model_id, prompt_path, reasoning_effort, temperature, max_tokens]
            ):
                model_config_override = ModelConfig(
                    vlm_model_id=vlm_model_id,
                    prompt_path=prompt_path,
                    reasoning_effort=reasoning_effort,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            search_config_override = None
            if any([stage1_top_k, reranker_model]):
                search_config_override = SearchConfig(
                    stage1_top_k=stage1_top_k,
                    reranker_model=reranker_model,
                )

            # Create progress callback
            async def progress_callback(stage: str, details: Optional[dict] = None):
                """Callback to emit progress events"""
                # Check if client disconnected
                if await request.is_disconnected():
                    raise asyncio.CancelledError("Client disconnected")
                return create_progress_event(stage, details)

            # Run streaming analysis
            result = None
            async for event in stream_analysis(
                pipeline=pipeline,
                image_bytes=image_bytes,
                user_context=user_context,
                model_config_override=model_config_override,
                search_config_override=search_config_override,
                include_debug_info=debug,
            ):
                if event["type"] == "progress":
                    yield {"event": "progress", "data": json.dumps(event["data"])}
                elif event["type"] == "result":
                    result = event["data"]

            # Final result
            processing_time = time.time() - start_time

            response = AnalysisResponse(
                analysis_id=analysis_id,
                input_type="image",
                meal_title=result.get("meal_title"),
                total_dishes=len(result["dishes"]),
                total_ingredients=sum(len(d.ingredients) for d in result["dishes"]),
                processing_time_seconds=processing_time,
                dishes=result["dishes"],
                total_nutrition=result["total_nutrition"],
                ai_model_used=result["ai_model_used"],
                prompt_file_used=result["prompt_file_used"],
                match_rate_percent=result["match_rate_percent"],
                usage=result.get("usage"),
                warnings=result.get("warnings", []),
            )

            yield {"event": "result", "data": response.model_dump_json()}

        except asyncio.CancelledError:
            logger.info(f"Client disconnected during analysis {analysis_id}")
            yield {
                "event": "error",
                "data": json.dumps(
                    {"error": "ClientDisconnected", "message": "Client disconnected"}
                ),
            }
        except Exception as e:
            logger.error(f"Streaming analysis failed: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "error": type(e).__name__,
                        "message": str(e),
                        "analysis_id": analysis_id,
                    }
                ),
            }

    return EventSourceResponse(event_generator())


async def stream_analysis(
    pipeline,
    image_bytes: bytes,
    user_context: Optional[str] = None,
    model_config_override=None,
    search_config_override=None,
    include_debug_info: bool = False,
) -> AsyncGenerator[dict, None]:
    """
    Stream analysis with progress events.

    Yields events in the format:
    {"type": "progress", "data": {...}}
    {"type": "result", "data": {...}}
    """
    from ..admin import get_config_manager
    from ..models.response_models import (
        IngredientDetail,
        DishDetail,
        NutritionInfo,
        UsageInfo,
    )

    config_manager = get_config_manager()
    config = config_manager.get_config()

    # ========== Stage: VLM Analysis ==========
    yield {"type": "progress", "data": create_progress_event("vlm_start")}

    # Apply model config
    vlm_kwargs = {}
    if model_config_override:
        if model_config_override.temperature is not None:
            vlm_kwargs["temperature"] = model_config_override.temperature
        if model_config_override.max_tokens is not None:
            vlm_kwargs["max_tokens"] = model_config_override.max_tokens
        if model_config_override.reasoning_effort is not None:
            vlm_kwargs["reasoning_effort"] = model_config_override.reasoning_effort
    else:
        vlm_kwargs["temperature"] = config.vlm.temperature
        vlm_kwargs["max_tokens"] = config.vlm.max_tokens
        vlm_kwargs["reasoning_effort"] = config.vlm.reasoning_effort

    # Apply prompt override
    if model_config_override and model_config_override.prompt_text:
        pipeline.vlm_service.prompt = model_config_override.prompt_text
    elif model_config_override and model_config_override.prompt_path:
        from ..config import get_settings

        settings = get_settings()
        prompt_full_path = settings.get_prompt_path(model_config_override.prompt_path)
        pipeline.vlm_service.prompt = pipeline.vlm_service._load_prompt(
            prompt_full_path
        )
    elif config.vlm.prompt_text:
        pipeline.vlm_service.prompt = config.vlm.prompt_text
    elif config.vlm.prompt_file:
        from ..config import get_settings

        settings = get_settings()
        prompt_full_path = settings.get_prompt_path(config.vlm.prompt_file)
        pipeline.vlm_service.prompt = pipeline.vlm_service._load_prompt(
            prompt_full_path
        )

    # Apply model ID override
    effective_model_id = None
    if model_config_override and model_config_override.vlm_model_id:
        effective_model_id = model_config_override.vlm_model_id
    elif config.vlm.model_id:
        effective_model_id = config.vlm.model_id

    if effective_model_id and effective_model_id != pipeline.vlm_service.model_id:
        pipeline.vlm_service.model_id = effective_model_id
        from ..services.providers import VLMProviderFactory

        pipeline.vlm_service.provider = VLMProviderFactory.create_provider(
            model_id=effective_model_id
        )
        pipeline.vlm_service.deepinfra_service = pipeline.vlm_service.provider

    # Run VLM
    vlm_response, usage = await pipeline.vlm_service.analyze_image(
        image_bytes=image_bytes, image_mime_type="image/jpeg", **vlm_kwargs
    )

    if vlm_response is None:
        raise ValueError("VLM returned None response")

    dishes = vlm_response.get("dishes", [])
    meal_title = vlm_response.get("meal_title")

    yield {
        "type": "progress",
        "data": create_progress_event("vlm_complete", {"dish_count": len(dishes)}),
    }

    # ========== Stage: Query Extraction ==========
    yield {"type": "progress", "data": create_progress_event("query_extraction")}

    queries = pipeline.query_extraction.extract_queries(vlm_response)
    query_texts = [q["search_name"] for q in queries]

    # ========== Stage: Embedding Generation ==========
    yield {
        "type": "progress",
        "data": create_progress_event(
            "embedding_start", {"query_count": len(query_texts)}
        ),
    }

    embeddings = await pipeline.food_search_service.batch_generate_embeddings(
        query_texts
    )

    yield {"type": "progress", "data": create_progress_event("embedding_complete")}

    # ========== Stage: Database Search (BM25 + FAISS) ==========
    yield {"type": "progress", "data": create_progress_event("search_start")}

    # Get search config
    effective_stage1_top_k = (
        search_config_override.stage1_top_k
        if search_config_override and search_config_override.stage1_top_k
        else config.search.stage1_top_k
    )
    effective_bm25_weight = config.search.bm25_weight
    effective_vector_weight = config.search.vector_weight
    effective_rrf_k = config.search.rrf_k
    effective_rrf_weight = config.search.rrf_weight

    queries_and_candidates = []
    for i, query in enumerate(queries):
        candidates = pipeline.food_search_service.get_candidates_only_sync(
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

    yield {"type": "progress", "data": create_progress_event("search_complete")}

    # ========== Stage: Reranking ==========
    yield {"type": "progress", "data": create_progress_event("rerank_start")}

    effective_reranker_model = (
        search_config_override.reranker_model
        if search_config_override and search_config_override.reranker_model
        else config.reranker.model
    )
    effective_reranker_instruction = config.reranker.instruction

    reranked_results = await pipeline.food_search_service.batch_rerank_candidates(
        queries_and_candidates=queries_and_candidates,
        reranker_model=effective_reranker_model,
        reranker_instruction=effective_reranker_instruction,
        top_k=1,
    )

    yield {"type": "progress", "data": create_progress_event("rerank_complete")}

    # Process results
    for i, result in enumerate(reranked_results):
        if result:
            result["score"] = result.get("rerank_score", 0)
        queries[i]["usda_match"] = result

    # ========== Stage: Nutrition Calculation ==========
    yield {"type": "progress", "data": create_progress_event("nutrition_start")}

    enriched_dishes = pipeline._build_enriched_dishes(dishes, queries)
    total_nutrition = pipeline._calculate_total_nutrition(enriched_dishes)

    yield {"type": "progress", "data": create_progress_event("nutrition_complete")}

    # ========== Build API Response ==========
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
                    pipeline.nutrition_service.get_nutrition_per_100g(main_fdc_id)
                    if main_fdc_id
                    else None
                )

                ingredients.append(
                    IngredientDetail(
                        ingredient_name=main_food.get(
                            "matched_description", main_food.get("search_name", "")
                        ),
                        vlm_query=main_food.get("search_name", ""),
                        matched_db_description=main_food.get("matched_description", ""),
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
                            carbs=nutrition.get("carbs_g", 0.0) if nutrition else 0.0,
                        ),
                        source_db="usda_fndds",
                        fdc_id=str(usda_match.get("fdc_id", "")),
                        calculation_notes=[f"Weight: {main_food.get('weight_g', 0)}g"],
                    )
                )

        # Add extras
        for extra in dish.get("extras", []):
            extra_nutrition = extra.get("nutrition", {})
            extra_usda = extra.get("usda_match", {})
            extra_fdc_id = extra_usda.get("fdc_id")
            extra_nutrition_per_100g = (
                pipeline.nutrition_service.get_nutrition_per_100g(extra_fdc_id)
                if extra_fdc_id
                else None
            )

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
                )
            )

        dish_nutrition = NutritionInfo(
            calories=sum(ing.calculated_nutrition.calories for ing in ingredients),
            protein=sum(ing.calculated_nutrition.protein for ing in ingredients),
            fat=sum(ing.calculated_nutrition.fat for ing in ingredients),
            carbs=sum(ing.calculated_nutrition.carbs for ing in ingredients),
        )

        api_dishes.append(
            DishDetail(
                dish_name=dish.get("dish_name"),
                ingredients=ingredients,
                total_nutrition=dish_nutrition,
                calculation_metadata={
                    "ingredient_count": len(ingredients),
                    "total_weight_g": sum(ing.weight_g for ing in ingredients),
                },
            )
        )

    # Total nutrition
    total_nutrition_info = NutritionInfo(
        calories=total_nutrition["calories"],
        protein=total_nutrition["protein_g"],
        fat=total_nutrition["fat_g"],
        carbs=total_nutrition["carbs_g"],
    )

    # Model info
    ai_model_used = pipeline.vlm_service.model_id
    if model_config_override and model_config_override.prompt_text:
        prompt_file_used = "[Custom Prompt Text (API Override)]"
    elif model_config_override and model_config_override.prompt_path:
        prompt_file_used = model_config_override.prompt_path
    elif config.vlm.prompt_text:
        prompt_file_used = "[Custom Prompt Text (Admin Config)]"
    else:
        prompt_file_used = config.vlm.prompt_file

    # Match rate
    total_queries_count = len(api_dishes)
    matched_queries = sum(1 for dish in api_dishes if len(dish.ingredients) > 0)
    match_rate = (
        (matched_queries / total_queries_count * 100)
        if total_queries_count > 0
        else 0.0
    )

    # Usage info
    usage_info = None
    if usage:
        cost_data = pipeline.cost_calculator.calculate_cost(
            model_id=ai_model_used,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )

        if cost_data is None:
            usage_info = UsageInfo(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )
        else:
            usage_info = UsageInfo(
                prompt_tokens=cost_data["prompt_tokens"],
                completion_tokens=cost_data["completion_tokens"],
                total_tokens=cost_data["total_tokens"],
                estimated_cost_usd=cost_data["estimated_cost_usd"],
                model_pricing=cost_data["model_pricing"],
            )

    yield {"type": "progress", "data": create_progress_event("complete")}

    yield {
        "type": "result",
        "data": {
            "dishes": api_dishes,
            "meal_title": meal_title,
            "total_nutrition": total_nutrition_info,
            "ai_model_used": ai_model_used,
            "prompt_file_used": prompt_file_used,
            "match_rate_percent": match_rate,
            "usage": usage_info,
            "warnings": [],
        },
    }


@router.post("/voice/stream")
async def analyze_meal_voice_stream(
    request: Request,
    audio_file: UploadFile = File(..., description="音声ファイル（WAV, MP3等）"),
    user_context: Optional[str] = Form(None, description="ユーザーコンテキスト"),
    # Voice model config
    voice_model_id: Optional[str] = Form(None, description="Voice解析用LLMモデルID"),
    voice_prompt_file: Optional[str] = Form(
        None, description="Voice解析用プロンプトファイル"
    ),
    whisper_model: Optional[str] = Form(None, description="Whisperモデル"),
    language: str = Form("en", description="言語コード"),
    # Model config overrides
    temperature: Optional[float] = Form(None, description="生成温度"),
    max_tokens: Optional[int] = Form(None, description="最大トークン数"),
    # Search config overrides
    stage1_top_k: Optional[int] = Form(None, description="Stage1候補数"),
    reranker_model: Optional[str] = Form(None, description="Rerankerモデル名"),
    # Options
    debug: bool = Form(False, description="デバッグ情報を含める"),
):
    """
    SSE streaming endpoint for voice-based meal analysis with real-time progress updates.

    ## Event Types

    - **progress**: Processing stage updates with progress percentage
    - **result**: Final analysis result (same format as /voice endpoint)
    - **error**: Error information if analysis fails

    ## Progress Stages

    1. upload (5%) - Audio received
    2. stt_start (10%) - Speech recognition starting
    3. stt_complete (30%) - Speech recognition complete
    4. llm_start (35%) - LLM text analysis starting
    5. llm_complete (50%) - LLM analysis complete
    6. query_extraction (55%) - Extracting food queries
    7. embedding_start (60%) - Generating embeddings
    8. embedding_complete (65%) - Embeddings generated
    9. search_start (70%) - Database search starting
    10. search_complete (77%) - Database search complete
    11. rerank_start (80%) - Reranking results
    12. rerank_complete (88%) - Reranking complete
    13. nutrition_start (92%) - Calculating nutrition
    14. nutrition_complete (97%) - Nutrition calculated
    15. complete (100%) - Analysis complete

    ## Usage (JavaScript)

    ```javascript
    const formData = new FormData();
    formData.append('audio_file', audioBlob);

    const response = await fetch('/api/v1/meal-analyses/voice/stream', {
        method: 'POST',
        body: formData
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        // Parse SSE events
    }
    ```
    """
    analysis_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # Read audio data BEFORE entering the generator (required for SSE)
    # FastAPI closes the file after the request handler returns
    audio_bytes = await audio_file.read()

    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Audio file is empty")

    # File size limit (50MB)
    if len(audio_bytes) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail="Audio file too large. Maximum size is 50MB."
        )

    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            # Stage: Upload received
            yield {
                "event": "progress",
                "data": json.dumps(
                    create_progress_event("upload", stages=VOICE_STAGES)
                ),
            }

            # audio_bytes is already read above

            # Get pipeline
            pipeline = get_pipeline()

            # Build config overrides
            model_config_override = None
            if any([temperature, max_tokens]):
                model_config_override = ModelConfig(
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            search_config_override = None
            if any([stage1_top_k, reranker_model]):
                search_config_override = SearchConfig(
                    stage1_top_k=stage1_top_k,
                    reranker_model=reranker_model,
                )

            # Run streaming voice analysis
            result = None
            async for event in stream_voice_analysis(
                pipeline=pipeline,
                audio_bytes=audio_bytes,
                user_context=user_context,
                model_config_override=model_config_override,
                search_config_override=search_config_override,
                voice_model_id=voice_model_id,
                voice_prompt_file=voice_prompt_file,
                whisper_model=whisper_model,
                language=language,
                include_debug_info=debug,
            ):
                if event["type"] == "progress":
                    yield {"event": "progress", "data": json.dumps(event["data"])}
                elif event["type"] == "result":
                    result = event["data"]

            # Final result
            processing_time = time.time() - start_time

            response = AnalysisResponse(
                analysis_id=analysis_id,
                input_type="voice",
                meal_title=result.get("meal_title"),
                total_dishes=len(result["dishes"]),
                total_ingredients=sum(len(d.ingredients) for d in result["dishes"]),
                processing_time_seconds=processing_time,
                dishes=result["dishes"],
                total_nutrition=result["total_nutrition"],
                ai_model_used=result["ai_model_used"],
                prompt_file_used=result["prompt_file_used"],
                match_rate_percent=result["match_rate_percent"],
                usage=result.get("usage"),
                transcript=result.get("transcript"),
                voice_metadata=result.get("voice_metadata"),
                warnings=result.get("warnings", []),
            )

            yield {"event": "result", "data": response.model_dump_json()}

        except asyncio.CancelledError:
            logger.info(f"Client disconnected during voice analysis {analysis_id}")
            yield {
                "event": "error",
                "data": json.dumps(
                    {"error": "ClientDisconnected", "message": "Client disconnected"}
                ),
            }
        except Exception as e:
            logger.error(f"Voice streaming analysis failed: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "error": type(e).__name__,
                        "message": str(e),
                        "analysis_id": analysis_id,
                    }
                ),
            }

    return EventSourceResponse(event_generator())


async def stream_voice_analysis(
    pipeline,
    audio_bytes: bytes,
    user_context: Optional[str] = None,
    model_config_override=None,
    search_config_override=None,
    voice_model_id: Optional[str] = None,
    voice_prompt_file: Optional[str] = None,
    whisper_model: Optional[str] = None,
    language: str = "en",
    include_debug_info: bool = False,
) -> AsyncGenerator[dict, None]:
    """
    Stream voice analysis with progress events.

    Yields events in the format:
    {"type": "progress", "data": {...}}
    {"type": "result", "data": {...}}
    """
    from ..admin import get_config_manager
    from ..services.speech_service import SpeechService
    from ..services.text_analysis_service import TextAnalysisService
    from ..models.response_models import (
        IngredientDetail,
        DishDetail,
        NutritionInfo,
        VoiceMetadata,
        UsageInfo,
    )

    config_manager = get_config_manager()
    config = config_manager.get_config()

    # ========== Stage: STT (Speech-to-Text) ==========
    yield {
        "type": "progress",
        "data": create_progress_event("stt_start", stages=VOICE_STAGES),
    }

    speech_service = SpeechService()
    try:
        transcript, stt_metadata = await speech_service.transcribe_audio(
            audio_data=audio_bytes, language=language, model=whisper_model
        )
    except Exception as e:
        logger.error(f"STT failed: {e}")
        raise RuntimeError(f"Speech-to-text failed: {e}") from e

    if not transcript or not transcript.strip():
        raise ValueError("Speech recognition returned empty text")

    yield {
        "type": "progress",
        "data": create_progress_event(
            "stt_complete",
            {
                "transcript_preview": transcript[:100] + "..."
                if len(transcript) > 100
                else transcript
            },
            stages=VOICE_STAGES,
        ),
    }

    # ========== Stage: LLM Text Analysis ==========
    yield {
        "type": "progress",
        "data": create_progress_event("llm_start", stages=VOICE_STAGES),
    }

    text_analysis_service = TextAnalysisService(
        model_id=voice_model_id, prompt_file=voice_prompt_file
    )

    try:
        llm_result, llm_usage = await text_analysis_service.analyze_text(
            text=transcript,
            temperature=model_config_override.temperature
            if model_config_override
            else None,
            max_tokens=model_config_override.max_tokens
            if model_config_override
            else None,
        )
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        raise RuntimeError(f"LLM text analysis failed: {e}") from e

    dishes = llm_result.get("dishes", [])
    meal_title = llm_result.get("meal_title")

    yield {
        "type": "progress",
        "data": create_progress_event(
            "llm_complete", {"dish_count": len(dishes)}, stages=VOICE_STAGES
        ),
    }

    # ========== Stage: Query Extraction ==========
    yield {
        "type": "progress",
        "data": create_progress_event("query_extraction", stages=VOICE_STAGES),
    }

    queries = pipeline.query_extraction.extract_queries(llm_result)
    query_texts = [q["search_name"] for q in queries]

    # ========== Stage: Embedding Generation ==========
    yield {
        "type": "progress",
        "data": create_progress_event(
            "embedding_start", {"query_count": len(query_texts)}, stages=VOICE_STAGES
        ),
    }

    embeddings = await pipeline.food_search_service.batch_generate_embeddings(
        query_texts
    )

    yield {
        "type": "progress",
        "data": create_progress_event("embedding_complete", stages=VOICE_STAGES),
    }

    # ========== Stage: Database Search (BM25 + FAISS) ==========
    yield {
        "type": "progress",
        "data": create_progress_event("search_start", stages=VOICE_STAGES),
    }

    # Get search config
    effective_stage1_top_k = (
        search_config_override.stage1_top_k
        if search_config_override and search_config_override.stage1_top_k
        else config.search.stage1_top_k
    )
    effective_bm25_weight = config.search.bm25_weight
    effective_vector_weight = config.search.vector_weight
    effective_rrf_k = config.search.rrf_k
    effective_rrf_weight = config.search.rrf_weight

    queries_and_candidates = []
    for i, query in enumerate(queries):
        candidates = pipeline.food_search_service.get_candidates_only_sync(
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

    yield {
        "type": "progress",
        "data": create_progress_event("search_complete", stages=VOICE_STAGES),
    }

    # ========== Stage: Reranking ==========
    yield {
        "type": "progress",
        "data": create_progress_event("rerank_start", stages=VOICE_STAGES),
    }

    effective_reranker_model = (
        search_config_override.reranker_model
        if search_config_override and search_config_override.reranker_model
        else config.reranker.model
    )
    effective_reranker_instruction = config.reranker.instruction

    reranked_results = await pipeline.food_search_service.batch_rerank_candidates(
        queries_and_candidates=queries_and_candidates,
        reranker_model=effective_reranker_model,
        reranker_instruction=effective_reranker_instruction,
        top_k=1,
    )

    yield {
        "type": "progress",
        "data": create_progress_event("rerank_complete", stages=VOICE_STAGES),
    }

    # Process results
    for i, result in enumerate(reranked_results):
        if result:
            result["score"] = result.get("rerank_score", 0)
        queries[i]["usda_match"] = result

    # ========== Stage: Nutrition Calculation ==========
    yield {
        "type": "progress",
        "data": create_progress_event("nutrition_start", stages=VOICE_STAGES),
    }

    enriched_dishes = pipeline._build_enriched_dishes(dishes, queries)
    total_nutrition = pipeline._calculate_total_nutrition(enriched_dishes)

    yield {
        "type": "progress",
        "data": create_progress_event("nutrition_complete", stages=VOICE_STAGES),
    }

    # ========== Build API Response ==========
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
                    pipeline.nutrition_service.get_nutrition_per_100g(main_fdc_id)
                    if main_fdc_id
                    else None
                )

                ingredients.append(
                    IngredientDetail(
                        ingredient_name=main_food.get(
                            "matched_description", main_food.get("search_name", "")
                        ),
                        vlm_query=main_food.get("search_name", ""),
                        matched_db_description=main_food.get("matched_description", ""),
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
                            carbs=nutrition.get("carbs_g", 0.0) if nutrition else 0.0,
                        ),
                        source_db="usda_fndds",
                        fdc_id=str(usda_match.get("fdc_id", "")),
                        calculation_notes=[f"Weight: {main_food.get('weight_g', 0)}g"],
                    )
                )

        # Add extras
        for extra in dish.get("extras", []):
            extra_nutrition = extra.get("nutrition", {})
            extra_usda = extra.get("usda_match", {})
            extra_fdc_id = extra_usda.get("fdc_id")
            extra_nutrition_per_100g = (
                pipeline.nutrition_service.get_nutrition_per_100g(extra_fdc_id)
                if extra_fdc_id
                else None
            )

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
                )
            )

        dish_nutrition = NutritionInfo(
            calories=sum(ing.calculated_nutrition.calories for ing in ingredients),
            protein=sum(ing.calculated_nutrition.protein for ing in ingredients),
            fat=sum(ing.calculated_nutrition.fat for ing in ingredients),
            carbs=sum(ing.calculated_nutrition.carbs for ing in ingredients),
        )

        api_dishes.append(
            DishDetail(
                dish_name=dish.get("dish_name"),
                ingredients=ingredients,
                total_nutrition=dish_nutrition,
                calculation_metadata={
                    "ingredient_count": len(ingredients),
                    "total_weight_g": sum(ing.weight_g for ing in ingredients),
                },
            )
        )

    # Total nutrition
    total_nutrition_info = NutritionInfo(
        calories=total_nutrition["calories"],
        protein=total_nutrition["protein_g"],
        fat=total_nutrition["fat_g"],
        carbs=total_nutrition["carbs_g"],
    )

    # Model info
    ai_model_used = voice_model_id or text_analysis_service.model_id
    prompt_file_used = voice_prompt_file or text_analysis_service.prompt_file

    # Match rate
    total_queries_count = len(api_dishes)
    matched_queries = sum(1 for dish in api_dishes if len(dish.ingredients) > 0)
    match_rate = (
        (matched_queries / total_queries_count * 100)
        if total_queries_count > 0
        else 0.0
    )

    # Usage info
    usage_info = None
    if llm_usage:
        cost_data = pipeline.cost_calculator.calculate_cost(
            model_id=ai_model_used,
            prompt_tokens=llm_usage.get("prompt_tokens", 0),
            completion_tokens=llm_usage.get("completion_tokens", 0),
        )

        if cost_data is None:
            usage_info = UsageInfo(
                prompt_tokens=llm_usage.get("prompt_tokens", 0),
                completion_tokens=llm_usage.get("completion_tokens", 0),
                total_tokens=llm_usage.get("total_tokens", 0),
            )
        else:
            usage_info = UsageInfo(
                prompt_tokens=cost_data["prompt_tokens"],
                completion_tokens=cost_data["completion_tokens"],
                total_tokens=cost_data["total_tokens"],
                estimated_cost_usd=cost_data["estimated_cost_usd"],
                model_pricing=cost_data["model_pricing"],
            )

    # Voice metadata
    voice_metadata = VoiceMetadata(
        whisper_model=stt_metadata.get("whisper_model", ""),
        audio_duration_seconds=stt_metadata.get("audio_duration_seconds"),
        audio_size_bytes=stt_metadata.get("audio_size_bytes", len(audio_bytes)),
        language_detected=stt_metadata.get("language_detected"),
        stt_processing_time_seconds=stt_metadata.get("stt_processing_time_seconds"),
    )

    yield {
        "type": "progress",
        "data": create_progress_event("complete", stages=VOICE_STAGES),
    }

    yield {
        "type": "result",
        "data": {
            "dishes": api_dishes,
            "meal_title": meal_title,
            "total_nutrition": total_nutrition_info,
            "ai_model_used": ai_model_used,
            "prompt_file_used": prompt_file_used,
            "match_rate_percent": match_rate,
            "usage": usage_info,
            "transcript": transcript,
            "voice_metadata": voice_metadata,
            "warnings": [],
        },
    }
