#!/usr/bin/env python3
"""
栄養計算観点での適切性調査スクリプト
7つの問題ケースについて、より適切な検索結果があるか調べる
"""

from app_v2.components.elasticsearch_nutrition_search_component import ElasticsearchNutritionSearchComponent
import json

def investigate_nutrition_matches():
    # 検索コンポーネントを初期化
    search_component = ElasticsearchNutritionSearchComponent()
    
    # 7つの問題ケースと期待される栄養特性
    problem_cases = {
        'pasta salad dressing': {
            'expected': {'kcal': '400-600', 'fat': '40-60g', 'type': 'ドレッシング'},
            'current_issue': 'パスタサラダ全体がヒット（脂質過小評価）'
        },
        'Spanish Rice': {
            'expected': {'kcal': '130-150', 'carbs': '28-32g', 'type': '調理済み米'},
            'current_issue': '特定ブランド商品（カロリー過小評価）'
        },
        'glaze': {
            'expected': {'kcal': '200-300', 'carbs': '20-40g', 'type': 'グレーズ・ソース'},
            'current_issue': 'サーモン料理全体がヒット（糖質過小評価）'
        },
        'creamy sauce': {
            'expected': {'kcal': '300-400', 'fat': '30-40g', 'type': 'クリームソース'},
            'current_issue': '特定のチポトレソース（風味特性異なる）'
        },
        'ice': {
            'expected': {'kcal': '0', 'fat': '0g', 'type': '氷'},
            'current_issue': 'アイスクリームがヒット（全栄養素過大評価）'
        },
        'cheese': {
            'expected': {'kcal': '350-400', 'protein': '25g', 'fat': '28g', 'type': '一般チーズ'},
            'current_issue': 'ブレンドチーズ（脂質過小評価）'
        },
        'Taco': {
            'expected': {'kcal': '200-250', 'protein': '12-15g', 'fat': '10-15g', 'type': '肉入りタコス'},
            'current_issue': 'ベジタリアン代替品（全栄養素過小評価）'
        }
    }
    
    print('=== 栄養計算観点での適切性調査 ===\n')
    
    for case, info in problem_cases.items():
        print(f'🔍 検索語: "{case}"')
        print(f'期待栄養特性: {info["expected"]}')
        print(f'現在の問題: {info["current_issue"]}')
        print('-' * 70)
        
        # より多くの結果を取得して適切なものを探す
        from app_v2.models.nutrition_search_models import NutritionQueryInput
        query_input = NutritionQueryInput(search_terms=[case])
        
        # 非同期メソッドを同期的に実行
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result_output = loop.run_until_complete(search_component.process(query_input))
        results = []
        
        # NutritionQueryOutputから結果を抽出
        if result_output and hasattr(result_output, 'matches') and result_output.matches:
            for term, matches in result_output.matches.items():
                for match in matches[:15]:  # 最大15件
                    results.append({
                        'name': match.name,
                        'score': match.score,
                        'source': match.source,
                        'data_type': match.data_type,
                        'nutrition': {
                            'kcal': match.nutrition.kcal if match.nutrition else 0,
                            'protein': match.nutrition.protein if match.nutrition else 0,
                            'fat': match.nutrition.fat if match.nutrition else 0,
                            'carbohydrates': match.nutrition.carbohydrates if match.nutrition else 0
                        }
                    })
        
        if results:
            print('検索結果（栄養計算適性順）:')
            
            # 栄養特性による適性評価
            evaluated_results = []
            for result in results:
                nutrition = result.get('nutrition', {})
                kcal = nutrition.get('kcal', 0)
                protein = nutrition.get('protein', 0)
                fat = nutrition.get('fat', 0)
                carbs = nutrition.get('carbohydrates', 0)
                
                # 適性スコア計算（ケース別）
                suitability_score = calculate_suitability(case, kcal, protein, fat, carbs, result)
                
                evaluated_results.append({
                    'result': result,
                    'suitability': suitability_score,
                    'nutrition': {'kcal': kcal, 'protein': protein, 'fat': fat, 'carbs': carbs}
                })
            
            # 適性スコア順にソート
            evaluated_results.sort(key=lambda x: x['suitability'], reverse=True)
            
            for i, item in enumerate(evaluated_results[:10], 1):
                result = item['result']
                nutrition = item['nutrition']
                suitability = item['suitability']
                
                # 適性レベル表示
                if suitability >= 80:
                    level = "🟢 最適"
                elif suitability >= 60:
                    level = "🟡 適切"
                elif suitability >= 40:
                    level = "🟠 可能"
                else:
                    level = "🔴 不適"
                
                print(f'{i:2d}. {level} {result["name"]} (ES score: {result["score"]:.1f}, 適性: {suitability:.0f}%)')
                print(f'    Source: {result["source"]} | Type: {result["data_type"]}')
                print(f'    栄養素(100g): {nutrition["kcal"]:.1f}kcal, P:{nutrition["protein"]:.1f}g, F:{nutrition["fat"]:.1f}g, C:{nutrition["carbs"]:.1f}g')
                print()
        else:
            print('検索結果なし\n')
        
        print('=' * 80)
        print()

def calculate_suitability(case, kcal, protein, fat, carbs, result):
    """ケース別の栄養適性スコア計算"""
    score = 0
    data_type = result.get('data_type', '')
    name = result.get('name', '').lower()
    
    if case == 'pasta salad dressing':
        # ドレッシングは高脂質・高カロリー
        if 'dressing' in name or 'sauce' in name:
            score += 30
        if fat >= 30:
            score += 25
        if 400 <= kcal <= 600:
            score += 25
        if data_type == 'ingredient':
            score += 20
            
    elif case == 'Spanish Rice':
        # 調理済み米は中程度カロリー・高炭水化物
        if 'rice' in name and 'spanish' in name:
            score += 40
        if 25 <= carbs <= 35:
            score += 25
        if 120 <= kcal <= 160:
            score += 25
        if data_type in ['ingredient', 'unified']:
            score += 10
            
    elif case == 'glaze':
        # グレーズは高糖質・中カロリー
        if 'glaze' in name and 'salmon' not in name and 'chicken' not in name:
            score += 40
        if carbs >= 15:
            score += 25
        if 150 <= kcal <= 350:
            score += 25
        if data_type == 'ingredient':
            score += 10
            
    elif case == 'creamy sauce':
        # クリームソースは高脂質・高カロリー
        if 'cream' in name and 'sauce' in name:
            score += 35
        if fat >= 25:
            score += 25
        if 250 <= kcal <= 450:
            score += 25
        if 'chipotle' not in name:  # 特定風味でない
            score += 15
            
    elif case == 'ice':
        # 氷は0カロリー
        if 'ice' in name and 'cream' not in name:
            score += 50
        if kcal <= 5:
            score += 40
        if fat <= 0.1:
            score += 10
            
    elif case == 'cheese':
        # 一般チーズは高タンパク・高脂質
        if 'cheese' in name and 'blend' not in name and 'coffeecake' not in name:
            score += 30
        if protein >= 20:
            score += 25
        if fat >= 25:
            score += 25
        if 300 <= kcal <= 450:
            score += 20
            
    elif case == 'Taco':
        # 肉入りタコスは中程度カロリー・タンパク質
        if 'taco' in name and 'chickpea' not in name and 'roasted' not in name:
            score += 35
        if protein >= 10:
            score += 25
        if fat >= 8:
            score += 20
        if 150 <= kcal <= 300:
            score += 20
    
    return min(score, 100)  # 最大100%

if __name__ == "__main__":
    investigate_nutrition_matches() 