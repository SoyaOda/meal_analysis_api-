from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any, Optional
import logging
from datetime import datetime

# 型変数の定義
InputType = TypeVar('InputType')
OutputType = TypeVar('OutputType')


class BaseComponent(ABC, Generic[InputType, OutputType]):
    """
    食事分析パイプラインのベースコンポーネント抽象クラス
    
    全てのコンポーネントはこのクラスを継承し、process メソッドを実装する必要があります。
    """
    
    def __init__(self, component_name: str, logger: Optional[logging.Logger] = None):
        """
        ベースコンポーネントの初期化
        
        Args:
            component_name: コンポーネント名
            logger: ロガーインスタンス（指定しない場合は自動生成）
        """
        self.component_name = component_name
        self.logger = logger or logging.getLogger(f"{__name__}.{component_name}")
        self.created_at = datetime.now()
        self.execution_count = 0
        self.current_execution_log = None  # 詳細ログ
        
    @abstractmethod
    async def process(self, input_data: InputType) -> OutputType:
        """
        メイン処理メソッド（抽象メソッド）
        
        Args:
            input_data: 入力データ
            
        Returns:
            OutputType: 処理結果
            
        Raises:
            ComponentError: 処理エラーが発生した場合
        """
        pass
    
    async def execute(self, input_data: InputType, execution_log: Optional['DetailedExecutionLog'] = None) -> OutputType:
        """
        ラップされた実行メソッド（ログ記録、エラーハンドリング付き）
        
        Args:
            input_data: 入力データ
            execution_log: 詳細実行ログ（オプション）
            
        Returns:
            OutputType: 処理結果
        """
        self.execution_count += 1
        execution_id = f"{self.component_name}_{self.execution_count}"
        
        # 詳細ログの設定
        if execution_log:
            self.current_execution_log = execution_log
            # 入力データを記録
            self.current_execution_log.set_input(self._safe_serialize_input(input_data))
        
        self.logger.info(f"[{execution_id}] Starting {self.component_name} processing")
        
        try:
            start_time = datetime.now()
            result = await self.process(input_data)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            self.logger.info(f"[{execution_id}] {self.component_name} completed in {processing_time:.2f}s")
            
            # 詳細ログに出力データを記録
            if self.current_execution_log:
                self.current_execution_log.set_output(self._safe_serialize_output(result))
                self.current_execution_log.finalize()
            
            return result
            
        except Exception as e:
            self.logger.error(f"[{execution_id}] {self.component_name} failed: {str(e)}", exc_info=True)
            
            # 詳細ログにエラーを記録
            if self.current_execution_log:
                self.current_execution_log.add_error(str(e))
                self.current_execution_log.finalize()
            
            raise ComponentError(f"{self.component_name} processing failed: {str(e)}") from e
        finally:
            self.current_execution_log = None
    
    def log_prompt(self, prompt_name: str, prompt_content: str, variables: dict = None):
        """プロンプトをログに記録"""
        if self.current_execution_log:
            self.current_execution_log.add_prompt(prompt_name, prompt_content, variables)
    
    def log_reasoning(self, decision_point: str, reason: str, confidence: float = None):
        """推論理由をログに記録"""
        if self.current_execution_log:
            self.current_execution_log.add_reasoning(decision_point, reason, confidence)
    
    def log_processing_detail(self, detail_key: str, detail_value: Any):
        """処理詳細をログに記録"""
        if self.current_execution_log:
            self.current_execution_log.add_processing_detail(detail_key, detail_value)
    
    def log_confidence_score(self, metric_name: str, score: float):
        """信頼度スコアをログに記録"""
        if self.current_execution_log:
            self.current_execution_log.add_confidence_score(metric_name, score)
    
    def log_warning(self, warning: str):
        """警告をログに記録"""
        if self.current_execution_log:
            self.current_execution_log.add_warning(warning)
    
    def _safe_serialize_input(self, input_data: InputType) -> dict:
        """入力データを安全にシリアライズ"""
        try:
            if hasattr(input_data, 'model_dump'):
                return input_data.model_dump()
            elif hasattr(input_data, '__dict__'):
                return input_data.__dict__
            else:
                return {"data": str(input_data)}
        except Exception as e:
            return {"serialization_error": str(e)}
    
    def _safe_serialize_output(self, output_data: OutputType) -> dict:
        """出力データを安全にシリアライズ"""
        try:
            if hasattr(output_data, 'model_dump'):
                return output_data.model_dump()
            elif hasattr(output_data, '__dict__'):
                return output_data.__dict__
            else:
                return {"data": str(output_data)}
        except Exception as e:
            return {"serialization_error": str(e)}
    
    def get_component_info(self) -> dict:
        """コンポーネント情報を取得"""
        return {
            "component_name": self.component_name,
            "created_at": self.created_at.isoformat(),
            "execution_count": self.execution_count,
            "component_type": self.__class__.__name__
        }


class ComponentError(Exception):
    """コンポーネント処理エラー"""
    
    def __init__(self, message: str, component_name: str = None, original_error: Exception = None):
        super().__init__(message)
        self.component_name = component_name
        self.original_error = original_error
        self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        """エラー情報を辞書形式で取得"""
        return {
            "error_message": str(self),
            "component_name": self.component_name,
            "timestamp": self.timestamp.isoformat(),
            "original_error": str(self.original_error) if self.original_error else None
        } 