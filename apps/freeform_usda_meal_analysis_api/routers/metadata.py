#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
USDA Metadata API Router
フロントエンド向けメタデータ配信エンドポイント
"""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
import logging
import json
import gzip
from pathlib import Path

from ..config import get_settings
from ..models.response_models import (
    MetadataSearchResponse,
    MetadataInfoResponse,
    MetadataItem,
    NormalizedUnit,
)
from ..services.portions_normalizer import normalize_portions_for_food

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.get("/api/v1/metadata")
async def get_usda_metadata(
    compressed: bool = Query(True, description="gzip圧縮して返すか（推奨）")
) -> Response:
    """
    USDA食材メタデータ全件取得（13,564件）

    ## 概要
    フロントエンドでの食材選択、栄養情報表示、portions変換に必要な
    全てのメタデータを取得します。

    ## パラメータ
    - **compressed**: gzip圧縮して返すか（デフォルト: True）
      - True: 8.4MB → 約1.5MB（推奨）
      - False: 8.4MB（非推奨、開発時のみ使用）

    ## レスポンス
    - Content-Type: application/json
    - Content-Encoding: gzip（compressed=Trueの場合）
    - Cache-Control: public, max-age=86400（24時間キャッシュ）

    ## データ構造
    ```json
    [
      {
        "fdc_id": 123456,
        "description": "Chicken, breast, grilled",
        "main_name": "Chicken, breast",
        "descriptors": "grilled",
        "source": "survey",
        "nutrition": {
          "calories": 165,
          "protein_g": 31.0,
          "fat_g": 3.6,
          "carbs_g": 0.0
        },
        "portions": [
          {
            "description": "1 breast, bone and skin removed",
            "gram_weight": 86.0
          }
        ]
      }
    ]
    ```

    ## 使用例（JavaScript）
    ```javascript
    // gzip圧縮版を取得（推奨）
    const response = await fetch('http://localhost:8006/api/v1/metadata?compressed=true');
    const metadata = await response.json();

    // ローカルストレージにキャッシュ
    localStorage.setItem('usda_metadata', JSON.stringify({
      items: metadata,
      timestamp: Date.now()
    }));
    ```
    """
    metadata_path = Path(settings.USDA_METADATA_FILE)

    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        raise HTTPException(
            status_code=404,
            detail=f"Metadata file not found: {metadata_path}"
        )

    try:
        if compressed:
            # gzip圧縮して返す（8.4MB → 約1.5MB）
            logger.info(f"📦 Serving compressed metadata from: {metadata_path}")

            with open(metadata_path, 'rb') as f:
                data = f.read()

            compressed_data = gzip.compress(data, compresslevel=6)

            logger.info(f"✅ Compressed: {len(data):,} bytes → {len(compressed_data):,} bytes (ratio: {len(compressed_data)/len(data)*100:.1f}%)")

            return Response(
                content=compressed_data,
                media_type="application/json",
                headers={
                    "Content-Encoding": "gzip",
                    "Cache-Control": "public, max-age=86400",  # 24時間キャッシュ
                    "X-Original-Size": str(len(data)),
                    "X-Compressed-Size": str(len(compressed_data)),
                }
            )
        else:
            # 非圧縮版（開発時のみ使用）
            logger.info(f"📄 Serving uncompressed metadata from: {metadata_path}")

            return FileResponse(
                path=metadata_path,
                media_type="application/json",
                headers={
                    "Cache-Control": "public, max-age=86400",
                }
            )

    except Exception as e:
        logger.error(f"❌ Failed to serve metadata: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve metadata: {str(e)}"
        )


@router.get("/api/v1/metadata/info", response_model=MetadataInfoResponse)
async def get_metadata_info() -> MetadataInfoResponse:
    """
    メタデータ情報取得

    ## 概要
    メタデータファイルの統計情報を取得します。

    ## レスポンス
    ```json
    {
      "total_items": 13564,
      "file_size_mb": 8.4,
      "compressed_size_mb": 1.5,
      "compression_ratio": 0.18,
      "sources": {
        "survey": 5000,
        "foundation": 6000,
        "sr_legacy": 2564
      },
      "last_updated": "2025-10-28T19:00:00Z"
    }
    ```
    """
    metadata_path = Path(settings.USDA_METADATA_FILE)

    if not metadata_path.exists():
        raise HTTPException(404, "Metadata file not found")

    try:
        # ファイルサイズ取得
        file_size = metadata_path.stat().st_size

        # メタデータ読み込み
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # 圧縮サイズ推定
        with open(metadata_path, 'rb') as f:
            data = f.read()
        compressed_size = len(gzip.compress(data, compresslevel=6))

        # ソース別集計
        sources = {}
        for item in metadata:
            source = item.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

        # portions カバレッジ計算
        items_with_portions = sum(1 for item in metadata if item.get('portions'))
        portions_coverage = items_with_portions / len(metadata) * 100 if metadata else 0

        return {
            "total_items": len(metadata),
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "compressed_size_bytes": compressed_size,
            "compressed_size_mb": round(compressed_size / 1024 / 1024, 2),
            "compression_ratio": round(compressed_size / file_size, 2),
            "sources": sources,
            "portions_coverage_percent": round(portions_coverage, 1),
            "items_with_portions": items_with_portions,
            "last_modified": metadata_path.stat().st_mtime,
        }

    except Exception as e:
        logger.error(f"Failed to get metadata info: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get metadata info: {str(e)}")


@router.get("/api/v1/metadata/search", response_model=MetadataSearchResponse)
async def search_metadata(
    q: str = Query(..., min_length=1, description="検索クエリ"),
    limit: int = Query(20, ge=1, le=100, description="返却件数（1-100）"),
    offset: int = Query(0, ge=0, description="オフセット"),
    source: Optional[str] = Query(None, description="データソースフィルター（survey/foundation/sr_legacy）")
) -> MetadataSearchResponse:
    """
    メタデータ検索（軽量版）

    ## 概要
    メタデータをクエリ文字列で検索します。
    descriptionとmain_nameフィールドを対象に部分一致検索を行います。

    ## パラメータ
    - **q**: 検索クエリ（例: "chicken breast"）
    - **limit**: 返却件数（デフォルト: 20、最大: 100）
    - **offset**: オフセット（ページネーション用）
    - **source**: データソースフィルター（例: "survey"）

    ## レスポンス
    ```json
    {
      "query": "chicken breast",
      "results": [...],
      "total": 50,
      "limit": 20,
      "offset": 0
    }
    ```

    ## 注意
    - この検索はシンプルな部分一致検索です
    - 高度な検索（セマンティック検索）には `/api/v1/retrieve` を使用してください
    """
    metadata_path = Path(settings.USDA_METADATA_FILE)

    if not metadata_path.exists():
        raise HTTPException(404, "Metadata file not found")

    try:
        # メタデータ読み込み
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # 検索実行
        query_lower = q.lower()
        results = []

        for item in metadata:
            # ソースフィルター
            if source and item.get('source') != source:
                continue

            # 検索
            description = item.get('description', '').lower()
            main_name = item.get('main_name', '').lower()

            if query_lower in description or query_lower in main_name:
                results.append(item)

        # ページネーション
        total = len(results)
        paginated_results = results[offset:offset + limit]

        logger.info(f"🔍 Metadata search: query='{q}', source={source}, total={total}, returned={len(paginated_results)}")

        return MetadataSearchResponse(
            query=q,
            results=paginated_results,
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + limit < total
        )

    except Exception as e:
        logger.error(f"Metadata search failed: {e}", exc_info=True)
        raise HTTPException(500, f"Metadata search failed: {str(e)}")


@router.get("/api/v1/metadata/{fdc_id}", response_model=MetadataItem)
async def get_metadata_by_fdc_id(
    fdc_id: int,
    include_normalized_units: bool = Query(
        True,
        description="正規化された単位リストを含めるか"
    )
) -> MetadataItem:
    """
    FDC ID指定でメタデータ取得

    ## 概要
    FDC IDを指定して単一の食材メタデータを取得します。
    `include_normalized_units=true`（デフォルト）の場合、アプリUI用に
    正規化された単位リスト（`normalized_units`）も含まれます。

    ## パラメータ
    - **fdc_id**: FDC ID（例: 746774）
    - **include_normalized_units**: 正規化された単位リストを含めるか（デフォルト: true）

    ## レスポンス
    ```json
    {
      "fdc_id": 746774,
      "description": "Chicken, breast, grilled",
      "main_name": "Chicken, breast",
      "descriptors": "grilled",
      "source": "survey",
      "nutrition": {...},
      "portions": [...],
      "normalized_units": [
        {"name": "g", "abbreviation": "g", "grams_per_unit": 1.0, ...},
        {"name": "cup", "abbreviation": "cup", "grams_per_unit": 135.0, ...}
      ]
    }
    ```

    ## normalized_unitsについて
    - `g`は常に先頭に含まれる（基準単位）
    - DBのportionsから正規化された単位のみ含まれる
    - 数量が1以外の場合は1単位あたりに換算済み
    - "Quantity not specified", "yields"等は除外済み
    """
    metadata_path = Path(settings.USDA_METADATA_FILE)

    if not metadata_path.exists():
        raise HTTPException(404, "Metadata file not found")

    try:
        # メタデータ読み込み
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # FDC ID検索
        for item in metadata:
            if item.get('fdc_id') == fdc_id:
                logger.info(f"✅ Found metadata for FDC ID: {fdc_id}")

                # normalized_unitsを追加
                if include_normalized_units:
                    portions = item.get('portions', [])
                    normalized = normalize_portions_for_food(portions)
                    item['normalized_units'] = [
                        {
                            'name': u.name,
                            'abbreviation': u.abbreviation,
                            'grams_per_unit': u.grams_per_unit,
                            'original_description': u.original_description,
                            'is_base_unit': u.is_base_unit,
                        }
                        for u in normalized
                    ]

                return item

        # 見つからない場合
        logger.warning(f"⚠️ FDC ID not found: {fdc_id}")
        raise HTTPException(404, f"FDC ID not found: {fdc_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metadata by FDC ID: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get metadata: {str(e)}")
