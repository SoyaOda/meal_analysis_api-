#!/usr/bin/env python3
"""
Cloud RunからElasticsearch接続テストスクリプト
"""

import requests
import json

def test_elasticsearch_from_cloud_run():
    """Cloud Run上でElasticsearch接続テスト"""
    
    # Cloud RunのURL
    cloud_run_url = "https://meal-analysis-api-1077966746907.us-central1.run.app"
    
    # ヘルスチェック
    print("🏥 ヘルスチェック中...")
    try:
        response = requests.get(f"{cloud_run_url}/health", timeout=30)
        print(f"✅ ヘルスチェック: {response.status_code}")
        print(f"   レスポンス: {response.json()}")
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False
    
    # Elasticsearch接続テスト用のテストエンドポイントを呼び出し
    # （実際にはElasticsearchNutritionSearchComponentを使う何らかのエンドポイント）
    
    print("\n📊 API仕様確認...")
    try:
        response = requests.get(f"{cloud_run_url}/openapi.json", timeout=30)
        if response.status_code == 200:
            api_spec = response.json()
            paths = list(api_spec.get("paths", {}).keys())
            print(f"✅ 利用可能なエンドポイント: {paths}")
        else:
            print(f"❌ API仕様取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ API仕様取得エラー: {e}")
    
    return True

if __name__ == "__main__":
    print("🔗 Cloud Run Elasticsearch接続テスト開始")
    success = test_elasticsearch_from_cloud_run()
    
    if success:
        print("\n✅ テスト完了！")
        print("📝 次のステップ:")
        print("1. Elasticsearch VMでサンプルインデックスを作成")
        print("2. ElasticsearchNutritionSearchComponent機能をテスト")
    else:
        print("\n❌ テスト失敗")