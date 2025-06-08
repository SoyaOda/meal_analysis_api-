"""
Painlessスクリプトデバッグ用テストファイル
"""
import json
from app_v2.elasticsearch.client import es_client
from app_v2.elasticsearch.config import es_config

def test_simple_script():
    """シンプルなPainlessスクリプトのテスト"""
    
    index_name = es_config.food_nutrition_index
    
    # 1. 基本的なスクリプトテスト
    print("1. 基本的なスクリプトテスト")
    try:
        result = es_client.client.search(
            index=index_name,
            body={
                "query": {
                    "function_score": {
                        "query": {"match_all": {}},
                        "functions": [
                            {
                                "script_score": {
                                    "script": {
                                        "source": "Math.log(2 + doc['nutrition.calories'].value)"
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": 2
            }
        )
        print("   ✅ 基本スクリプト成功")
        for hit in result['hits']['hits']:
            print(f"   {hit['_score']:.2f}: {hit['_source']['food_name']}")
    except Exception as e:
        print(f"   ❌ 基本スクリプトエラー: {e}")
    
    # 2. パラメータありスクリプト
    print("\\n2. パラメータありスクリプトテスト")
    try:
        result = es_client.client.search(
            index=index_name,
            body={
                "query": {
                    "function_score": {
                        "query": {"match_all": {}},
                        "functions": [
                            {
                                "script_score": {
                                    "script": {
                                        "source": "Math.log(2 + doc['nutrition.calories'].value) * params.multiplier",
                                        "params": {"multiplier": 1.5}
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": 2
            }
        )
        print("   ✅ パラメータスクリプト成功")
        for hit in result['hits']['hits']:
            print(f"   {hit['_score']:.2f}: {hit['_source']['food_name']}")
    except Exception as e:
        print(f"   ❌ パラメータスクリプトエラー: {e}")
        
    # 3. 栄養値計算スクリプト（簡素化版）
    print("\\n3. 栄養値計算スクリプト（簡素化版）")
    try:
        result = es_client.client.search(
            index=index_name,
            body={
                "query": {
                    "function_score": {
                        "query": {"match_all": {}},
                        "functions": [
                            {
                                "script_score": {
                                    "script": {
                                        "source": """
                                            double target_cal = params.target_calories;
                                            double current_cal = doc['nutrition.calories'].value;
                                            double diff = Math.abs(current_cal - target_cal);
                                            return 1.0 / (1.0 + diff / 100.0);
                                        """,
                                        "params": {"target_calories": 165.0}
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": 3
            }
        )
        print("   ✅ 栄養値計算スクリプト成功")
        for hit in result['hits']['hits']:
            source = hit['_source']
            calories = source['nutrition']['calories']
            print(f"   {hit['_score']:.3f}: {source['food_name']} (Cal: {calories})")
    except Exception as e:
        print(f"   ❌ 栄養値計算スクリプトエラー: {e}")

if __name__ == "__main__":
    test_simple_script() 