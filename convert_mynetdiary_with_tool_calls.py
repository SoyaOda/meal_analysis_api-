#!/usr/bin/env python3
"""
Tool callsを使用してMyNetDiaryデータベースを確実に変換
検索意図最適化のために食品名を適切に分離
"""

import os
import json
import asyncio
import time
from typing import Dict, List, Any
from anthropic import Anthropic
from pydantic import BaseModel, Field

# Pydanticモデル定義
class FoodSeparationResult(BaseModel):
    search_name: str = Field(description="Primary searchable term representing core food identity")
    description: str = Field(description="Additional modifiers as comma-separated values or 'None'")

class MyNetDiaryConverter:
    """MyNetDiaryデータベース変換クラス（Tool calls使用）"""
    
    def __init__(self, api_key: str, prompt_file: str = "food_name_separation_prompt_v2.txt"):
        self.client = Anthropic(api_key=api_key)
        self.converted_count = 0
        self.error_count = 0
        self.batch_size = 5  # Tool callsは少し遅いので小さくする
        
        # プロンプトファイルを読み込み
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self.system_prompt = f.read().strip()
            print(f"✅ Loaded prompt from: {prompt_file}")
        except FileNotFoundError:
            print(f"❌ Prompt file not found: {prompt_file}")
            raise
        except Exception as e:
            print(f"❌ Error reading prompt file: {e}")
            raise
        
    async def convert_food_item(self, food_name: str) -> Dict[str, str]:
        """単一食品項目の変換（Tool calls使用）"""
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                system=self.system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Please separate this food name: {food_name}"
                }],
                tools=[{
                    "name": "separate_food_name",
                    "description": "Separate a food name into search_name and description components",
                    "input_schema": FoodSeparationResult.model_json_schema()
                }],
                tool_choice={"type": "tool", "name": "separate_food_name"}  # 強制的にツールを使用
            )
            
            # Tool callの結果を取得
            tool_result = response.content[0].input
            self.converted_count += 1
            return tool_result
            
        except Exception as e:
            self.error_count += 1
            print(f"❌ Error converting '{food_name}': {e}")
            return {"search_name": food_name, "description": "None", "error": str(e)}
    
    async def convert_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """バッチ変換"""
        converted_items = []
        
        # バッチごとに処理
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = []
            
            print(f"🔄 Processing batch {i//self.batch_size + 1}/{(len(items) + self.batch_size - 1)//self.batch_size} (items {i+1}-{min(i+self.batch_size, len(items))})")
            
            # 並列処理は遅くなるので逐次処理に変更
            for item in batch:
                try:
                    original_name = item["search_name"]
                    separation_result = await self.convert_food_item(original_name)
                    
                    # 新しい構造で項目を作成
                    converted_item = {
                        "id": item["id"],
                        "original_name": item["search_name"],  # 元の名前を保持
                        "search_name": separation_result["search_name"],
                        "description": separation_result["description"],
                        "nutrition": item["nutrition"],
                        "data_type": item["data_type"],
                        "source": item["source"],
                        "processing_method": "improved_prompt_v2_tool_calls",
                        "conversion_timestamp": time.time()
                    }
                    
                    # エラー情報があれば追加
                    if "error" in separation_result:
                        converted_item["conversion_error"] = separation_result["error"]
                    
                    batch_results.append(converted_item)
                    
                    # 変換結果を即座に表示
                    print(f"  ✅ {original_name} → {separation_result['search_name']} | {separation_result['description']}")
                    
                except Exception as e:
                    print(f"❌ Failed to process item {item['id']}: {e}")
                    # エラー時も基本構造は保持
                    error_item = item.copy()
                    error_item["original_name"] = item["search_name"]
                    error_item["conversion_error"] = str(e)
                    batch_results.append(error_item)
            
            converted_items.extend(batch_results)
            
            # 進捗表示
            print(f"✅ Batch completed. Converted: {self.converted_count}, Errors: {self.error_count}")
            print(f"📊 Overall progress: {len(converted_items)}/{len(items)} ({len(converted_items)/len(items)*100:.1f}%)")
            
            # APIレート制限対策（tool callsは少し遅い）
            if i + self.batch_size < len(items):
                print("⏳ Waiting 3 seconds...")
                await asyncio.sleep(3)
        
        return converted_items
    
    def save_results(self, converted_items: List[Dict[str, Any]], output_file: str):
        """結果をファイルに保存"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(converted_items, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Results saved to: {output_file}")
        print(f"📊 Final statistics:")
        print(f"   - Total items: {len(converted_items)}")
        print(f"   - Successful conversions: {self.converted_count}")
        print(f"   - Errors: {self.error_count}")
        print(f"   - Success rate: {(self.converted_count/len(converted_items)*100):.1f}%")


async def main():
    """メイン変換処理"""
    
    # API key確認
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        print("   Please set: export ANTHROPIC_API_KEY='your-api-key'")
        return
    
    # 入力ファイル確認
    input_file = "db/mynetdiary_db.json"
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    # データロード
    print("📂 Loading MyNetDiary database...")
    with open(input_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    print(f"✅ Loaded {len(original_data)} items")
    
    # 変換器初期化
    converter = MyNetDiaryConverter(api_key)
    
    # 変換実行
    print("🚀 Starting conversion with Tool Calls (100% reliable)...")
    converted_data = await converter.convert_batch(original_data)
    
    # 結果保存
    output_file = "db/mynetdiary_converted_tool_calls.json"
    converter.save_results(converted_data, output_file)
    
    # サンプル結果表示
    print("\n🔍 Sample conversion results:")
    for i, item in enumerate(converted_data[:5], 1):
        print(f"{i}. Original: \"{item['original_name']}\"")
        print(f"   New search_name: \"{item['search_name']}\"")
        print(f"   New description: \"{item['description']}\"")
        if 'conversion_error' in item:
            print(f"   ⚠️ Error: {item['conversion_error']}")
        print()


if __name__ == "__main__":
    asyncio.run(main()) 