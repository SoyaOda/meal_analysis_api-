"""
共通プロンプトコンポーネント

音声分析と画像分析で共通して使用されるMyNetDiary制約やJSON構造などのプロンプト要素を管理します。
"""
from ...utils.mynetdiary_utils import format_mynetdiary_ingredients_for_prompt


class CommonPrompts:
    """音声分析と画像分析で共通のプロンプトコンポーネント"""

    @classmethod
    def get_mynetdiary_ingredients_list_with_header(cls) -> str:
        """MyNetDiary食材名リスト（ヘッダー付き）を生成"""
        ingredients_list = format_mynetdiary_ingredients_for_prompt()
        return f"""
MYNETDIARY INGREDIENT CONSTRAINT - ABSOLUTELY CRITICAL:
For ALL ingredients, you MUST select ONLY from the following MyNetDiary ingredient list.
Do NOT create custom ingredient names. Use the EXACTLY IDENTICAL names as they appear in this list.
COPY the ingredient names EXACTLY, character-by-character, from this list:

{ingredients_list}

CRITICAL: You MUST NOT modify, abbreviate, or paraphrase any ingredient names.
If you cannot find a suitable match in the MyNetDiary list for a visible ingredient,
choose the closest available option or omit that ingredient rather than creating a custom name.
ABSOLUTELY NO custom ingredient names are allowed - ONLY exact copies from the list above.
"""

    @classmethod
    def get_mynetdiary_ingredients_list_only(cls) -> str:
        """MyNetDiary食材名リストのみ（制約指示なし）を生成"""
        return format_mynetdiary_ingredients_for_prompt()

    @classmethod
    def get_query_generation_guidelines(cls) -> str:
        """クエリ生成ガイドライン（共通）"""
        return """
QUERY GENERATION GUIDELINES (CRITICAL for correct per-100g nutrition matching):
1. For ingredients: COPY EXACTLY from the MyNetDiary list above - ZERO tolerance for custom names
2. For dish names: Use simple, searchable names that exist as separate database entries
3. Avoid overly generic or misleading single-word queries
4. When a cooking or preservation method materially changes nutrition, include it
5. Output MUST be in English
6. Do NOT include quantities, units, brand marketing slogans, or flavour adjectives
7. MANDATORY: Each ingredient_name MUST be an IDENTICAL COPY from the MyNetDiary list
"""

    @classmethod
    def get_critical_verification_step(cls) -> str:
        """最終検証ステップ（共通）"""
        return """
CRITICAL FINAL VERIFICATION STEP - ABSOLUTELY MANDATORY:
Before finalizing your response, you MUST perform a TRIPLE verification check:

STEP 1: Go through EVERY SINGLE ingredient name in your response
STEP 2: For each ingredient name, SEARCH for it EXACTLY in the MyNetDiary ingredient list above
STEP 3: VERIFY character-by-character that your ingredient name is IDENTICAL to the list entry

REQUIREMENTS:
• Each ingredient name MUST be found EXACTLY in the MyNetDiary list (exact spelling, capitalization, word order)
• If ANY ingredient name does not match EXACTLY, you MUST replace it with the EXACT name from the list
• If no exact match exists, choose the closest available option from the MyNetDiary list
• ZERO tolerance for approximations or paraphrasing
• This verification is ABSOLUTELY MANDATORY - ingredient names that don't match exactly will cause system failures

FINAL CHECK: Before submitting, re-read each ingredient_name and confirm it is a PERFECT COPY from the MyNetDiary list.
"""

    @classmethod
    def get_json_structure_section(cls) -> str:
        """JSON レスポンス構造（共通）"""
        return """
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
          "ingredient_name": "string (MUST be EXACT match from MyNetDiary list - verify before submitting)",
          "weight_g": "number (MANDATORY - estimated weight in grams based on analysis)",
          "confidence": 0.0-1.0
        }}
      ]
    }}
  ]
}}
"""

    @classmethod
    def get_final_reminder(cls) -> str:
        """最終リマインダー（共通）"""
        return """
FINAL REMINDER: After completing your JSON response, perform a FINAL verification that every "ingredient_name" value is an EXACT, CHARACTER-BY-CHARACTER COPY from the MyNetDiary ingredient list provided above. NO EXCEPTIONS.
"""

    @classmethod
    def get_basic_guidelines(cls) -> str:
        """基本ガイドライン（共通）"""
        return """
**Guidelines:**
- For ingredients: Use ONLY exact names from the MyNetDiary ingredient list provided below
- Estimate typical serving weights (e.g., 1 egg ≈ 50g, 1 slice bread ≈ 30g)
- For complex dishes, break down into main MyNetDiary ingredient components
- If quantity mentioned (e.g., "two eggs"), calculate total weight
- Confidence should reflect how certain you are about the identification
"""

    @classmethod
    def get_json_format_section(cls) -> str:
        """JSON フォーマットセクション（共通）"""
        return """
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
"""

    @classmethod
    def get_formatting_requirements(cls) -> str:
        """フォーマット要件（共通）"""
        return """
**CRITICAL FORMATTING REQUIREMENTS:**
- For ALL ingredients, you MUST select ONLY from the MyNetDiary ingredient list above
- Use the EXACT names as they appear in the list (e.g., "Rice brown long grain cooked without salt")
- Do NOT add commas between descriptive words (e.g., "Rice, brown, long grain, cooked, without salt" is WRONG)
- The ingredient names in the MyNetDiary list are already in the correct format - use them exactly as shown
- If you cannot find a suitable match, choose the closest available option or omit that ingredient
"""

    @classmethod
    def get_final_verification_for_voice(cls) -> str:
        """音声用最終検証（共通）"""
        return """
**CRITICAL FINAL VERIFICATION STEP:**
Before finalizing your response, you MUST perform a strict verification check:
• Go through EVERY SINGLE ingredient name in your response
• Verify that each ingredient name appears EXACTLY as written in the MyNetDiary ingredient list provided above
• Check for exact spelling, capitalization, and word order matches
• If ANY ingredient name does not match EXACTLY, you MUST replace it with the correct name from the list
• This verification is MANDATORY - ingredient names that don't match exactly will cause system failures
"""