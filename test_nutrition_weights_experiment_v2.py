#!/usr/bin/env python3
"""
栄養素重み最適化実験スクリプト v2

第1回実験の結果を受けて、より精密な調整を実施
"""

import asyncio
import json
from typing import Dict, List, Tuple
from app_v2.elasticsearch.search_service import food_search_service, SearchQuery, NutritionTarget

class NutritionWeightExperimentV2:
    """栄養素重み実験クラス v2"""
    
    def __init__(self):
        # 第1回実験で問題のあった項目を重点的にテスト
        self.test_queries = [
            "Chicken", "Walnuts", "Lettuce", "Tomato", 
            "Corn", "Red Onion", "Microgreens", "Potato"
        ]
        
        # 目標栄養プロファイル (現在のPhase1出力に基づく)
        self.nutrition_target = NutritionTarget(
            calories=150.4,
            protein_g=10.0,
            fat_total_g=2.7,
            carbohydrate_by_difference_g=15.3
        )
        
        # より厳密な評価基準
        self.expected_results = {
            "Chicken": {
                "preferred_keywords": ["breast", "thigh", "leg", "wing"],
                "avoid_keywords": ["sauce", "pasta", "flour", "soup"],
                "preferred_categories": ["ingredient", "dish"]
            },
            "Walnuts": {
                "preferred_keywords": ["walnut", "nuts"],
                "avoid_keywords": ["oil", "butter", "sauce", "pasta"],
                "preferred_categories": ["ingredient", "dish"]
            }, 
            "Lettuce": {
                "preferred_keywords": ["lettuce", "green", "leaf"],
                "avoid_keywords": ["soup", "sauce", "cooked", "pasta"],
                "preferred_categories": ["ingredient", "dish"]
            },
            "Tomato": {
                "preferred_keywords": ["tomato"],
                "avoid_keywords": ["sauce", "paste", "soup", "powder"],
                "preferred_categories": ["ingredient", "dish"]
            },
            "Corn": {
                "preferred_keywords": ["corn", "sweet corn", "yellow"],
                "avoid_keywords": ["pasta", "flour", "syrup", "starch"],
                "preferred_categories": ["ingredient", "dish"]
            },
            "Red Onion": {
                "preferred_keywords": ["onion", "red"],
                "avoid_keywords": ["powder", "sauce", "soup", "paste"],
                "preferred_categories": ["ingredient", "dish"]
            },
            "Microgreens": {
                "preferred_keywords": ["green", "micro", "sprout", "lettuce"],
                "avoid_keywords": ["milk", "meat", "pasta", "sauce"],
                "preferred_categories": ["ingredient", "dish"]
            },
            "Potato": {
                "preferred_keywords": ["potato"],
                "avoid_keywords": ["flour", "starch", "chips", "powder"],
                "preferred_categories": ["ingredient", "dish"]
            }
        }
    
    async def test_weight_configuration(self, weights: Dict[str, float], experiment_name: str) -> Dict:
        """特定の重み設定でテストを実行"""
        print(f"\n🧪 実験: {experiment_name}")
        print(f"重み設定: {weights}")
        print("-" * 60)
        
        # 重みを一時的に更新
        original_weights = food_search_service.nutrition_weights.copy()
        food_search_service.nutrition_weights.update(weights)
        
        results = {}
        total_score = 0
        problem_items = []
        category_stats = {"ingredient": 0, "dish": 0, "branded": 0}
        
        try:
            for query_term in self.test_queries:
                query = SearchQuery(
                    elasticsearch_query_terms=query_term,
                    target_nutrition_vector=self.nutrition_target
                )
                
                search_results = await food_search_service.search_foods(
                    query, size=5, enable_nutritional_similarity=True  # 結果数を増やして分析
                )
                
                if search_results:
                    top_result = search_results[0]
                    score = self.evaluate_result_quality(query_term, top_result)
                    total_score += score
                    
                    # カテゴリ統計
                    category = top_result.data_type or "unknown"
                    if "ingredient" in category.lower():
                        category_stats["ingredient"] += 1
                    elif "dish" in category.lower():
                        category_stats["dish"] += 1
                    elif "branded" in category.lower():
                        category_stats["branded"] += 1
                    
                    results[query_term] = {
                        "result": top_result.food_name,
                        "category": category,
                        "score": score,
                        "calories": top_result.nutrition.get('calories', 0),
                        "protein": top_result.nutrition.get('protein_g', 0),
                        "fat": top_result.nutrition.get('fat_total_g', 0),
                        "carbs": top_result.nutrition.get('carbohydrate_by_difference_g', 0)
                    }
                    
                    if score < 80:  # 80点未満は問題あり
                        problem_items.append(f"{query_term} → {top_result.food_name} ({score}点)")
                    
                    print(f"✅ {query_term:12} → {top_result.food_name[:35]:35} [{category:8}] ({score:3.0f}点)")
                else:
                    results[query_term] = {"result": "No results", "score": 0, "category": "none"}
                    print(f"❌ {query_term:12} → No results (0点)")
        
        finally:
            # 重みを元に戻す
            food_search_service.nutrition_weights = original_weights
        
        avg_score = total_score / len(self.test_queries)
        
        print(f"\n📊 結果サマリー:")
        print(f"   平均スコア: {avg_score:.1f}点")
        print(f"   問題項目数: {len(problem_items)}/{len(self.test_queries)}")
        print(f"   カテゴリ分布: Ingredient({category_stats['ingredient']}) Dish({category_stats['dish']}) Branded({category_stats['branded']})")
        
        if problem_items:
            print(f"   問題項目: {', '.join(problem_items)}")
        
        return {
            "experiment_name": experiment_name,
            "weights": weights,
            "average_score": avg_score,
            "results": results,
            "problem_count": len(problem_items),
            "problem_items": problem_items,
            "category_stats": category_stats
        }
    
    def evaluate_result_quality(self, query: str, result) -> float:
        """検索結果の品質を評価（0-100点）"""
        if query not in self.expected_results:
            return 50  # 不明な場合は中立
        
        expected = self.expected_results[query]
        food_name = result.food_name.lower()
        
        score = 100  # 基本点
        
        # 避けるべきキーワードがある場合は大幅減点
        for avoid_keyword in expected["avoid_keywords"]:
            if avoid_keyword.lower() in food_name:
                score -= 35  # 1つにつき35点減点（厳しく）
        
        # 好ましいキーワードがある場合はボーナス
        has_preferred = False
        for prefer_keyword in expected["preferred_keywords"]:
            if prefer_keyword.lower() in food_name:
                has_preferred = True
                break
        
        if not has_preferred:
            score -= 20  # 好ましいキーワードがない場合は減点
        
        # カテゴリボーナス（ingredient が一般的に好ましい）
        category = (result.data_type or "").lower()
        if "ingredient" in category:
            score += 5  # ingredient はわずかにボーナス
        
        # 特別なケース評価
        if query == "Corn" and "pasta" in food_name:
            score -= 70  # コーンパスタは絶対NG
        elif query == "Microgreens" and "milk" in food_name:
            score -= 90  # マイクログリーンと牛乳は全く無関係
        elif query == "Tomato" and "sauce" in food_name:
            score -= 50  # トマトソースは生トマトと違いすぎる
        
        return max(0, min(100, score))  # 0-100の範囲に制限

async def run_nutrition_weight_experiments_v2():
    """栄養素重み最適化実験v2を実行"""
    
    experiment = NutritionWeightExperimentV2()
    
    print("🚀 栄養素重み最適化実験 v2 開始")
    print("="*80)
    
    # 第1回実験の結果を受けて、より精密な実験設定
    experiments = [
        # 第1回実験のベスト設定を確認
        {
            "name": "第1回ベスト（語彙的重視）",
            "weights": {
                "calories": 0.1,
                "protein_g": 0.1,
                "fat_total_g": 0.1, 
                "carbohydrate_by_difference_g": 0.1
            }
        },
        
        # 栄養重みをさらに下げる
        {
            "name": "極度語彙重視（栄養重み0.05）",
            "weights": {
                "calories": 0.05,
                "protein_g": 0.05,
                "fat_total_g": 0.05,
                "carbohydrate_by_difference_g": 0.05
            }
        },
        
        # 栄養重みを完全に無効化
        {
            "name": "純粋語彙的マッチング",
            "weights": {
                "calories": 0.0,
                "protein_g": 0.0,
                "fat_total_g": 0.0,
                "carbohydrate_by_difference_g": 0.0
            }
        },
        
        # 第1回の炭水化物重視も確認
        {
            "name": "第1回同率1位（炭水化物重視）",
            "weights": {
                "calories": 0.1,
                "protein_g": 0.1,
                "fat_total_g": 0.1,
                "carbohydrate_by_difference_g": 0.7
            }
        },
        
        # 中間的な設定
        {
            "name": "中間バランス（0.15）",
            "weights": {
                "calories": 0.15,
                "protein_g": 0.15,
                "fat_total_g": 0.15,
                "carbohydrate_by_difference_g": 0.15
            }
        },
        
        # カロリーのみ重視
        {
            "name": "カロリー単独重視",
            "weights": {
                "calories": 1.0,
                "protein_g": 0.0,
                "fat_total_g": 0.0,
                "carbohydrate_by_difference_g": 0.0
            }
        }
    ]
    
    all_results = []
    
    # 各実験を実行
    for exp in experiments:
        result = await experiment.test_weight_configuration(
            exp["weights"], 
            exp["name"]
        )
        all_results.append(result)
    
    # 結果をランキング
    print("\n" + "="*80)
    print("🏆 実験結果ランキング v2")
    print("="*80)
    
    sorted_results = sorted(all_results, key=lambda x: x["average_score"], reverse=True)
    
    for i, result in enumerate(sorted_results, 1):
        print(f"{i}位. {result['experiment_name']}")
        print(f"    平均スコア: {result['average_score']:.1f}点")
        print(f"    問題項目: {result['problem_count']}/{len(experiment.test_queries)}項目")
        print(f"    カテゴリ: I({result['category_stats']['ingredient']}) D({result['category_stats']['dish']}) B({result['category_stats']['branded']})")
        print(f"    重み: {result['weights']}")
        print()
    
    # ベストな設定を特定
    best_result = sorted_results[0]
    
    print("🎯 v2推奨設定:")
    print(f"実験名: {best_result['experiment_name']}")
    print(f"平均スコア: {best_result['average_score']:.1f}点")
    print(f"推奨重み設定: {best_result['weights']}")
    
    # 結果をファイルに保存
    with open("nutrition_weight_experiment_v2_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": "2025-06-08",
            "experiment_version": "v2",
            "all_results": all_results,
            "best_configuration": best_result
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 詳細結果を nutrition_weight_experiment_v2_results.json に保存しました")

if __name__ == "__main__":
    asyncio.run(run_nutrition_weight_experiments_v2()) 