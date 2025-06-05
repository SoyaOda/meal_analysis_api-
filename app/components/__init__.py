# app/components/__init__.py
"""
食事分析パイプラインコンポーネント

4つの主要フェーズをコンポーネントとして分離:
- Phase1Component: 画像分析
- USDAQueryComponent: データベース照合  
- Phase2Component: 計算戦略決定
- NutritionCalculationComponent: 栄養計算
"""

from .phase1_component import Phase1Component
from .usda_query_component import USDAQueryComponent
from .phase2_component import Phase2Component
from .nutrition_calculation_component import NutritionCalculationComponent
from .pipeline import MealAnalysisPipeline
from .types import *

__all__ = [
    'Phase1Component',
    'USDAQueryComponent', 
    'Phase2Component',
    'NutritionCalculationComponent',
    'MealAnalysisPipeline',
] 