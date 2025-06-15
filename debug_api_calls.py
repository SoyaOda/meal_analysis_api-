#!/usr/bin/env python3
"""
Deep Infra APIコールのデバッグスクリプト
実際にどのAPIが呼ばれているかを詳細にログ出力
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ログレベルを詳細に設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def debug_api_calls():
    """APIコールの詳細をデバッグ"""
    print("🔍 APIコール詳細調査開始...")
    
    # 環境変数の確認
    print(f"DEEPINFRA_API_KEY: {'設定済み' if os.environ.get('DEEPINFRA_API_KEY') else '未設定'}")
    print(f"GEMINI_PROJECT_ID: {'設定済み' if os.environ.get('GEMINI_PROJECT_ID') else '未設定'}")
    print(f"service-account-key.json: {'存在' if Path('service-account-key.json').exists() else '不存在'}")
    
    try:
        from app_v2.services.deepinfra_service import DeepInfraService
        
        # DeepInfraServiceの詳細確認
        print("\n🔧 DeepInfraService詳細確認...")
        service = DeepInfraService()
        print(f"Model ID: {service.model_id}")
        print(f"Client base URL: {service.client.base_url}")
        print(f"Client API Key (first 10 chars): {service.client.api_key[:10]}...")
        
        # 実際のAPIコールテスト
        print("\n📡 実際のAPIコールテスト...")
        
        # テスト画像を読み込み
        image_path = Path("test_images/food1.jpg")
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # プロンプトを取得
        from app_v2.config.prompts.phase1_prompts import Phase1Prompts
        prompt = Phase1Prompts.get_gemma3_prompt()
        
        print(f"使用プロンプト (最初の100文字): {prompt[:100]}...")
        
        # APIコール実行（詳細ログ付き）
        result = await service.analyze_image(
            image_bytes=image_bytes,
            image_mime_type="image/jpeg",
            prompt=prompt,
            temperature=0.0
        )
        
        print(f"\n📋 APIレスポンス (最初の500文字):")
        print(result[:500])
        print("...")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン実行関数"""
    print("🔍 APIコール詳細調査")
    print("=" * 50)
    
    success = await debug_api_calls()
    
    print("\n" + "=" * 50)
    if success:
        print("🎯 調査完了")
    else:
        print("⚠️ 調査中にエラーが発生")

if __name__ == "__main__":
    asyncio.run(main()) 