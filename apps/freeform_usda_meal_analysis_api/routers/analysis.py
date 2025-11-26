"""
Analysis router for meal analysis endpoints
"""
import uuid
import time
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from ..models.request_models import ImageAnalysisRequest, ModelConfig, SearchConfig
from ..models.response_models import AnalysisResponse, ErrorResponse, EndpointInfoResponse
from ..services.pipeline import MealAnalysisPipeline
from ..config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/meal-analyses", tags=["Analysis"])

# グローバルパイプラインインスタンス（起動時に初期化）
_pipeline: Optional[MealAnalysisPipeline] = None


def get_pipeline() -> MealAnalysisPipeline:
    """パイプラインインスタンスを取得"""
    global _pipeline
    if _pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Pipeline not initialized. Please check server logs."
        )
    return _pipeline


def initialize_pipeline(hybrid_engine=None, use_lazy_loading=True):
    """パイプラインを初期化（アプリ起動時に呼び出す）"""
    global _pipeline
    settings = get_settings()

    try:
        logger.info("Initializing meal analysis pipeline (Full Index Only)...")
        _pipeline = MealAnalysisPipeline(
            vlm_model_id=settings.DEFAULT_VLM_MODEL_ID,
            vlm_prompt_file=settings.get_prompt_path(),
            index_dir=settings.USDA_INDEX_DIR,
            usda_metadata_file=settings.USDA_METADATA_FILE,
            stage1_top_k=settings.DEFAULT_STAGE1_TOP_K,
            device=settings.DEFAULT_DEVICE,
            hybrid_engine=hybrid_engine,
            use_lazy_loading=use_lazy_loading
        )
        logger.info("✅ Pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Pipeline initialization failed: {e}", exc_info=True)
        raise


@router.post("/complete", response_model=AnalysisResponse)
async def analyze_meal_from_image(
    image: UploadFile = File(..., description="食事画像ファイル"),
    user_context: Optional[str] = Form(None, description="ユーザーコンテキスト"),
    # Model config overrides
    model_id: Optional[str] = Form(None, description="VLMモデルID"),
    prompt_path: Optional[str] = Form(None, description="プロンプトファイルパス(prompts/以下)"),
    prompt_text: Optional[str] = Form(None, description="プロンプトテキスト全文(prompt_pathより優先)"),
    thinking_budget: Optional[int] = Form(None, description="思考トークン数(QVQモデル用)"),
    enable_thinking: Optional[bool] = Form(None, description="Thinking modeのon/off(Alibabaモデル用)"),
    temperature: Optional[float] = Form(None, description="生成温度"),
    max_tokens: Optional[int] = Form(None, description="最大トークン数"),
    # Search config overrides
    stage1_top_k: Optional[int] = Form(None, description="Stage1候補数"),
    bm25_weight: Optional[float] = Form(None, description="BM25検索の重み(0.0-1.0)"),
    vector_weight: Optional[float] = Form(None, description="Vector検索の重み(0.0-1.0)"),
    rrf_k: Optional[int] = Form(None, description="RRFのkパラメータ"),
    reranker_model: Optional[str] = Form(None, description="Rerankerモデル名"),
    reranker_instruction: Optional[str] = Form(None, description="Reranker instruction"),
    reranker_top_n: Optional[int] = Form(None, description="Reranker返却数"),
):
    """
    画像から食事を分析して栄養価を計算(Fullインデックスのみ使用)

    ## リクエストパラメータ
    - **image**: 食事画像ファイル(必須)
    - **user_context**: 食事の説明やコンテキスト(オプション)

    ## モデル設定(オプション、指定しない場合はデフォルト値を使用)
    - **model_id**: DeepInfra VLMモデルID
    - **prompt_path**: プロンプトファイル名(例: "freeform_prompt_usda_format_ver_v7_production_20251027.txt")
    - **thinking_budget**: 思考トークン数(QVQモデル使用時)
    - **temperature**: 生成温度(0.0-2.0)
    - **max_tokens**: 最大トークン数

    ## 検索設定(オプション)
    - **stage1_top_k**: Stage1で取得する候補数(デフォルト: 50)
    - **bm25_weight**: BM25検索の重み(デフォルト: 0.4)
    - **vector_weight**: Vector検索の重み(デフォルト: 0.6)
    - **rrf_k**: RRFのkパラメータ(デフォルト: 60)
    - **reranker_model**: Rerankerモデル名(デフォルト: Qwen/Qwen3-Reranker-8B)
    - **reranker_instruction**: Reranker用instruction
    - **reranker_top_n**: Rerankerで返す結果数

    ## レスポンス
    - 検出された料理と食材の詳細
    - 栄養価計算結果
    - 処理時間とメタデータ
    """
    analysis_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    try:
        # 画像データ読み込み
        image_bytes = await image.read()

        # パイプライン取得
        pipeline = get_pipeline()

        # モデル設定のオーバーライド処理
        model_config_override = None
        if any([model_id, prompt_path, prompt_text, thinking_budget, enable_thinking, temperature, max_tokens]):
            model_config_override = ModelConfig(
                model_id=model_id,
                prompt_path=prompt_path,
                prompt_text=prompt_text,
                thinking_budget=thinking_budget,
                enable_thinking=enable_thinking,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # 検索設定のオーバーライド処理
        search_config_override = None
        if any([stage1_top_k, bm25_weight, vector_weight, rrf_k, reranker_model, reranker_instruction, reranker_top_n]):
            search_config_override = SearchConfig(
                stage1_top_k=stage1_top_k,
                bm25_weight=bm25_weight,
                vector_weight=vector_weight,
                rrf_k=rrf_k,
                reranker_model=reranker_model,
                reranker_instruction=reranker_instruction,
                reranker_top_n=reranker_top_n,
            )

        # パイプライン実行
        result = await pipeline.analyze_meal_from_image(
            image_bytes=image_bytes,
            user_context=user_context,
            model_config_override=model_config_override,
            search_config_override=search_config_override,
        )

        # レスポンス作成
        processing_time = time.time() - start_time

        response = AnalysisResponse(
            analysis_id=analysis_id,
            input_type="image",
            total_dishes=len(result["dishes"]),
            total_ingredients=sum(len(d.ingredients) for d in result["dishes"]),
            processing_time_seconds=processing_time,
            dishes=result["dishes"],
            total_nutrition=result["total_nutrition"],
            ai_model_used=result["ai_model_used"],
            prompt_file_used=result["prompt_file_used"],
            match_rate_percent=result["match_rate_percent"],
            usage=result.get("usage"),  # ✅ Added: Usage情報を取得
            warnings=result.get("warnings", []),
        )

        return response

    except FileNotFoundError as e:
        logger.error(f"Prompt file not found: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # エラーメッセージを確実に取得
        error_message = str(e) if str(e) else f"An error occurred: {type(e).__name__}"
        logger.error(f"Analysis failed: {error_message}", exc_info=True)

        # エラーの詳細情報を取得（デバッグ用）
        import traceback
        error_detail = traceback.format_exc()

        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError",
                message=error_message,
                analysis_id=analysis_id,
            ).model_dump()
        )


@router.get("/", response_model=EndpointInfoResponse)
async def list_endpoint_info():
    """
    利用可能なエンドポイント情報取得

    ## 概要
    Meal Analysis APIで利用可能なエンドポイントの一覧を取得します。

    Returns:
        EndpointInfoResponse: エンドポイント情報
    """
    return {
        "endpoints": {
            "POST /api/v1/meal-analyses/complete": "画像から食事を分析",
            "GET /health": "ヘルスチェック",
        },
        "documentation": "/docs",
    }
