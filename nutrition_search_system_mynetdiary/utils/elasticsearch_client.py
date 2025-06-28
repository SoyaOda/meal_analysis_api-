"""
Elasticsearch接続管理ユーティリティ
"""

import logging
from typing import Optional, Dict, Any
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Elasticsearch接続管理クラス"""
    
    def __init__(self, url: str = "http://localhost:9200", index_name: str = "mynetdiary_list_support_db"):
        self.url = url
        self.index_name = index_name
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Elasticsearchクライアント初期化"""
        try:
            self.client = Elasticsearch([self.url])
            
            if self.client.ping():
                logger.info(f"✅ Elasticsearch connected: {self.url}")
                
                if self.client.indices.exists(index=self.index_name):
                    logger.info(f"✅ Index '{self.index_name}' found")
                else:
                    logger.error(f"❌ Index '{self.index_name}' not found")
                    self.client = None
            else:
                logger.error(f"❌ Elasticsearch ping failed: {self.url}")
                self.client = None
                
        except Exception as e:
            logger.error(f"❌ Elasticsearch connection failed: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """接続状態確認"""
        return self.client is not None
    
    async def search(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """検索実行"""
        if not self.is_connected():
            return None
        
        try:
            response = self.client.search(index=self.index_name, body=query)
            return response
        except Exception as e:
            logger.error(f"Search error: {e}")
            return None
    
    def get_total_documents(self) -> int:
        """総ドキュメント数取得"""
        if not self.is_connected():
            return 0
        
        try:
            result = self.client.count(index=self.index_name)
            return result.get('count', 0)
        except Exception as e:
            logger.error(f"Count error: {e}")
            return 0
    
    def get_index_stats(self) -> Dict[str, Any]:
        """インデックス統計取得"""
        if not self.is_connected():
            return {}
        
        try:
            stats = self.client.indices.stats(index=self.index_name)
            return {
                "total_docs": stats['_all']['total']['docs']['count'],
                "index_size": stats['_all']['total']['store']['size_in_bytes'],
                "health": "green" if self.client.cluster.health()['status'] == 'green' else "yellow"
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}


# グローバルクライアントインスタンス
_es_client = None

def get_elasticsearch_client() -> ElasticsearchClient:
    """グローバルElasticsearchクライアント取得"""
    global _es_client
    if _es_client is None:
        _es_client = ElasticsearchClient()
    return _es_client 