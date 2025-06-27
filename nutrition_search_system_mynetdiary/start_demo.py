#!/usr/bin/env python3
"""
栄養検索システム デモランチャー
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# パスの設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_elasticsearch():
    """Elasticsearchの接続チェック"""
    try:
        from utils.elasticsearch_client import get_elasticsearch_client
        es_client = get_elasticsearch_client()
        
        if es_client.is_connected():
            total_docs = es_client.get_total_documents()
            logger.info(f"✅ Elasticsearch connected: {total_docs} documents available")
            return True
        else:
            logger.error("❌ Elasticsearch not connected")
            return False
    except Exception as e:
        logger.error(f"❌ Elasticsearch connection failed: {e}")
        return False


def run_flask_demo(host='0.0.0.0', port=5000):
    """Flask デモ起動"""
    try:
        from demo import run_demo
        logger.info(f"🚀 Starting Flask Demo on http://{host}:{port}")
        run_demo(host=host, port=port, debug=False)
    except Exception as e:
        logger.error(f"❌ Flask demo failed: {e}")
        sys.exit(1)


def run_fastapi_demo(host='0.0.0.0', port=8001):
    """FastAPI デモ起動"""
    try:
        from api.search_api import run_api
        logger.info(f"🚀 Starting FastAPI Demo on http://{host}:{port}")
        run_api(host=host, port=port)
    except Exception as e:
        logger.error(f"❌ FastAPI demo failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='栄養検索システム デモランチャー')
    parser.add_argument('--mode', choices=['flask', 'fastapi'], default='flask', help='デモのタイプ')
    parser.add_argument('--host', default='0.0.0.0', help='ホストアドレス')
    parser.add_argument('--port', type=int, help='ポート番号')
    parser.add_argument('--check-only', action='store_true', help='接続チェックのみ')
    
    args = parser.parse_args()
    
    # ポート番号のデフォルト設定
    if args.port is None:
        args.port = 5000 if args.mode == 'flask' else 8001
    
    print("🔍 Nutrition Search System Demo Launcher")
    print("=" * 50)
    
    # Elasticsearch接続チェック
    if not check_elasticsearch():
        print("\n❌ Elasticsearch is not running or not connected!")
        print("💡 Please ensure Elasticsearch is running:")
        print("   ../elasticsearch-8.10.4/bin/elasticsearch")
        sys.exit(1)
    
    if args.check_only:
        print("✅ All systems ready!")
        return
    
    print(f"\n🚀 Starting {args.mode.upper()} demo on http://{args.host}:{args.port}")
    print("=" * 50)
    
    if args.mode == 'flask':
        run_flask_demo(args.host, args.port)
    else:
        run_fastapi_demo(args.host, args.port)


if __name__ == '__main__':
    main() 