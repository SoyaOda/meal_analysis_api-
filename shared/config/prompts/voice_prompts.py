"""
音声分析（NLU）用プロンプトテンプレート

音声認識されたテキストから料理・食材・重量を抽出するためのプロンプトを管理します。
"""
from typing import Optional
from .common_prompts import CommonPrompts


class VoicePrompts:
    """音声分析（NLU処理）のプロンプトテンプレート（MyNetDiary制約付き）"""


    @classmethod
    def get_system_prompt(cls, use_mynetdiary_constraint: bool = True) -> str:
        """
        音声NLU用システムプロンプトを取得

        Args:
            use_mynetdiary_constraint: MyNetDiary制約を使用するかどうか

        Returns:
            システムプロンプト文字列
        """
        base_prompt = f"""You are an AI assistant specialized in nutrition analysis from speech transcripts.

{CommonPrompts.get_mynetdiary_ingredients_list_with_header()}

{cls.get_voice_specific_flexible_matching()}

{CommonPrompts.get_dish_decomposition_rule()}

{CommonPrompts.get_nutritional_completeness_requirements()}

{CommonPrompts.get_weight_estimation_requirements()}

{CommonPrompts.get_cooking_state_requirements()}

{CommonPrompts.get_query_generation_guidelines()}

{CommonPrompts.get_json_structure_section()}

{CommonPrompts.get_final_verification_for_voice()}"""

        return base_prompt

    @classmethod
    def get_example_prompt(cls) -> str:
        """使用例を含むプロンプトセクションを取得"""
        return """
**Example input:** "I had scrambled eggs and toast with butter for breakfast"
**Example output:**
{
  "dishes": [
    {
      "dish_name": "Scrambled Eggs",
      "confidence": 0.95,
      "ingredients": [
        {"ingredient_name": "Egg whole raw", "weight_g": 100.0}
      ]
    },
    {
      "dish_name": "Buttered Toast",
      "confidence": 0.9,
      "ingredients": [
        {"ingredient_name": "White bread", "weight_g": 30.0},
        {"ingredient_name": "Butter salted", "weight_g": 5.0}
      ]
    }
  ]
}

**Example input:** "I had brown rice with steamed broccoli"
**Example output:**
{
  "dishes": [
    {
      "dish_name": "Brown Rice with Steamed Broccoli",
      "confidence": 0.9,
      "ingredients": [
        {"ingredient_name": "Rice brown long grain cooked without salt", "weight_g": 150.0},
        {"ingredient_name": "Broccoli steamed", "weight_g": 100.0}
      ]
    }
  ]
}"""

    @classmethod
    def get_complete_prompt(cls, use_mynetdiary_constraint: bool = True, include_examples: bool = True) -> str:
        """
        完全なプロンプト（システム + 例）を取得

        Args:
            use_mynetdiary_constraint: MyNetDiary制約を使用するかどうか
            include_examples: 例を含めるかどうか

        Returns:
            完全なプロンプト文字列
        """
        system_prompt = cls.get_system_prompt(use_mynetdiary_constraint)

        if include_examples:
            example_prompt = cls.get_example_prompt()
            return f"{system_prompt}\n{example_prompt}"

        return system_prompt

    @classmethod
    def get_fallback_foods(cls) -> dict:
        """フォールバック用の一般的な食品リスト"""
        return {
            "egg": 50, "eggs": 100, "bread": 30, "toast": 30,
            "coffee": 200, "tea": 200, "milk": 200,
            "apple": 150, "banana": 120, "orange": 150,
            "chicken": 150, "beef": 150, "fish": 150,
            "rice": 100, "pasta": 100, "salad": 150,
            "butter": 5, "cheese": 30, "yogurt": 150
        }

    @classmethod
    def get_voice_specific_flexible_matching(cls) -> str:
        """音声特有の柔軟なマッチング指示"""
        return """
⚠️ VOICE INPUT SPECIAL RULE - EQUALLY CRITICAL AS ABOVE:
The above rule says "ONLY exact copies from the list" - BUT for voice input, users speak informal names.
You MUST interpret this rule flexibly: Find the CLOSEST MATCH from the MyNetDiary list, NOT fail because the spoken name isn't perfect.

ABSOLUTELY CRITICAL - SYSTEM WILL FAIL OTHERWISE:
• If user says "Pizza dough" → Search MyNetDiary list for bread/dough items (e.g., "Bread white", "Dough")
• If user says "Pepperoni" → Search MyNetDiary list for processed pork/beef items (e.g., "Sausage", "Ham")
• If user says "Mozzarella" → Search MyNetDiary list for cheese items (e.g., "Cheese mozzarella", "Mozzarella cheese")

MATCHING PROCESS YOU MUST FOLLOW:
1. User speaks a food name → Identify its food category (meat? cheese? vegetable? grain?)
2. Scan the ENTIRE MyNetDiary list above for items in that category
3. Pick the closest match based on:
   - Same food type (if spoken "chicken", find "Chicken..." entries)
   - Similar preparation (if spoken "grilled", look for "raw" or "cooked" variants)
   - Comparable nutrition (high protein → meat/fish/eggs, high carbs → grains/bread)
4. Output that MyNetDiary name EXACTLY as it appears in the list

THE CRITICAL POINT:
Your job is NOT to output what the user said. Your job is to TRANSLATE what the user said into a valid MyNetDiary ingredient name.
Think of it like translation: "Pizza dough" (informal) → "Bread white" or "Dough refrigerated" (formal MyNetDiary name)

DO NOT OUTPUT NAMES THAT DON'T EXIST IN THE MYNETDIARY LIST - THE SYSTEM WILL REJECT THEM AND FAIL.
"""
