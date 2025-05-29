import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class LogLevel(str, Enum):
    """ログレベル定義"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ProcessingPhase(str, Enum):
    """処理フェーズ定義"""
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    PHASE1_START = "PHASE1_START"
    PHASE1_COMPLETE = "PHASE1_COMPLETE"
    USDA_SEARCH_START = "USDA_SEARCH_START"
    USDA_SEARCH_COMPLETE = "USDA_SEARCH_COMPLETE"
    PHASE2_START = "PHASE2_START"
    PHASE2_COMPLETE = "PHASE2_COMPLETE"
    NUTRITION_CALC_START = "NUTRITION_CALC_START"
    NUTRITION_CALC_COMPLETE = "NUTRITION_CALC_COMPLETE"
    RESPONSE_SENT = "RESPONSE_SENT"
    ERROR_OCCURRED = "ERROR_OCCURRED"

@dataclass
class LogEntry:
    """ログエントリの標準構造"""
    timestamp: str
    request_id: str
    log_level: LogLevel
    phase: ProcessingPhase
    message: str
    data: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None
    error_details: Optional[str] = None

@dataclass
class MealAnalysisSession:
    """食事分析セッション全体のログ"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    endpoint: str = ""
    image_filename: Optional[str] = None
    image_size_bytes: Optional[int] = None
    
    # フェーズ1結果
    phase1_duration_ms: Optional[float] = None
    phase1_dishes_count: Optional[int] = None
    phase1_usda_queries_count: Optional[int] = None
    phase1_output: Optional[Dict[str, Any]] = None
    
    # USDA検索結果
    usda_search_duration_ms: Optional[float] = None
    usda_queries_executed: Optional[int] = None
    usda_results_found: Optional[int] = None
    usda_search_details: Optional[List[Dict[str, Any]]] = None
    
    # フェーズ2結果
    phase2_duration_ms: Optional[float] = None
    phase2_strategy_decisions: Optional[Dict[str, Any]] = None
    phase2_fdc_selections: Optional[Dict[str, Any]] = None
    phase2_output: Optional[Dict[str, Any]] = None
    
    # 栄養計算結果
    nutrition_calc_duration_ms: Optional[float] = None
    total_calories: Optional[float] = None
    final_nutrition: Optional[Dict[str, Any]] = None
    
    # エラー・警告
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    
    # パフォーマンス
    total_duration_ms: Optional[float] = None
    gemini_api_calls: Optional[int] = None
    usda_api_calls: Optional[int] = None

class MealAnalysisLogger:
    """食事分析専用ログ管理クラス"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # セッション管理
        self.active_sessions: Dict[str, MealAnalysisSession] = {}
        
        # ログファイル設定
        self.setup_file_logging()
    
    def setup_file_logging(self):
        """ファイルログの設定"""
        # 詳細ログファイル
        detailed_log_file = self.log_dir / "meal_analysis_detailed.jsonl"
        
        # セッションログファイル
        session_log_file = self.log_dir / "meal_analysis_sessions.jsonl"
        
        # エラーログファイル
        error_log_file = self.log_dir / "meal_analysis_errors.log"
        
        self.detailed_log_file = detailed_log_file
        self.session_log_file = session_log_file
        self.error_log_file = error_log_file
    
    def start_session(
        self, 
        endpoint: str,
        image_filename: Optional[str] = None,
        image_size_bytes: Optional[int] = None
    ) -> str:
        """新しい分析セッションを開始"""
        session_id = str(uuid.uuid4())
        
        session = MealAnalysisSession(
            session_id=session_id,
            start_time=datetime.now(timezone.utc).isoformat(),
            endpoint=endpoint,
            image_filename=image_filename,
            image_size_bytes=image_size_bytes
        )
        
        self.active_sessions[session_id] = session
        
        self.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.REQUEST_RECEIVED,
            message=f"Started meal analysis session for endpoint: {endpoint}",
            data={
                "endpoint": endpoint,
                "image_filename": image_filename,
                "image_size_bytes": image_size_bytes
            }
        )
        
        return session_id
    
    def log_entry(
        self,
        session_id: str,
        level: LogLevel,
        phase: ProcessingPhase,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None,
        error_details: Optional[str] = None
    ):
        """個別のログエントリを記録"""
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=session_id,
            log_level=level,
            phase=phase,
            message=message,
            data=data,
            execution_time_ms=execution_time_ms,
            error_details=error_details
        )
        
        # JSONLファイルに追記
        try:
            with open(self.detailed_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write detailed log: {e}")
        
        # エラーレベルの場合は専用ファイルにも記録
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            try:
                with open(self.error_log_file, "a", encoding="utf-8") as f:
                    f.write(f"[{entry.timestamp}] {session_id} - {message}\n")
                    if error_details:
                        f.write(f"  Error Details: {error_details}\n")
                    if data:
                        f.write(f"  Data: {json.dumps(data, ensure_ascii=False)}\n")
                    f.write("\n")
            except Exception as e:
                logger.error(f"Failed to write error log: {e}")
    
    def update_phase1_results(
        self,
        session_id: str,
        duration_ms: float,
        dishes_count: int,
        usda_queries_count: int,
        phase1_output: Dict[str, Any]
    ):
        """フェーズ1結果を記録"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.phase1_duration_ms = duration_ms
            session.phase1_dishes_count = dishes_count
            session.phase1_usda_queries_count = usda_queries_count
            session.phase1_output = phase1_output
        
        self.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.PHASE1_COMPLETE,
            message=f"Phase 1 completed: {dishes_count} dishes, {usda_queries_count} USDA queries",
            data={
                "duration_ms": duration_ms,
                "dishes_count": dishes_count,
                "usda_queries_count": usda_queries_count,
                "phase1_output": phase1_output
            },
            execution_time_ms=duration_ms
        )
    
    def update_usda_search_results(
        self,
        session_id: str,
        duration_ms: float,
        queries_executed: int,
        results_found: int,
        search_details: List[Dict[str, Any]]
    ):
        """USDA検索結果を記録"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.usda_search_duration_ms = duration_ms
            session.usda_queries_executed = queries_executed
            session.usda_results_found = results_found
            session.usda_search_details = search_details
        
        self.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.USDA_SEARCH_COMPLETE,
            message=f"USDA search completed: {queries_executed} queries, {results_found} results",
            data={
                "duration_ms": duration_ms,
                "queries_executed": queries_executed,
                "results_found": results_found,
                "search_summary": search_details
            },
            execution_time_ms=duration_ms
        )
    
    def update_phase2_results(
        self,
        session_id: str,
        duration_ms: float,
        strategy_decisions: Dict[str, Any],
        fdc_selections: Dict[str, Any],
        phase2_output: Dict[str, Any]
    ):
        """フェーズ2結果を記録"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.phase2_duration_ms = duration_ms
            session.phase2_strategy_decisions = strategy_decisions
            session.phase2_fdc_selections = fdc_selections
            session.phase2_output = phase2_output
        
        self.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.PHASE2_COMPLETE,
            message="Phase 2 completed: Strategy decisions and FDC ID selections made",
            data={
                "duration_ms": duration_ms,
                "strategy_decisions": strategy_decisions,
                "fdc_selections": fdc_selections,
                "phase2_output": phase2_output
            },
            execution_time_ms=duration_ms
        )
    
    def update_nutrition_results(
        self,
        session_id: str,
        duration_ms: float,
        total_calories: float,
        final_nutrition: Dict[str, Any]
    ):
        """栄養計算結果を記録"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.nutrition_calc_duration_ms = duration_ms
            session.total_calories = total_calories
            session.final_nutrition = final_nutrition
        
        self.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.NUTRITION_CALC_COMPLETE,
            message=f"Nutrition calculation completed: {total_calories:.1f} kcal total",
            data={
                "duration_ms": duration_ms,
                "total_calories": total_calories,
                "final_nutrition": final_nutrition
            },
            execution_time_ms=duration_ms
        )
    
    def end_session(
        self,
        session_id: str,
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None
    ):
        """セッションを終了し、完全なログを保存"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session.end_time = datetime.now(timezone.utc).isoformat()
        session.warnings = warnings
        session.errors = errors
        
        # 総実行時間を計算
        if session.start_time and session.end_time:
            start = datetime.fromisoformat(session.start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(session.end_time.replace('Z', '+00:00'))
            session.total_duration_ms = (end - start).total_seconds() * 1000
        
        # セッションログファイルに保存
        try:
            with open(self.session_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(session), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write session log: {e}")
        
        self.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.RESPONSE_SENT,
            message=f"Session completed in {session.total_duration_ms:.1f}ms",
            data={
                "total_duration_ms": session.total_duration_ms,
                "warnings_count": len(warnings) if warnings else 0,
                "errors_count": len(errors) if errors else 0
            },
            execution_time_ms=session.total_duration_ms
        )
        
        # アクティブセッションから削除
        del self.active_sessions[session_id]
    
    def log_error(
        self,
        session_id: str,
        phase: ProcessingPhase,
        error_message: str,
        error_details: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """エラーログを記録"""
        self.log_entry(
            session_id=session_id,
            level=LogLevel.ERROR,
            phase=phase,
            message=error_message,
            data=data,
            error_details=error_details
        )

# グローバルロガーインスタンス
meal_analysis_logger = MealAnalysisLogger()

def get_meal_analysis_logger() -> MealAnalysisLogger:
    """ロガーインスタンスを取得"""
    return meal_analysis_logger 