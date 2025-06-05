from typing import Optional, List, Dict

from .base import BaseComponent
from ..models.usda_models import USDAQueryInput, USDAQueryOutput, USDAMatch, USDANutrient
from ..services.usda_service import USDAService
from ..config import get_settings


class USDAQueryComponent(BaseComponent[USDAQueryInput, USDAQueryOutput]):
    """
    USDA照合コンポーネント
    
    食材名をUSDAデータベースで検索し、最適なマッチを見つけます。
    """
    
    def __init__(self, usda_service: Optional[USDAService] = None):
        super().__init__("USDAQueryComponent")
        
        # USDAServiceの初期化
        if usda_service is None:
            settings = get_settings()
            self.usda_service = USDAService()
        else:
            self.usda_service = usda_service
    
    async def process(self, input_data: USDAQueryInput) -> USDAQueryOutput:
        """
        USDA照合の主処理
        
        Args:
            input_data: USDAQueryInput (ingredient_names, dish_names)
            
        Returns:
            USDAQueryOutput: 照合結果
        """
        self.logger.info(f"Starting USDA query for {len(input_data.get_all_search_terms())} terms")
        
        search_terms = input_data.get_all_search_terms()
        
        # 検索対象の詳細をログに記録
        self.log_processing_detail("search_terms", search_terms)
        self.log_processing_detail("ingredient_names", input_data.ingredient_names)
        self.log_processing_detail("dish_names", input_data.dish_names)
        self.log_processing_detail("total_search_terms", len(search_terms))
        
        matches = {}
        warnings = []
        errors = []
        
        successful_matches = 0
        total_searches = len(search_terms)
        
        # 各検索語彙について照合を実行
        for search_index, search_term in enumerate(search_terms):
            self.logger.debug(f"Searching USDA for: {search_term}")
            
            # 検索開始をログ
            self.log_processing_detail(f"search_{search_index}_term", search_term)
            self.log_processing_detail(f"search_{search_index}_start", f"Starting USDA search for '{search_term}'")
            
            try:
                # USDAサービスで検索
                usda_results = await self.usda_service.search_foods(
                    query=search_term,
                    data_types=["Foundation", "SR Legacy", "FNDDS", "Branded"],
                    page_size=5
                )
                
                # 検索結果の詳細をログ
                self.log_processing_detail(f"search_{search_index}_results_count", len(usda_results))
                
                if usda_results:
                    # 最も適切なマッチを選択
                    best_match = usda_results[0]
                    
                    # マッチ選択の推論理由をログ
                    self.log_reasoning(
                        f"match_selection_{search_index}",
                        f"Selected USDA item '{best_match.description}' (FDC: {best_match.fdc_id}) for search term '{search_term}' based on description similarity and data type '{best_match.data_type}'"
                    )
                    
                    # 詳細なマッチ情報をログ
                    self.log_processing_detail(f"search_{search_index}_selected_fdc_id", best_match.fdc_id)
                    self.log_processing_detail(f"search_{search_index}_selected_description", best_match.description)
                    self.log_processing_detail(f"search_{search_index}_data_type", best_match.data_type)
                    self.log_processing_detail(f"search_{search_index}_nutrients_count", len(best_match.food_nutrients))
                    
                    # USDANutrientオブジェクトに変換
                    nutrients = []
                    for nutrient in best_match.food_nutrients:
                        nutrients.append(USDANutrient(
                            name=nutrient.name,
                            amount=nutrient.amount,
                            unit_name=nutrient.unit_name,
                            nutrient_id=nutrient.nutrient_id,
                            nutrient_number=nutrient.nutrient_number
                        ))
                    
                    # USDAMatchオブジェクトを作成
                    match = USDAMatch(
                        fdc_id=best_match.fdc_id,
                        description=best_match.description,
                        data_type=best_match.data_type,
                        brand_owner=best_match.brand_owner,
                        ingredients_text=best_match.ingredients_text,
                        food_nutrients=nutrients,
                        score=best_match.score,
                        original_usda_data=best_match.original_data
                    )
                    
                    matches[search_term] = match
                    successful_matches += 1
                    
                    self.logger.debug(f"Found match for '{search_term}': FDC ID {best_match.fdc_id}")
                    
                else:
                    # マッチしなかった理由をログ
                    self.log_reasoning(
                        f"no_match_{search_index}",
                        f"No USDA match found for '{search_term}' - may be too specific, contain typos, or be a regional/non-standard food name"
                    )
                    self.logger.warning(f"No USDA match found for: {search_term}")
                    warnings.append(f"No USDA match found for: {search_term}")
                    
            except Exception as e:
                error_msg = f"USDA search error for '{search_term}': {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                
                # エラーの詳細をログ
                self.log_reasoning(
                    f"search_error_{search_index}",
                    f"USDA API error for '{search_term}': {str(e)}"
                )
        
        # 検索サマリーを作成
        search_summary = {
            "total_searches": total_searches,
            "successful_matches": successful_matches,
            "failed_searches": total_searches - successful_matches,
            "match_rate_percent": round((successful_matches / total_searches) * 100, 1) if total_searches > 0 else 0
        }
        
        # 全体的な検索成功率をログ
        overall_success_rate = successful_matches / total_searches if total_searches > 0 else 0
        self.log_processing_detail("search_summary", search_summary)
        
        # 検索品質の評価をログ
        if overall_success_rate >= 0.8:
            self.log_reasoning("search_quality", "Excellent search results with high match rate")
        elif overall_success_rate >= 0.6:
            self.log_reasoning("search_quality", "Good search results with acceptable match rate")
        elif overall_success_rate >= 0.4:
            self.log_reasoning("search_quality", "Moderate search results, some items may need manual review")
        else:
            self.log_reasoning("search_quality", "Poor search results, many items not found in USDA database")
        
        result = USDAQueryOutput(
            matches=matches,
            search_summary=search_summary,
            warnings=warnings if warnings else None,
            errors=errors if errors else None
        )
        
        self.logger.info(f"USDA query completed: {successful_matches}/{total_searches} matches ({result.get_match_rate():.1%})")
        
        return result 