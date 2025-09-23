#!/usr/bin/env python3
"""
語幹化フィールドを含む新しいデータベースでElasticsearchインデックスを更新

手順:
1. 既存インデックスの削除
2. 新しい設定でインデックス作成
3. 語幹化データの一括インポート
"""

import json
import requests
import time
from typing import Dict, Any, List

# Production Elasticsearch VM設定
ELASTICSEARCH_URL = "http://35.193.16.212:9200"
SETTINGS_FILE = "elasticsearch_settings.json"
DATA_FILE = "db/mynetdiary_converted_tool_calls_list_stemmed.json"

# JSONファイル名から動的にINDEX_NAMEを生成
import os
def get_dynamic_index_name(data_file_path: str) -> str:
    """データファイルパスからインデックス名を動的生成"""
    # ファイル名のみ取得（パス除去）
    filename = os.path.basename(data_file_path)
    # 拡張子除去
    index_name = os.path.splitext(filename)[0]
    return index_name

INDEX_NAME = get_dynamic_index_name(DATA_FILE)

def check_elasticsearch_connection():
    """Elasticsearchの接続確認"""
    try:
        response = requests.get(f"{ELASTICSEARCH_URL}/_cluster/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Elasticsearch接続確認: {health.get('status', 'unknown')} status")
            return True
        else:
            print(f"❌ Elasticsearch接続エラー: status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Elasticsearch接続失敗: {e}")
        return False

def delete_existing_index():
    """既存インデックスの削除"""
    print(f"🗑️ 既存インデックス '{INDEX_NAME}' を削除中...")

    try:
        response = requests.delete(f"{ELASTICSEARCH_URL}/{INDEX_NAME}")
        if response.status_code in [200, 404]:
            print(f"✅ インデックス削除完了")
            return True
        else:
            print(f"⚠️ インデックス削除警告: status {response.status_code}")
            return True  # 404は正常（インデックスが存在しない）
    except Exception as e:
        print(f"❌ インデックス削除エラー: {e}")
        return False

def create_index_with_settings():
    """新しい設定でインデックス作成"""
    print(f"🏗️ 新しいインデックス '{INDEX_NAME}' を作成中...")

    # 設定ファイル読み込み
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")
        return False

    # インデックス作成
    try:
        response = requests.put(
            f"{ELASTICSEARCH_URL}/{INDEX_NAME}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(settings),
            timeout=120
        )

        if response.status_code == 200:
            print(f"✅ インデックス作成完了")
            return True
        else:
            print(f"❌ インデックス作成エラー: status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ インデックス作成失敗: {e}")
        return False

def bulk_import_data():
    """データの一括インポート"""
    import os

    # ファイルの存在確認とタイプ判定
    if not os.path.exists(DATA_FILE):
        print(f"❌ データファイルが見つかりません: {DATA_FILE}")
        return False

    file_type = "語幹化データ" if "stemmed" in DATA_FILE else "通常データ"
    print(f"📥 データインポート開始: {DATA_FILE}")
    print(f"📋 データタイプ: {file_type}")

    # データファイル読み込み
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"📊 読み込みレコード数: {len(data)}")

        # サンプルデータ確認
        if len(data) > 0:
            sample = data[0]
            has_stemmed_fields = 'stemmed_search_name' in sample and 'stemmed_description' in sample
            if has_stemmed_fields:
                print(f"✅ 語幹化フィールド確認済み: stemmed_search_name, stemmed_description")
            else:
                print(f"⚠️ 注意: 語幹化フィールドが見つかりません")

    except Exception as e:
        print(f"❌ データファイル読み込みエラー: {e}")
        return False

    # バッチサイズ設定
    batch_size = 100
    total_batches = (len(data) + batch_size - 1) // batch_size

    print(f"🔄 バッチ処理開始: {total_batches}バッチ（バッチサイズ: {batch_size}）")

    success_count = 0
    error_count = 0

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(data))
        batch_data = data[start_idx:end_idx]

        # Bulk APIフォーマット作成
        bulk_body = []
        for record in batch_data:
            # インデックス操作
            index_action = {
                "index": {
                    "_index": INDEX_NAME,
                    "_id": record.get("id", "")
                }
            }
            bulk_body.append(json.dumps(index_action))
            bulk_body.append(json.dumps(record))

        bulk_data = "\n".join(bulk_body) + "\n"

        # Bulk API実行
        try:
            response = requests.post(
                f"{ELASTICSEARCH_URL}/_bulk",
                headers={"Content-Type": "application/x-ndjson"},
                data=bulk_data,
                timeout=600
            )

            if response.status_code == 200:
                result = response.json()
                batch_errors = [item for item in result.get("items", []) if "error" in item.get("index", {})]

                if not batch_errors:
                    success_count += len(batch_data)
                    print(f"⚡ バッチ {batch_idx + 1}/{total_batches} 完了 ({len(batch_data)}件)")
                else:
                    error_count += len(batch_errors)
                    success_count += len(batch_data) - len(batch_errors)
                    print(f"⚠️ バッチ {batch_idx + 1}/{total_batches} 部分完了: {len(batch_errors)}件エラー")

                    # エラーの詳細を表示（最初の5つまで）
                    print("📋 エラー詳細:")
                    for i, error_item in enumerate(batch_errors[:5]):
                        error_detail = error_item.get("index", {}).get("error", {})
                        error_type = error_detail.get("type", "unknown")
                        error_reason = error_detail.get("reason", "unknown reason")
                        print(f"   エラー {i+1}: {error_type} - {error_reason}")

                    if len(batch_errors) > 5:
                        print(f"   ... 他 {len(batch_errors) - 5} 件のエラー")
            else:
                error_count += len(batch_data)
                print(f"❌ バッチ {batch_idx + 1}/{total_batches} 失敗: status {response.status_code}")

        except Exception as e:
            error_count += len(batch_data)
            print(f"❌ バッチ {batch_idx + 1}/{total_batches} 例外: {e}")

        # 少し待機（Elasticsearchの負荷軽減）
        time.sleep(0.1)

    print(f"\n📊 インポート結果:")
    print(f"   ✅ 成功: {success_count}件")
    print(f"   ❌ エラー: {error_count}件")
    print(f"   📈 総件数: {len(data)}件")

    return error_count == 0

def verify_import():
    """インポート結果の確認"""
    print(f"🔍 インポート結果確認中...")

    try:
        # ドキュメント数確認
        response = requests.get(f"{ELASTICSEARCH_URL}/{INDEX_NAME}/_count")
        if response.status_code == 200:
            count = response.json().get("count", 0)
            print(f"📊 インデックス内ドキュメント数: {count}")

        # サンプルデータ確認
        response = requests.get(f"{ELASTICSEARCH_URL}/{INDEX_NAME}/_search?size=1")
        if response.status_code == 200:
            result = response.json()
            hits = result.get("hits", {}).get("hits", [])
            if hits:
                sample = hits[0]["_source"]
                print(f"✅ サンプルレコード確認:")
                print(f"   original_name: {sample.get('original_name', 'N/A')}")
                print(f"   stemmed_search_name: {sample.get('stemmed_search_name', 'N/A')}")
                print(f"   stemmed_description: {sample.get('stemmed_description', 'N/A')}")
                return True

        return False

    except Exception as e:
        print(f"❌ 確認処理エラー: {e}")
        return False

def main():
    """メイン処理"""
    import os

    # 動的タイトル生成
    file_type = "語幹化データ" if "stemmed" in DATA_FILE else "通常データ"
    index_type = "語幹化対応" if "stemmed" in DATA_FILE else "標準"

    print(f"🚀 Elasticsearch {index_type}インデックス更新開始")
    print(f"📄 対象ファイル: {DATA_FILE}")
    print(f"📋 データタイプ: {file_type}")
    print(f"🏷️ インデックス名: {INDEX_NAME}")
    print("=" * 70)

    # Step 1: 接続確認
    if not check_elasticsearch_connection():
        print("❌ 処理中止: Elasticsearch接続不可")
        return False

    # Step 2: 既存インデックス削除
    if not delete_existing_index():
        print("❌ 処理中止: インデックス削除失敗")
        return False

    # Step 3: 新しいインデックス作成
    if not create_index_with_settings():
        print("❌ 処理中止: インデックス作成失敗")
        return False

    # インデックス作成完了とシャード準備を待つ
    print("⏳ インデックス作成完了とシャード準備待機中...")

    # シャードが準備できるまで待機
    max_wait_time = 60  # 最大60秒待機
    wait_interval = 5   # 5秒間隔でチェック
    waited_time = 0

    while waited_time < max_wait_time:
        try:
            # インデックスの健康状態を確認
            health_response = requests.get(f"{ELASTICSEARCH_URL}/_cluster/health/{INDEX_NAME}?wait_for_status=yellow&timeout=10s")
            if health_response.status_code == 200:
                health = health_response.json()
                status = health.get('status', 'unknown')
                print(f"📊 インデックス状態: {status}")

                if status in ['yellow', 'green']:
                    print("✅ シャード準備完了")
                    break

            print(f"⏳ シャード準備中... ({waited_time + wait_interval}/{max_wait_time}秒)")
            time.sleep(wait_interval)
            waited_time += wait_interval

        except Exception as e:
            print(f"⚠️ 健康状態チェックエラー: {e}")
            time.sleep(wait_interval)
            waited_time += wait_interval

    if waited_time >= max_wait_time:
        print("⚠️ 警告: シャード準備の確認がタイムアウトしました。インポートを続行します...")

    # Step 4: データインポート
    if not bulk_import_data():
        print("❌ 処理中止: データインポート失敗")
        return False

    # 少し待機（インデックス更新を待つ）
    print("⏳ インデックス更新完了待機中...")
    time.sleep(5)

    # Step 5: 確認
    if not verify_import():
        print("⚠️ 警告: インポート確認で問題発生")

    # 完了メッセージも動的に
    completion_type = "語幹化対応" if "stemmed" in DATA_FILE else "標準"
    print(f"\n🎉 Elasticsearch {completion_type}インデックス更新完了！")
    print("=" * 70)

    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)