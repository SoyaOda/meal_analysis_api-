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
from ..models.response_models import AnalysisResponse, ErrorResponse
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


def initialize_pipeline(hybrid_engine=None):
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
            hybrid_engine=hybrid_engine
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
    thinking_budget: Optional[int] = Form(None, description="思考トークン数(QVQモデル用)"),
    temperature: Optional[float] = Form(None, description="生成温度"),
    max_tokens: Optional[int] = Form(None, description="最大トークン数"),
    # Search config overrides
    stage1_top_k: Optional[int] = Form(None, description="Stage1候補数"),
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
    - **stage1_top_k**: Stage1で取得する候補数(デフォルト: 40)

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
        if any([model_id, prompt_path, thinking_budget, temperature, max_tokens]):
            model_config_override = ModelConfig(
                model_id=model_id,
                prompt_path=prompt_path,
                thinking_budget=thinking_budget,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # 検索設定のオーバーライド処理
        search_config_override = None
        if stage1_top_k is not None:
            search_config_override = SearchConfig(
                stage1_top_k=stage1_top_k,
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
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError",
                message=str(e),
                analysis_id=analysis_id,
            ).model_dump()
        )


@router.get("/")
async def list_endpoint_info():
    """
    利用可能なエンドポイント情報

    Returns:
        dict: エンドポイント情報
    """
    return {
        "endpoints": {
            "POST /api/v1/meal-analyses/complete": "画像から食事を分析",
            "GET /health": "ヘルスチェック",
        },
        "documentation": "/docs",
    }
