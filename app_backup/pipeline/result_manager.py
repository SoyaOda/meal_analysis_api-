import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DetailedExecutionLog:
    """各コンポーネントの詳細実行ログ"""
    
    def __init__(self, component_name: str, execution_id: str):
        self.component_name = component_name
        self.execution_id = execution_id
        self.execution_start_time = datetime.now()
        self.execution_end_time = None
        self.input_data = {}
        self.output_data = {}
        self.processing_details = {}
        self.prompts_used = {}
        self.reasoning = {}
        self.confidence_scores = {}
        self.warnings = []
        self.errors = []
        
    def set_input(self, input_data: Dict[str, Any]):
        """入力データを記録（機密情報は除外）"""
        # 画像データは大きすぎるので、メタデータのみ保存
        safe_input = {}
        for key, value in input_data.items():
            if key == 'image_bytes':
                safe_input[key] = {
                    "size_bytes": len(value) if value else 0,
                    "type": "binary_image_data"
                }
            else:
                safe_input[key] = value
        self.input_data = safe_input
    
    def set_output(self, output_data: Dict[str, Any]):
        """出力データを記録"""
        self.output_data = output_data
        
    def add_prompt(self, prompt_name: str, prompt_content: str, variables: Dict[str, Any] = None):
        """使用されたプロンプトを記録"""
        self.prompts_used[prompt_name] = {
            "content": prompt_content,
            "variables": variables or {},
            "timestamp": datetime.now().isoformat()
        }
    
    def add_reasoning(self, decision_point: str, reason: str, confidence: float = None):
        """推論理由を記録"""
        self.reasoning[decision_point] = {
            "reason": reason,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
    
    def add_processing_detail(self, detail_key: str, detail_value: Any):
        """処理詳細を記録"""
        self.processing_details[detail_key] = detail_value
    
    def add_confidence_score(self, metric_name: str, score: float):
        """信頼度スコアを記録"""
        self.confidence_scores[metric_name] = score
    
    def add_warning(self, warning: str):
        """警告を記録"""
        self.warnings.append({
            "message": warning,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_error(self, error: str):
        """エラーを記録"""
        self.errors.append({
            "message": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def finalize(self):
        """実行完了時の最終処理"""
        self.execution_end_time = datetime.now()
    
    def get_execution_time(self) -> float:
        """実行時間を取得（秒）"""
        if self.execution_end_time:
            return (self.execution_end_time - self.execution_start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で取得"""
        return {
            "component_name": self.component_name,
            "execution_id": self.execution_id,
            "execution_start_time": self.execution_start_time.isoformat(),
            "execution_end_time": self.execution_end_time.isoformat() if self.execution_end_time else None,
            "execution_time_seconds": self.get_execution_time(),
            "input_data": self.input_data,
            "output_data": self.output_data,
            "processing_details": self.processing_details,
            "prompts_used": self.prompts_used,
            "reasoning": self.reasoning,
            "confidence_scores": self.confidence_scores,
            "warnings": self.warnings,
            "errors": self.errors
        }


class ResultManager:
    """分析結果の管理とファイル出力を行うクラス"""
    
    def __init__(self, base_dir: str = "analysis_results"):
        self.base_dir = base_dir
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.analysis_id = None
        self.session_dir = None
        self.analysis_dir = None
        self.phase_results = {}  # フェーズ別結果を管理
        
    def initialize_session(self, analysis_id: str) -> str:
        """セッションを初期化し、分析IDを設定"""
        self.analysis_id = analysis_id
        self.session_dir = os.path.join(self.base_dir, f"meal_analysis_{self.session_id}")
        self.analysis_dir = os.path.join(self.session_dir, f"analysis_{analysis_id}")
        
        # 基本ディレクトリのみ作成
        os.makedirs(self.analysis_dir, exist_ok=True)
        
        return self.analysis_dir

    def add_phase_result(self, phase_name: str, phase_data: dict) -> None:
        """フェーズ結果を追加
        
        Args:
            phase_name: フェーズ名（例：Phase1SpeechComponent）
            phase_data: フェーズの結果データ
        """
        self.phase_results[phase_name] = phase_data
    
    def save_phase_results(self, phase1_data: dict, nutrition_query_results: dict, 
                          nutrition_calculation_results: dict, component_logs: list,
                          processing_time_seconds: float) -> dict:
        """新しい3ファイル構造で結果を保存"""
        
        if not self.analysis_dir:
            raise ValueError("Session not initialized")
        
        # 1. analysis_summary.json - 軽量サマリー（API応答用）
        summary_data = self._create_analysis_summary(
            phase1_data, nutrition_calculation_results, processing_time_seconds
        )
        summary_path = os.path.join(self.analysis_dir, "analysis_summary.json")
        self._save_json(summary_path, summary_data)
        
        # 2. detailed_analysis.json - 包括的データ（デバッグ・分析用）
        detailed_data = self._create_detailed_analysis(
            phase1_data, nutrition_query_results, nutrition_calculation_results
        )
        detailed_path = os.path.join(self.analysis_dir, "detailed_analysis.json")
        self._save_json(detailed_path, detailed_data)
        
        # 3. execution_log.json - 詳細ログ（開発・トラブルシューティング用）
        log_data = self._create_execution_log(
            component_logs, processing_time_seconds
        )
        log_path = os.path.join(self.analysis_dir, "execution_log.json")
        self._save_json(log_path, log_data)
        
        return {
            "analysis_summary_path": summary_path,
            "detailed_analysis_path": detailed_path,
            "execution_log_path": log_path,
            "analysis_dir": self.analysis_dir
        }
    
    def _create_analysis_summary(self) -> dict:
        """軽量サマリーデータを作成（API応答用）"""
        
        # phase_resultsから各フェーズのデータを取得
        phase1_data = self.phase_results.get("Phase1SpeechComponent", self.phase_results.get("Phase1Component", {}))
        nutrition_calculation_data = self.phase_results.get("NutritionCalculationComponent", {})
        
        # 入力タイプを判定
        input_type = "image"
        if phase1_data.get("input_data", {}).get("audio_bytes") or phase1_data.get("input_data", {}).get("language_code"):
            input_type = "voice"
        
        # final_resultから基本情報を取得
        final_result = getattr(self, 'final_result', {})
        processing_time = final_result.get("processing_time_seconds", 0.0)
        
        summary_data = {
            "analysis_id": self.analysis_id,
            "input_type": input_type,
            "total_dishes": len(nutrition_calculation_data.get("dishes", [])),
            "total_ingredients": sum(len(dish.get("ingredients", [])) for dish in nutrition_calculation_data.get("dishes", [])),
            "processing_time_seconds": processing_time,
            "dishes": nutrition_calculation_data.get("dishes", []),
            "total_nutrition": nutrition_calculation_data.get("total_nutrition", {}),
            "ai_model_used": phase1_data.get("input_data", {}).get("llm_model_id", "unknown"),
            "match_rate_percent": nutrition_calculation_data.get("match_rate_percent", 0.0),
            "search_method": nutrition_calculation_data.get("search_method", "unknown")
        }
        
        # 音声入力の場合、テキスト変換の基本情報を追加
        if input_type == "voice":
            processing_details = phase1_data.get("processing_details", {})
            if "speech_recognition_result" in processing_details:
                transcript = processing_details["speech_recognition_result"]
                summary_data["speech_transcription_summary"] = {
                    "original_text": transcript,
                    "text_length": len(transcript),
                    "language_code": phase1_data.get("input_data", {}).get("language_code", "en-US")
                }
        
        return summary_data
    
    def _create_detailed_analysis(self) -> dict:
        """包括的データを作成（デバッグ・分析用）"""
        
        # phase_resultsから各フェーズのデータを取得
        phase1_data = self.phase_results.get("Phase1SpeechComponent", self.phase_results.get("Phase1Component", {}))
        nutrition_search_data = self.phase_results.get("AdvancedNutritionSearchComponent", {})
        nutrition_calculation_data = self.phase_results.get("NutritionCalculationComponent", {})
        
        # 音声入力のテキスト変換結果を抽出
        speech_transcription = None
        if phase1_data.get("input_data", {}).get("audio_bytes") or phase1_data.get("input_data", {}).get("language_code"):
            # 音声入力の場合、処理詳細からテキスト変換結果を取得
            processing_details = phase1_data.get("processing_details", {})
            if "speech_recognition_result" in processing_details:
                speech_transcription = {
                    "original_text": processing_details["speech_recognition_result"],
                    "language_code": phase1_data.get("input_data", {}).get("language_code", "en-US"),
                    "audio_size_bytes": phase1_data.get("input_data", {}).get("audio_bytes", 0),
                    "timestamp": datetime.now().isoformat()
                }
        
        detailed_data = {
            "analysis_id": self.analysis_id,
            "timestamp": datetime.now().isoformat(),
            "input_type": "voice" if speech_transcription else "image",
            "phase1_results": phase1_data,
            "nutrition_search_results": nutrition_search_data,
            "nutrition_calculation_results": nutrition_calculation_data,
            "input_data": {
                "phase1_input": phase1_data.get("input_data", {}),
                "nutrition_query_input": nutrition_search_data.get("input_data", {}),
                "nutrition_calculation_input": nutrition_calculation_data.get("input_data", {})
            },
            "intermediate_data": {
                "extracted_foods": phase1_data.get("detected_food_items", []),
                "search_terms": nutrition_search_data.get("search_summary", {}).get("search_terms", []),
                "nutrition_mappings": nutrition_search_data.get("matches", [])
            },
            "output_data": {
                "final_dishes": nutrition_calculation_data.get("dishes", []),
                "total_nutrition": nutrition_calculation_data.get("total_nutrition", {}),
                "search_summary": nutrition_search_data.get("search_summary", {})
            }
        }
        
        # 音声入力の場合、テキスト変換結果を追加
        if speech_transcription:
            detailed_data["speech_transcription"] = speech_transcription
            
        return detailed_data
    
    def _create_execution_log(self, component_logs: list, processing_time: float) -> dict:
        """詳細ログデータを作成（開発・トラブルシューティング用）"""
        return {
            "analysis_id": self.analysis_id,
            "timestamp": datetime.now().isoformat(),
            "processing_time_seconds": processing_time,
            "component_execution_logs": component_logs,
            "pipeline_summary": {
                "total_components": len(component_logs),
                "successful_components": len([log for log in component_logs if log.get("status") == "success"]),
                "failed_components": len([log for log in component_logs if log.get("status") == "error"]),
                "warnings_count": sum(len(log.get("warnings", [])) for log in component_logs),
                "errors_count": sum(len(log.get("errors", [])) for log in component_logs)
            },
            "system_info": {
                "session_id": self.session_id,
                "analysis_dir": self.analysis_dir,
                "timestamp_utc": datetime.utcnow().isoformat()
            }
        }
    
    def _save_json(self, file_path: str, data: dict):
        """JSONファイルを保存"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_analysis_summary_path(self) -> str:
        """サマリーファイルパスを取得"""
        if not self.analysis_dir:
            raise ValueError("Session not initialized")
        return os.path.join(self.analysis_dir, "analysis_summary.json") 

    
    def set_final_result(self, final_result: dict):
        """互換性のため: 最終結果を設定（既存のパイプラインとの互換性維持）"""
        self.final_result = final_result
    
    def finalize_pipeline(self):
        """パイプラインの終了処理：3つのファイルを作成して保存"""
        try:
            # 3つのファイルを作成して保存
            # 1. analysis_summary.json
            summary_data = self._create_analysis_summary()
            summary_path = os.path.join(self.analysis_dir, "analysis_summary.json")
            self._save_json(summary_path, summary_data)
            
            # 2. detailed_analysis.json
            detailed_data = self._create_detailed_analysis()
            detailed_path = os.path.join(self.analysis_dir, "detailed_analysis.json")
            self._save_json(detailed_path, detailed_data)
            
            # 3. execution_log.json
            component_logs = []
            for phase_name, phase_data in self.phase_results.items():
                component_logs.append({
                    "component_name": phase_name,
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "execution_time_ms": 0,
                    "warnings": [],
                    "errors": []
                })
            
            processing_time = getattr(self, 'final_result', {}).get('processing_time_seconds', 0.0)
            execution_log_data = self._create_execution_log(component_logs, processing_time)
            execution_log_path = os.path.join(self.analysis_dir, "execution_log.json")
            self._save_json(execution_log_path, execution_log_data)
            
            print(f"✅ 分析結果が保存されました: {self.analysis_dir}")
            
        except Exception as e:
            print(f"❌ ファイル保存エラー: {e}")
            raise  # 新しい構造では特別な終了処理は不要
    
    def get_analysis_folder_path(self) -> str:
        """互換性のため: 分析フォルダパスを取得"""
        if not self.analysis_dir:
            raise ValueError("Session not initialized")
        return self.analysis_dir
    
    def save_phase_results(self, phase1_data: dict = None, nutrition_query_results: dict = None, 
                          nutrition_calculation_results: dict = None, component_logs: list = None,
                          processing_time_seconds: float = None) -> dict:
        """
        新しい3ファイル構造で結果を保存
        互換性維持のため、引数が渡された場合は従来の動作をサポート
        """
        if not self.analysis_dir:
            raise ValueError("Session not initialized")
        
        # 引数が渡された場合は従来の方式で処理（互換性維持）
        if phase1_data is not None or nutrition_query_results is not None or nutrition_calculation_results is not None:
            # 従来の引数ベースの処理
            if phase1_data is None:
                phase1_data = {}
            if nutrition_query_results is None:
                nutrition_query_results = {}
            if nutrition_calculation_results is None:
                nutrition_calculation_results = {}
            if component_logs is None:
                component_logs = []
            if processing_time_seconds is None:
                processing_time_seconds = 0.0
                
            # 従来の方式でデータを作成（メソッドは新しいバージョンを使用）
            summary_data = self._create_analysis_summary()
            detailed_data = self._create_detailed_analysis()
            
        else:
            # 新しい方式：phase_resultsを使用
            summary_data = self._create_analysis_summary()
            detailed_data = self._create_detailed_analysis()
        
        # 新しい3ファイル構造で結果を保存
        summary_path = os.path.join(self.analysis_dir, "analysis_summary.json")
        self._save_json(summary_path, summary_data)
        
        detailed_path = os.path.join(self.analysis_dir, "detailed_analysis.json")
        self._save_json(detailed_path, detailed_data)
        
        # 実行ログ作成（簡略化版）
        log_data = self._create_execution_log(
            component_logs or [], 
            getattr(self, 'final_result', {}).get('processing_time_seconds', 0.0)
        )
        log_path = os.path.join(self.analysis_dir, "execution_log.json")
        self._save_json(log_path, log_data)
        
        return {
            "analysis_summary_path": summary_path,
            "detailed_analysis_path": detailed_path,
            "execution_log_path": log_path,
            "analysis_dir": self.analysis_dir
        }

    
    def create_execution_log(self, component_name: str, log_id: str):
        """互換性のため: 実行ログオブジェクトを作成（既存のパイプラインとの互換性維持）"""
        return DetailedExecutionLog(component_name, log_id)
