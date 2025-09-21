"""
音声分析（NLU）用プロンプトテンプレート

音声認識されたテキストから料理・食材・重量を抽出するためのプロンプトを管理します。
"""
from typing import Optional
from ...utils.mynetdiary_utils import format_mynetdiary_ingredients_for_prompt


class VoicePrompts:
    """音声分析（NLU処理）のプロンプトテンプレート（MyNetDiary制約付き）"""

    @classmethod
    def _get_mynetdiary_ingredients_section(cls) -> str:
        """MyNetDiary食材名リストのセクションを生成"""
        ingredients_list = format_mynetdiary_ingredients_for_prompt()
        return f"""
MYNETDIARY INGREDIENT CONSTRAINT:
You must ONLY use ingredient names from this approved MyNetDiary database. Do not use any ingredient names that are not in this list.

{ingredients_list}

If you cannot find an exact match in the MyNetDiary list, choose the closest available ingredient or break down complex dishes into their basic MyNetDiary-approved components.
"""

    @classmethod
    def get_system_prompt(cls, use_mynetdiary_constraint: bool = True) -> str:
        """
        音声NLU用システムプロンプトを取得

        Args:
            use_mynetdiary_constraint: MyNetDiary制約を使用するかどうか

        Returns:
            システムプロンプト文字列
        """
        base_prompt = """You are an AI assistant specialized in nutrition analysis. Your task is to extract food and meal information from user speech transcripts and convert them into a structured JSON format.

**Instructions:**
1. Identify dishes/meals and their ingredients from the user's description
2. Estimate reasonable serving sizes and weights in grams for each ingredient
3. Output in the following JSON structure only, no additional text

**Required JSON format:**
{
  "dishes": [
    {
      "dish_name": "Dish Name",
      "confidence": 0.9,
      "ingredients": [
        {
          "ingredient_name": "ingredient name",
          "weight_g": 100.0
        }
      ]
    }
  ]
}

**Guidelines:**
- Use standard ingredient names (e.g., "egg" not "scrambled eggs")
- Estimate typical serving weights (e.g., 1 egg ≈ 50g, 1 slice bread ≈ 30g)
- For complex dishes, break down into main ingredients
- If quantity mentioned (e.g., "two eggs"), calculate total weight
- Confidence should reflect how certain you are about the identification"""

        if use_mynetdiary_constraint:
            mynetdiary_section = cls._get_mynetdiary_ingredients_section()
            base_prompt = f"{base_prompt}\n\n{mynetdiary_section}"

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
        {"ingredient_name": "egg", "weight_g": 100.0}
      ]
    },
    {
      "dish_name": "Buttered Toast",
      "confidence": 0.9,
      "ingredients": [
        {"ingredient_name": "bread", "weight_g": 30.0},
        {"ingredient_name": "butter", "weight_g": 5.0}
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