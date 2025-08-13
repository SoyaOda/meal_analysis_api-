#!/usr/bin/env python3
"""
改良プロンプトを使用してMyNetDiaryデータベースを変換
検索意図最適化のために食品名を適切に分離
"""

import os
import json
import asyncio
import time
from typing import Dict, List, Any
from anthropic import Anthropic

# 改良版プロンプト
IMPROVED_PROMPT = """You are a food database expert specializing in separating food names into searchable components that optimize search relevance and user intent.

Your task is to separate food names into two parts:
1. **search_name**: The primary searchable term that represents the core food identity users would query for
2. **description**: Additional modifiers as comma-separated values (or "None" if no modifiers)

## CORE PRINCIPLE: Search Intent Optimization

**General Search Intent**: When users search for "coffee", they typically want basic coffee, not specialized products like instant powder.
**Specific Search Intent**: When users search for "coffee powder", they want that specific product.

## CRITICAL RULES:

### Search Name Guidelines:

#### **Include in search_name (Core Food Identity):**
1. **Base food names**: coffee, tea, rice, beans, chicken
2. **Alternative names with "or"**: "Chickpeas or garbanzo beans", "Cannellini or white kidney beans"  
3. **Distinct food forms/products**: 
   - **Powders**: coffee powder, tea powder, garlic powder, onion powder
   - **Sauces**: tomato sauce, pasta sauce, soy sauce, buffalo wing sauce
   - **Pastes**: tomato paste, curry paste, miso paste  
   - **Purees**: tomato puree, fruit puree
   - **Juices**: tomato juice, orange juice, apple juice
   - **Oils**: olive oil, coconut oil, sesame oil
   - **Butters**: peanut butter, almond butter, apple butter
4. **Specific varieties**: "Mozzarella string cheese", "Basmati rice", "Jasmine rice"
5. **Compound foods**: "Buffalo wing sauce", "Greek yogurt", "Swiss cheese"
6. **Baking/cooking ingredients**: "Baking powder", "Baking soda", "Vanilla extract"

#### **Separate into description (Modifiers):**
1. **Preparation methods**: boiled, baked, grilled, fried, steamed, roasted, cooked, toasted, sautéed
2. **Container/preservation**: canned, fresh, frozen, dried, raw, bottled, jarred, instant
3. **Additives/characteristics**: with salt, without salt, no salt added, low sodium, unsalted, salted, regular, unsweetened
4. **Physical modifications**: chopped, diced, sliced, whole, crushed, ground (when not part of product identity)
5. **Quality descriptors**: reduced fat, low fat, extra virgin, smooth, chunky

### Decision Framework:

**Ask yourself:**
1. **Identity Test**: Is this word essential to the food's core identity?
   - "Coffee powder" → YES (distinct product)  
   - "Coffee regular" → NO (regular is a modifier)

2. **Search Intent Test**: Would users specifically search for this combination?
   - "Tea powder" → YES (specific product search)
   - "Tea regular" → NO (regular is a modifier)

3. **Product Independence Test**: Can this be found as a separate product?
   - "Baking powder" → YES (independent product)
   - "Coffee instant" → NO (instant is a preparation method)

## OUTPUT FORMAT:
Respond with ONLY a JSON object in this exact format:
{"search_name": "...", "description": "..."}

## FINAL VERIFICATION:
1. **Search Intent Check**: Would users searching for just the search_name expect this item to appear prominently?
2. **Reconstruction Check**: Does search_name + description meaningfully reconstruct the original?
3. **Product Identity Check**: Is the search_name a recognizable food product or ingredient?

Now process this food item:"""


class MyNetDiaryConverter:
    """MyNetDiaryデータベース変換クラス"""
    
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.converted_count = 0
        self.error_count = 0
        self.batch_size = 10
        
    async def convert_food_item(self, food_name: str) -> Dict[str, str]:
        """単一食品項目の変換"""
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"{IMPROVED_PROMPT}\n\n{food_name}"
                }]
            )
            
            result_text = response.content[0].text.strip()
            
            # JSONを抽出
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            
            # 追加のテキストを削除（改行後の説明文など）
            if "\n" in result_text:
                lines = result_text.split("\n")
                for line in lines:
                    if line.strip().startswith("{") and line.strip().endswith("}"):
                        result_text = line.strip()
                        break
            
            result = json.loads(result_text)
            self.converted_count += 1
            return result
            
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
            
            # バッチ内の並列処理
            tasks = []
            for item in batch:
                original_name = item["search_name"]
                task = self.convert_food_item(original_name)
                tasks.append((item, task))
            
            # 並列実行
            for item, task in tasks:
                try:
                    separation_result = await task
                    
                    # 新しい構造で項目を作成
                    converted_item = {
                        "id": item["id"],
                        "original_name": item["search_name"],  # 元の名前を保持
                        "search_name": separation_result["search_name"],
                        "description": separation_result["description"],
                        "nutrition": item["nutrition"],
                        "data_type": item["data_type"],
                        "source": item["source"],
                        "processing_method": "improved_prompt_v2",
                        "conversion_timestamp": time.time()
                    }
                    
                    # エラー情報があれば追加
                    if "error" in separation_result:
                        converted_item["conversion_error"] = separation_result["error"]
                    
                    batch_results.append(converted_item)
                    
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
            
            # APIレート制限対策
            if i + self.batch_size < len(items):
                print("⏳ Waiting 2 seconds...")
                await asyncio.sleep(2)
        
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
    print("🚀 Starting conversion with improved prompt...")
    converted_data = await converter.convert_batch(original_data)
    
    # 結果保存
    output_file = "db/mynetdiary_converted_improved.json"
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