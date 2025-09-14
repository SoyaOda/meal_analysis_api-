#!/usr/bin/env python3
"""
DeepInfra APIでMultipart方式とBase64方式の比較テスト
"""
import asyncio
import json
import base64
import aiohttp
import hashlib
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

load_dotenv()

class DeepInfraMultipartTest:
    def __init__(self):
        self.api_key = os.getenv("DEEPINFRA_API_KEY")
        self.model_id = "google/gemma-3-27b-it"
        self.base_url = "https://api.deepinfra.com/v1"
        
    async def analyze_image_base64(self, image_bytes, prompt):
        """Base64方式での分析（現在の方式）"""
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{base64_image}"
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_uri}}
            ]
        }]
        
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.0,
            "seed": 123456,
            "top_p": 1.0,
            "response_format": {"type": "json_object"}
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/openai/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    text = await response.text()
                    raise Exception(f"Base64 API error {response.status}: {text}")
    
    async def analyze_image_multipart(self, image_bytes, prompt):
        """Multipart方式での分析（新しく試す方式）"""
        # DeepInfraのマルチパート対応APIエンドポイントを確認
        # 注意: DeepInfraがmultipart対応していない場合、このメソッドは失敗する
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # multipart/form-dataでの送信を試行
        data = aiohttp.FormData()
        data.add_field('image', image_bytes, filename='image.jpg', content_type='image/jpeg')
        data.add_field('prompt', prompt)
        data.add_field('max_tokens', '4096')
        data.add_field('temperature', '0.0')
        data.add_field('seed', '123456')
        data.add_field('model', self.model_id)
        
        async with aiohttp.ClientSession() as session:
            try:
                # 推測：multipart対応のエンドポイント
                async with session.post(
                    f"{self.base_url}/inference/{self.model_id}",
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        text = await response.text()
                        raise Exception(f"Multipart API error {response.status}: {text}")
            except Exception as e:
                print(f"❌ Multipart方式はサポートされていません: {e}")
                return None

async def test_both_methods():
    """両方式での比較テスト"""
    tester = DeepInfraMultipartTest()
    
    # テスト画像の読み込み
    image_path = "test_images/food1.jpg"
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # プロンプト（Phase1と同じ）
    from app_v2.config.prompts.phase1_prompts import Phase1Prompts
    prompt = Phase1Prompts.get_gemma3_prompt()
    
    # 画像ハッシュ
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    print(f"🔍 Test Image: {image_path}")
    print(f"📄 Image Hash: {image_hash}")
    print()
    
    # Base64方式テスト
    print("🧪 Base64方式テスト中...")
    try:
        base64_result = await tester.analyze_image_base64(image_bytes, prompt)
        print("✅ Base64方式成功")
        
        # JSONパース
        base64_data = json.loads(base64_result)
        if "dishes" in base64_data:
            print(f"🍽️ Base64結果: {len(base64_data['dishes'])}料理検出")
        
    except Exception as e:
        print(f"❌ Base64方式エラー: {e}")
        base64_result = None
    
    print()
    
    # Multipart方式テスト
    print("🧪 Multipart方式テスト中...")
    try:
        multipart_result = await tester.analyze_image_multipart(image_bytes, prompt)
        if multipart_result:
            print("✅ Multipart方式成功")
            print(f"🍽️ Multipart結果: {multipart_result}")
        else:
            print("❌ Multipart方式未対応")
            multipart_result = None
    except Exception as e:
        print(f"❌ Multipart方式エラー: {e}")
        multipart_result = None
    
    # 結果比較
    if base64_result and multipart_result:
        print("\n📊 比較結果:")
        print("Base64とMultipart両方式で結果取得成功")
        # 詳細比較は後で実装
    else:
        print("\n💡 結論:")
        print("DeepInfraはMultipart方式をサポートしていない可能性があります")
        print("Base64方式のみが利用可能です")

if __name__ == "__main__":
    asyncio.run(test_both_methods())
