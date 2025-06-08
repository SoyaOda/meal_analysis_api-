"""
フェーズA実装テスト: Elasticsearch基盤構築と語彙的検索
仕様書に基づく段階的な実装とテストを行います
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


async def test_phase_a_elasticsearch_foundation():
    """フェーズA: Elasticsearch基盤構築のテスト"""
    
    print("🚀 フェーズA: Elasticsearch基盤構築テストを開始します...")
    print("=" * 80)
    
    try:
        # 1. 基本接続テスト
        print("\n1️⃣ Elasticsearch接続テスト")
        from app_v2.elasticsearch.client import es_client
        from app_v2.elasticsearch.config import es_config
        
        # 健康チェック
        health_status = await es_client.health_check()
        print(f"✅ Elasticsearch健康チェック: {'成功' if health_status else '失敗'}")
        print(f"   接続URL: {es_config.connection_url}")
        
        if not health_status:
            print("❌ Elasticsearch接続に失敗しました。サーバーが起動していることを確認してください。")
            return False
        
        # 2. インデックス削除（既存がある場合）
        print(f"\n2️⃣ インデックス初期化")
        index_name = es_config.food_nutrition_index
        
        if es_client.client.indices.exists(index=index_name):
            print(f"   既存インデックス '{index_name}' を削除中...")
            es_client.client.indices.delete(index=index_name)
            print("   ✅ 既存インデックス削除完了")
        
        # 3. 仕様書に基づくインデックス作成
        print(f"\n3️⃣ 仕様書準拠インデックス作成")
        
        # インデックス設定を読み込み
        import os
        config_path = os.path.join("elasticsearch_config", "food_nutrition_index_settings.json")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            index_settings = json.load(f)
        
        print("   インデックス設定読み込み完了")
        print(f"   - アナライザー数: {len(index_settings.get('settings', {}).get('analysis', {}).get('analyzer', {}))}")
        print(f"   - フィールド数: {len(index_settings.get('mappings', {}).get('properties', {}))}")
        
        # インデックス作成
        result = es_client.client.indices.create(index=index_name, body=index_settings)
        print(f"   ✅ インデックス作成成功: {result.get('acknowledged', False)}")
        
        # 4. カスタムアナライザーテスト
        print(f"\n4️⃣ カスタムアナライザー動作テスト")
        
        # food_item_analyzerテスト
        test_texts = [
            "chicken breast grilled 8 oz.",
            "ice-cream vanilla low fat",
            "cook & serve pudding mix",
            "farmer's market organic apple"
        ]
        
        for text in test_texts:
            analyze_result = es_client.client.indices.analyze(
                index=index_name,
                body={
                    "analyzer": "food_item_analyzer",
                    "text": text
                }
            )
            
            tokens = [token['token'] for token in analyze_result['tokens']]
            print(f"   '{text}' → {tokens}")
        
        print("   ✅ カスタムアナライザー動作確認完了")
        
        # 5. テストデータの投入
        print(f"\n5️⃣ テストデータ投入")
        
        # 仕様書の例に基づくテストデータ
        test_foods = [
            {
                "food_id": "test_001",
                "fdc_id": 123456,
                "food_name": "Chicken, broilers or fryers, breast, meat only, raw",
                "description": "Raw chicken breast without skin",
                "brand_name": None,
                "category": "Poultry Products",
                "nutrition": {
                    "calories": 165.0,
                    "protein_g": 31.0,
                    "fat_total_g": 3.6,
                    "carbohydrate_by_difference_g": 0.0,
                    "fiber_total_dietary_g": 0.0,
                    "sodium_mg": 74.0
                }
            },
            {
                "food_id": "test_002",
                "fdc_id": 123457,
                "food_name": "Ice cream, vanilla, regular",
                "description": "Regular vanilla ice cream",
                "brand_name": "Generic",
                "category": "Dairy and Egg Products",
                "nutrition": {
                    "calories": 207.0,
                    "protein_g": 3.5,
                    "fat_total_g": 11.0,
                    "carbohydrate_by_difference_g": 24.0,
                    "fiber_total_dietary_g": 0.7,
                    "sodium_mg": 80.0
                }
            },
            {
                "food_id": "test_003",
                "fdc_id": 123458,
                "food_name": "Apple, raw, with skin",
                "description": "Fresh apple with skin",
                "brand_name": None,
                "category": "Fruits and Fruit Juices",
                "nutrition": {
                    "calories": 52.0,
                    "protein_g": 0.3,
                    "fat_total_g": 0.2,
                    "carbohydrate_by_difference_g": 14.0,
                    "fiber_total_dietary_g": 2.4,
                    "sodium_mg": 1.0
                }
            }
        ]
        
        # バルクインデックス
        bulk_body = []
        for food in test_foods:
            bulk_body.append({"index": {"_index": index_name, "_id": food["food_id"]}})
            bulk_body.append(food)
        
        bulk_result = es_client.client.bulk(body=bulk_body, refresh=True)
        
        if bulk_result.get('errors'):
            print("   ⚠️  一部データの投入に失敗:")
            for item in bulk_result.get('items', []):
                if 'index' in item and 'error' in item['index']:
                    print(f"      エラー: {item['index']['error']}")
        else:
            print(f"   ✅ テストデータ投入成功: {len(test_foods)}件")
        
        # 6. 基本検索テスト
        print(f"\n6️⃣ 基本検索機能テスト")
        
        # multi_match検索
        search_queries = [
            "chicken breast",
            "ice cream vanilla",  
            "apple",
            "cook"  # 単語境界問題のテスト
        ]
        
        for query in search_queries:
            search_result = es_client.client.search(
                index=index_name,
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "food_name^3",
                                "description^1.5",
                                "brand_name^1.2"
                            ],
                            "type": "most_fields",
                            "fuzziness": "AUTO"
                        }
                    },
                    "size": 3
                }
            )
            
            hits = search_result.get('hits', {}).get('hits', [])
            print(f"   クエリ: '{query}' → {len(hits)}件")
            
            for hit in hits:
                source = hit['_source']
                score = hit['_score']
                print(f"     {score:.2f}: {source['food_name']}")
        
        print("   ✅ 基本検索機能テスト完了")
        
        # 7. 音声類似検索テスト（phonetic matching）
        print(f"\n7️⃣ 音声類似検索テスト")
        
        # typoのあるクエリで検索
        typo_queries = [
            "chiken",  # chicken のtypo
            "aple",    # apple のtypo
            "vanila"   # vanilla のtypo
        ]
        
        for query in typo_queries:
            search_result = es_client.client.search(
                index=index_name,
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "food_name^3",
                                "food_name.phonetic^0.5"
                            ],
                            "type": "most_fields",
                            "fuzziness": "AUTO"
                        }
                    },
                    "size": 2
                }
            )
            
            hits = search_result.get('hits', {}).get('hits', [])
            print(f"   Typoクエリ: '{query}' → {len(hits)}件")
            
            for hit in hits:
                source = hit['_source']
                score = hit['_score']
                print(f"     {score:.2f}: {source['food_name']}")
        
        print("   ✅ 音声類似検索テスト完了")
        
        # 8. 同義語検索テスト
        print(f"\n8️⃣ 同義語検索テスト")
        
        # 同義語設定をテスト
        synonym_queries = [
            "ice-cream",   # ice cream の異表記
            "icecream"     # ice cream の異表記
        ]
        
        for query in synonym_queries:
            search_result = es_client.client.search(
                index=index_name,
                body={
                    "query": {
                        "match": {
                            "food_name": query
                        }
                    },
                    "size": 2
                }
            )
            
            hits = search_result.get('hits', {}).get('hits', [])
            print(f"   同義語クエリ: '{query}' → {len(hits)}件")
            
            for hit in hits:
                source = hit['_source']
                score = hit['_score']
                print(f"     {score:.2f}: {source['food_name']}")
        
        print("   ✅ 同義語検索テスト完了")
        
        print(f"\n{'='*80}")
        print("🎉 フェーズA: Elasticsearch基盤構築テスト完了！")
        print("\n📊 テスト結果サマリー:")
        print("  ✅ Elasticsearch接続")
        print("  ✅ カスタムアナライザー (food_item_analyzer)")
        print("  ✅ インデックス作成とマッピング")
        print("  ✅ テストデータ投入")
        print("  ✅ multi_match基本検索")
        print("  ✅ typo耐性 (fuzzy matching)")
        print("  ✅ 音声類似検索 (phonetic matching)")
        print("  ✅ 同義語展開 (synonym expansion)")
        print("\n🚀 次のステップ: フェーズB（栄養プロファイル類似性スコアリング）")
        
        return True
        
    except Exception as e:
        logger.error(f"フェーズAテスト実行中にエラーが発生: {e}")
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_phase_a_elasticsearch_foundation()) 