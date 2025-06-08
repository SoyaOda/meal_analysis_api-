#!/usr/bin/env python3
"""
栄養素重み最適化実験スクリプト

PDCAサイクルで最適な栄養素重みを探索する
"""

import asyncio
import json
from typing import Dict, List, Tuple
from app_v2.elasticsearch.search_service import food_search_service, SearchQuery, NutritionTarget

class NutritionWeightExperiment:
    """栄養素重み実験クラス"""
    
    def __init__(self):
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
        
        # 正解データ（手動で定義した期待される適切な結果）
        self.expected_results = {
            "Chicken": {"preferred_type": "生肉", "avoid_keywords": ["sauce", "pasta", "flour"]},
            "Walnuts": {"preferred_type": "生ナッツ", "avoid_keywords": ["oil", "butter", "sauce"]}, 
            "Lettuce": {"preferred_type": "生野菜", "avoid_keywords": ["soup", "sauce", "cooked"]},
            "Tomato": {"preferred_type": "生野菜", "avoid_keywords": ["sauce", "paste", "soup"]},
            "Corn": {"preferred_type": "生野菜", "avoid_keywords": ["pasta", "flour", "syrup"]},
            "Red Onion": {"preferred_type": "生野菜", "avoid_keywords": ["powder", "sauce", "soup"]},
            "Microgreens": {"preferred_type": "生野菜", "avoid_keywords": ["milk", "meat", "pasta"]},
            "Potato": {"preferred_type": "生野菜", "avoid_keywords": ["flour", "starch", "chips"]}
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
        
        try:
            for query_term in self.test_queries:
                query = SearchQuery(
                    elasticsearch_query_terms=query_term,
                    target_nutrition_vector=self.nutrition_target
                )
                
                search_results = await food_search_service.search_foods(
                    query, size=3, enable_nutritional_similarity=True
                )
                
                if search_results:
                    top_result = search_results[0]
                    score = self.evaluate_result_quality(query_term, top_result)
                    total_score += score
                    
                    results[query_term] = {
                        "result": top_result.food_name,
                        "score": score,
                        "calories": top_result.nutrition.get('calories', 0),
                        "protein": top_result.nutrition.get('protein_g', 0),
                        "fat": top_result.nutrition.get('fat_total_g', 0),
                        "carbs": top_result.nutrition.get('carbohydrate_by_difference_g', 0)
                    }
                    
                    if score < 80:  # 80点未満は問題あり
                        problem_items.append(f"{query_term} → {top_result.food_name} ({score}点)")
                    
                    print(f"✅ {query_term:12} → {top_result.food_name[:40]:40} ({score:3.0f}点)")
                else:
                    results[query_term] = {"result": "No results", "score": 0}
                    print(f"❌ {query_term:12} → No results (0点)")
        
        finally:
            # 重みを元に戻す
            food_search_service.nutrition_weights = original_weights
        
        avg_score = total_score / len(self.test_queries)
        
        print(f"\n📊 結果サマリー:")
        print(f"   平均スコア: {avg_score:.1f}点")
        print(f"   問題項目数: {len(problem_items)}/11")
        
        if problem_items:
            print(f"   問題項目: {', '.join(problem_items)}")
        
        return {
            "experiment_name": experiment_name,
            "weights": weights,
            "average_score": avg_score,
            "results": results,
            "problem_count": len(problem_items),
            "problem_items": problem_items
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
                score -= 30  # 1つにつき30点減点
        
        # 特別なケース評価
        if query == "Chicken":
            if "breast" in food_name and "raw" not in food_name:
                score += 10  # 鶏胸肉はボーナス
            if "sauce" in food_name or "pasta" in food_name:
                score -= 50  # 加工品は大幅減点
                
        elif query == "Tomato":
            if "raw" in food_name or ("tomato" in food_name and "sauce" not in food_name):
                score += 10  # 生トマトはボーナス
            if "sauce" in food_name or "paste" in food_name:
                score -= 40  # ソースやペーストは減点
                
        elif query == "Corn":
            if "pasta" in food_name:
                score -= 60  # パスタは大幅減点
            if "sweet" in food_name or "yellow" in food_name:
                score += 10  # スイートコーンやイエローコーンはボーナス
                
        elif query == "Potato":
            if "flour" in food_name or "starch" in food_name:
                score -= 50  # 粉類は大幅減点
            if "sweet potato" in food_name:
                score -= 20  # サツマイモは部分減点（違う食材だが栄養的に近い）
                
        elif query == "Microgreens":
            if "milk" in food_name:
                score -= 80  # 牛乳は完全に無関係
            if "green" in food_name or "lettuce" in food_name:
                score += 20  # 緑色野菜はボーナス
        
        return max(0, min(100, score))  # 0-100の範囲に制限

async def run_nutrition_weight_experiments():
    """栄養素重み最適化実験を実行"""
    
    experiment = NutritionWeightExperiment()
    
    print("🚀 栄養素重み最適化実験開始")
    print("="*80)
    
    # 実験設定リスト
    experiments = [
        # ベースライン（均等）
        {
            "name": "ベースライン（均等重み）",
            "weights": {
                "calories": 0.25,
                "protein_g": 0.25, 
                "fat_total_g": 0.25,
                "carbohydrate_by_difference_g": 0.25
            }
        },
        
        # 語彙的マッチング重視（栄養重みを下げる）
        {
            "name": "語彙的マッチング重視",
            "weights": {
                "calories": 0.1,
                "protein_g": 0.1,
                "fat_total_g": 0.1, 
                "carbohydrate_by_difference_g": 0.1
            }
        },
        
        # カロリー重視
        {
            "name": "カロリー重視",
            "weights": {
                "calories": 0.7,
                "protein_g": 0.1,
                "fat_total_g": 0.1,
                "carbohydrate_by_difference_g": 0.1
            }
        },
        
        # タンパク質重視
        {
            "name": "タンパク質重視", 
            "weights": {
                "calories": 0.1,
                "protein_g": 0.7,
                "fat_total_g": 0.1,
                "carbohydrate_by_difference_g": 0.1
            }
        },
        
        # 炭水化物重視
        {
            "name": "炭水化物重視",
            "weights": {
                "calories": 0.1,
                "protein_g": 0.1,
                "fat_total_g": 0.1,
                "carbohydrate_by_difference_g": 0.7
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
    print("🏆 実験結果ランキング")
    print("="*80)
    
    sorted_results = sorted(all_results, key=lambda x: x["average_score"], reverse=True)
    
    for i, result in enumerate(sorted_results, 1):
        print(f"{i}位. {result['experiment_name']}")
        print(f"    平均スコア: {result['average_score']:.1f}点")
        print(f"    問題項目: {result['problem_count']}/8項目")
        print(f"    重み: {result['weights']}")
        print()
    
    # ベストな設定を保存
    best_result = sorted_results[0]
    
    print("🎯 推奨設定:")
    print(f"実験名: {best_result['experiment_name']}")
    print(f"平均スコア: {best_result['average_score']:.1f}点")
    print(f"推奨重み設定: {best_result['weights']}")
    
    # 結果をファイルに保存
    with open("nutrition_weight_experiment_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": "2025-06-08",
            "all_results": all_results,
            "best_configuration": best_result
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 詳細結果を nutrition_weight_experiment_results.json に保存しました")

if __name__ == "__main__":
    asyncio.run(run_nutrition_weight_experiments()) 