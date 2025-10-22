#!/usr/bin/env python
"""
USDA食材名分割処理 v2 - 前処理済みデータ版

前処理済みデータを使用してLLM処理を行うバージョン。
データがすでにクリーニングされているため、プロンプトがシンプルになります。

入力:
- usda_raw_ingredients_preprocessed.json
- usda_prepared_ingredients_preprocessed.json

出力:
- usda_raw_ingredients_search_patterns.json
- usda_prepared_ingredients_search_patterns.json
"""

import asyncio
import json
import os
import time
import random
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from openai import AsyncOpenAI


# =================================
# 設定
# =================================

# DeepInfra設定
DEEPINFRA_BASE_URL = "https://api.deepinfra.com/v1/openai"
MODEL = "google/gemma-3-27b-it"

# バッチ処理設定
BATCH_SIZE = 10
DELAY_BETWEEN_BATCHES = 1.0
MAX_RETRIES = 3


# =================================
# データ読み込み
# =================================

def load_preprocessed_data(filepath: str) -> List[Dict]:
    """前処理済みデータを読み込み、フラット化"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # カテゴリごとのデータをフラット化
    flat_list = []
    for category, category_info in data['categories'].items():
        for food in category_info['foods']:
            # LLM処理に必要な情報のみ抽出
            flat_list.append({
                'foodCode': food['foodCode'],
                'description': food['description'],
                'category': category,
                'category_emoji': food.get('category_emoji', '🍽️'),  # 絵文字を抽出
                'original_description': food.get('original_description'),
                'preprocessed_info': food.get('preprocessed_info', {}),
                'foodNutrients': food.get('foodNutrients', [])
            })

    return flat_list


# =================================
# プロンプト生成（シンプル版）
# =================================

def create_search_pattern_prompt(recent_results: List[Dict] = None, upcoming_items: List[Dict] = None) -> str:
    """
    前処理済みデータ用の包括的プロンプト
    display_name、ai_descriptionなど全フィールドを生成
    
    Args:
        recent_results: 最近処理した10件の結果（全フィールド情報を含む）
        upcoming_items: 次に処理する10件のアイテム（descriptionのみ）
    """

    # 文脈セクション - 前10例（全フィールド表示）
    context_section = ""
    if recent_results and len(recent_results) > 0:
        context_section = "\n\n📝 RECENT EXAMPLES FOR CONSISTENCY:\n"
        context_section += "Use these recent examples to maintain consistent formatting and classification.\n"
        context_section += "Pay special attention to display_name + display_variant combinations to avoid duplicates.\n\n"

        for i, result in enumerate(recent_results[-10:], 1):  # 最新10件を使用
            search_patterns = json.dumps(result.get('search_name', []), ensure_ascii=False)
            context_section += f"{i}. \"{result.get('description', 'N/A')}\"\n"
            
            # 全フィールドを表示
            context_section += f"   → display_name: \"{result.get('display_name', 'N/A')}\"\n"
            context_section += f"   → display_variant: {json.dumps(result.get('display_variant'), ensure_ascii=False)}\n"
            context_section += f"   → display_badges: {json.dumps(result.get('display_badges', []), ensure_ascii=False)}\n"
            context_section += f"   → brand_name: {json.dumps(result.get('brand_name'), ensure_ascii=False)}\n"
            context_section += f"   → item_type: \"{result.get('item_type', 'N/A')}\"\n"
            context_section += f"   → ai_description: {json.dumps(result.get('ai_description'), ensure_ascii=False)}\n"
            context_section += f"   → food_specific_emoji: {json.dumps(result.get('food_specific_emoji'), ensure_ascii=False)}\n"
            context_section += f"   → consumption_frequency: \"{result.get('consumption_frequency', 'N/A')}\" (score: {result.get('frequency_score', 0)})\n"
            context_section += f"   → search_name: {search_patterns}\n"
            context_section += "\n"

    # 後10例セクション
    upcoming_section = ""
    if upcoming_items and len(upcoming_items) > 0:
        upcoming_section = "\n\n🔮 UPCOMING ITEMS TO DIFFERENTIATE:\n"
        upcoming_section += "The following items will be processed next. Make sure your current output creates a UNIQUE\n"
        upcoming_section += "display_name + display_variant combination that won't conflict with these:\n\n"
        
        for i, item in enumerate(upcoming_items[:10], 1):  # 最大10件
            description = item.get('description', 'N/A')
            upcoming_section += f"{i}. \"{description}\"\n"
        
        upcoming_section += "\n"

    # 重複防止ルールセクション
    duplication_rules = """

🚫 CRITICAL: DUPLICATE PREVENTION RULES

The combination of display_name + display_variant MUST be completely unique!

✅ DIFFERENTIATION STRATEGIES FOR SIMILAR FOODS:

1. **Same Base Food (e.g., Chicken Nuggets, French Fries)**
   → Use same display_name, differentiate with display_variant
   
   Examples:
   - "Chicken nuggets, NFS" → display_name: "Chicken Nuggets", display_variant: null
   - "Chicken nuggets, from fast food" → display_name: "Chicken Nuggets", display_variant: "Fast Food"
   - "Chicken nuggets, from restaurant" → display_name: "Chicken Nuggets", display_variant: "Restaurant"
   - "Chicken nuggets, from school lunch" → display_name: "Chicken Nuggets", display_variant: "School"

2. **Branded Products**
   → Include brand_name in display_name
   
   Examples:
   - "Crackers, butter (Ritz)" → display_name: "Ritz Butter Crackers", brand_name: "Ritz"
   - "Crackers, butter (Nabisco)" → display_name: "Nabisco Butter Crackers", brand_name: "Nabisco"

3. **Different Cooking Methods or Preparations**
   → Use display_variant to distinguish
   
   Examples:
   - "Potato, mashed, NFS" → display_name: "Mashed Potatoes", display_variant: null
   - "Potato, mashed, ready-to-heat" → display_name: "Mashed Potatoes", display_variant: "Ready-to-Heat"
   - "Potato, mashed, from fast food" → display_name: "Mashed Potatoes", display_variant: "Fast Food"

4. **Key Variants (sugar-free, low-fat, diet, organic)**
   → MUST be reflected in display_name OR display_variant
   
   Examples:
   - "Tea, iced, black, unsweetened" → display_name: "Unsweetened Iced Black Tea", display_variant: null
   - "Tea, iced, black, pre-sweetened" → display_name: "Pre-Sweetened Iced Black Tea", display_variant: null
   - "Tea, iced, black, pre-sweetened (diet)" → display_name: "Pre-Sweetened Iced Black Tea", display_variant: "Diet"

⚠️ BEFORE FINALIZING YOUR OUTPUT:
- Check recent examples above - does your display_name + display_variant combination already exist?
- Check upcoming items - will your output conflict with likely outputs for those items?
- If conflict is possible, adjust display_variant to make it unique

"""

    return f"""You are a food search optimization AI. Return ONLY a valid JSON object with NO additional text.

{context_section}{upcoming_section}{duplication_rules}
🎯 YOUR TASK:
Transform food descriptions into search patterns optimized for autocomplete/predictive search systems.
IMPORTANT: Return ONLY the JSON object. Do not include any explanatory text before or after the JSON.

⚡ REQUIRED OUTPUT FORMAT:
{{
  "search_name": ["pattern1", "pattern2", "pattern3"],
  "display_name": "User Friendly Name",
  "display_variant": "Variant" or null,
  "display_badges": ["Badge1"] or [],
  "ai_description": "extra info" or null,
  "consumption_frequency": "common" | "moderate" | "rare",
  "frequency_score": 3 | 2 | 1,
  "food_specific_emoji": "🍓" or null,
  "brand_name": "Brand Name" or null,
  "item_type": "raw_ingredient" | "processed_ingredient" | "prepared_dish"
}}

📋 FIELD RULES:

1️⃣ **search_name** (REQUIRED ARRAY)
   - Generate 3-6 search patterns for autocomplete/predictive search
   
   🎯 **PRIMARY GOAL: Autocomplete Optimization**
   - System shows multiple ranked suggestions as user types
   - Patterns should match partial inputs at any typing stage
   - Balance between specificity and discoverability
   - Users rely on suggestions rather than typing complete queries
   
   📝 **USDA Format Interpretation**
   - "Main, modifier" format describes specific food variants
   - Interpret the semantic relationship to generate natural search terms
   - "Wine, rice" = rice wine/sake (not wine + rice)
   - "Bread, French" = French bread/baguette (not bread + French)
   - Generate patterns users would recognize and select from suggestions
   
   🔍 **Pattern Strategy**
   - PRIORITY ORDER (most to least specific):
     1. Most complete/specific name (best for users who know exactly what they want)
     2. Common alternative names (regional/cultural variations)
     3. Shortened but recognizable forms
     4. Category terms (for browsing users)
   - Include partial patterns that would trigger relevant suggestions
   - Consider progressive refinement: user types generic → sees options → selects specific
   
   💡 **Practical Considerations**
   - Include patterns for different user knowledge levels
   - Some redundancy is acceptable for better coverage
   - Think about the autocomplete experience: what would help users find this item?
   - Balance: too specific = hard to find; too generic = lost in results

2️⃣ **display_name** (REQUIRED STRING)
   - **PRIMARY GOAL: Uniqueness and Clarity**
   - Display name must be unique enough to distinguish similar items
   - Length: 15-40 characters (extended for brands/variants)

   **CRITICAL RULES FOR UNIQUENESS**:

   ⭐ **Rule 1: Brand Names are MANDATORY in display_name if present**
      - If `brand_name` field is not null, INCLUDE it in display_name
      - Examples:
        * "Crackers, butter (Ritz)" → display_name: "Ritz Butter Crackers" (NOT just "Butter Crackers")
        * "Energy drink (Monster)" → display_name: "Monster Energy Drink" (NOT just "Energy Drink")
        * "Granola bar (Quaker Chewy)" → display_name: "Quaker Chewy Granola Bar" (NOT just "Granola Bar")

   ⭐ **Rule 2: Key Variants MUST be included**
      - Sugar-free, low-fat, diet, organic, etc. are distinguishing features
      - Examples:
        * "Energy drink, sugar-free (Monster)" → display_name: "Monster Sugar-Free Energy Drink"
        * "Milk, reduced fat (2%)" → display_name: "2% Reduced Fat Milk"
        * "Tea, iced, decaffeinated, diet" → display_name: "Diet Decaf Iced Tea"

   ⭐ **Rule 3: Avoid Generic Names**
      - NEVER use just "Granola Bar", "Energy Drink", "Crackers", "Pizza" alone
      - ALWAYS add distinguishing features: brand, variant, or type
      - Examples:
        * BAD: "Granola Bar" (too generic, will create duplicates)
        * GOOD: "Nature Valley Granola Bar", "Chewy Granola Bar", "Chocolate Granola Bar"

   ⭐ **Rule 4: Check for Potential Duplicates**
      - If the description has parenthetical info (brand/variant), it MUST appear in display_name
      - If there are specific modifiers (sugar-free, diet, organic), they MUST appear in display_name
      - Think: "Would this display_name distinguish it from similar products?"

   **Format Priority**:
   1. With Brand: "[Brand] [Key Variant] [Base Food]" (e.g., "Monster Sugar-Free Energy Drink")
   2. With Variant: "[Key Variant] [Base Food]" (e.g., "Diet Iced Tea")
   3. Generic: "[Specific Type] [Base Food]" (e.g., "Thin Crust Cheese Pizza")

3️⃣ **display_variant** (OPTIONAL STRING or null)
   - 5-15 characters
   - Only if there's a significant variant NOT already in display_name
   - Examples: "Fast Food", "Restaurant", "School", "No-Bake", "Thin Crust", "Toasted", "Skinless"
   - Set to null if not applicable
   - **CRITICAL**: Use this field to differentiate similar items with same base display_name

4️⃣ **display_badges** (OPTIONAL ARRAY)
   - Array of 0-3 short badges
   - Each badge 3-8 characters
   - Priority: Nutrition > Cooking > Source
   - Common badges: "Diet", "Lite", "Fiber+", "Grilled", "Raw", "School"
   - Empty array [] if none apply

5️⃣ **ai_description** (OPTIONAL STRING or null)
   - ONLY include modifiers NOT in search_name
   - Examples: "reduced calorie", "from restaurant", "low fat"
   - Set to null if everything is covered by search_name

6️⃣ **consumption_frequency** (REQUIRED STRING)
   - North American consumption frequency classification
   - "common" = Daily staples (3+ times/week) - bread, milk, chicken, eggs
   - "moderate" = Weekly items (1-2 times/week) - salmon, avocado, berries
   - "rare" = Special occasions (<1 time/month) - lobster, caviar, exotic items
   - Consider: price point, availability at Walmart/Costco, typical diet

   IMPORTANT RAW FOOD RULES:
   - Salad vegetables (cucumber, lettuce, tomato, carrot) → Keep normal frequency even if "raw"
   - Fruits (apple, banana, orange, berries) → Keep normal frequency even if "raw"
   - Raw meat/fish/poultry → Lower frequency by 1 level (people cook before eating)
   - Raw grains/beans → Lower frequency by 1 level (require cooking)

7️⃣ **frequency_score** (REQUIRED NUMBER)
   - Numeric score matching consumption_frequency
   - common = 3, moderate = 2, rare = 1

8️⃣ **food_specific_emoji** (OPTIONAL STRING or null)
   - **CRITICAL**: This is for the FOOD ITSELF, NOT flavors, variants, or cooking methods
   - ONLY suggest when:
     * Category emoji is generic (🍽️) AND the food deserves a specific emoji
     * The emoji represents the MAIN FOOD ITEM, not its flavor or preparation

   - **NEVER suggest for**:
     * Flavors: chocolate, strawberry, vanilla, blueberry (these are NOT the main food)
     * Cooking methods: grilled, fried, baked, toasted
     * Variants: low-fat, sugar-free, organic

   - **DO suggest for**:
     * Generic category with specific food: "Cocoa powder" (🍽️) → ☕
     * Generic category with specific food: "Wheat germ" (🍽️) → 🌾
     * Generic category with specific food: "Basil, raw" (🍽️) → 🌿

   - Set to null for 95%+ of items

9️⃣ **brand_name** (OPTIONAL STRING or null)
   - Extract brand names from parenthetical information ONLY
   - Brand names are proper nouns identifying commercial products
   - Examples of BRAND NAMES to extract:
     * "Crackers, butter (Ritz)" → brand_name: "Ritz"
     * "Energy drink (Red Bull)" → brand_name: "Red Bull"
     * "Cheeseburger (McDonalds)" → brand_name: "McDonalds"
     * "Instant oatmeal (Quaker)" → brand_name: "Quaker"

   - Examples of NON-BRAND parenthetical info (set to null):
     * "Milk, reduced fat (2%)" → brand_name: null (specification, not brand)
     * "Milk, fat free (skim)" → brand_name: null (description, not brand)
     * "Milk (vitamin D fortified)" → brand_name: null (feature, not brand)
     * "Flour (enriched)" → brand_name: null (processing method, not brand)

   - Set to null if:
     * No parentheses exist in the description
     * Parenthetical info is a specification/description, not a brand
     * Unsure whether it's a brand name

🔟 **item_type** (REQUIRED STRING)
   - Classify into one of three categories:

   **"raw_ingredient"** = Unprocessed, single-ingredient foods
   - Fresh produce: vegetables, fruits, herbs
   - Raw proteins: chicken, beef, fish, eggs (without cooking keywords)
   - Basic grains/legumes: rice, beans, wheat
   - Examples: "Chicken breast", "Tomato, raw", "Rice", "Apple"

   **"processed_ingredient"** = Commercially processed but still ingredients
   - Packaged foods: crackers, cereal, pasta, bread
   - Processed proteins: bacon, sausage, deli meat
   - Dairy products: cheese, yogurt, butter
   - Condiments and sauces: ketchup, mayo, soy sauce
   - Canned/jarred items: canned beans, pickles
   - Items with brand names in parentheses
   - Examples: "Crackers, butter (Ritz)", "Bread, white", "Cheese, Cheddar"

   **"prepared_dish"** = Ready-to-eat or cooked dishes
   - Contains cooking keywords: cooked, grilled, baked, fried, toasted, etc.
   - Restaurant items: "from restaurant", "fast food"
   - Ready-to-eat meals: "Pizza, cheese", "Sandwich, turkey"
   - Composite dishes: foods made from multiple ingredients
   - Examples: "Chicken breast, grilled", "Pizza, cheese, from restaurant", "Mashed potatoes"

   CLASSIFICATION TIPS:
   - If description contains cooking keywords (cooked, grilled, baked, fried, toasted, broiled, roasted, boiled, steamed, sauteed, braised, stewed, smoked) → "prepared_dish"
   - If has brand name OR is packaged/commercially processed → "processed_ingredient"
   - If raw, unprocessed, single ingredient → "raw_ingredient"
   - Default to "processed_ingredient" if uncertain

📚 EXAMPLES WITH AUTOCOMPLETE FOCUS:

"Cookie, chocolate chip" (category emoji: 🍪)
{{
  "search_name": ["Chocolate chip cookie", "Choc chip cookie", "Cookie chocolate", "Cookie", "Choc chip"],
  "display_name": "Chocolate Chip Cookie",
  "display_variant": null,
  "display_badges": [],
  "ai_description": null,
  "consumption_frequency": "common",
  "frequency_score": 3,
  "food_specific_emoji": null,
  "brand_name": null,
  "item_type": "processed_ingredient"
}}

"Wine, rice" (category emoji: 🍷)
{{
  "search_name": ["Rice wine", "Sake", "Japanese rice wine", "Rice alcohol", "Asian wine"],
  "display_name": "Rice Wine",
  "display_variant": null,
  "display_badges": [],
  "ai_description": null,
  "consumption_frequency": "moderate",
  "frequency_score": 2,
  "food_specific_emoji": null,
  "brand_name": null,
  "item_type": "processed_ingredient"
}}

"Bread, French or Vienna, toasted" (category emoji: 🍞)
{{
  "search_name": ["French bread", "Vienna bread", "Baguette", "French toast", "Toasted bread"],
  "display_name": "French Bread",
  "display_variant": "Toasted",
  "display_badges": [],
  "ai_description": null,
  "consumption_frequency": "common",
  "frequency_score": 3,
  "food_specific_emoji": null,
  "brand_name": null,
  "item_type": "prepared_dish"
}}

"Pizza, cheese, from restaurant, thin crust" (category emoji: 🍕)
{{
  "search_name": ["Cheese pizza", "Thin crust pizza", "Pizza cheese", "Pizza thin", "Restaurant pizza"],
  "display_name": "Cheese Pizza",
  "display_variant": "Thin Crust",
  "display_badges": ["Restaurant"],
  "ai_description": "from restaurant",
  "consumption_frequency": "common",
  "frequency_score": 3,
  "food_specific_emoji": null,
  "brand_name": null,
  "item_type": "prepared_dish"
}}

"Chicken breast, grilled, skinless" (category emoji: 🍗)
{{
  "search_name": ["Chicken breast", "Grilled chicken", "Chicken grilled", "Skinless chicken", "Chicken"],
  "display_name": "Grilled Chicken Breast",
  "display_variant": "Skinless",
  "display_badges": ["Grilled"],
  "ai_description": null,
  "consumption_frequency": "common",
  "frequency_score": 3,
  "food_specific_emoji": null,
  "brand_name": null,
  "item_type": "prepared_dish"
}}

"Cereal or granola bar (General Mills Nature Valley Chewy Trail Mix)" (category emoji: 🍪)
{{
  "search_name": ["Nature Valley granola bar", "Nature Valley chewy", "Trail mix granola", "Granola bar trail mix", "Nature Valley trail mix"],
  "display_name": "Nature Valley Chewy Granola Bar",
  "display_variant": "Trail Mix",
  "display_badges": [],
  "ai_description": null,
  "consumption_frequency": "common",
  "frequency_score": 3,
  "food_specific_emoji": null,
  "brand_name": "Nature Valley",
  "item_type": "processed_ingredient"
}}

"Energy drink, sugar-free (Monster)" (category emoji: 🥤)
{{
  "search_name": ["Monster energy drink", "Monster sugar free", "Sugar free energy drink", "Energy drink Monster", "Monster energy"],
  "display_name": "Monster Sugar-Free Energy Drink",
  "display_variant": "Sugar-Free",
  "display_badges": ["Diet"],
  "ai_description": null,
  "consumption_frequency": "moderate",
  "frequency_score": 2,
  "food_specific_emoji": null,
  "brand_name": "Monster",
  "item_type": "processed_ingredient"
}}

"Crackers, butter (Ritz)" (category emoji: 🍘)
{{
  "search_name": ["Ritz crackers", "Butter crackers Ritz", "Crackers Ritz", "Ritz butter", "Ritz"],
  "display_name": "Ritz Butter Crackers",
  "display_variant": null,
  "display_badges": [],
  "ai_description": null,
  "consumption_frequency": "common",
  "frequency_score": 3,
  "food_specific_emoji": null,
  "brand_name": "Ritz",
  "item_type": "processed_ingredient"
}}

"Tomato, raw" (category emoji: 🍅)
{{
  "search_name": ["Tomato", "Raw tomato", "Fresh tomato", "Tomatoes"],
  "display_name": "Tomato",
  "display_variant": "Raw",
  "display_badges": ["Raw"],
  "ai_description": null,
  "consumption_frequency": "common",
  "frequency_score": 3,
  "food_specific_emoji": null,
  "brand_name": null,
  "item_type": "raw_ingredient"
}}

CRITICAL: Return ONLY valid JSON. No explanatory text. No prefix like "Here is..." or "The result is...". Start directly with {{ and end with }}."""
# =================================
# LLM処理
# =================================

async def generate_search_patterns(
    description: str,
    api_key: str,
    client: AsyncOpenAI,
    category_emoji: str = "🍽️",
    recent_results: List[Dict] = None,
    upcoming_items: List[Dict] = None,
    max_retries: int = 3
) -> Optional[Dict]:
    """
    食材説明から包括的な検索パターンと表示情報を生成
    """
    prompt = create_search_pattern_prompt(recent_results, upcoming_items)

    # カテゴリ絵文字を含むユーザーメッセージを作成
    user_message = f"{description} (category emoji: {category_emoji})"

    for attempt in range(max_retries):
        try:
            # リトライごとにtemperatureを増やす（0 → 0.2 → 0.4）
            current_temperature = attempt * 0.2
            
            response = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=current_temperature,  # リトライごとに増加
                max_tokens=2048  # 最大値に設定
            )

            response_text = response.choices[0].message.content.strip()

            # ```json``` タグを除去
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # ```json を削除
            elif response_text.startswith('```'):
                response_text = response_text[3:]   # ``` を削除
            
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # 末尾の ``` を削除

            # JSONを抽出（余分なテキストがあっても対応）
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
            else:
                json_text = response_text

            # JSONパース
            result = json.loads(json_text)

            # 1. search_name (必須)の検証
            if not isinstance(result.get('search_name'), list):
                if isinstance(result.get('search_name'), str):
                    result['search_name'] = [result['search_name']]
                else:
                    result['search_name'] = [description.split(',')[0].strip()]

            # 最低3パターン確保
            if len(result['search_name']) < 3:
                base = description.split(',')[0].strip()
                if base not in result['search_name']:
                    result['search_name'].insert(0, base)
                while len(result['search_name']) < 3:
                    result['search_name'].append(description.strip())

            # 2. display_name (必須)の検証
            if 'display_name' not in result or not result['display_name']:
                # デフォルト値を生成
                parts = description.split(',')
                if len(parts) >= 2:
                    result['display_name'] = f"{parts[0].strip()} {parts[1].strip()}"[:40]
                else:
                    result['display_name'] = parts[0].strip()[:40]
            elif len(result['display_name']) > 40:
                result['display_name'] = result['display_name'][:40]

            # 3. display_variant (オプション)の検証
            if 'display_variant' not in result:
                result['display_variant'] = None
            elif result['display_variant'] and len(str(result['display_variant'])) > 15:
                result['display_variant'] = str(result['display_variant'])[:15]

            # 4. display_badges (オプション)の検証
            if 'display_badges' not in result:
                result['display_badges'] = []
            elif not isinstance(result['display_badges'], list):
                result['display_badges'] = []
            elif len(result['display_badges']) > 3:
                result['display_badges'] = result['display_badges'][:3]

            # 5. ai_description (オプション)の検証
            if 'ai_description' not in result:
                result['ai_description'] = None

            # 6. consumption_frequency (必須)の検証
            if 'consumption_frequency' not in result:
                # デフォルト値を設定
                result['consumption_frequency'] = 'moderate'
                result['frequency_score'] = 2
            else:
                # frequency_scoreとの整合性確認
                freq_map = {'common': 3, 'moderate': 2, 'rare': 1}
                if result['consumption_frequency'] in freq_map:
                    result['frequency_score'] = freq_map[result['consumption_frequency']]
                else:
                    # 不正な値の場合はmoderateにフォールバック
                    result['consumption_frequency'] = 'moderate'
                    result['frequency_score'] = 2

            # 7. frequency_score (必須)の検証
            if 'frequency_score' not in result:
                # consumption_frequencyから自動設定（上で処理済み）
                pass

            # 8. food_specific_emoji (オプション)の検証
            if 'food_specific_emoji' not in result:
                result['food_specific_emoji'] = None
            elif result['food_specific_emoji'] == "null" or result['food_specific_emoji'] == "":
                result['food_specific_emoji'] = None

            # 9. brand_name (オプション)の検証
            if 'brand_name' not in result:
                result['brand_name'] = None
            elif result['brand_name'] == "null" or result['brand_name'] == "":
                result['brand_name'] = None
            elif isinstance(result['brand_name'], str) and len(result['brand_name']) > 50:
                result['brand_name'] = result['brand_name'][:50]

            # 10. item_type (必須)の検証
            if 'item_type' not in result:
                result['item_type'] = 'processed_ingredient'
            else:
                valid_types = ['raw_ingredient', 'processed_ingredient', 'prepared_dish']
                if result['item_type'] not in valid_types:
                    result['item_type'] = 'processed_ingredient'

            return result

        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSONパースエラー (試行 {attempt+1}/{max_retries}, temp={current_temperature:.1f}): {e}")
            if attempt == 0:  # 初回エラー時のみ詳細表示
                print(f"      レスポンス: {response_text[:200] if 'response_text' in locals() else 'なし'}")
        except Exception as e:
            print(f"   ❌ エラー (試行 {attempt+1}/{max_retries}): {e}")

        if attempt < max_retries - 1:
            await asyncio.sleep(1.0)

    # 失敗した場合のフォールバック（全フィールド付き）
    base = description.split(',')[0].strip()
    return {
        "search_name": [base, description.strip()],
        "display_name": base[:40],
        "display_variant": None,
        "display_badges": [],
        "ai_description": None,
        "consumption_frequency": "moderate",
        "frequency_score": 2,
        "food_specific_emoji": None,
        "brand_name": None,
        "item_type": "processed_ingredient"
    }


# =================================
# バッチ処理
# =================================

async def process_batch(
    items: List[Dict],
    api_key: str,
    recent_results: List[Dict] = None,
    upcoming_items: List[Dict] = None
) -> List[Dict]:
    """バッチ単位で処理（全フィールド対応）"""
    client = AsyncOpenAI(api_key=api_key, base_url=DEEPINFRA_BASE_URL)
    results = []

    tasks = []
    for item in items:
        task = generate_search_patterns(
            item['description'],
            api_key,
            client,
            item.get('category_emoji', '🍽️'),  # カテゴリ絵文字を渡す
            recent_results,
            upcoming_items
        )
        tasks.append(task)

    # 並列実行
    batch_results = await asyncio.gather(*tasks)

    for item, patterns in zip(items, batch_results):
        if patterns:
            results.append({
                'foodCode': item['foodCode'],
                'description': item['description'],
                'category': item['category'],
                'category_emoji': item.get('category_emoji', '🍽️'),  # 絵文字追加
                'search_name': patterns['search_name'],
                'display_name': patterns.get('display_name'),  # 新規追加
                'display_variant': patterns.get('display_variant'),  # 新規追加
                'display_badges': patterns.get('display_badges', []),  # 新規追加
                'ai_description': patterns.get('ai_description'),  # 新規追加
                'consumption_frequency': patterns.get('consumption_frequency', 'moderate'),  # 新規追加
                'frequency_score': patterns.get('frequency_score', 2),  # 新規追加
                'food_specific_emoji': patterns.get('food_specific_emoji'),  # 個別絵文字追加
                'brand_name': patterns.get('brand_name'),  # ブランド名
                'item_type': patterns.get('item_type', 'processed_ingredient'),  # 食材タイプ
                'original_description': item.get('original_description'),
                'foodNutrients': item.get('foodNutrients', [])
            })

    return results


async def process_all_items(
    items: List[Dict],
    api_key: str,
    checkpoint_path: Path = None
) -> List[Dict]:
    """すべてのアイテムを処理"""

    # チェックポイントから復元
    processed_codes = set()
    all_results = []

    if checkpoint_path and checkpoint_path.exists():
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
            all_results = checkpoint_data['results']
            processed_codes = set(r['foodCode'] for r in all_results)
            print(f"   📌 チェックポイントから復元: {len(all_results)}件処理済み")

    # 未処理のアイテムをフィルタ
    remaining_items = [item for item in items if item['foodCode'] not in processed_codes]

    if not remaining_items:
        print("   ✅ すべて処理済みです")
        return all_results

    print(f"   🔄 処理対象: {len(remaining_items)}件")

    # バッチ処理
    for i in range(0, len(remaining_items), BATCH_SIZE):
        batch = remaining_items[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(remaining_items) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"   📦 バッチ {batch_num}/{total_batches}: {len(batch)}件処理中...")

        # 次のバッチから最大10件を取得（upcoming items）
        next_batch_start = i + BATCH_SIZE
        upcoming_items = remaining_items[next_batch_start:next_batch_start+10] if next_batch_start < len(remaining_items) else None

        batch_results = await process_batch(
            batch,
            api_key,
            all_results[-10:] if all_results else None,  # 最新10件を文脈として使用
            upcoming_items  # 次に処理する10件
        )

        all_results.extend(batch_results)

        # チェックポイント保存
        if checkpoint_path:
            checkpoint_data = {
                'timestamp': datetime.now().isoformat(),
                'total_processed': len(all_results),
                'results': all_results
            }
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

        # 次のバッチまで待機
        if i + BATCH_SIZE < len(remaining_items):
            await asyncio.sleep(DELAY_BETWEEN_BATCHES)

    return all_results


# =================================
# テストモード処理
# =================================

async def test_mode_process(
    items: List[Dict],
    api_key: str,
    sample_size: int = 20
) -> List[Dict]:
    """テストモードで指定件数のランダムサンプルを処理"""

    # ランダムサンプル抽出
    sample_items = random.sample(items, min(sample_size, len(items)))
    print(f"\n📊 テストモード: {len(sample_items)}件のランダムサンプルを処理")

    # カテゴリ分布を表示
    categories = {}
    for item in sample_items:
        cat = item['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("\n📂 サンプルのカテゴリ分布:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {count}件 - {cat}")

    # バッチ処理
    all_results = []
    batch_size = 5  # テスト時は小さめのバッチ

    for i in range(0, len(sample_items), batch_size):
        batch = sample_items[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(sample_items) + batch_size - 1) // batch_size

        print(f"\n📦 バッチ {batch_num}/{total_batches}: {len(batch)}件処理中...")

        # 次のバッチから最大10件を取得（upcoming items）
        next_batch_start = i + batch_size
        upcoming_items = sample_items[next_batch_start:next_batch_start+10] if next_batch_start < len(sample_items) else None

        batch_results = await process_batch(
            batch,
            api_key,
            all_results[-5:] if all_results else None,  # 最新5件を文脈として使用
            upcoming_items  # 次に処理する10件
        )

        all_results.extend(batch_results)

        # 処理結果のサンプルを表示
        for result in batch_results[:2]:  # 各バッチ最初の2件を表示
            print(f"   ✅ {result['description'][:40]}...")
            print(f"      → display_name: {result.get('display_name', 'なし')}")

        # 次のバッチまで待機
        if i + batch_size < len(sample_items):
            print("   ⏳ 次のバッチまで待機中...")
            await asyncio.sleep(2.0)  # テスト時は長めに待機

    return all_results


# =================================
# メイン処理
# =================================

async def main():
    """メイン処理"""

    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='USDA検索パターン生成 v2（改良版）')
    parser.add_argument('--test', action='store_true', help='テストモードで実行（20件のサンプル）')
    parser.add_argument('--sample-size', type=int, default=20, help='テストモードのサンプル数（デフォルト: 20）')
    parser.add_argument('--retry-failed', action='store_true', help='フォールバックパターンのアイテムのみ再処理')
    args = parser.parse_args()

    # API設定
    api_key = os.getenv('DEEPINFRA_API_KEY')
    if not api_key:
        print("❌ DEEPINFRA_API_KEYが設定されていません")
        print("   export DEEPINFRA_API_KEY=your_api_key")
        return

    # パス設定
    base_dir = Path("/Users/odasoya/meal_analysis_api_2")
    input_dir = base_dir / "usda_data_processing" / "output"
    output_dir = base_dir / "usda_data_processing" / "output"

    # テストモード用の出力ディレクトリ
    if args.test:
        output_dir = output_dir / "test_results"
        output_dir.mkdir(exist_ok=True)

    print("="*80)
    print("🤖 USDA検索パターン生成 v2（改良版 - 全フィールド対応）")
    print("="*80)
    print(f"📂 入力: {input_dir}")
    print(f"📂 出力: {output_dir}")
    print(f"🤖 モデル: {MODEL}")
    print(f"🔧 モード: {'失敗アイテム再処理' if args.retry_failed else 'テスト' if args.test else 'フル処理'}")
    if args.test:
        print(f"📊 サンプル数: {args.sample_size}")
    print()

    # 処理対象ファイル
    if args.test:
        # テストモードでは最初のファイルのみ
        files_to_process = [
            ("usda_raw_ingredients_preprocessed.json",
             "test_search_patterns.json",
             None)  # テストモードではチェックポイント不要
        ]
    else:
        files_to_process = [
            ("usda_raw_ingredients_preprocessed.json",
             "usda_raw_ingredients_search_patterns.json",
             "usda_raw_search_patterns_checkpoint.json"),
            ("usda_prepared_ingredients_preprocessed.json",
             "usda_prepared_ingredients_search_patterns.json",
             "usda_prepared_search_patterns_checkpoint.json")
        ]

    for input_file, output_file, checkpoint_file in files_to_process:
        input_path = input_dir / input_file
        output_path = output_dir / output_file
        checkpoint_path = output_dir / checkpoint_file if checkpoint_file else None

        print(f"\n📋 処理中: {input_file}")

        # データ読み込み
        try:
            items = load_preprocessed_data(str(input_path))
            print(f"   ✅ {len(items)}件の食材を読み込みました")
        except FileNotFoundError:
            print(f"   ❌ ファイルが見つかりません: {input_path}")
            continue

        # 失敗アイテム再処理モードの場合
        if args.retry_failed:
            # 既存の出力ファイルから失敗アイテムを特定
            if not output_path.exists():
                print(f"   ❌ 出力ファイルが存在しません: {output_path}")
                print(f"      まず通常モードで処理を実行してください")
                continue
            
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # フォールバックパターンのアイテムを検出（search_nameが2個のみ）
            failed_items_codes = set()
            successful_items = []
            
            for item in existing_data.get('items', []):
                if len(item.get('search_name', [])) <= 2:
                    # フォールバックパターンの可能性が高い
                    failed_items_codes.add(item['foodCode'])
                    print(f"   ⚠️ 失敗アイテム検出: {item['description'][:50]}...")
                else:
                    successful_items.append(item)
            
            if not failed_items_codes:
                print(f"   ✅ 失敗アイテムは見つかりませんでした")
                continue
            
            # 失敗アイテムのみフィルタ
            items_to_retry = [item for item in items if item['foodCode'] in failed_items_codes]
            print(f"   🔄 {len(items_to_retry)}件の失敗アイテムを再処理します")
            
            # 再処理実行
            start_time = time.time()
            retry_results = await process_all_items(items_to_retry, api_key, None)
            elapsed_time = time.time() - start_time
            
            # 成功したアイテムと再処理結果を結合
            all_results = successful_items + retry_results
            
            # 結果をfoodCodeでソート
            all_results.sort(key=lambda x: x['foodCode'])
            
            print(f"   📊 再処理結果:")
            success_count = sum(1 for r in retry_results if len(r.get('search_name', [])) > 2)
            print(f"      成功: {success_count}件")
            print(f"      失敗: {len(retry_results) - success_count}件")
            
        # 通常処理
        else:
            start_time = time.time()
            
            if args.test:
                # テストモード処理
                all_results = await test_mode_process(items, api_key, args.sample_size)
            else:
                # フル処理
                all_results = await process_all_items(items, api_key, checkpoint_path)
            
            elapsed_time = time.time() - start_time

        # 結果保存
        output_data = {
            "metadata": {
                "source": input_file,
                "generated": datetime.now().isoformat(),
                "model": MODEL,
                "mode": "retry_failed" if args.retry_failed else "test" if args.test else "full",
                "total_items": len(all_results),
                "processing_time_seconds": elapsed_time if 'elapsed_time' in locals() else 0
            },
            "items": all_results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n   ✅ 保存完了: {output_path}")
        print(f"   📊 処理結果: {len(all_results)}件")
        if 'elapsed_time' in locals():
            print(f"   ⏱️ 処理時間: {elapsed_time:.1f}秒")

        # テストモードの場合、サンプル表示
        if args.test and all_results:
            print("\n📝 生成結果のサンプル（全フィールド）:")
            for item in all_results[:3]:
                print(f"\n   {item.get('category_emoji', '🍽️')} {item['description']}")
                print(f"      search_name: {item['search_name'][:3]}...")
                print(f"      display_name: {item.get('display_name', 'なし')}")
                print(f"      display_variant: {item.get('display_variant', 'なし')}")
                print(f"      display_badges: {item.get('display_badges', [])}")
                print(f"      ai_description: {item.get('ai_description', 'なし')}")
                print(f"      consumption_frequency: {item.get('consumption_frequency', 'なし')} (score: {item.get('frequency_score', 0)})")

        # チェックポイント削除（フルモードのみ）
        if not args.test and not args.retry_failed and checkpoint_path and checkpoint_path.exists():
            checkpoint_path.unlink()
            print(f"   🗑️ チェックポイント削除: {checkpoint_file}")

    print("\n" + "="*80)
    print("🎉 処理完了！")
    if args.retry_failed:
        print("📁 失敗アイテムの再処理が完了しました")
    elif args.test:
        print(f"📁 テスト結果は {output_dir} に保存されました")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())