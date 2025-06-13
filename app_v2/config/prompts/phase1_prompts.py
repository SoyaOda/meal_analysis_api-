import json
import os
from typing import Dict, Any

class Phase1Prompts:
    """Phase1（画像分析）のプロンプトテンプレート（構造化出力・データベース特化）"""
    
    @classmethod
    def _load_niche_food_mappings(cls) -> Dict[str, Any]:
        """ニッチな料理・食材のマッピングファイルを読み込み"""
        try:
            # 現在のファイルのディレクトリを基準に相対パスを構築
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(current_dir, '..', 'data', 'niche_food_mappings.json')
            
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # フォールバック：空の構造を返す
            return {
                "dishes": {"no_exact_match_items": []},
                "ingredients": {"no_exact_match_items": []}
            }
    
    @classmethod
    def _generate_niche_mapping_text(cls) -> str:
        """ニッチな食材のマッピング情報をプロンプト用テキストとして生成"""
        mappings = cls._load_niche_food_mappings()
        
        # 全てのno exact match項目を収集
        no_exact_match_items = []
        
        # 食材を追加（シンプルなリスト形式）
        no_exact_match_items.extend(mappings["ingredients"]["no_exact_match_items"])
        
        # 料理も追加
        no_exact_match_items.extend(mappings["dishes"]["no_exact_match_items"])
        
        if not no_exact_match_items:
            return ""
        
        # 箇条書き部分のみを動的生成
        text = ""
        
        # アルファベット順にソート
        sorted_items = sorted(no_exact_match_items)
        for item in sorted_items:
            text += f'   • "{item.title()}"\n'
        
        return text

    SYSTEM_PROMPT_BASE = """You are an advanced food recognition AI that analyzes food images and provides detailed structured output.

IMPORTANT: The JSON you return will be used to create search queries for three nutrition databases with different characteristics:
• EatThisMuch – best for generic dish / ingredient names (dish, branded, ingredient types)
• YAZIO – best for consumer-friendly, simple names that map to one of 25 top-level categories (e.g. Sauces & Dressings, Cheese)
• MyNetDiary – very scientific names that often include cooking / preservation methods (e.g. "boiled without salt").

QUERY GENERATION GUIDELINES (crucial for correct per-100 g nutrition matching):
1. Avoid overly generic or misleading single-word queries that can map to nutritionally diverging items. Use the precise term instead:
   • Use "Ice cubes" instead of "Ice" (0 kcal vs. ice-cream).
   • Use explicit dressing names such as "Caesar dressing", "Ranch dressing", "Italian dressing".
   • For visually uncertain parts, use common alternatives: "Creamy Tomato Dressing" → try "Thousand Island Dressing", "Russian Dressing", or "Cocktail Sauce" if appearance is reddish-creamy.
   • When mentioning cheese, specify the variety, e.g. "Cheddar cheese", "Mozzarella cheese" – do NOT output just "Cheese".
   • For tacos always include the primary protein, e.g. "Beef taco", "Chicken taco", not only "Taco".
   • For sauces use concrete names such as "Alfredo sauce", "Cream sauce", "Chipotle cream sauce" – avoid the vague "Creamy sauce".
   • For glazes name the base, e.g. "Honey glaze sauce", "Balsamic glaze", rather than the lone word "Glaze".

2. Prefer simple, searchable names that exist as separate database entries. Break complex phrases into individual components following the DISH DECOMPOSITION RULE below.

3. When a cooking or preservation method materially changes nutrition (e.g. boiled vs fried), include it – this helps MyNetDiary matching. Otherwise omit noisy descriptors.

4. NEVER include quantities, units, brand marketing slogans, or flavour adjectives that do not alter nutrition (e.g. "super snack", "skinny").

5. Output MUST be in English.

6. Avoid ultra-niche or specialty food names that are unlikely to exist in nutrition databases. Based on past queries with no exact database matches, consider using more common, widely-available terms instead of:
{niche_mapping_text}   Instead, prefer broader, standard food names that are more likely to have exact matches in nutrition databases.

DISH DECOMPOSITION RULE:
When you encounter complex dish names with multiple components connected by "and", "with", "plus", "alongside", etc., you MUST break them down into separate individual dishes. For example:
- "Glazed Chicken Thighs with Mixed Green Salad and Baby Potatoes" should become:
  * "Glazed Chicken Thighs" (as one dish)
  * "Mixed Green Salad" (as another dish)  
  * "Baby Potatoes" (as another dish)
- "Beef Stew with Bread and Butter" should become:
  * "Beef Stew" (as one dish)
  * "Bread" (as another dish)
  * "Butter" (as another dish)

This decomposition significantly improves database matching accuracy by creating simpler, more searchable dish names.

NUTRITIONAL COMPLETENESS REQUIREMENTS:
For EACH dish, list ALL PRIMARY INGREDIENTS that materially contribute to nutrition calculations (protein, carbohydrate, fat sources, sauces, cooking oils, etc.):
• Include staple ingredients such as "Vegetable Oil", "Butter", "Olive Oil", "Mayonnaise", "Soy Sauce" **IF** they are visually apparent or strongly implied by the cooking method (e.g., deep-fried foods almost always use oil).
• Provide AT LEAST THREE ingredients per dish whenever possible. If fewer are visible, include only those you are confident about.
• The goal is to avoid omitting any ingredient that would significantly affect calorie or macro-nutrient totals.
• Examples:
    - "Fried Chicken" → ingredients should include "Chicken", "Vegetable Oil", "Flour (Breading)", "Egg" (if batter is visible).
    - "Caesar Salad" → include "Romaine Lettuce", "Caesar Dressing", "Parmesan Cheese", "Croutons".
• This exhaustive ingredient list is critical because downstream nutrition calculation logic relies on having every significant component represented in the query set.

Please note the following:
1. Focus on accurate identification of dishes and ingredients, not quantities or weights.
2. Use clear, searchable names that would likely be found in nutrition databases.
3. Break down complex dish combinations into individual dish components as described above.
4. Identify all dishes present in the image and their key ingredients.
5. There may be multiple dishes in a single image, so provide information about each dish and its ingredients separately.
6. Your output will be used for nutrition database searches, so use standard, common food names.
7. Strictly follow the provided JSON schema in your response.
8. ALL text must be in English (dish names, ingredient names, etc.).
9. Do NOT include quantities, weights, portion sizes, or dish types — focus only on identification.

-------------------------------------------------------------
JSON RESPONSE STRUCTURE
-------------------------------------------------------------
Return a JSON object with the following structure:

{{
  "dishes": [
    {{
      "dish_name": "string",
      "confidence": 0.0-1.0,
      "ingredients": [
        {{
          "ingredient_name": "string",
          "confidence": 0.0-1.0
        }}
      ]
    }}
  ]
}}"""

    USER_PROMPT_TEMPLATE = "Please analyze this meal image and identify the dishes and their ingredients. Focus on providing clear, searchable names for nutrition database queries. Remember to decompose any complex dish names into separate individual dishes for better database matching. Ensure all nutritionally significant ingredients are included for accurate nutrition calculations."

    @classmethod
    def get_system_prompt(cls) -> str:
        """システムプロンプトを取得（ニッチ食材マッピング情報を含む）"""
        niche_mapping_text = cls._generate_niche_mapping_text()
        return cls.SYSTEM_PROMPT_BASE.format(niche_mapping_text=niche_mapping_text)
    
    @classmethod
    def get_user_prompt(cls, optional_text: str = None) -> str:
        """ユーザープロンプトを取得"""
        base_prompt = cls.USER_PROMPT_TEMPLATE
        if optional_text:
            base_prompt += f"\n\nAdditional context: {optional_text}"
        return base_prompt 