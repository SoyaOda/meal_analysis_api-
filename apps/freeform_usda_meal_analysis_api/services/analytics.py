#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Search Analytics Service

検索クエリのログ記録とBigQueryへの非同期書き込みを管理するサービス。
検索精度向上のためのデータ収集を目的とする。
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import json
import os

logger = logging.getLogger(__name__)

# BigQuery設定
BIGQUERY_DATASET = "search_analytics"
BIGQUERY_TABLE = "search_logs"


@dataclass
class SearchLogEntry:
    """検索ログエントリ"""
    timestamp: str  # ISO 8601 format
    query: str
    query_length: int
    results_count: int
    mode: str  # fast, accurate, hybrid, hybrid_reranker
    latency_ms: int
    offset: int
    top_k: int
    cache_hit: bool
    selected_fdc_id: Optional[str] = None
    selected_food_name: Optional[str] = None
    result_position: Optional[int] = None  # 選択された結果の位置（0-indexed）
    user_id: Optional[str] = None  # 将来的にユーザー識別用
    session_id: Optional[str] = None  # セッション識別用


class SearchAnalytics:
    """
    検索分析サービス

    検索クエリをBigQueryに非同期でログ記録する。
    バッチ処理でパフォーマンスを最適化。
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        dataset_id: str = BIGQUERY_DATASET,
        table_id: str = BIGQUERY_TABLE,
        batch_size: int = 100,
        flush_interval_seconds: int = 60,
        enabled: bool = True
    ):
        """
        Args:
            project_id: GCP Project ID（Noneの場合は環境変数から取得）
            dataset_id: BigQuery Dataset ID
            table_id: BigQuery Table ID
            batch_size: バッチ書き込みサイズ
            flush_interval_seconds: フラッシュ間隔（秒）
            enabled: ログ記録を有効にするか
        """
        self._project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._dataset_id = dataset_id
        self._table_id = table_id
        self._batch_size = batch_size
        self._flush_interval = flush_interval_seconds
        self._enabled = enabled

        self._queue: asyncio.Queue[SearchLogEntry] = asyncio.Queue()
        self._buffer: List[SearchLogEntry] = []
        self._client = None
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

        # 統計情報
        self._logs_received = 0
        self._logs_written = 0
        self._write_errors = 0

    async def start(self):
        """バックグラウンドフラッシュタスクを開始"""
        if not self._enabled:
            logger.info("SearchAnalytics is disabled")
            return

        if self._running:
            return

        self._running = True

        # BigQueryクライアント初期化（遅延ロード）
        try:
            from google.cloud import bigquery
            self._client = bigquery.Client(project=self._project_id)
            logger.info(f"SearchAnalytics initialized with BigQuery project: {self._project_id}")

            # テーブル存在確認（なければ作成）
            await self._ensure_table_exists()
        except ImportError:
            logger.warning("google-cloud-bigquery not installed. Analytics will use local logging only.")
            self._client = None
        except Exception as e:
            logger.warning(f"Failed to initialize BigQuery client: {e}. Analytics will use local logging only.")
            self._client = None

        # バックグラウンドフラッシュタスク開始
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("SearchAnalytics background flush task started")

    async def stop(self):
        """バックグラウンドタスクを停止し、残りのログをフラッシュ"""
        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # 残りのログをフラッシュ
        await self._flush_buffer()
        logger.info("SearchAnalytics stopped")

    async def log_search(
        self,
        query: str,
        results_count: int,
        mode: str,
        latency_ms: int,
        offset: int = 0,
        top_k: int = 10,
        cache_hit: bool = False,
        selected_fdc_id: Optional[str] = None,
        selected_food_name: Optional[str] = None,
        result_position: Optional[int] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        検索クエリをログに記録（非同期）

        Args:
            query: 検索クエリ
            results_count: 結果数
            mode: 検索モード
            latency_ms: 処理時間（ミリ秒）
            offset: オフセット
            top_k: 要求された結果数
            cache_hit: キャッシュヒットしたか
            selected_fdc_id: 選択された食品のFDC ID
            selected_food_name: 選択された食品名
            result_position: 選択された結果の位置
            user_id: ユーザーID
            session_id: セッションID
        """
        if not self._enabled:
            return

        entry = SearchLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            query=query,
            query_length=len(query),
            results_count=results_count,
            mode=mode,
            latency_ms=latency_ms,
            offset=offset,
            top_k=top_k,
            cache_hit=cache_hit,
            selected_fdc_id=selected_fdc_id,
            selected_food_name=selected_food_name,
            result_position=result_position,
            user_id=user_id,
            session_id=session_id
        )

        self._logs_received += 1
        await self._queue.put(entry)

    async def log_selection(
        self,
        query: str,
        selected_fdc_id: str,
        selected_food_name: str,
        result_position: int,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        食品選択をログに記録（検索後の選択イベント用）

        Args:
            query: 元の検索クエリ
            selected_fdc_id: 選択された食品のFDC ID
            selected_food_name: 選択された食品名
            result_position: 選択された結果の位置（0-indexed）
            user_id: ユーザーID
            session_id: セッションID
        """
        if not self._enabled:
            return

        entry = SearchLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            query=query,
            query_length=len(query),
            results_count=0,  # 選択イベントでは不明
            mode="selection",  # 選択イベントを識別
            latency_ms=0,
            offset=0,
            top_k=0,
            cache_hit=False,
            selected_fdc_id=selected_fdc_id,
            selected_food_name=selected_food_name,
            result_position=result_position,
            user_id=user_id,
            session_id=session_id
        )

        self._logs_received += 1
        await self._queue.put(entry)

    async def _periodic_flush(self):
        """定期的にバッファをフラッシュするバックグラウンドタスク"""
        while self._running:
            try:
                await asyncio.sleep(self._flush_interval)

                # キューからバッファに移動
                while not self._queue.empty():
                    try:
                        entry = self._queue.get_nowait()
                        self._buffer.append(entry)
                    except asyncio.QueueEmpty:
                        break

                # バッファをフラッシュ
                if self._buffer:
                    await self._flush_buffer()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")

    async def _flush_buffer(self):
        """バッファの内容をBigQueryに書き込む"""
        if not self._buffer:
            return

        entries_to_write = self._buffer[:self._batch_size]
        self._buffer = self._buffer[self._batch_size:]

        # BigQueryクライアントがない場合はローカルログのみ
        if not self._client:
            for entry in entries_to_write:
                logger.info(f"[SEARCH_LOG] {json.dumps(asdict(entry))}")
            self._logs_written += len(entries_to_write)
            return

        try:
            # BigQueryに書き込み
            table_ref = f"{self._project_id}.{self._dataset_id}.{self._table_id}"
            rows = [asdict(entry) for entry in entries_to_write]

            errors = self._client.insert_rows_json(table_ref, rows)

            if errors:
                logger.error(f"BigQuery insert errors: {errors}")
                self._write_errors += len(errors)
            else:
                self._logs_written += len(entries_to_write)
                logger.debug(f"Wrote {len(entries_to_write)} search logs to BigQuery")

        except Exception as e:
            logger.error(f"Failed to write to BigQuery: {e}")
            self._write_errors += len(entries_to_write)
            # フォールバック: ローカルログに出力
            for entry in entries_to_write:
                logger.info(f"[SEARCH_LOG] {json.dumps(asdict(entry))}")

    async def _ensure_table_exists(self):
        """BigQueryテーブルが存在することを確認（なければ作成）"""
        if not self._client:
            return

        from google.cloud import bigquery

        dataset_ref = f"{self._project_id}.{self._dataset_id}"
        table_ref = f"{dataset_ref}.{self._table_id}"

        # Dataset確認・作成
        try:
            self._client.get_dataset(dataset_ref)
        except Exception:
            logger.info(f"Creating BigQuery dataset: {dataset_ref}")
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            self._client.create_dataset(dataset, exists_ok=True)

        # Table確認・作成
        try:
            self._client.get_table(table_ref)
            logger.info(f"BigQuery table exists: {table_ref}")
        except Exception:
            logger.info(f"Creating BigQuery table: {table_ref}")
            schema = [
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("query", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("query_length", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("results_count", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("mode", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("latency_ms", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("offset", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("top_k", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("cache_hit", "BOOLEAN", mode="REQUIRED"),
                bigquery.SchemaField("selected_fdc_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("selected_food_name", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("result_position", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("session_id", "STRING", mode="NULLABLE"),
            ]
            table = bigquery.Table(table_ref, schema=schema)
            # パーティショニング設定（timestampでパーティション）
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp"
            )
            self._client.create_table(table, exists_ok=True)
            logger.info(f"Created BigQuery table: {table_ref}")

    def stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            "enabled": self._enabled,
            "running": self._running,
            "logs_received": self._logs_received,
            "logs_written": self._logs_written,
            "write_errors": self._write_errors,
            "buffer_size": len(self._buffer),
            "queue_size": self._queue.qsize(),
            "bigquery_connected": self._client is not None
        }


# グローバルインスタンス（シングルトン）
_analytics_instance: Optional[SearchAnalytics] = None


def get_analytics() -> Optional[SearchAnalytics]:
    """SearchAnalyticsのグローバルインスタンスを取得"""
    return _analytics_instance


def set_analytics(analytics: SearchAnalytics):
    """SearchAnalyticsのグローバルインスタンスを設定"""
    global _analytics_instance
    _analytics_instance = analytics


async def init_analytics(
    project_id: Optional[str] = None,
    enabled: bool = True
) -> SearchAnalytics:
    """
    SearchAnalyticsを初期化して開始

    Args:
        project_id: GCP Project ID
        enabled: ログ記録を有効にするか

    Returns:
        SearchAnalyticsインスタンス
    """
    analytics = SearchAnalytics(
        project_id=project_id,
        enabled=enabled
    )
    await analytics.start()
    set_analytics(analytics)
    return analytics
