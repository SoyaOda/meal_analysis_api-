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
        self.start_time = datetime.now()
        self.end_time = None
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
        self.end_time = datetime.now()
    
    def get_execution_time(self) -> float:
        """実行時間を取得（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で取得"""
        return {
            "component_name": self.component_name,
            "execution_id": self.execution_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
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
    """解析結果と詳細ログの管理クラス（フェーズ別整理版）"""
    
    def __init__(self, analysis_id: str, save_directory: str = "analysis_results"):
        self.analysis_id = analysis_id
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 実行ごとのフォルダを作成
        self.analysis_folder_name = f"analysis_{self.timestamp}_{self.analysis_id}"
        self.analysis_dir = Path(save_directory) / self.analysis_folder_name
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # 各フェーズのフォルダを作成
        self.phase1_dir = self.analysis_dir / "phase1"
        self.usda_query_dir = self.analysis_dir / "usda_query"
        self.phase2_dir = self.analysis_dir / "phase2"
        self.nutrition_dir = self.analysis_dir / "nutrition_calculation"
        
        for phase_dir in [self.phase1_dir, self.usda_query_dir, self.phase2_dir, self.nutrition_dir]:
            phase_dir.mkdir(exist_ok=True)
        
        self.pipeline_start_time = datetime.now()
        self.pipeline_end_time = None
        self.execution_logs: List[DetailedExecutionLog] = []
        self.final_result = {}
        self.pipeline_metadata = {
            "analysis_id": analysis_id,
            "version": "v2.0",
            "analysis_folder": self.analysis_folder_name,
            "pipeline_start_time": self.pipeline_start_time.isoformat()
        }
        
    def create_execution_log(self, component_name: str, execution_id: str) -> DetailedExecutionLog:
        """新しい実行ログを作成"""
        log = DetailedExecutionLog(component_name, execution_id)
        self.execution_logs.append(log)
        return log
    
    def set_final_result(self, result: Dict[str, Any]):
        """最終結果を設定"""
        self.final_result = result
        
    def finalize_pipeline(self):
        """パイプライン完了時の最終処理"""
        self.pipeline_end_time = datetime.now()
        self.pipeline_metadata["pipeline_end_time"] = self.pipeline_end_time.isoformat()
        self.pipeline_metadata["total_execution_time_seconds"] = (
            self.pipeline_end_time - self.pipeline_start_time
        ).total_seconds()
    
    def save_phase_results(self) -> Dict[str, str]:
        """フェーズ別に結果を保存"""
        saved_files = {}
        
        # 実行されたコンポーネントのログを処理
        executed_components = set()
        for log in self.execution_logs:
            if log.component_name == "Phase1Component":
                files = self._save_phase1_results(log)
                saved_files.update(files)
                executed_components.add("Phase1Component")
            elif log.component_name == "USDAQueryComponent":
                files = self._save_usda_query_results(log)
                saved_files.update(files)
                executed_components.add("USDAQueryComponent")
            elif log.component_name == "Phase2Component":
                files = self._save_phase2_results(log)
                saved_files.update(files)
                executed_components.add("Phase2Component")
            elif log.component_name == "NutritionCalculationComponent":
                files = self._save_nutrition_results(log)
                saved_files.update(files)
                executed_components.add("NutritionCalculationComponent")
        
        # 未実装/未実行のコンポーネントにプレースホルダーファイルを作成
        if "Phase2Component" not in executed_components:
            placeholder_log = DetailedExecutionLog("Phase2Component", f"{self.analysis_id}_phase2_placeholder")
            placeholder_log.input_data = {"note": "Phase2Component not yet implemented"}
            placeholder_log.output_data = {"note": "Phase2Component not yet implemented"}
            placeholder_log.finalize()
            files = self._save_phase2_results(placeholder_log)
            saved_files.update(files)
        
        if "NutritionCalculationComponent" not in executed_components:
            placeholder_log = DetailedExecutionLog("NutritionCalculationComponent", f"{self.analysis_id}_nutrition_placeholder")
            placeholder_log.input_data = {"note": "NutritionCalculationComponent not yet implemented"}
            placeholder_log.output_data = {"note": "NutritionCalculationComponent not yet implemented"}
            placeholder_log.finalize()
            files = self._save_nutrition_results(placeholder_log)
            saved_files.update(files)
        
        # パイプライン全体のサマリーを保存
        summary_files = self._save_pipeline_summary()
        saved_files.update(summary_files)
        
        return saved_files
    
    def _save_phase1_results(self, log: DetailedExecutionLog) -> Dict[str, str]:
        """Phase1の結果を保存"""
        files = {}
        
        # 1. JSON形式の入出力データ
        input_output_file = self.phase1_dir / "input_output.json"
        with open(input_output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "input_data": log.input_data,
                "output_data": log.output_data,
                "execution_time_seconds": log.get_execution_time()
            }, f, indent=2, ensure_ascii=False)
        files["phase1_input_output"] = str(input_output_file)
        
        # 2. プロンプトと推論理由のマークダウン
        prompts_md_file = self.phase1_dir / "prompts_and_reasoning.md"
        prompts_content = self._generate_phase1_prompts_md(log)
        with open(prompts_md_file, 'w', encoding='utf-8') as f:
            f.write(prompts_content)
        files["phase1_prompts_md"] = str(prompts_md_file)
        
        # 3. 検出された料理・食材のテキスト
        detected_items_file = self.phase1_dir / "detected_items.txt"
        detected_content = self._generate_phase1_detected_items_txt(log)
        with open(detected_items_file, 'w', encoding='utf-8') as f:
            f.write(detected_content)
        files["phase1_detected_txt"] = str(detected_items_file)
        
        return files
    
    def _save_usda_query_results(self, log: DetailedExecutionLog) -> Dict[str, str]:
        """USDA Queryの結果を保存"""
        files = {}
        
        # 1. JSON形式の入出力データ
        input_output_file = self.usda_query_dir / "input_output.json"
        with open(input_output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "input_data": log.input_data,
                "output_data": log.output_data,
                "execution_time_seconds": log.get_execution_time()
            }, f, indent=2, ensure_ascii=False)
        files["usda_input_output"] = str(input_output_file)
        
        # 2. 検索結果の詳細マークダウン
        search_results_md_file = self.usda_query_dir / "search_results.md"
        search_content = self._generate_usda_search_results_md(log)
        with open(search_results_md_file, 'w', encoding='utf-8') as f:
            f.write(search_content)
        files["usda_search_md"] = str(search_results_md_file)
        
        # 3. マッチ詳細のテキスト
        match_details_file = self.usda_query_dir / "match_details.txt"
        match_content = self._generate_usda_match_details_txt(log)
        with open(match_details_file, 'w', encoding='utf-8') as f:
            f.write(match_content)
        files["usda_match_txt"] = str(match_details_file)
        
        return files
    
    def _save_phase2_results(self, log: DetailedExecutionLog) -> Dict[str, str]:
        """Phase2の結果を保存（将来実装用）"""
        files = {}
        
        # 1. JSON形式の入出力データ
        input_output_file = self.phase2_dir / "input_output.json"
        with open(input_output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "input_data": log.input_data,
                "output_data": log.output_data,
                "execution_time_seconds": log.get_execution_time(),
                "note": "Phase2Component is not yet implemented"
            }, f, indent=2, ensure_ascii=False)
        files["phase2_input_output"] = str(input_output_file)
        
        # 2. 戦略決定のマークダウン
        strategy_md_file = self.phase2_dir / "strategy_decisions.md"
        with open(strategy_md_file, 'w', encoding='utf-8') as f:
            f.write("# Phase2 Strategy Decisions\n\n*Phase2Component is not yet implemented*\n")
        files["phase2_strategy_md"] = str(strategy_md_file)
        
        # 3. 選択項目のテキスト
        selected_items_file = self.phase2_dir / "selected_items.txt"
        with open(selected_items_file, 'w', encoding='utf-8') as f:
            f.write("Phase2Component is not yet implemented\n")
        files["phase2_items_txt"] = str(selected_items_file)
        
        return files
    
    def _save_nutrition_results(self, log: DetailedExecutionLog) -> Dict[str, str]:
        """栄養計算の結果を保存（将来実装用）"""
        files = {}
        
        # 1. JSON形式の入出力データ
        input_output_file = self.nutrition_dir / "input_output.json"
        with open(input_output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "input_data": log.input_data,
                "output_data": log.output_data,
                "execution_time_seconds": log.get_execution_time(),
                "note": "NutritionCalculationComponent is not yet implemented"
            }, f, indent=2, ensure_ascii=False)
        files["nutrition_input_output"] = str(input_output_file)
        
        # 2. 計算式のマークダウン
        formulas_md_file = self.nutrition_dir / "calculation_formulas.md"
        with open(formulas_md_file, 'w', encoding='utf-8') as f:
            f.write("# Nutrition Calculation Formulas\n\n*NutritionCalculationComponent is not yet implemented*\n")
        files["nutrition_formulas_md"] = str(formulas_md_file)
        
        # 3. 栄養サマリーのテキスト
        summary_txt_file = self.nutrition_dir / "nutrition_summary.txt"
        with open(summary_txt_file, 'w', encoding='utf-8') as f:
            f.write("NutritionCalculationComponent is not yet implemented\n")
        files["nutrition_summary_txt"] = str(summary_txt_file)
        
        return files
    
    def _save_pipeline_summary(self) -> Dict[str, str]:
        """パイプライン全体のサマリーを保存"""
        files = {}
        
        # 1. パイプラインサマリーJSON
        summary_file = self.analysis_dir / "pipeline_summary.json"
        summary_data = {
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp,
            "pipeline_metadata": self.pipeline_metadata,
            "execution_summary": {
                log.component_name: {
                    "execution_time": log.get_execution_time(),
                    "success": len(log.errors) == 0,
                    "warnings_count": len(log.warnings),
                    "errors_count": len(log.errors)
                }
                for log in self.execution_logs
            },
            "final_result": self.final_result
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        files["pipeline_summary"] = str(summary_file)
        
        # 2. 完全な詳細ログJSON
        complete_log_file = self.analysis_dir / "complete_analysis_log.json"
        complete_data = {
            "pipeline_metadata": self.pipeline_metadata,
            "execution_logs": [log.to_dict() for log in self.execution_logs],
            "final_result": self.final_result,
            "summary": {
                "total_components": len(self.execution_logs),
                "total_warnings": sum(len(log.warnings) for log in self.execution_logs),
                "total_errors": sum(len(log.errors) for log in self.execution_logs),
                "average_confidence": self._calculate_average_confidence()
            }
        }
        
        with open(complete_log_file, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, indent=2, ensure_ascii=False)
        files["complete_log"] = str(complete_log_file)
        
        return files
    
    def _generate_phase1_prompts_md(self, log: DetailedExecutionLog) -> str:
        """Phase1のプロンプトと推論理由のマークダウンを生成"""
        content = f"""# Phase1: 画像分析 - プロンプトと推論

## 実行情報
- 実行ID: {log.execution_id}
- 開始時刻: {log.start_time.isoformat()}
- 終了時刻: {log.end_time.isoformat() if log.end_time else 'N/A'}
- 実行時間: {log.get_execution_time():.2f}秒

## 使用されたプロンプト

"""
        
        # プロンプト情報
        for prompt_name, prompt_data in log.prompts_used.items():
            content += f"### {prompt_name.replace('_', ' ').title()}\n\n"
            content += f"**タイムスタンプ**: {prompt_data['timestamp']}\n\n"
            content += f"```\n{prompt_data['content']}\n```\n\n"
            
            if prompt_data.get('variables'):
                content += f"**変数**:\n"
                for var_name, var_value in prompt_data['variables'].items():
                    content += f"- {var_name}: {var_value}\n"
                content += "\n"
        
        # 推論理由
        content += "## AI推論の詳細\n\n"
        
        # 料理識別の推論
        dish_reasoning = [r for r in log.reasoning.items() if r[0].startswith('dish_identification_')]
        if dish_reasoning:
            content += "### 料理識別の推論\n\n"
            for decision_point, reasoning_data in dish_reasoning:
                dish_num = decision_point.split('_')[-1]
                content += f"**料理 {dish_num}**:\n"
                content += f"- 推論: {reasoning_data['reason']}\n"
                content += f"- 信頼度: {reasoning_data['confidence']}\n"
                content += f"- タイムスタンプ: {reasoning_data['timestamp']}\n\n"
        
        # 食材選択の推論
        ingredient_reasoning = [r for r in log.reasoning.items() if r[0].startswith('ingredient_selection_')]
        if ingredient_reasoning:
            content += "### 食材選択の推論\n\n"
            for decision_point, reasoning_data in ingredient_reasoning:
                content += f"**{decision_point.replace('_', ' ').title()}**:\n"
                content += f"- 推論: {reasoning_data['reason']}\n"
                content += f"- 信頼度: {reasoning_data['confidence']}\n"
                content += f"- タイムスタンプ: {reasoning_data['timestamp']}\n\n"
        
        # 信頼度計算の推論
        confidence_reasoning = [r for r in log.reasoning.items() if r[0].startswith('confidence_')]
        if confidence_reasoning:
            content += "### 信頼度計算の詳細\n\n"
            for decision_point, reasoning_data in confidence_reasoning:
                content += f"**{decision_point.replace('_', ' ').title()}**:\n"
                content += f"- 推論: {reasoning_data['reason']}\n"
                content += f"- 信頼度: {reasoning_data['confidence']}\n"
                content += f"- タイムスタンプ: {reasoning_data['timestamp']}\n\n"
        
        # 警告とエラー
        if log.warnings:
            content += "## 警告\n\n"
            for warning in log.warnings:
                content += f"- {warning['message']} (at {warning['timestamp']})\n"
            content += "\n"
        
        if log.errors:
            content += "## エラー\n\n"
            for error in log.errors:
                content += f"- {error['message']} (at {error['timestamp']})\n"
            content += "\n"
        
        return content
    
    def _generate_phase1_detected_items_txt(self, log: DetailedExecutionLog) -> str:
        """Phase1で検出された料理・食材のテキストを生成（USDA検索特化）"""
        content = f"Phase1 検出結果 - {log.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "=" * 60 + "\n\n"
        
        if 'output_data' in log.output_data and 'dishes' in log.output_data['output_data']:
            dishes = log.output_data['output_data']['dishes']
            content += f"検出された料理数: {len(dishes)}\n\n"
            
            for i, dish in enumerate(dishes, 1):
                content += f"料理 {i}: {dish['dish_name']}\n"
                content += f"  食材数: {len(dish['ingredients'])}\n"
                content += "  食材詳細:\n"
                
                for j, ingredient in enumerate(dish['ingredients'], 1):
                    content += f"    {j}. {ingredient['ingredient_name']}\n"
                content += "\n"
        
        # USDA検索準備情報
        if 'usda_search_terms' in log.processing_details:
            search_terms = log.processing_details['usda_search_terms']
            content += f"USDA検索語彙 ({len(search_terms)}個):\n"
            for i, term in enumerate(search_terms, 1):
                content += f"  {i}. {term}\n"
            content += "\n"
        
        # 信頼度スコア
        if log.confidence_scores:
            content += "信頼度スコア:\n"
            for metric, score in log.confidence_scores.items():
                content += f"  {metric}: {score:.3f}\n"
            content += "\n"
        
        # 処理詳細
        if log.processing_details:
            content += "処理詳細:\n"
            for detail_key, detail_value in log.processing_details.items():
                if detail_key == 'usda_search_terms':
                    continue  # 既に上で表示済み
                if isinstance(detail_value, (dict, list)):
                    content += f"  {detail_key}: {json.dumps(detail_value, ensure_ascii=False)}\n"
                else:
                    content += f"  {detail_key}: {detail_value}\n"
        
        return content
    
    def _generate_usda_search_results_md(self, log: DetailedExecutionLog) -> str:
        """USDA検索結果のマークダウンを生成"""
        content = f"""# USDA Query: データベース検索結果

## 実行情報
- 実行ID: {log.execution_id}
- 開始時刻: {log.start_time.isoformat()}
- 終了時刻: {log.end_time.isoformat() if log.end_time else 'N/A'}
- 実行時間: {log.get_execution_time():.2f}秒

## 検索概要

"""
        
        # 検索サマリー
        if 'search_summary' in log.processing_details:
            summary = log.processing_details['search_summary']
            content += f"- 総検索数: {summary.get('total_searches', 0)}\n"
            content += f"- 成功マッチ数: {summary.get('successful_matches', 0)}\n"
            content += f"- 失敗数: {summary.get('failed_searches', 0)}\n"
            content += f"- マッチ率: {summary.get('match_rate_percent', 0)}%\n\n"
        
        # 検索品質評価
        quality_reasoning = [r for r in log.reasoning.items() if 'search_quality' in r[0]]
        if quality_reasoning:
            content += "## 検索品質評価\n\n"
            for _, reasoning_data in quality_reasoning:
                content += f"**評価**: {reasoning_data['reason']}\n"
                content += f"**信頼度**: {reasoning_data['confidence']}\n\n"
        
        # 個別検索結果
        content += "## 個別検索結果\n\n"
        
        # 検索語彙ごとの結果
        search_terms = log.processing_details.get('search_terms', [])
        for i, term in enumerate(search_terms):
            content += f"### 検索 {i+1}: {term}\n\n"
            
            # 検索結果数
            results_count_key = f"search_{i}_results_count"
            if results_count_key in log.processing_details:
                results_count = log.processing_details[results_count_key]
                content += f"**検索結果数**: {results_count}\n"
            
            # 選択されたアイテム
            fdc_id_key = f"search_{i}_selected_fdc_id"
            desc_key = f"search_{i}_selected_description"
            data_type_key = f"search_{i}_data_type"
            
            if fdc_id_key in log.processing_details:
                content += f"**選択されたアイテム**:\n"
                content += f"- FDC ID: {log.processing_details[fdc_id_key]}\n"
                content += f"- 説明: {log.processing_details[desc_key]}\n"
                content += f"- データタイプ: {log.processing_details[data_type_key]}\n"
            
            # マッチ推論
            match_reasoning = [r for r in log.reasoning.items() if f"match_selection_{i}" in r[0]]
            if match_reasoning:
                for _, reasoning_data in match_reasoning:
                    content += f"**選択理由**: {reasoning_data['reason']}\n"
                    content += f"**マッチ信頼度**: {reasoning_data['confidence']}\n"
            
            # マッチしなかった場合の理由
            no_match_reasoning = [r for r in log.reasoning.items() if f"no_match_{i}" in r[0]]
            if no_match_reasoning:
                for _, reasoning_data in no_match_reasoning:
                    content += f"**マッチしなかった理由**: {reasoning_data['reason']}\n"
            
            content += "\n"
        
        return content
    
    def _generate_usda_match_details_txt(self, log: DetailedExecutionLog) -> str:
        """USDAマッチ詳細のテキストを生成"""
        content = f"USDA マッチ詳細 - {log.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "=" * 60 + "\n\n"
        
        # 検索語彙とマッチ結果の対応表
        search_terms = log.processing_details.get('search_terms', [])
        ingredient_names = log.processing_details.get('ingredient_names', [])
        dish_names = log.processing_details.get('dish_names', [])
        
        content += f"検索対象:\n"
        content += f"  食材名: {len(ingredient_names)}個\n"
        for name in ingredient_names:
            content += f"    - {name}\n"
        content += f"  料理名: {len(dish_names)}個\n"
        for name in dish_names:
            content += f"    - {name}\n"
        content += "\n"
        
        content += "マッチ結果:\n"
        for i, term in enumerate(search_terms):
            content += f"  {i+1}. 検索語: {term}\n"
            
            # 結果の詳細
            fdc_id_key = f"search_{i}_selected_fdc_id"
            desc_key = f"search_{i}_selected_description"
            data_type_key = f"search_{i}_data_type"
            nutrients_key = f"search_{i}_nutrients_count"
            
            if fdc_id_key in log.processing_details:
                content += f"     → マッチ: {log.processing_details[desc_key]}\n"
                content += f"     → FDC ID: {log.processing_details[fdc_id_key]}\n"
                content += f"     → データタイプ: {log.processing_details[data_type_key]}\n"
                content += f"     → 栄養素数: {log.processing_details.get(nutrients_key, 'N/A')}\n"
            else:
                content += f"     → マッチなし\n"
            content += "\n"
        
        # 信頼度情報
        if log.confidence_scores:
            content += "信頼度スコア:\n"
            for metric, score in log.confidence_scores.items():
                content += f"  {metric}: {score:.3f}\n"
        
        return content
    
    def _calculate_average_confidence(self) -> float:
        """平均信頼度を計算"""
        all_scores = []
        for log in self.execution_logs:
            all_scores.extend(log.confidence_scores.values())
        
        if all_scores:
            return sum(all_scores) / len(all_scores)
        return 0.0
    
    def get_analysis_folder_path(self) -> str:
        """解析フォルダパスを取得"""
        return str(self.analysis_dir) 