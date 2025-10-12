"""
Elasticsearch食材リストプロバイダー（DB確定的取得・フォールバックなし）

将来的なDB変更・アップデートに対応するため、original_nameフィールドのみに依存した設計。
"""
import logging
import requests
import json
from typing import List, Optional
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


class ElasticsearchIngredientProvider:
    """
    Elasticsearchから食材リストを確定的に取得するプロバイダー

    設計原則:
    - フォールバック実装なし（DB取得失敗時は例外を投げる）
    - original_nameフィールドのみに依存（DB変更に対応）
    - メモリキャッシュでパフォーマンス最適化
    - 設定ファイルでElasticsearch情報を管理
    """

    # クラスレベルのキャッシュ
    _cached_list: Optional[str] = None
    _cached_list_no_uncooked: Optional[str] = None
    _cache_timestamp: Optional[datetime] = None
    _cache_lock = Lock()
    _cache_ttl_hours: int = 24  # 24時間キャッシュ

    def __init__(
        self,
        elasticsearch_url: str,
        index_name: str,
        timeout: int = 10
    ):
        """
        Args:
            elasticsearch_url: Elasticsearch URL（例: http://35.193.16.212:9200）
            index_name: インデックス名（例: mynetdiary_converted_tool_calls_list_stemmed）
            timeout: リクエストタイムアウト（秒）
        """
        self.elasticsearch_url = elasticsearch_url
        self.index_name = index_name
        self.timeout = timeout

    def get_ingredient_list_for_prompt(self, exclude_uncooked: bool = True) -> str:
        """
        プロンプト用にフォーマットされた食材リストを取得

        Args:
            exclude_uncooked: uncooked食材を除外するか

        Returns:
            str: 番号付きフォーマットされた食材リスト

        Raises:
            RuntimeError: Elasticsearch取得失敗時
        """
        # キャッシュチェック
        if self._is_cache_valid():
            cached_result = self._get_from_cache(exclude_uncooked)
            if cached_result is not None:
                logger.info(
                    f"Using cached ingredient list (exclude_uncooked={exclude_uncooked}, "
                    f"cache_age={(datetime.now() - self._cache_timestamp).total_seconds():.1f}s)"
                )
                return cached_result

        # Elasticsearchから取得
        logger.info(
            f"Fetching ingredient list from Elasticsearch "
            f"(url={self.elasticsearch_url}, index={self.index_name}, exclude_uncooked={exclude_uncooked})"
        )

        with self._cache_lock:
            # ダブルチェック（他のスレッドが既に取得した可能性）
            if self._is_cache_valid():
                cached_result = self._get_from_cache(exclude_uncooked)
                if cached_result is not None:
                    return cached_result

            try:
                # 両方のバージョンを取得してキャッシュ
                names_all = self._fetch_ingredient_names(exclude_uncooked=False)
                names_no_uncooked = self._fetch_ingredient_names(exclude_uncooked=True)

                # フォーマット
                formatted_all = self._format_for_prompt(names_all)
                formatted_no_uncooked = self._format_for_prompt(names_no_uncooked)

                # キャッシュ更新
                self._cached_list = formatted_all
                self._cached_list_no_uncooked = formatted_no_uncooked
                self._cache_timestamp = datetime.now()

                logger.info(
                    f"Successfully fetched and cached ingredient lists "
                    f"(all={len(names_all)}, no_uncooked={len(names_no_uncooked)})"
                )

                return formatted_no_uncooked if exclude_uncooked else formatted_all

            except Exception as e:
                error_msg = (
                    f"Failed to fetch ingredient list from Elasticsearch "
                    f"(url={self.elasticsearch_url}, index={self.index_name}): {e}"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e

    def _fetch_ingredient_names(self, exclude_uncooked: bool = True) -> List[str]:
        """
        Elasticsearchからoriginal_name一覧を取得

        Args:
            exclude_uncooked: uncooked食材を除外するか

        Returns:
            List[str]: ソート済みのoriginal_name一覧

        Raises:
            requests.RequestException: リクエスト失敗時
            ValueError: レスポンス解析失敗時
        """
        # Elasticsearchクエリ構築
        query_body = {
            "size": 10000,  # 十分な数を取得（現在は1142件）
            "_source": ["original_name"],
            "query": {
                "bool": {
                    "must": [{"match_all": {}}]
                }
            }
        }

        # uncooked除外フィルタ
        if exclude_uncooked:
            query_body["query"]["bool"]["must_not"] = [{
                "wildcard": {
                    "original_name": "*uncooked*"
                }
            }]

        # Elasticsearchへリクエスト
        search_url = f"{self.elasticsearch_url}/{self.index_name}/_search"

        response = requests.post(
            search_url,
            headers={"Content-Type": "application/json"},
            json=query_body,
            timeout=self.timeout
        )
        response.raise_for_status()

        # レスポンス解析
        result = response.json()

        if "error" in result:
            raise ValueError(f"Elasticsearch error: {result['error']}")

        hits = result.get("hits", {}).get("hits", [])

        if not hits:
            raise ValueError("No documents found in Elasticsearch index")

        # original_nameを抽出してソート
        names = []
        for hit in hits:
            source = hit.get("_source", {})
            original_name = source.get("original_name")

            if not original_name:
                logger.warning(f"Document missing original_name: {hit.get('_id')}")
                continue

            names.append(original_name)

        # アルファベット順にソート
        names.sort()

        logger.info(f"Fetched {len(names)} ingredient names from Elasticsearch")

        return names

    def _format_for_prompt(self, names: List[str]) -> str:
        """
        食材名リストをプロンプト用にフォーマット

        Args:
            names: 食材名リスト

        Returns:
            str: 番号付きフォーマット済み文字列
        """
        formatted_lines = [f"{i+1}. {name}" for i, name in enumerate(names)]
        return "\n".join(formatted_lines)

    def _is_cache_valid(self) -> bool:
        """キャッシュが有効かチェック"""
        if self._cache_timestamp is None:
            return False

        cache_age = datetime.now() - self._cache_timestamp
        return cache_age < timedelta(hours=self._cache_ttl_hours)

    def _get_from_cache(self, exclude_uncooked: bool) -> Optional[str]:
        """キャッシュから取得"""
        if exclude_uncooked:
            return self._cached_list_no_uncooked
        else:
            return self._cached_list

    @classmethod
    def clear_cache(cls):
        """キャッシュをクリア（テスト用）"""
        with cls._cache_lock:
            cls._cached_list = None
            cls._cached_list_no_uncooked = None
            cls._cache_timestamp = None
            logger.info("Ingredient list cache cleared")

    @classmethod
    def get_cache_info(cls) -> dict:
        """キャッシュ情報を取得（デバッグ用）"""
        if cls._cache_timestamp is None:
            return {
                "cached": False,
                "cache_age_seconds": None,
                "ttl_hours": cls._cache_ttl_hours
            }

        cache_age = (datetime.now() - cls._cache_timestamp).total_seconds()

        return {
            "cached": True,
            "cache_age_seconds": cache_age,
            "cache_valid": cache_age < (cls._cache_ttl_hours * 3600),
            "ttl_hours": cls._cache_ttl_hours,
            "cached_list_length": len(cls._cached_list) if cls._cached_list else 0,
            "cached_list_no_uncooked_length": len(cls._cached_list_no_uncooked) if cls._cached_list_no_uncooked else 0
        }
