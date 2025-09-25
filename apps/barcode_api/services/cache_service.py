#!/usr/bin/env python3
"""
バーコードAPIキャッシュサービス

TTLCache（Time To Live Cache）を使用したメモリベースキャッシュシステム
"""

import json
import logging
import hashlib
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
from cachetools import TTLCache
import threading


logger = logging.getLogger(__name__)


class CacheService:
    """バーコード検索結果キャッシュサービス"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        キャッシュサービスの初期化

        Args:
            max_size: キャッシュの最大エントリ数
            ttl_seconds: キャッシュの生存時間（秒）
        """
        self.cache = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
        self.ttl_seconds = ttl_seconds

        logger.info(f"キャッシュサービス初期化完了: max_size={max_size}, ttl={ttl_seconds}秒")

    def _generate_cache_key(self, gtin: str, include_all_nutrients: bool = False) -> str:
        """
        キャッシュキーを生成

        Args:
            gtin: GTIN文字列
            include_all_nutrients: 全栄養素を含むかどうか

        Returns:
            ハッシュ化されたキャッシュキー
        """
        # 正規化されたキー文字列を作成
        key_data = {
            'gtin': gtin.strip(),
            'include_all_nutrients': include_all_nutrients
        }
        key_string = json.dumps(key_data, sort_keys=True)

        # SHA256でハッシュ化（短縮版）
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    def get(self, gtin: str, include_all_nutrients: bool = False) -> Optional[Dict[str, Any]]:
        """
        キャッシュから栄養情報を取得

        Args:
            gtin: GTIN文字列
            include_all_nutrients: 全栄養素を含むかどうか

        Returns:
            キャッシュされた栄養情報、存在しない場合はNone
        """
        cache_key = self._generate_cache_key(gtin, include_all_nutrients)

        with self.lock:
            try:
                cached_data = self.cache.get(cache_key)
                if cached_data:
                    self.stats['hits'] += 1
                    # cached=Trueフラグを設定
                    cached_data['cached'] = True
                    cached_data['cache_hit_time'] = datetime.now().isoformat()

                    logger.debug(f"キャッシュヒット: {gtin} -> {cache_key}")
                    return cached_data
                else:
                    self.stats['misses'] += 1
                    logger.debug(f"キャッシュミス: {gtin} -> {cache_key}")
                    return None

            except Exception as e:
                logger.error(f"キャッシュ取得エラー ({gtin}): {e}")
                self.stats['misses'] += 1
                return None

    def set(self, gtin: str, nutrition_data: Dict[str, Any], include_all_nutrients: bool = False) -> bool:
        """
        栄養情報をキャッシュに保存

        Args:
            gtin: GTIN文字列
            nutrition_data: 栄養情報データ
            include_all_nutrients: 全栄養素を含むかどうか

        Returns:
            保存成功時True
        """
        cache_key = self._generate_cache_key(gtin, include_all_nutrients)

        with self.lock:
            try:
                # キャッシュメタデータを追加
                cached_data = nutrition_data.copy()
                cached_data['cached'] = False  # 初期保存時はFalse
                cached_data['cache_stored_time'] = datetime.now().isoformat()
                cached_data['cache_ttl_seconds'] = self.ttl_seconds

                self.cache[cache_key] = cached_data
                self.stats['sets'] += 1

                logger.debug(f"キャッシュ保存: {gtin} -> {cache_key}")
                return True

            except Exception as e:
                logger.error(f"キャッシュ保存エラー ({gtin}): {e}")
                return False

    def delete(self, gtin: str, include_all_nutrients: bool = False) -> bool:
        """
        特定のキャッシュエントリを削除

        Args:
            gtin: GTIN文字列
            include_all_nutrients: 全栄養素を含むかどうか

        Returns:
            削除成功時True
        """
        cache_key = self._generate_cache_key(gtin, include_all_nutrients)

        with self.lock:
            try:
                if cache_key in self.cache:
                    del self.cache[cache_key]
                    logger.debug(f"キャッシュ削除: {gtin} -> {cache_key}")
                    return True
                return False

            except Exception as e:
                logger.error(f"キャッシュ削除エラー ({gtin}): {e}")
                return False

    def clear(self) -> bool:
        """
        全キャッシュエントリをクリア

        Returns:
            クリア成功時True
        """
        with self.lock:
            try:
                self.cache.clear()
                logger.info("キャッシュ全削除完了")
                return True

            except Exception as e:
                logger.error(f"キャッシュクリアエラー: {e}")
                return False

    def get_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計情報を取得

        Returns:
            統計情報辞書
        """
        with self.lock:
            current_size = len(self.cache)
            max_size = self.cache.maxsize

            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

            return {
                'current_size': current_size,
                'max_size': max_size,
                'utilization_percent': (current_size / max_size * 100) if max_size > 0 else 0,
                'ttl_seconds': self.ttl_seconds,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'sets': self.stats['sets'],
                'hit_rate_percent': round(hit_rate, 2),
                'total_requests': total_requests
            }

    def health_check(self) -> Dict[str, Any]:
        """
        キャッシュサービスのヘルスチェック

        Returns:
            ヘルスチェック結果
        """
        try:
            with self.lock:
                # テスト用データでキャッシュ機能確認
                test_key = "health_check_test"
                test_data = {"test": True, "timestamp": datetime.now().isoformat()}

                # 書き込みテスト
                self.cache[test_key] = test_data

                # 読み込みテスト
                retrieved = self.cache.get(test_key)

                # テストデータ削除
                if test_key in self.cache:
                    del self.cache[test_key]

                # 結果判定
                is_healthy = retrieved is not None and retrieved.get("test") is True

                return {
                    "healthy": is_healthy,
                    "message": "キャッシュサービス正常" if is_healthy else "キャッシュサービス異常",
                    "stats": self.get_stats()
                }

        except Exception as e:
            logger.error(f"キャッシュヘルスチェックエラー: {e}")
            return {
                "healthy": False,
                "message": f"キャッシュサービスエラー: {str(e)}",
                "stats": {}
            }


# グローバルキャッシュインスタンス（シングルトン）
_cache_instance: Optional[CacheService] = None
_cache_lock = threading.Lock()


def get_cache_service(max_size: int = 1000, ttl_seconds: int = 3600) -> CacheService:
    """
    キャッシュサービスのシングルトンインスタンスを取得

    Args:
        max_size: キャッシュの最大エントリ数
        ttl_seconds: キャッシュの生存時間（秒）

    Returns:
        CacheServiceインスタンス
    """
    global _cache_instance

    with _cache_lock:
        if _cache_instance is None:
            _cache_instance = CacheService(max_size=max_size, ttl_seconds=ttl_seconds)
            logger.info("グローバルキャッシュサービスインスタンス作成")

        return _cache_instance


def reset_cache_service() -> None:
    """
    キャッシュサービスインスタンスをリセット（テスト用）
    """
    global _cache_instance

    with _cache_lock:
        if _cache_instance:
            _cache_instance.clear()

        _cache_instance = None
        logger.info("グローバルキャッシュサービスインスタンスリセット")