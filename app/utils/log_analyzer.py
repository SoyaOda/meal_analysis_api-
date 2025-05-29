import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class AnalysisStats:
    """分析統計情報"""
    total_sessions: int
    successful_sessions: int
    failed_sessions: int
    avg_duration_ms: float
    avg_phase1_duration_ms: float
    avg_usda_search_duration_ms: float
    avg_phase2_duration_ms: float
    avg_nutrition_calc_duration_ms: float
    
    # 戦略統計
    dish_level_count: int
    ingredient_level_count: int
    
    # エラー統計
    common_errors: Dict[str, int]
    warning_counts: Dict[str, int]

class MealAnalysisLogAnalyzer:
    """食事分析ログの分析ユーティリティ"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        if not self.log_dir.exists():
            raise ValueError(f"Log directory does not exist: {log_dir}")
    
    def load_session_logs(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """セッションログを読み込み"""
        session_log_file = self.log_dir / "meal_analysis_sessions.jsonl"
        
        if not session_log_file.exists():
            logger.warning(f"Session log file not found: {session_log_file}")
            return []
        
        sessions = []
        with open(session_log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    session = json.loads(line.strip())
                    
                    # 日付フィルタリング
                    if start_date or end_date:
                        session_time = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                        if start_date and session_time < start_date:
                            continue
                        if end_date and session_time > end_date:
                            continue
                    
                    sessions.append(session)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse session log line: {e}")
        
        return sessions
    
    def analyze_sessions(self, sessions: List[Dict[str, Any]]) -> AnalysisStats:
        """セッション群を分析"""
        if not sessions:
            return AnalysisStats(
                total_sessions=0, successful_sessions=0, failed_sessions=0,
                avg_duration_ms=0, avg_phase1_duration_ms=0,
                avg_usda_search_duration_ms=0, avg_phase2_duration_ms=0,
                avg_nutrition_calc_duration_ms=0,
                dish_level_count=0, ingredient_level_count=0,
                common_errors={}, warning_counts={}
            )
        
        total_sessions = len(sessions)
        successful_sessions = sum(1 for s in sessions if not s.get('errors'))
        failed_sessions = total_sessions - successful_sessions
        
        # 実行時間統計
        durations = [s.get('total_duration_ms', 0) for s in sessions if s.get('total_duration_ms')]
        phase1_durations = [s.get('phase1_duration_ms', 0) for s in sessions if s.get('phase1_duration_ms')]
        usda_durations = [s.get('usda_search_duration_ms', 0) for s in sessions if s.get('usda_search_duration_ms')]
        phase2_durations = [s.get('phase2_duration_ms', 0) for s in sessions if s.get('phase2_duration_ms')]
        nutrition_durations = [s.get('nutrition_calc_duration_ms', 0) for s in sessions if s.get('nutrition_calc_duration_ms')]
        
        # 戦略統計
        dish_level_count = 0
        ingredient_level_count = 0
        
        for session in sessions:
            strategy_decisions = session.get('phase2_strategy_decisions', {})
            for dish_name, decision in strategy_decisions.items():
                if decision.get('strategy') == 'dish_level':
                    dish_level_count += 1
                elif decision.get('strategy') == 'ingredient_level':
                    ingredient_level_count += 1
        
        # エラー統計
        error_counts = defaultdict(int)
        warning_counts = defaultdict(int)
        
        for session in sessions:
            errors = session.get('errors', [])
            warnings = session.get('warnings', [])
            
            for error in errors:
                error_counts[error] += 1
            
            for warning in warnings:
                warning_counts[warning] += 1
        
        return AnalysisStats(
            total_sessions=total_sessions,
            successful_sessions=successful_sessions,
            failed_sessions=failed_sessions,
            avg_duration_ms=sum(durations) / len(durations) if durations else 0,
            avg_phase1_duration_ms=sum(phase1_durations) / len(phase1_durations) if phase1_durations else 0,
            avg_usda_search_duration_ms=sum(usda_durations) / len(usda_durations) if usda_durations else 0,
            avg_phase2_duration_ms=sum(phase2_durations) / len(phase2_durations) if phase2_durations else 0,
            avg_nutrition_calc_duration_ms=sum(nutrition_durations) / len(nutrition_durations) if nutrition_durations else 0,
            dish_level_count=dish_level_count,
            ingredient_level_count=ingredient_level_count,
            common_errors=dict(error_counts),
            warning_counts=dict(warning_counts)
        )
    
    def generate_report(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> str:
        """分析レポートを生成"""
        sessions = self.load_session_logs(start_date, end_date)
        stats = self.analyze_sessions(sessions)
        
        period_str = ""
        if start_date:
            period_str += f"From: {start_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
        if end_date:
            period_str += f"To: {end_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        report = f"""
# 食事分析API ログ分析レポート

{period_str}

## 📊 基本統計

- **総セッション数**: {stats.total_sessions}
- **成功セッション**: {stats.successful_sessions} ({stats.successful_sessions/max(stats.total_sessions,1)*100:.1f}%)
- **失敗セッション**: {stats.failed_sessions} ({stats.failed_sessions/max(stats.total_sessions,1)*100:.1f}%)

## ⏱️ パフォーマンス統計

- **平均総実行時間**: {stats.avg_duration_ms:.1f}ms
- **平均Phase1時間**: {stats.avg_phase1_duration_ms:.1f}ms
- **平均USDA検索時間**: {stats.avg_usda_search_duration_ms:.1f}ms
- **平均Phase2時間**: {stats.avg_phase2_duration_ms:.1f}ms
- **平均栄養計算時間**: {stats.avg_nutrition_calc_duration_ms:.1f}ms

## 🎯 戦略統計

- **Dish Level戦略**: {stats.dish_level_count}回
- **Ingredient Level戦略**: {stats.ingredient_level_count}回
- **戦略比率**: Dish {stats.dish_level_count/(max(stats.dish_level_count+stats.ingredient_level_count,1))*100:.1f}% vs Ingredient {stats.ingredient_level_count/(max(stats.dish_level_count+stats.ingredient_level_count,1))*100:.1f}%

## ⚠️ エラー・警告統計

### よくあるエラー:
"""
        
        for error, count in sorted(stats.common_errors.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"- {error}: {count}回\n"
        
        report += "\n### よくある警告:\n"
        for warning, count in sorted(stats.warning_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"- {warning}: {count}回\n"
        
        return report
    
    def export_to_csv(self, output_file: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        """セッションデータをCSVにエクスポート"""
        sessions = self.load_session_logs(start_date, end_date)
        
        if not sessions:
            logger.warning("No sessions to export")
            return
        
        # データを平坦化
        rows = []
        for session in sessions:
            row = {
                'session_id': session.get('session_id'),
                'start_time': session.get('start_time'),
                'end_time': session.get('end_time'),
                'endpoint': session.get('endpoint'),
                'image_filename': session.get('image_filename'),
                'image_size_bytes': session.get('image_size_bytes'),
                'total_duration_ms': session.get('total_duration_ms'),
                'phase1_duration_ms': session.get('phase1_duration_ms'),
                'usda_search_duration_ms': session.get('usda_search_duration_ms'),
                'phase2_duration_ms': session.get('phase2_duration_ms'),
                'nutrition_calc_duration_ms': session.get('nutrition_calc_duration_ms'),
                'dishes_count': session.get('phase1_dishes_count'),
                'usda_queries_count': session.get('phase1_usda_queries_count'),
                'usda_results_found': session.get('usda_results_found'),
                'total_calories': session.get('total_calories'),
                'has_errors': bool(session.get('errors')),
                'has_warnings': bool(session.get('warnings')),
                'error_count': len(session.get('errors', [])),
                'warning_count': len(session.get('warnings', []))
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        logger.info(f"Exported {len(rows)} sessions to {output_file}")
    
    def find_slow_sessions(self, threshold_ms: float = 10000) -> List[Dict[str, Any]]:
        """遅いセッションを特定"""
        sessions = self.load_session_logs()
        slow_sessions = [
            s for s in sessions 
            if s.get('total_duration_ms', 0) > threshold_ms
        ]
        return sorted(slow_sessions, key=lambda x: x.get('total_duration_ms', 0), reverse=True)
    
    def find_error_patterns(self) -> Dict[str, List[str]]:
        """エラーパターンを分析"""
        sessions = self.load_session_logs()
        error_patterns = defaultdict(list)
        
        for session in sessions:
            errors = session.get('errors', [])
            session_id = session.get('session_id', 'unknown')
            
            for error in errors:
                error_patterns[error].append(session_id)
        
        return dict(error_patterns)

def create_log_analyzer(log_dir: str = "logs") -> MealAnalysisLogAnalyzer:
    """ログアナライザーのファクトリー関数"""
    return MealAnalysisLogAnalyzer(log_dir) 