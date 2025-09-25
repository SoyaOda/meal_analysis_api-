#!/usr/bin/env python3
"""
バーコード検索API

バーコード（GTIN/UPC）から栄養情報を検索するAPIエンドポイント
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from ..models.nutrition import BarcodeRequest, NutritionResponse, ErrorResponse
from ..services.fdc_service import FDCDatabaseService

logger = logging.getLogger(__name__)

# APIルーター作成
router = APIRouter(
    prefix="/api/v1/barcode",
    tags=["barcode"],
    responses={404: {"model": ErrorResponse}}
)

# FDCサービスの依存性注入
def get_fdc_service() -> FDCDatabaseService:
    """FDCデータベースサービスを取得"""
    try:
        return FDCDatabaseService()
    except Exception as e:
        logger.error(f"FDCサービス初期化エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail="データベースサービスの初期化に失敗しました"
        )


@router.post("/lookup", response_model=NutritionResponse)
async def lookup_barcode(
    request: BarcodeRequest,
    fdc_service: FDCDatabaseService = Depends(get_fdc_service)
) -> NutritionResponse:
    """
    バーコードから栄養情報を検索

    Args:
        request: バーコード検索リクエスト
        fdc_service: FDCデータベースサービス

    Returns:
        栄養情報レスポンス

    Raises:
        HTTPException: 製品が見つからない場合やエラーが発生した場合
    """
    try:
        logger.info(f"バーコード検索開始: {request.gtin}")

        # GTINの基本的な形式チェック
        gtin = request.gtin.strip()
        if not gtin.isdigit():
            raise HTTPException(
                status_code=400,
                detail="GTINコードは数字のみである必要があります"
            )

        # FDCデータベースで検索
        result = fdc_service.search_by_gtin(
            gtin=gtin,
            include_all_nutrients=request.include_all_nutrients
        )

        if not result:
            logger.warning(f"製品が見つかりません: {gtin}")
            raise HTTPException(
                status_code=404,
                detail=f"バーコード '{gtin}' の製品が見つかりません"
            )

        logger.info(f"バーコード検索成功: {gtin} -> FDC ID: {result.product.fdc_id if result.product else 'None'}")
        return result

    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        logger.error(f"バーコード検索エラー ({request.gtin}): {e}")
        raise HTTPException(
            status_code=500,
            detail="内部サーバーエラーが発生しました"
        )


@router.get("/health")
async def health_check(
    fdc_service: FDCDatabaseService = Depends(get_fdc_service)
) -> dict:
    """
    バーコードAPIのヘルスチェック

    Returns:
        ヘルスチェック結果
    """
    try:
        # データベース接続確認
        db_healthy = fdc_service.health_check()

        # データベース統計取得
        stats = fdc_service.get_database_stats()

        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database_connected": db_healthy,
            "database_stats": stats,
            "service": "barcode_api",
            "version": "1.0.0"
        }

    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        return {
            "status": "unhealthy",
            "database_connected": False,
            "error": str(e),
            "service": "barcode_api",
            "version": "1.0.0"
        }


@router.get("/stats")
async def get_database_statistics(
    fdc_service: FDCDatabaseService = Depends(get_fdc_service)
) -> dict:
    """
    データベース統計情報を取得

    Returns:
        データベース統計
    """
    try:
        stats = fdc_service.get_database_stats()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"統計情報取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail="統計情報の取得に失敗しました"
        )

@router.get("/cache-stats")
async def get_cache_statistics():
    """
    キャッシュ統計情報を取得
    """
    try:
        fdc_service = get_fdc_service()
        
        if not fdc_service.use_cache or not fdc_service.cache_service:
            return {
                "cache_enabled": False,
                "message": "キャッシュが無効化されています"
            }
            
        cache_stats = fdc_service.cache_service.get_stats()
        cache_health = fdc_service.cache_service.health_check()
        
        return {
            "cache_enabled": True,
            "statistics": cache_stats,
            "health": cache_health,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"キャッシュ統計取得エラー: {e}")
        raise HTTPException(status_code=500, detail="キャッシュ統計情報の取得に失敗しました")


@router.delete("/cache")
async def clear_cache():
    """
    キャッシュをクリア
    """
    try:
        fdc_service = get_fdc_service()
        
        if not fdc_service.use_cache or not fdc_service.cache_service:
            return {
                "cache_enabled": False,
                "message": "キャッシュが無効化されています"
            }
            
        success = fdc_service.cache_service.clear()
        
        if success:
            return {
                "success": True,
                "message": "キャッシュをクリアしました",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="キャッシュクリアに失敗しました")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"キャッシュクリアエラー: {e}")
        raise HTTPException(status_code=500, detail="キャッシュクリアに失敗しました")


# エラーハンドラー（将来の拡張用）
def create_error_response(error_code: str, message: str, gtin: Optional[str] = None) -> ErrorResponse:
    """
    エラーレスポンス作成ヘルパー

    Args:
        error_code: エラーコード
        message: エラーメッセージ
        gtin: GTINコード（オプション）

    Returns:
        エラーレスポンス
    """
    return ErrorResponse(
        success=False,
        error_code=error_code,
        error_message=message,
        gtin=gtin
    )