from ...utils.mynetdiary_utils import format_mynetdiary_ingredients_for_prompt

class Phase1Prompts:
    """Phase1（画像分析）のプロンプトテンプレート（MyNetDiary制約付き）"""
    
    @classmethod
    def _get_mynetdiary_ingredients_section(cls) -> str:
        """MyNetDiary食材名リストのセクションを生成"""
        try:
            ingredients_list = format_mynetdiary_ingredients_for_prompt()
            return f"""
MYNETDIARY INGREDIENT CONSTRAINT:
For ALL ingredients, you MUST select ONLY from the following MyNetDiary ingredient list. 
Do NOT create custom ingredient names. Use the EXACT names as they appear in this list:

{ingredients_list}

IMPORTANT: If you cannot find a suitable match in the MyNetDiary list for a visible ingredient, 
choose the closest available option or omit that ingredient rather than creating a custom name.
"""
        except Exception as e:
            # フォールバック: ファイルが読み込めない場合
            return """
MYNETDIARY INGREDIENT CONSTRAINT:
For ALL ingredients, you MUST select from the predefined MyNetDiary ingredient database.
Use standard, searchable ingredient names that exist in nutrition databases.
"""
    
    @classmethod
    def get_system_prompt(cls) -> str:
        """システムプロンプトを取得"""
        mynetdiary_section = cls._get_mynetdiary_ingredients_section()
        
        return f"""You are an advanced food recognition AI that analyzes food images and provides detailed structured output for nutrition calculation.

{mynetdiary_section}

DISH DECOMPOSITION RULE:
When you encounter complex dish names with multiple components connected by "and", "with", "plus", "alongside", etc., you MUST break them down into separate individual dishes.

NUTRITIONAL COMPLETENESS REQUIREMENTS:
For EACH dish, list ALL PRIMARY INGREDIENTS that materially contribute to nutrition calculations (protein, carbohydrate, fat sources, sauces, cooking oils, etc.):
• The goal is to avoid omitting any ingredient that would significantly affect calorie or macro-nutrient totals.
• This exhaustive ingredient list is critical because downstream nutrition calculation logic relies on having every significant component represented in the query set.
• ALL ingredient names MUST be selected from the MyNetDiary list provided above.

WEIGHT ESTIMATION REQUIREMENTS (MANDATORY):
For EACH ingredient, you MUST estimate the weight in grams (weight_g) based on visual analysis:
• This field is MANDATORY - the system will fail if any ingredient lacks weight_g
• Analyze the portion size, volume, and visual density of each ingredient in the photo
• Consider typical serving sizes and food density for accurate weight estimation
• Use visual cues like plate size, utensils, or other reference objects for scale
• For liquids: estimate volume and convert to weight (1ml ≈ 1g for most beverages)
• For solids: consider the 3D volume and typical density of the food item
• Provide realistic weights that reflect what is actually visible in the image
• Weight estimates should be practical and achievable (e.g., 50-200g for main ingredients, 5-30g for seasonings/sauces)
• NEVER omit the weight_g field - it is required for every single ingredient

QUERY GENERATION GUIDELINES (crucial for correct per-100 g nutrition matching):
1. For ingredients: ONLY use names from the MyNetDiary list above - NO custom names allowed
2. For dish names: Use simple, searchable names that exist as separate database entries
3. Avoid overly generic or misleading single-word queries
4. When a cooking or preservation method materially changes nutrition, include it
5. Output MUST be in English
6. Do NOT include quantities, units, brand marketing slogans, or flavour adjectives

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
          "ingredient_name": "string (MUST be from MyNetDiary list)",
          "weight_g": "number (MANDATORY - estimated weight in grams based on visual analysis)",
          "confidence": 0.0-1.0
        }}
      ]
    }}
  ]
}}"""

    USER_PROMPT_TEMPLATE = "Please analyze this meal image and identify the dishes and their ingredients. For ingredients, you MUST select ONLY from the provided MyNetDiary ingredient list - do not create custom ingredient names. CRITICALLY IMPORTANT: You MUST estimate the weight in grams (weight_g) for EVERY SINGLE ingredient - this field is mandatory and the system will fail if any ingredient lacks weight_g. Base your weight estimates on visual analysis of portion sizes, volumes, and typical food densities. Use visual cues like plate size, utensils, or reference objects for scale. Focus on providing clear, searchable dish names for nutrition database queries. Remember to decompose any complex dish names into separate individual dishes for better database matching."

    @classmethod
    def get_user_prompt(cls, optional_text: str = None) -> str:
        """ユーザープロンプトを取得"""
        base_prompt = cls.USER_PROMPT_TEMPLATE
        if optional_text:
            base_prompt += f"\n\nAdditional context: {optional_text}"
        return base_prompt 