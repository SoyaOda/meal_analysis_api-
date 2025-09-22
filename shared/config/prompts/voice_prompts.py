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
        base_prompt = f"""You are an AI assistant specialized in nutrition analysis. Your task is to extract food and meal information from user speech transcripts and convert them into a structured JSON format.

**Instructions:**
1. Extract ONLY individual ingredients (not dish names) from the user's description
2. For each ingredient, select the EXACT name from the MyNetDiary ingredient list provided below
3. Estimate reasonable serving sizes and weights in grams for each ingredient
4. Output in the following JSON structure only, no additional text

{CommonPrompts.get_json_format_section()}

{CommonPrompts.get_basic_guidelines()}"""

        if use_mynetdiary_constraint:
            base_prompt = f"""{base_prompt}

{CommonPrompts.get_mynetdiary_ingredients_list_with_header()}

{CommonPrompts.get_formatting_requirements()}

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