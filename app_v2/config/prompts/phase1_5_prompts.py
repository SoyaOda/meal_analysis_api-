#!/usr/bin/env python3
"""
Phase1.5 プロンプト設定
Phase1のプロンプトをベースにした代替クエリ生成のためのプロンプトテンプレート
"""

import json
import os
from typing import List, Dict, Any, Optional


class Phase1_5Prompts:
    """Phase1.5 代替クエリ生成用プロンプト（Phase1ベース）"""
    
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

    @staticmethod
    def get_system_prompt() -> str:
        """システムプロンプト（Phase1ベース + 代替クエリ生成文脈）"""
        niche_mapping_text = Phase1_5Prompts._generate_niche_mapping_text()
        
        return f"""You are an advanced food recognition AI that analyzes food images and generates alternative search queries for nutrition databases.

CONTEXT: You are being called because the initial food identification queries failed to find exact matches in nutrition databases. Your task is to re-analyze the image and generate better alternative queries that are more likely to succeed.

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

ALTERNATIVE QUERY GENERATION STRATEGIES:
Since the original queries failed to find exact matches, apply these strategies:

1. **broader_terms**: Replace specific/niche terms with more common alternatives
   - "Broccolini" → "Broccoli"
   - "Baby spinach" → "Spinach"
   - "Purple carrots" → "Carrots"

2. **standard_cooking**: Add or modify cooking method descriptors
   - "Chicken" → "Grilled chicken" or "Roasted chicken"
   - "Potatoes" → "Boiled potatoes" or "Baked potatoes"

3. **generic_categories**: Use broader food category terms
   - "Microgreens" → "Mixed greens" or "Leafy greens"
   - "Sprouted alfalfa" → "Alfalfa sprouts"

4. **database_friendly**: Use terms commonly found in nutrition databases
   - Avoid brand names, marketing terms, or ultra-specific varieties
   - Prefer scientific/standard food names over colloquial terms

5. **visual_reanalysis**: Re-examine the image to confirm the food identification
   - Sometimes the original identification might be too specific
   - Consider if a simpler, more generic term better describes what's visible

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
JSON RESPONSE STRUCTURE FOR ALTERNATIVE QUERIES
-------------------------------------------------------------
Return a JSON object with the following structure:

{{
  "alternative_queries": [
    {{
      "original_query": "string",
      "alternative_query": "string",
      "strategy": "broader_terms|standard_cooking|generic_categories|database_friendly|visual_reanalysis",
      "reasoning": "string",
      "confidence": 0.0-1.0
    }}
  ]
}}"""

    @staticmethod
    def get_user_prompt(
        phase1_result: Dict[str, Any],
        failed_queries: List[str],
        failure_history: List[Dict[str, Any]] = None,
        iteration: int = 1
    ) -> str:
        """ユーザープロンプト（Phase1結果と失敗クエリを含む）"""
        
        # Phase1結果の要約
        dishes_summary = ""
        if "dishes" in phase1_result:
            dishes_summary = "ORIGINAL PHASE1 ANALYSIS:\n"
            for i, dish in enumerate(phase1_result["dishes"], 1):
                dish_name = dish.get("dish_name", "Unknown")
                confidence = dish.get("confidence", 0.0)
                dishes_summary += f"{i}. {dish_name} (confidence: {confidence:.2f})\n"
                
                ingredients = dish.get("ingredients", [])
                if ingredients:
                    dishes_summary += "   Ingredients:\n"
                    for ingredient in ingredients:
                        ing_name = ingredient.get("ingredient_name", "Unknown")
                        ing_conf = ingredient.get("confidence", 0.0)
                        dishes_summary += f"   - {ing_name} (confidence: {ing_conf:.2f})\n"
                dishes_summary += "\n"
        
        # 失敗履歴の要約
        history_summary = ""
        if failure_history and len(failure_history) > 0:
            history_summary = f"\nPREVIOUS PHASE1.5 ATTEMPTS (Iteration {iteration}):\n"
            history_summary += "=" * 50 + "\n"
            
            for i, history in enumerate(failure_history[-3:], 1):  # 最新3回分のみ
                failed_in_history = history.get("failed_queries", [])
                history_summary += f"\nAttempt {i}:\n"
                history_summary += f"  Failed queries: {', '.join(failed_in_history)}\n"
                
                alt_queries = history.get("alternative_queries", [])
                if alt_queries:
                    history_summary += f"  Alternative queries suggested:\n"
                    for alt in alt_queries[:3]:  # 最初の3つのみ表示
                        original = alt.get("original_query", "Unknown")
                        alternative = alt.get("alternative_query", "Unknown")
                        strategy = alt.get("strategy", "Unknown")
                        history_summary += f"    - '{original}' → '{alternative}' (Strategy: {strategy})\n"
                    if len(alt_queries) > 3:
                        history_summary += f"    ... and {len(alt_queries) - 3} more\n"
                
                history_summary += f"  Result: STILL FAILED TO FIND EXACT MATCHES\n"
            
            history_summary += "\n" + "=" * 50 + "\n"
            history_summary += "IMPORTANT: The above attempts all failed. You must try different strategies!\n"
            history_summary += "Consider:\n"
            history_summary += "- Even broader/more generic terms than previously tried\n"
            history_summary += "- Different cooking methods or preparation styles\n"
            history_summary += "- Alternative food categories or classifications\n"
            history_summary += "- Simpler, more basic food names\n"
            history_summary += "- Re-examining the image for different interpretations\n\n"
        
        prompt = f"""Please analyze this food image and generate alternative search queries for the failed items.

{dishes_summary}

FAILED SEARCH QUERIES (No Exact Matches Found):
{', '.join(failed_queries)}
{history_summary}

INSTRUCTIONS:
1. Re-examine the image carefully to understand why the original queries failed
2. For each failed query, generate a better alternative that is more likely to find exact matches in nutrition databases
3. Apply the alternative query generation strategies described in the system prompt
4. Focus on database-friendly, common food names rather than niche or specialty terms
5. Use the same high-quality query generation guidelines as Phase1 analysis
6. Provide clear reasoning for each alternative query

Based on the image and the failed search results, please generate alternative search queries that are more likely to find exact matches in nutrition databases. Focus on making the terms more generic, database-friendly, and searchable while maintaining nutritional accuracy.

Remember to follow the same dish decomposition and nutritional completeness requirements as the original Phase1 analysis, but with a focus on generating more successful database queries."""
        
        return prompt 