"""
Elasticsearchクライアント管理
"""
import json
import logging
from typing import Optional, Dict, Any, List
from elasticsearch import Elasticsearch, NotFoundError, RequestError
from elasticsearch.helpers import bulk

from .config import es_config

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Elasticsearchクライアント管理クラス"""
    
    def __init__(self):
        """初期化"""
        self._client: Optional[Elasticsearch] = None
    
    @property
    def client(self) -> Elasticsearch:
        """Elasticsearchクライアントを取得"""
        if self._client is None:
            self._client = Elasticsearch(**es_config.connection_config)
        return self._client
    
    async def health_check(self) -> bool:
        """Elasticsearchの接続チェック"""
        try:
            health = self.client.cluster.health()
            logger.info(f"Elasticsearch cluster health: {health['status']}")
            return health['status'] in ['green', 'yellow']
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return False
    
    async def create_index(self, index_name: str, settings_file_path: str) -> bool:
        """インデックスを作成"""
        try:
            # 既存インデックスをチェック
            if self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} already exists")
                return True
            
            # 設定ファイルを読み込み
            with open(settings_file_path, 'r', encoding='utf-8') as f:
                index_config = json.load(f)
            
            # インデックス作成
            response = self.client.indices.create(
                index=index_name,
                body=index_config
            )
            
            logger.info(f"Index {index_name} created successfully: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False
    
    async def delete_index(self, index_name: str) -> bool:
        """インデックスを削除"""
        try:
            if self.client.indices.exists(index=index_name):
                response = self.client.indices.delete(index=index_name)
                logger.info(f"Index {index_name} deleted: {response}")
                return True
            else:
                logger.warning(f"Index {index_name} does not exist")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            return False
    
    async def index_document(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """単一ドキュメントをインデックス"""
        try:
            response = self.client.index(
                index=index_name,
                id=doc_id,
                body=document
            )
            logger.debug(f"Document {doc_id} indexed: {response['result']}")
            return response['result'] in ['created', 'updated']
            
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            return False
    
    async def bulk_index_documents(self, index_name: str, documents: List[Dict[str, Any]]) -> bool:
        """バルクドキュメントインデックス"""
        try:
            actions = []
            for doc in documents:
                action = {
                    "_index": index_name,
                    "_id": doc.get("food_id", doc.get("fdc_id")),
                    "_source": doc
                }
                actions.append(action)
            
            success, failed = bulk(self.client, actions)
            logger.info(f"Bulk indexing: {success} successful, {len(failed)} failed")
            
            if failed:
                logger.error(f"Failed documents: {failed[:5]}")  # 最初の5件のエラーをログ
            
            return len(failed) == 0
            
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return False
    
    async def search(self, index_name: str, query: Dict[str, Any], size: int = None) -> Optional[Dict[str, Any]]:
        """検索実行"""
        try:
            search_size = size or es_config.default_search_size
            if search_size > es_config.max_search_size:
                search_size = es_config.max_search_size
            
            response = self.client.search(
                index=index_name,
                body=query,
                size=search_size
            )
            
            logger.debug(f"Search executed: {response['hits']['total']['value']} total hits")
            return response
            
        except NotFoundError:
            logger.error(f"Index {index_name} not found")
            return None
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return None
    
    async def analyze_text(self, index_name: str, analyzer: str, text: str) -> Optional[List[str]]:
        """テキスト分析を実行"""
        try:
            response = self.client.indices.analyze(
                index=index_name,
                body={
                    "analyzer": analyzer,
                    "text": text
                }
            )
            
            tokens = [token['token'] for token in response['tokens']]
            logger.debug(f"Analyzed text '{text}' -> {tokens}")
            return tokens
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return None
    
    def close(self):
        """クライアント接続を閉じる"""
        if self._client:
            try:
                self._client.close()
                logger.info("Elasticsearch client connection closed")
            except Exception as e:
                logger.error(f"Error closing Elasticsearch client: {e}")
            finally:
                self._client = None


# グローバルクライアントインスタンス
es_client = ElasticsearchClient() 