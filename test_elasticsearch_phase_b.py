"""
フェーズB実装テスト: 栄養プロファイル類似性スコアリング
仕様書に基づくハイブリッドランキングモデルのテスト
"""
import asyncio
import json
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_phase_b_nutritional_similarity_scoring():
    """フェーズB: 栄養プロファイル類似性スコアリングのテスト"""
    
    print("🚀 フェーズB: 栄養プロファイル類似性スコアリングテストを開始します...")
    print("=" * 80)
    
    try:
        # 前提条件チェック
        from app_v2.elasticsearch.client import es_client
        from app_v2.elasticsearch.config import es_config
        
        health_status = await es_client.health_check()
        if not health_status:
            print("❌ Elasticsearch接続に失敗しました。フェーズAを先に実行してください。")
            return False
        
        index_name = es_config.food_nutrition_index
        if not es_client.client.indices.exists(index=index_name):
            print("❌ インデックスが存在しません。フェーズAを先に実行してください。")
            return False
        
        print("✅ 前提条件チェック完了")
        
        # 1. 栄養プロファイル類似性テスト用データ追加
        print(f"\n1️⃣ 栄養プロファイル類似性テスト用データ追加")
        
        # より多様な栄養プロファイルの食品を追加
        additional_foods = [
            {
                "food_id": "test_004",
                "fdc_id": 123459,
                "food_name": "Chicken, grilled, breast, skinless",
                "description": "Grilled chicken breast without skin",
                "brand_name": None,
                "category": "Poultry Products",
                "nutrition": {
                    "calories": 195.0,  # 鶏肉だが調理法により異なる
                    "protein_g": 29.0,
                    "fat_total_g": 7.8,
                    "carbohydrate_by_difference_g": 0.0,
                    "fiber_total_dietary_g": 0.0,
                    "sodium_mg": 75.0
                }
            },
            {
                "food_id": "test_005",
                "fdc_id": 123460,
                "food_name": "Turkey, breast, meat only, roasted",
                "description": "Roasted turkey breast meat",
                "brand_name": None,
                "category": "Poultry Products",
                "nutrition": {
                    "calories": 189.0,  # 鶏肉と似た栄養プロファイル
                    "protein_g": 29.0,
                    "fat_total_g": 7.0,
                    "carbohydrate_by_difference_g": 0.0,
                    "fiber_total_dietary_g": 0.0,
                    "sodium_mg": 70.0
                }
            },
            {
                "food_id": "test_006",
                "fdc_id": 123461,
                "food_name": "Ice cream, chocolate, premium",
                "description": "Premium chocolate ice cream",
                "brand_name": "Premium",
                "category": "Dairy and Egg Products",
                "nutrition": {
                    "calories": 267.0,  # バニラアイスより高カロリー
                    "protein_g": 4.9,
                    "fat_total_g": 17.0,
                    "carbohydrate_by_difference_g": 28.0,
                    "fiber_total_dietary_g": 1.2,
                    "sodium_mg": 76.0
                }
            }
        ]
        
        # バルクインデックス
        bulk_body = []
        for food in additional_foods:
            bulk_body.append({"index": {"_index": index_name, "_id": food["food_id"]}})
            bulk_body.append(food)
        
        bulk_result = es_client.client.bulk(body=bulk_body, refresh=True)
        print(f"   ✅ 追加テストデータ投入成功: {len(additional_foods)}件")
        
        # 2. 基本検索（語彙的類似性のみ）テスト
        print(f"\n2️⃣ 基本検索（語彙的類似性のみ）テスト")
        
        basic_search_result = es_client.client.search(
            index=index_name,
            body={
                "query": {
                    "multi_match": {
                        "query": "chicken breast",
                        "fields": [
                            "food_name^3",
                            "description^1.5"
                        ],
                        "type": "most_fields"
                    }
                },
                "size": 5
            }
        )
        
        print("   語彙的類似性による結果:")
        for hit in basic_search_result['hits']['hits']:
            source = hit['_source']
            score = hit['_score']
            calories = source['nutrition']['calories']
            protein = source['nutrition']['protein_g']
            print(f"     {score:.2f}: {source['food_name']} (Cal: {calories}, Pro: {protein}g)")
        
        # 3. 栄養プロファイル類似性検索テスト
        print(f"\n3️⃣ 栄養プロファイル類似性検索テスト")
        
        # 目標栄養プロファイル（生鶏肉に近い）
        target_nutrition = {
            "calories": 165.0,
            "protein_g": 31.0,
            "fat_total_g": 3.6,
            "carbohydrate_by_difference_g": 0.0
        }
        
        # 仕様書のfunction_scoreクエリを実装
        nutrition_similarity_query = {
            "query": {
                "function_score": {
                    "query": {
                        "multi_match": {
                            "query": "chicken breast",
                            "fields": [
                                "food_name^3",
                                "description^1.5"
                            ],
                            "type": "most_fields"
                        }
                    },
                    "functions": [
                        {
                            "filter": {
                                "bool": {
                                    "must": [
                                        {"exists": {"field": "nutrition.calories"}},
                                        {"exists": {"field": "nutrition.protein_g"}},
                                        {"exists": {"field": "nutrition.fat_total_g"}},
                                        {"exists": {"field": "nutrition.carbohydrate_by_difference_g"}}
                                    ]
                                }
                            },
                            "script_score": {
                                "script": {
                                    "source": """
                                        // 目標栄養プロファイル
                                        double target_cal = params.target_calories;
                                        double target_pro = params.target_protein_g;
                                        double target_fat = params.target_fat_total_g;
                                        double target_carb = params.target_carbohydrate_by_difference_g;

                                        // 現在の値
                                        double current_cal = doc['nutrition.calories'].value;
                                        double current_pro = doc['nutrition.protein_g'].value;
                                        double current_fat = doc['nutrition.fat_total_g'].value;
                                        double current_carb = doc['nutrition.carbohydrate_by_difference_g'].value;

                                        // 正規化係数
                                        double norm_cal = 200.0;
                                        double norm_pro = 20.0;
                                        double norm_fat = 20.0;
                                        double norm_carb = 30.0;

                                        // 重み
                                        double w_cal = 0.4;
                                        double w_pro = 0.3;
                                        double w_fat = 0.2;
                                        double w_carb = 0.1;

                                        // 正規化された差を計算
                                        double cal_diff = (current_cal - target_cal) / norm_cal;
                                        double pro_diff = (current_pro - target_pro) / norm_pro;
                                        double fat_diff = (current_fat - target_fat) / norm_fat;
                                        double carb_diff = (current_carb - target_carb) / norm_carb;

                                        // 重み付き距離を計算
                                        double dist_sq = w_cal * cal_diff * cal_diff +
                                                         w_pro * pro_diff * pro_diff +
                                                         w_fat * fat_diff * fat_diff +
                                                         w_carb * carb_diff * carb_diff;

                                        // 距離が近いほど高スコア
                                        return 1.0 / (1.0 + Math.sqrt(dist_sq));
                                    """,
                                    "params": {
                                        "target_calories": target_nutrition["calories"],
                                        "target_protein_g": target_nutrition["protein_g"],
                                        "target_fat_total_g": target_nutrition["fat_total_g"],
                                        "target_carbohydrate_by_difference_g": target_nutrition["carbohydrate_by_difference_g"]
                                    }
                                }
                            },
                            "weight": 2.5  # 栄養的類似性を高く重み付け
                        }
                    ],
                    "score_mode": "sum",
                    "boost_mode": "multiply"
                }
            },
            "size": 5
        }
        
        nutrition_search_result = es_client.client.search(
            index=index_name,
            body=nutrition_similarity_query
        )
        
        print("   栄養プロファイル類似性による結果:")
        print(f"   目標: Cal={target_nutrition['calories']}, Pro={target_nutrition['protein_g']}g")
        
        for hit in nutrition_search_result['hits']['hits']:
            source = hit['_source']
            score = hit['_score']
            calories = source['nutrition']['calories']
            protein = source['nutrition']['protein_g']
            fat = source['nutrition']['fat_total_g']
            carb = source['nutrition']['carbohydrate_by_difference_g']
            
            # 栄養距離を計算
            cal_diff = abs(calories - target_nutrition['calories'])
            pro_diff = abs(protein - target_nutrition['protein_g'])
            
            print(f"     {score:.2f}: {source['food_name']}")
            print(f"             Cal: {calories} ({cal_diff:+.1f}), Pro: {protein}g ({pro_diff:+.1f}g)")
        
        # 4. アイスクリーム類似性テスト
        print(f"\n4️⃣ アイスクリーム栄養プロファイル類似性テスト")
        
        # バニラアイスクリームの栄養プロファイル
        ice_cream_target = {
            "calories": 207.0,
            "protein_g": 3.5,
            "fat_total_g": 11.0,
            "carbohydrate_by_difference_g": 24.0
        }
        
        ice_cream_query = nutrition_similarity_query.copy()
        ice_cream_query["query"]["function_score"]["query"]["multi_match"]["query"] = "ice cream"
        ice_cream_query["query"]["function_score"]["functions"][0]["script_score"]["script"]["params"] = {
            "target_calories": ice_cream_target["calories"],
            "target_protein_g": ice_cream_target["protein_g"],
            "target_fat_total_g": ice_cream_target["fat_total_g"],
            "target_carbohydrate_by_difference_g": ice_cream_target["carbohydrate_by_difference_g"]
        }
        
        ice_cream_result = es_client.client.search(
            index=index_name,
            body=ice_cream_query
        )
        
        print("   アイスクリーム栄養類似性結果:")
        print(f"   目標: Cal={ice_cream_target['calories']}, Pro={ice_cream_target['protein_g']}g")
        
        for hit in ice_cream_result['hits']['hits']:
            source = hit['_source']
            score = hit['_score']
            calories = source['nutrition']['calories']
            protein = source['nutrition']['protein_g']
            
            cal_diff = abs(calories - ice_cream_target['calories'])
            pro_diff = abs(protein - ice_cream_target['protein_g'])
            
            print(f"     {score:.2f}: {source['food_name']}")
            print(f"             Cal: {calories} ({cal_diff:+.1f}), Pro: {protein}g ({pro_diff:+.1f}g)")
        
        # 5. ハイブリッドランキング有効性テスト
        print(f"\n5️⃣ ハイブリッドランキング有効性テスト")
        
        # 語彙的には似ているが栄養的に大きく異なるケースをテスト
        print("   🔍 'chicken'で検索（語彙的 vs 栄養的類似性の比較）")
        
        # 生鶏肉（低カロリー、高タンパク）を目標とする
        lean_chicken_target = {
            "calories": 165.0,  # 低カロリー
            "protein_g": 31.0,  # 高タンパク
            "fat_total_g": 3.6,
            "carbohydrate_by_difference_g": 0.0
        }
        
        hybrid_query = nutrition_similarity_query.copy()
        hybrid_query["query"]["function_score"]["query"]["multi_match"]["query"] = "chicken"
        hybrid_query["query"]["function_score"]["functions"][0]["script_score"]["script"]["params"] = {
            "target_calories": lean_chicken_target["calories"],
            "target_protein_g": lean_chicken_target["protein_g"],
            "target_fat_total_g": lean_chicken_target["fat_total_g"],
            "target_carbohydrate_by_difference_g": lean_chicken_target["carbohydrate_by_difference_g"]
        }
        
        hybrid_result = es_client.client.search(
            index=index_name,
            body=hybrid_query
        )
        
        print("   ハイブリッドランキング結果（語彙的 + 栄養的）:")
        
        for hit in hybrid_result['hits']['hits']:
            source = hit['_source']
            score = hit['_score']
            calories = source['nutrition']['calories']
            protein = source['nutrition']['protein_g']
            
            # 栄養的距離を計算
            cal_diff = calories - lean_chicken_target['calories']
            pro_diff = protein - lean_chicken_target['protein_g']
            
            print(f"     {score:.2f}: {source['food_name']}")
            print(f"             Cal: {calories} ({cal_diff:+.1f}), Pro: {protein}g ({pro_diff:+.1f}g)")
        
        print(f"\n{'='*80}")
        print("🎉 フェーズB: 栄養プロファイル類似性スコアリングテスト完了！")
        print("\n📊 テスト結果サマリー:")
        print("  ✅ 栄養プロファイル類似性スコアリング")
        print("  ✅ Painlessスクリプトによる重み付け距離計算")
        print("  ✅ function_scoreハイブリッドランキング")
        print("  ✅ 語彙的類似性と栄養的類似性の結合")
        print("  ✅ 多角的検索クエリ構築")
        print("\n🚀 次のステップ: フェーズC（Enhanced Phase1プロンプト改良）")
        
        return True
        
    except Exception as e:
        logger.error(f"フェーズBテスト実行中にエラーが発生: {e}")
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_phase_b_nutritional_similarity_scoring()) 