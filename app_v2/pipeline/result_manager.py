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
        self.nutrition_search_dir = self.analysis_dir / "nutrition_search_query"
        self.phase2_dir = self.analysis_dir / "phase2"
        self.nutrition_dir = self.analysis_dir / "nutrition_calculation"
        
        for phase_dir in [self.phase1_dir, self.nutrition_search_dir, self.phase2_dir, self.nutrition_dir]:
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
            elif log.component_name in ["USDAQueryComponent", "LocalNutritionSearchComponent", "ElasticsearchNutritionSearchComponent"]:
                files = self._save_nutrition_search_results(log)
                saved_files.update(files)
                executed_components.add(log.component_name)
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
    
    def _save_nutrition_search_results(self, log: DetailedExecutionLog) -> Dict[str, str]:
        """栄養データベース検索の結果を保存（USDAQueryComponent、LocalNutritionSearchComponent、ElasticsearchNutritionSearchComponent対応）"""
        files = {}
        
        # 検索方法の判定
        search_method = "unknown"
        db_source = "unknown"
        
        if log.component_name == "USDAQueryComponent":
            search_method = "usda_api"
            db_source = "usda_database"
        elif log.component_name == "LocalNutritionSearchComponent":
            search_method = "local_search"
            db_source = "local_nutrition_database"
        elif log.component_name == "ElasticsearchNutritionSearchComponent":
            search_method = "elasticsearch_advanced"
            db_source = "elasticsearch_food_nutrition_v2"
        
        # 1. JSON形式の入出力データ（検索方法情報を含む）
        input_output_file = self.nutrition_search_dir / "input_output.json"
        with open(input_output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "input_data": log.input_data,
                "output_data": log.output_data,
                "execution_time_seconds": log.get_execution_time(),
                "search_metadata": {
                    "component_name": log.component_name,
                    "search_method": search_method,
                    "database_source": db_source,
                    "timestamp": log.execution_end_time.isoformat() if log.execution_end_time else None
                }
            }, f, indent=2, ensure_ascii=False)
        files["nutrition_search_input_output"] = str(input_output_file)
        
        # 2. 検索結果の詳細マークダウン
        search_results_md_file = self.nutrition_search_dir / "search_results.md"
        search_content = self._generate_nutrition_search_results_md(log, search_method, db_source)
        with open(search_results_md_file, 'w', encoding='utf-8') as f:
            f.write(search_content)
        files["nutrition_search_results_md"] = str(search_results_md_file)
        
        # 3. マッチ詳細のテキスト
        match_details_file = self.nutrition_search_dir / "match_details.txt"
        match_content = self._generate_nutrition_match_details_txt(log, search_method, db_source)
        with open(match_details_file, 'w', encoding='utf-8') as f:
            f.write(match_content)
        files["nutrition_search_match_details"] = str(match_details_file)
        
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
                "total_errors": sum(len(log.errors) for log in self.execution_logs)
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
- 開始時刻: {log.execution_start_time.isoformat()}
- 終了時刻: {log.execution_end_time.isoformat() if log.execution_end_time else 'N/A'}
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
                content += f"- タイムスタンプ: {reasoning_data['timestamp']}\n\n"
        
        # 食材選択の推論
        ingredient_reasoning = [r for r in log.reasoning.items() if r[0].startswith('ingredient_selection_')]
        if ingredient_reasoning:
            content += "### 食材選択の推論\n\n"
            for decision_point, reasoning_data in ingredient_reasoning:
                content += f"**{decision_point.replace('_', ' ').title()}**:\n"
                content += f"- 推論: {reasoning_data['reason']}\n"
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
        content = f"Phase1 検出結果 - {log.execution_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
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
    
    def _generate_nutrition_search_results_md(self, log: DetailedExecutionLog, search_method: str, db_source: str) -> str:
        """栄養データベース検索結果のマークダウンを生成（USDA/ローカル対応）"""
        content = []
        
        content.append(f"# Nutrition Database Search Results")
        content.append(f"")
        content.append(f"**Search Method:** {search_method}")
        content.append(f"**Database Source:** {db_source}")
        content.append(f"**Component:** {log.component_name}")
        content.append(f"**Execution Time:** {log.get_execution_time():.3f} seconds")
        content.append(f"**Timestamp:** {log.execution_start_time.isoformat()}")
        content.append(f"")
        
        # 入力データの表示
        if log.input_data:
            content.append(f"## Input Data")
            if 'ingredient_names' in log.input_data:
                ingredients = log.input_data['ingredient_names']
                content.append(f"**Ingredients ({len(ingredients)}):** {', '.join(ingredients)}")
            if 'dish_names' in log.input_data:
                dishes = log.input_data['dish_names']
                content.append(f"**Dishes ({len(dishes)}):** {', '.join(dishes)}")
            content.append(f"")
        
        # 出力データの表示
        if log.output_data and 'matches' in log.output_data:
            matches = log.output_data['matches']
            content.append(f"## Search Results")
            content.append(f"**Total Matches:** {len(matches)}")
            content.append(f"")
            
            for i, (search_term, match_data) in enumerate(matches.items(), 1):
                # 🎯 修正: より分かりやすい表示名称
                content.append(f"### {i}. Query: \"{search_term}\"")
                if isinstance(match_data, dict):
                    # 🎯 修正: dict形式の場合、キーに応じてアクセス
                    fdc_id = match_data.get('fdc_id', 0)
                    original_data = match_data.get('original_usda_data', {})
                    elasticsearch_id = original_data.get('fdc_id') if isinstance(original_data, dict) else None
                    
                    display_id = elasticsearch_id if elasticsearch_id else fdc_id
                    content.append(f"**ID:** {display_id if display_id != 0 else 'N/A'}")
                    content.append(f"**Matched Food Name:** {match_data.get('description', 'N/A')}")  # 🎯 修正
                    
                    # 🎯 修正: DB Typeを適切に表示
                    data_type = match_data.get('data_type', 'N/A')
                    if search_method == "elasticsearch_advanced":
                        if data_type.startswith('Local '):
                            db_category = data_type.replace('Local ', '')  # Local Dish → Dish
                            content.append(f"**DB Type:** {db_category}")
                        else:
                            content.append(f"**DB Type:** {data_type}")
                    else:
                        content.append(f"**Data Type:** {data_type}")
                    
                    if 'food_nutrients' in match_data and match_data['food_nutrients']:
                        content.append(f"**Nutrients ({len(match_data['food_nutrients'])}):**")
                        for nutrient in match_data['food_nutrients'][:5]:  # 最初の5つだけ表示
                            if isinstance(nutrient, dict):
                                name = nutrient.get('name', 'Unknown')
                                amount = nutrient.get('amount', 0)
                                unit = nutrient.get('unit_name', '')
                                content.append(f"  - {name}: {amount} {unit}")
                        if len(match_data['food_nutrients']) > 5:
                            content.append(f"  - ... and {len(match_data['food_nutrients']) - 5} more nutrients")
                else:
                    # 🎯 NutritionMatchオブジェクトの場合
                    content.append(f"**ID:** {getattr(match_data, 'id', 'N/A')}")
                    content.append(f"**Matched Food Name:** {getattr(match_data, 'description', 'N/A')}")  # 🎯 修正
                    
                    # 🎯 修正: DB Typeを適切に表示
                    data_type = getattr(match_data, 'data_type', 'N/A')
                    if search_method == "elasticsearch_advanced":
                        if data_type.startswith('Local '):
                            db_category = data_type.replace('Local ', '')  # Local Dish → Dish
                            content.append(f"**DB Type:** {db_category}")
                        else:
                            content.append(f"**DB Type:** {data_type}")
                    else:
                        content.append(f"**Data Type:** {data_type}")
                    
                    nutrients = getattr(match_data, 'nutrients', [])
                    if nutrients:
                        content.append(f"**Nutrients ({len(nutrients)}):**")
                        for nutrient in nutrients[:5]:  # 最初の5つだけ表示
                            if hasattr(nutrient, 'name'):
                                name = getattr(nutrient, 'name', 'Unknown')
                                amount = getattr(nutrient, 'amount', 0)
                                unit = getattr(nutrient, 'unit_name', '')
                                content.append(f"  - {name}: {amount} {unit}")
                        if len(nutrients) > 5:
                            content.append(f"  - ... and {len(nutrients) - 5} more nutrients")
                content.append(f"")
        
        # 検索サマリー
        if log.output_data and 'search_summary' in log.output_data:
            summary = log.output_data['search_summary']
            content.append(f"## Search Summary")
            content.append(f"**Total Searches:** {summary.get('total_searches', 0)}")
            content.append(f"**Successful Matches:** {summary.get('successful_matches', 0)}")
            content.append(f"**Failed Searches:** {summary.get('failed_searches', 0)}")
            content.append(f"**Match Rate:** {summary.get('match_rate_percent', 0)}%")
            content.append(f"**Search Method:** {summary.get('search_method', 'unknown')}")
            
            if search_method == "local_search":
                content.append(f"**Database Items:** {summary.get('total_database_items', 0)}")
        
        # 検索理由の表示
        if hasattr(log, 'reasoning') and log.reasoning:
            content.append(f"")
            content.append(f"## Search Reasoning")
            for key, reasoning in log.reasoning.items():
                content.append(f"**{key}:** {reasoning}")
        
        return "\n".join(content)
    
    def _generate_nutrition_match_details_txt(self, log: DetailedExecutionLog, search_method: str, db_source: str) -> str:
        """栄養データベース検索のマッチ詳細テキストを生成（USDA/ローカル対応）"""
        lines = []
        
        lines.append(f"Nutrition Database Search Match Details")
        lines.append(f"=" * 50)
        lines.append(f"Search Method: {search_method}")
        lines.append(f"Database Source: {db_source}")
        lines.append(f"Component: {log.component_name}")
        lines.append(f"Execution Time: {log.get_execution_time():.3f} seconds")
        lines.append(f"Timestamp: {log.execution_start_time.isoformat()}")
        lines.append(f"")
        
        if log.output_data and 'matches' in log.output_data:
            matches = log.output_data['matches']
            lines.append(f"Total Matches: {len(matches)}")
            lines.append(f"")
            
            for search_term, match_data in matches.items():
                # 🎯 修正: より分かりやすい表示名称
                lines.append(f"Query: \"{search_term}\"")
                lines.append(f"-" * 30)
                
                if isinstance(match_data, dict):
                    # 🎯 修正: dict形式の場合の処理
                    fdc_id = match_data.get('fdc_id', 0)
                    original_data = match_data.get('original_usda_data', {})
                    elasticsearch_id = original_data.get('fdc_id') if isinstance(original_data, dict) else None
                    
                    display_id = elasticsearch_id if elasticsearch_id else fdc_id
                    lines.append(f"  ID: {display_id if display_id != 0 else 'N/A'}")
                    lines.append(f"  Matched Food Name: {match_data.get('description', 'N/A')}")  # 🎯 修正
                    
                    # 🎯 修正: DB Typeを適切に表示
                    data_type = match_data.get('data_type', 'N/A')
                    if search_method == "elasticsearch_advanced":
                        if data_type.startswith('Local '):
                            db_category = data_type.replace('Local ', '')  # Local Dish → Dish
                            lines.append(f"  DB Type: {db_category}")
                        else:
                            lines.append(f"  DB Type: {data_type}")
                    else:
                        lines.append(f"  Data Type: {data_type}")
                        
                    lines.append(f"  Score: {match_data.get('score', 'N/A')}")
                    
                    if 'food_nutrients' in match_data and match_data['food_nutrients']:
                        lines.append(f"  Nutrients ({len(match_data['food_nutrients'])}):")
                        for nutrient in match_data['food_nutrients']:
                            if isinstance(nutrient, dict):
                                name = nutrient.get('name', 'Unknown')
                                amount = nutrient.get('amount', 0)
                                unit = nutrient.get('unit_name', '')
                                lines.append(f"    - {name}: {amount} {unit}")
                    
                    if 'original_usda_data' in match_data:
                        original_data = match_data['original_usda_data']
                        if isinstance(original_data, dict):
                            lines.append(f"  Original Data Source: {original_data.get('source', 'Unknown')}")
                            if search_method == "local_search":
                                lines.append(f"  Local DB Source: {original_data.get('db_source', 'Unknown')}")
                else:
                    # 🎯 NutritionMatchオブジェクトの場合
                    lines.append(f"  ID: {getattr(match_data, 'id', 'N/A')}")
                    lines.append(f"  Matched Food Name: {getattr(match_data, 'description', 'N/A')}")  # 🎯 修正
                    
                    # 🎯 修正: DB Typeを適切に表示
                    data_type = getattr(match_data, 'data_type', 'N/A')
                    if search_method == "elasticsearch_advanced":
                        if data_type.startswith('Local '):
                            db_category = data_type.replace('Local ', '')  # Local Dish → Dish
                            lines.append(f"  DB Type: {db_category}")
                        else:
                            lines.append(f"  DB Type: {data_type}")
                    else:
                        lines.append(f"  Data Type: {data_type}")
                        
                    lines.append(f"  Score: {getattr(match_data, 'score', 'N/A')}")
                    
                    nutrients = getattr(match_data, 'nutrients', [])
                    if nutrients:
                        lines.append(f"  Nutrients ({len(nutrients)}):")
                        for nutrient in nutrients:
                            if hasattr(nutrient, 'name'):
                                name = getattr(nutrient, 'name', 'Unknown')
                                amount = getattr(nutrient, 'amount', 0)
                                unit = getattr(nutrient, 'unit_name', '')
                                lines.append(f"    - {name}: {amount} {unit}")
                    
                    original_data = getattr(match_data, 'original_data', {})
                    if original_data:
                        lines.append(f"  Original Data Source: {original_data.get('source', 'Unknown')}")
                        if search_method == "local_search":
                            lines.append(f"  Local DB Source: {original_data.get('db_source', 'Unknown')}")
                
                lines.append(f"")
        
        # 検索統計
        if log.output_data and 'search_summary' in log.output_data:
            summary = log.output_data['search_summary']
            lines.append(f"Search Statistics:")
            lines.append(f"  Total Searches: {summary.get('total_searches', 0)}")
            lines.append(f"  Successful Matches: {summary.get('successful_matches', 0)}")
            lines.append(f"  Failed Searches: {summary.get('failed_searches', 0)}")
            lines.append(f"  Match Rate: {summary.get('match_rate_percent', 0)}%")
            
            if search_method == "local_search":
                lines.append(f"  Total Database Items: {summary.get('total_database_items', 0)}")
        
        return "\n".join(lines)
    
    def get_analysis_folder_path(self) -> str:
        """解析フォルダパスを取得"""
        return str(self.analysis_dir) 