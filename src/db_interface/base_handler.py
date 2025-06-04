"""
DB Handler抽象基底クラス

データベース操作の共通インターフェース
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from .db_models import QueryParameters, RawDBResult


class DBHandler(ABC):
    """データベースハンドラーの抽象基底クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        設定で初期化
        
        Args:
            config: データベース固有の設定
        """
        self.config = config
    
    @abstractmethod
    async def connect(self):
        """データベースへの接続を確立"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """データベースへの接続を閉じる"""
        pass
    
    @abstractmethod
    async def fetch_nutrition_data(self, params: QueryParameters) -> RawDBResult:
        """
        栄養データを取得
        
        Args:
            params: クエリパラメータ
            
        Returns:
            RawDBResult: 検索結果
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """接続状態を確認"""
        pass 