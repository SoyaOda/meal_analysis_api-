"""
Voice Analysis Router

音声入力による食事分析エンドポイント
Whisper STT → LLM → USDA検索 → 栄養価計算
"""

import logging
import time
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from ..models.response_models import AnalysisResponse, ErrorResponse
from ..models.request_models import ModelConfig, SearchConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/meal-analyses", tags=["Voice Analysis"])

# パイプラインインスタンス（main.pyから設定される）
_pipeline = None


def set_pipeline(pipeline):
    """パイプラインインスタンスを設定"""
    global _pipeline
    _pipeline = pipeline


@router.post(
    "/voice",
    response_model=AnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="音声から食事を分析",
    description="""
## 概要
音声ファイルから食事を分析し、栄養価を計算します。

## 処理フロー
1. **音声認識 (STT)**: Whisper APIで音声をテキストに変換
2. **テキスト分析 (LLM)**: LLMで食事情報を抽出（USDA形式JSON）
3. **USDA検索**: FAISSベクトル検索 + BM25 + Rerankerで食材をマッチング
4. **栄養価計算**: マッチした食材の栄養素を重量に基づいて計算

## 対応音声フォーマット
- WAV (audio/wav)
- MP3 (audio/mpeg)
- FLAC (audio/flac)
- OGG (audio/ogg)
- M4A (audio/m4a)
- WEBM (audio/webm)

## レスポンス
画像分析APIと同じフォーマットに加えて:
- `transcript`: 音声認識結果テキスト
- `voice_metadata`: 音声メタデータ（Whisperモデル、処理時間等）
"""
)
async def analyze_meal_from_voice(
    audio_file: UploadFile = File(..., description="音声ファイル（WAV, MP3, FLAC等）"),
    user_context: Optional[str] = Form(None, description="ユーザーコンテキスト（オプション）"),
    language: Optional[str] = Form("en", description="言語コード（en, ja等）"),
    # Voice model config
    voice_model_id: Optional[str] = Form(
        None,
        description="Voice解析用LLM/VLMモデルID（デフォルト: google/gemma-3-27b-it）"
    ),
    voice_prompt_file: Optional[str] = Form(
        None,
        description="Voice解析用プロンプトファイル（デフォルト: freeform_voice_prompt_usda.txt）"
    ),
    whisper_model: Optional[str] = Form(
        None,
        description="Whisperモデル（デフォルト: openai/whisper-large-v3-turbo）"
    ),
    # Model config overrides
    temperature: Optional[float] = Form(None, description="LLM生成温度（0.0-2.0）"),
    max_tokens: Optional[int] = Form(None, description="最大トークン数"),
    # Search config overrides
    stage1_top_k: Optional[int] = Form(None, description="Stage1検索候補数（デフォルト: 50）"),
    bm25_weight: Optional[float] = Form(None, description="BM25検索の重み（デフォルト: 0.4）"),
    vector_weight: Optional[float] = Form(None, description="Vector検索の重み（デフォルト: 0.6）"),
    rrf_k: Optional[int] = Form(None, description="RRFのkパラメータ（デフォルト: 60）"),
    reranker_model: Optional[str] = Form(None, description="Rerankerモデル名"),
    reranker_instruction: Optional[str] = Form(None, description="Reranker instruction"),
    reranker_top_n: Optional[int] = Form(None, description="Reranker結果数"),
    # Debug option
    debug: Optional[bool] = Form(False, description="デバッグ情報を含める"),
):
    """
    音声から食事を分析して栄養価を計算

    音声ファイルをアップロードすると、以下の処理が行われます:
    1. Whisper STTで音声をテキストに変換
    2. LLMでテキストから食事情報を抽出
    3. USDA DBから食材を検索してマッチング
    4. 栄養価を計算して返却
    """
    global _pipeline

    if _pipeline is None:
        raise HTTPException(
            status_code=500,
            detail="Pipeline not initialized. Please try again later."
        )

    start_time = time.time()
    analysis_id = str(uuid.uuid4())[:8]

    logger.info(f"[{analysis_id}] Voice analysis request received")
    logger.info(f"[{analysis_id}] File: {audio_file.filename}, Size: {audio_file.size}")

    try:
        # 音声データを読み込み
        audio_bytes = await audio_file.read()

        if len(audio_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Audio file is empty"
            )

        # ファイルサイズ制限 (50MB)
        if len(audio_bytes) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Audio file too large. Maximum size is 50MB."
            )

        logger.info(f"[{analysis_id}] Audio size: {len(audio_bytes)} bytes")

        # Model config override
        model_config = None
        if temperature is not None or max_tokens is not None:
            model_config = ModelConfig(
                temperature=temperature,
                max_tokens=max_tokens
            )

        # Search config override
        search_config = None
        if any([stage1_top_k, bm25_weight, vector_weight, rrf_k,
                reranker_model, reranker_instruction, reranker_top_n]):
            search_config = SearchConfig(
                stage1_top_k=stage1_top_k,
                bm25_weight=bm25_weight,
                vector_weight=vector_weight,
                rrf_k=rrf_k,
                reranker_model=reranker_model,
                reranker_instruction=reranker_instruction,
                reranker_top_n=reranker_top_n
            )

        # パイプライン実行
        result = await _pipeline.analyze_meal_from_voice(
            audio_bytes=audio_bytes,
            user_context=user_context,
            model_config_override=model_config,
            search_config_override=search_config,
            voice_model_id=voice_model_id,
            voice_prompt_file=voice_prompt_file,
            whisper_model=whisper_model,
            language=language or "en",
            include_debug_info=debug or False
        )

        # 処理時間
        processing_time = time.time() - start_time

        # レスポンス構築
        response = AnalysisResponse(
            analysis_id=analysis_id,
            input_type="voice",
            meal_title=result.get("meal_title"),
            total_dishes=len(result["dishes"]),
            total_ingredients=sum(len(d.ingredients) for d in result["dishes"]),
            processing_time_seconds=round(processing_time, 2),
            dishes=result["dishes"],
            total_nutrition=result["total_nutrition"],
            ai_model_used=result["ai_model_used"],
            prompt_file_used=result["prompt_file_used"],
            match_rate_percent=result["match_rate_percent"],
            usage=result.get("usage"),
            transcript=result.get("transcript"),
            voice_metadata=result.get("voice_metadata"),
            warnings=result.get("warnings", [])
        )

        logger.info(f"[{analysis_id}] Voice analysis completed in {processing_time:.2f}s")
        logger.info(f"[{analysis_id}] Dishes: {response.total_dishes}, Ingredients: {response.total_ingredients}")

        return response

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"[{analysis_id}] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"[{analysis_id}] Runtime error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"[{analysis_id}] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
