#!/usr/bin/env python3
"""
USDA Unified Database Loader for Elasticsearch
usda_unified_db.jsonをElasticsearchにインデックス化するスクリプト
"""

import json
import requests
import sys
from pathlib import Path
from typing import Dict, List

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apps.usda_word_query_api.config import ELASTICSEARCH_URL, USDA_INDEX_NAME
from apps.usda_word_query_api.elasticsearch.index_settings import get_index_settings


def check_elasticsearch_connection(es_url: str) -> bool:
    """Elasticsearchへの接続確認"""
    try:
        response = requests.get(es_url, timeout=5)
        response.raise_for_status()
        print(f"✅ Elasticsearch接続成功: {es_url}")
        return True
    except Exception as e:
        print(f"❌ Elasticsearch接続失敗: {e}")
        return False


def delete_index_if_exists(es_url: str, index_name: str) -> bool:
    """既存インデックスを削除"""
    try:
        # インデックスの存在確認
        response = requests.head(f"{es_url}/{index_name}")

        if response.status_code == 200:
            print(f"⚠️  既存インデックス '{index_name}' を削除中...")
            delete_response = requests.delete(f"{es_url}/{index_name}")
            delete_response.raise_for_status()
            print(f"✅ インデックス削除完了")
            return True
        else:
            print(f"ℹ️  インデックス '{index_name}' は存在しません")
            return True

    except Exception as e:
        print(f"❌ インデックス削除失敗: {e}")
        return False


def create_index(es_url: str, index_name: str, settings: Dict) -> bool:
    """新しいインデックスを作成"""
    try:
        print(f"📝 インデックス '{index_name}' を作成中...")
        response = requests.put(
            f"{es_url}/{index_name}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(settings),
            timeout=30
        )
        response.raise_for_status()
        print(f"✅ インデックス作成完了")
        return True
    except Exception as e:
        print(f"❌ インデックス作成失敗: {e}")
        return False


def load_usda_data(json_file_path: str) -> List[Dict]:
    """USDA統合DBを読み込み"""
    try:
        print(f"📖 USDAデータ読み込み中: {json_file_path}")
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"✅ {len(data)}件のアイテムを読み込みました")
        return data
    except Exception as e:
        print(f"❌ データ読み込み失敗: {e}")
        return []


def bulk_index_documents(es_url: str, index_name: str, documents: List[Dict], batch_size: int = 500) -> bool:
    """ドキュメントをバルクインデックス"""
    try:
        total_docs = len(documents)
        print(f"💾 {total_docs}件のドキュメントをインデックス化中...")

        # バッチ処理
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i+batch_size]

            # Bulk APIフォーマット作成
            bulk_data = []
            for doc in batch:
                # インデックス指示
                bulk_data.append(json.dumps({"index": {"_index": index_name, "_id": doc["id"]}}))
                # ドキュメント本体
                bulk_data.append(json.dumps(doc))

            bulk_body = "\n".join(bulk_data) + "\n"

            # Bulk APIリクエスト
            response = requests.post(
                f"{es_url}/_bulk",
                headers={"Content-Type": "application/x-ndjson"},
                data=bulk_body.encode('utf-8'),
                timeout=60
            )
            response.raise_for_status()

            result = response.json()

            # エラーチェック
            if result.get("errors", False):
                print(f"⚠️  バッチ {i//batch_size + 1}: 一部エラーがあります")
                for item in result.get("items", []):
                    if "error" in item.get("index", {}):
                        print(f"   エラー: {item['index']['error']}")
            else:
                progress = min(i + batch_size, total_docs)
                print(f"   ✅ 進捗: {progress}/{total_docs} ({progress/total_docs*100:.1f}%)")

        print(f"✅ インデックス化完了: {total_docs}件")
        return True

    except Exception as e:
        print(f"❌ インデックス化失敗: {e}")
        return False


def verify_index(es_url: str, index_name: str) -> Dict:
    """インデックスの確認"""
    try:
        print(f"🔍 インデックス検証中: {index_name}")

        # ドキュメント数確認
        count_response = requests.get(
            f"{es_url}/{index_name}/_count",
            timeout=10
        )
        count_response.raise_for_status()
        count_result = count_response.json()
        doc_count = count_result.get("count", 0)

        # インデックス情報確認
        stats_response = requests.get(
            f"{es_url}/{index_name}/_stats",
            timeout=10
        )
        stats_response.raise_for_status()
        stats_result = stats_response.json()

        size_in_bytes = stats_result["indices"][index_name]["total"]["store"]["size_in_bytes"]
        size_mb = size_in_bytes / (1024 * 1024)

        print(f"✅ インデックス検証完了:")
        print(f"   - ドキュメント数: {doc_count}件")
        print(f"   - インデックスサイズ: {size_mb:.2f} MB")

        return {
            "doc_count": doc_count,
            "size_mb": size_mb
        }

    except Exception as e:
        print(f"❌ インデックス検証失敗: {e}")
        return {}


def main():
    """メイン処理"""
    print("="*80)
    print("🚀 USDA Unified Database Elasticsearch Loader")
    print("="*80)
    print()

    # 設定情報表示
    print(f"📋 設定情報:")
    print(f"   - Elasticsearch URL: {ELASTICSEARCH_URL}")
    print(f"   - インデックス名: {USDA_INDEX_NAME}")
    print()

    # USDA統合DBのパス
    db_path = Path(__file__).parent.parent.parent.parent / "usda_data_processing" / "db" / "usda_unified_db.json"

    if not db_path.exists():
        print(f"❌ エラー: USDAデータが見つかりません: {db_path}")
        return False

    print(f"📁 データパス: {db_path}")
    print()

    # ステップ1: Elasticsearch接続確認
    print("ステップ1: Elasticsearch接続確認")
    if not check_elasticsearch_connection(ELASTICSEARCH_URL):
        return False
    print()

    # ステップ2: 既存インデックス削除
    print("ステップ2: 既存インデックス削除")
    if not delete_index_if_exists(ELASTICSEARCH_URL, USDA_INDEX_NAME):
        return False
    print()

    # ステップ3: 新しいインデックス作成
    print("ステップ3: 新しいインデックス作成")
    index_settings = get_index_settings()
    if not create_index(ELASTICSEARCH_URL, USDA_INDEX_NAME, index_settings):
        return False
    print()

    # ステップ4: USDAデータ読み込み
    print("ステップ4: USDAデータ読み込み")
    documents = load_usda_data(str(db_path))
    if not documents:
        return False
    print()

    # ステップ5: ドキュメントのインデックス化
    print("ステップ5: ドキュメントのインデックス化")
    if not bulk_index_documents(ELASTICSEARCH_URL, USDA_INDEX_NAME, documents):
        return False
    print()

    # ステップ6: インデックス検証
    print("ステップ6: インデックス検証")
    verify_index(ELASTICSEARCH_URL, USDA_INDEX_NAME)
    print()

    print("="*80)
    print("🎉 インデックス化完了！")
    print("="*80)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
