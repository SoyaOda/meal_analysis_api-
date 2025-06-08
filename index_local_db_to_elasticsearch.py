#!/usr/bin/env python3
"""
Local DB全データをElasticsearchにインデックスするスクリプト
仕様書対応: 実際のLocal DBデータでElasticsearchを動作させる
人気度指標（num_favorites）も統合
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import time

from app_v2.elasticsearch.client import es_client
from app_v2.elasticsearch.config import es_config

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

LOCAL_DB_PATH = Path("/Users/odasoya/meal_analysis_api /nutrition_db_experiment/nutrition_db/unified_nutrition_db.json")


def load_popularity_metrics() -> Dict[str, int]:
    """
    processed_newフォルダから人気度指標（num_favorites）を読み込み
    
    Returns:
        食品IDとnum_favoritesのマッピング辞書
    """
    popularity_data = {}
    processed_count = 0
    error_count = 0
    
    # raw_nutrition_dataディレクトリを検索
    raw_data_dir = Path("raw_nutrition_data")
    if not raw_data_dir.exists():
        logger.warning(f"raw_nutrition_dataディレクトリが見つかりません: {raw_data_dir}")
        return popularity_data
    
    logger.info("人気度指標（num_favorites）を読み込み中...")
    
    # recipe, food, brandedカテゴリを処理
    for category in ['recipe', 'food', 'branded']:
        category_dir = raw_data_dir / category
        
        if not category_dir.exists():
            continue
        
        for item_dir in category_dir.iterdir():
            if not item_dir.is_dir():
                continue
                
            # processed_newディレクトリ内のJSONファイルを確認
            processed_new_dir = item_dir / 'processed_new'
            popularity_file = processed_new_dir / 'data_with_popularity.json'
            
            if popularity_file.exists():
                try:
                    with open(popularity_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 人気度指標を抽出
                    popularity_metrics = data.get('popularity_metrics', {})
                    num_favorites = popularity_metrics.get('num_favorites', 0)
                    
                    # 食品IDを生成（Local DBのIDと一致させる）
                    food_id = data.get('id')
                    if food_id:
                        popularity_data[food_id] = num_favorites
                        processed_count += 1
                        
                        # 高い人気度のアイテムをログ
                        if num_favorites > 100:
                            logger.debug(f"高人気度アイテム: {data.get('title', 'Unknown')} - {num_favorites} favorites")
                    
                except Exception as e:
                    logger.error(f"人気度データ読み込みエラー {popularity_file}: {e}")
                    error_count += 1
    
    logger.info(f"人気度指標読み込み完了: 成功 {processed_count}, エラー {error_count}")
    
    # 統計情報をログ
    if popularity_data:
        values = list(popularity_data.values())
        avg_favorites = sum(values) / len(values)
        max_favorites = max(values)
        min_favorites = min(values)
        
        logger.info(f"人気度統計: 平均 {avg_favorites:.1f}, 最大 {max_favorites}, 最小 {min_favorites}")
    
    return popularity_data


def convert_local_db_item_to_elasticsearch(
    item: Dict[str, Any], 
    index: int, 
    popularity_data: Dict[str, int]
) -> Dict[str, Any]:
    """
    Local DBアイテムをElasticsearch用フォーマットに変換（人気度指標付き）
    
    Args:
        item: Local DBアイテム
        index: インデックス番号
        popularity_data: 人気度指標のマッピング
    
    Returns:
        Elasticsearch用データ
    """
    # 栄養情報を変換（Local DB → Elasticsearch形式）
    nutrition_data = item.get("nutrition", {})
    weight = item.get("weight", 100.0)  # デフォルト100g
    
    # 🎯 重要な修正: 栄養素を100gあたりの値に正規化
    def normalize_to_100g(value, weight):
        """栄養素値を100gあたりに正規化"""
        if weight <= 0:
            return 0.0
        return (value / weight) * 100.0
    
    # 🎯 修正：コア4栄養素のみを使用（fiber_total_dietary, sodium等は削除）
    core_nutrients = {
        "calories": "calories",
        "protein_g": "protein", 
        "fat_total_g": "fat",
        "carbohydrate_by_difference_g": "carbs"
    }
    
    elasticsearch_nutrition = {}
    for es_key, local_key in core_nutrients.items():
        raw_value = nutrition_data.get(local_key, 0.0)
        normalized_value = normalize_to_100g(raw_value, weight)
        elasticsearch_nutrition[es_key] = normalized_value
    
    # データタイプの正規化
    db_type = item.get("db_type", "unknown")
    if db_type == "dish":
        data_type = "dish"
    elif db_type == "ingredient":
        data_type = "ingredient"
    elif db_type == "branded":
        data_type = "branded"
    else:
        data_type = f"local_{db_type}"
    
    # 🎯 人気度指標を取得
    item_id = str(item.get('id', index))
    num_favorites = popularity_data.get(item_id, 0)
    
    # Elasticsearch用データ構造
    elasticsearch_item = {
        "food_id": f"local_{item_id}",
        "fdc_id": item.get('id'),  # Local DBのIDを保持
        "food_name": item.get("search_name", "Unknown Food"),
        "description": item.get("search_name", "Unknown Food"),
        "brand_name": None,  # Local DBにはブランド情報なし
        "category": data_type,
        "data_type": data_type,  # 🎯 重要：data_typeを正しく設定
        "num_favorites": num_favorites,  # 🎯 人気度指標を追加
        "ingredients_text": None,  # Local DBには詳細な材料リストなし
        "nutrition": elasticsearch_nutrition,  # 🎯 100gあたりに正規化済み
        "weight": 100.0,  # 🎯 常に100gとして統一（正規化済みのため）
        # Local DB特有の情報を保持
        "local_db_metadata": {
            "original_db_type": db_type,
            "original_id": item.get('id'),
            "original_weight": weight,  # 元のweight値は保持
            "nutrition_normalized_to_100g": True,  # 正規化済みであることを明示
            "num_favorites": num_favorites,  # メタデータにも保持
            "has_popularity_data": num_favorites > 0  # 人気度データの有無
        }
    }
    
    return elasticsearch_item


async def index_local_db_to_elasticsearch():
    """Local DBの全データをElasticsearchにインデックス"""
    
    print("🚀 Local DB全データのElasticsearchインデックス開始")
    print("=" * 70)
    
    # 1. Local DBデータの読み込み
    print(f"📁 Local DBファイル読み込み: {LOCAL_DB_PATH}")
    
    if not LOCAL_DB_PATH.exists():
        print(f"❌ ファイルが見つかりません: {LOCAL_DB_PATH}")
        return False
    
    with open(LOCAL_DB_PATH, 'r', encoding='utf-8') as f:
        local_db_data = json.load(f)
    
    print(f"✅ データ読み込み完了: {len(local_db_data):,}件")
    
    # データタイプ別の統計
    db_type_counts = {}
    for item in local_db_data:
        db_type = item.get("db_type", "unknown")
        db_type_counts[db_type] = db_type_counts.get(db_type, 0) + 1
    
    print(f"📊 データタイプ別統計:")
    for db_type, count in sorted(db_type_counts.items()):
        print(f"   {db_type}: {count:,}件")
    
    # 1.5. 人気度指標の読み込み（一度だけ）
    print(f"\n⭐ 人気度指標読み込み...")
    popularity_data = load_popularity_metrics()
    print(f"✅ 人気度指標読み込み完了: {len(popularity_data):,}件のアイテムに人気度データあり")
    
    # 2. Elasticsearch接続確認
    print(f"\n🔌 Elasticsearch接続確認...")
    es_healthy = await es_client.health_check()
    if not es_healthy:
        print(f"❌ Elasticsearch接続失敗")
        return False
    print(f"✅ Elasticsearch接続成功")
    
    # 3. 既存インデックスの削除・再作成
    index_name = es_config.food_nutrition_index
    print(f"\n🗑️  既存インデックス削除・再作成: {index_name}")
    
    try:
        # インデックス削除
        if es_client.client.indices.exists(index=index_name):
            es_client.client.indices.delete(index=index_name)
            print(f"   既存インデックス削除完了")
        
        # インデックス設定読み込み
        settings_path = Path("elasticsearch_config/food_nutrition_index_settings.json")
        with open(settings_path, 'r', encoding='utf-8') as f:
            index_settings = json.load(f)
        
        # インデックス作成
        es_client.client.indices.create(
            index=index_name,
            body=index_settings
        )
        print(f"   新規インデックス作成完了")
        
    except Exception as e:
        print(f"❌ インデックス作成エラー: {e}")
        return False
    
    # 4. データ変換・インデックス（バッチ処理）
    print(f"\n📝 データ変換・インデックス処理...")
    
    batch_size = 1000  # バッチサイズ
    total_items = len(local_db_data)
    successful_indexed = 0
    failed_indexed = 0
    
    start_time = time.time()
    
    for i in range(0, total_items, batch_size):
        batch_data = local_db_data[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_items + batch_size - 1) // batch_size
        
        print(f"   バッチ {batch_num}/{total_batches}: {len(batch_data)}件処理中...")
        
        # バルクインデックス用データ準備
        bulk_body = []
        
        for j, item in enumerate(batch_data):
            try:
                # データ変換（人気度データを再利用）
                es_item = convert_local_db_item_to_elasticsearch(item, i + j, popularity_data)
                
                # バルクインデックスに追加
                bulk_body.append({
                    "index": {
                        "_index": index_name,
                        "_id": es_item["food_id"]
                    }
                })
                bulk_body.append(es_item)
                
            except Exception as e:
                logger.error(f"データ変換エラー (index {i + j}): {e}")
                failed_indexed += 1
        
        # バルクインデックス実行
        try:
            if bulk_body:
                bulk_result = es_client.client.bulk(
                    body=bulk_body,
                    refresh=False  # 最後にまとめてrefresh
                )
                
                # 結果処理
                if bulk_result.get("errors"):
                    for item in bulk_result.get("items", []):
                        if "index" in item and "error" in item["index"]:
                            failed_indexed += 1
                            logger.error(f"インデックスエラー: {item['index']['error']}")
                        else:
                            successful_indexed += 1
                else:
                    successful_indexed += len(batch_data)
                
                # 進捗表示
                progress = (i + len(batch_data)) / total_items * 100
                elapsed = time.time() - start_time
                rate = (i + len(batch_data)) / elapsed if elapsed > 0 else 0
                print(f"   進捗: {progress:.1f}% ({successful_indexed:,}件成功, {failed_indexed}件失敗) - {rate:.1f}件/秒")
        
        except Exception as e:
            logger.error(f"バルクインデックスエラー (batch {batch_num}): {e}")
            failed_indexed += len(batch_data)
    
    # 5. インデックスrefresh
    print(f"\n🔄 インデックスrefresh...")
    es_client.client.indices.refresh(index=index_name)
    
    # 6. 結果確認
    total_time = time.time() - start_time
    print(f"\n✅ インデックス処理完了!")
    print(f"📊 結果サマリー:")
    print(f"   総件数: {total_items:,}件")
    print(f"   成功: {successful_indexed:,}件")
    print(f"   失敗: {failed_indexed}件")
    print(f"   処理時間: {total_time:.2f}秒")
    print(f"   処理速度: {total_items / total_time:.1f}件/秒")
    
    # 人気度統計
    items_with_popularity = sum(1 for item in local_db_data if str(item.get('id', '')) in popularity_data)
    print(f"   人気度データ付きアイテム: {items_with_popularity:,}件 ({items_with_popularity/total_items*100:.1f}%)")
    
    # インデックス件数確認
    count_result = es_client.client.count(index=index_name)
    indexed_count = count_result["count"]
    print(f"   Elasticsearchインデックス件数: {indexed_count:,}件")
    
    if indexed_count != successful_indexed:
        print(f"⚠️  インデックス件数が一致しません!")
    
    return indexed_count > 0


async def test_indexed_data():
    """インデックスされたデータのテスト検索"""
    
    print(f"\n🔍 インデックスデータテスト検索...")
    
    # サンプル検索
    test_queries = ["chicken", "rice", "salad", "ice cream"]
    
    for query in test_queries:
        try:
            result = es_client.client.search(
                index=es_config.food_nutrition_index,
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["food_name^3", "description^1.5"],
                            "type": "most_fields"
                        }
                    },
                    "size": 3
                },
                request_timeout=30
            )
            
            hits = result.get("hits", {}).get("hits", [])
            print(f"\n'{query}' 検索結果: {len(hits)}件")
            
            for hit in hits[:2]:  # 上位2件
                source = hit["_source"]
                score = hit["_score"]
                data_type = source.get("data_type", "unknown")
                calories = source.get("nutrition", {}).get("calories", 0)
                print(f"  {score:.2f}: {source['food_name']} ({data_type}, {calories}cal)")
        
        except Exception as e:
            print(f"❌ 検索エラー '{query}': {e}")


if __name__ == "__main__":
    asyncio.run(index_local_db_to_elasticsearch())
    asyncio.run(test_indexed_data()) 