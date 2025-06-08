"""
Elasticsearchコンポーネントデバッグ用スクリプト
"""
import asyncio
from app_v2.components.elasticsearch_nutrition_search_component import ElasticsearchNutritionSearchComponent
from app_v2.models.usda_models import USDAQueryInput

async def debug_component_output():
    """Elasticsearchコンポーネントの出力を詳細確認"""
    
    print("🔍 Elasticsearchコンポーネント詳細デバッグ")
    print("=" * 50)
    
    es_component = ElasticsearchNutritionSearchComponent()
    
    query = USDAQueryInput(
        ingredient_names=["chicken breast"],
        dish_names=[]
    )
    
    result = await es_component.process(query)
    
    print(f"結果の型: {type(result)}")
    print(f"結果の属性: {dir(result)}")
    
    print(f"\\nmatches属性の型: {type(result.matches)}")
    print(f"matches属性の内容: {result.matches}")
    
    if hasattr(result.matches, '__len__'):
        print(f"matches長さ: {len(result.matches)}")
    
    if hasattr(result.matches, '__iter__'):
        print("\\nmatches内容（最初の3件）:")
        for i, match in enumerate(result.matches):
            if i >= 3:
                break
            print(f"  {i}: {type(match)} - {match}")

if __name__ == "__main__":
    asyncio.run(debug_component_output()) 