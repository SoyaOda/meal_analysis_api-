"""
共通プロンプトコンポーネント

音声分析と画像分析で共通して使用されるMyNetDiary制約やJSON構造などのプロンプト要素を管理します。
"""
from ...utils.elasticsearch_ingredient_provider import ElasticsearchIngredientProvider
from ...config.settings import get_settings


class CommonPrompts:
    """音声分析と画像分析で共通のプロンプトコンポーネント"""

    # シングルトンプロバイダー（クラスレベル）
    _provider: ElasticsearchIngredientProvider = None

    @classmethod
    def _get_provider(cls) -> ElasticsearchIngredientProvider:
        """
        プロバイダーのシングルトンインスタンスを取得

        環境変数INGREDIENT_ELASTICSEARCH_INDEXで使用するインデックスを制御：
        - デフォルト: mynetdiary_converted_tool_calls_list_stemmed_with_nutrition
        - USDA使用時: INGREDIENT_ELASTICSEARCH_INDEX=usda_unified_nutrition_db
        """
        if cls._provider is None:
            settings = get_settings()
            cls._provider = ElasticsearchIngredientProvider(
                elasticsearch_url=settings.INGREDIENT_ELASTICSEARCH_URL,
                index_name=settings.INGREDIENT_ELASTICSEARCH_INDEX,
                timeout=settings.INGREDIENT_ELASTICSEARCH_TIMEOUT
            )
        return cls._provider

    @classmethod
    def get_mynetdiary_ingredients_list_with_header(cls, exclude_uncooked: bool = True) -> str:
        """MyNetDiary食材名リスト（ヘッダー付き）をElasticsearchから動的取得

        Args:
            exclude_uncooked: uncooked食材を除外するかどうか（デフォルト: True）

        Returns:
            str: ヘッダー付き食材リスト

        Raises:
            RuntimeError: Elasticsearch取得失敗時
        """
        provider = cls._get_provider()
        ingredients_list = provider.get_ingredient_list_for_prompt(exclude_uncooked=exclude_uncooked)
        exclusion_note = " (excluding uncooked items)" if exclude_uncooked else ""

        return f"""
MYNETDIARY INGREDIENT CONSTRAINT - ABSOLUTELY CRITICAL:
For ALL ingredients, you MUST select ONLY from the following MyNetDiary ingredient list{exclusion_note}.
Do NOT create custom ingredient names. Use the EXACTLY IDENTICAL names as they appear in this list.
COPY the ingredient names EXACTLY, character-by-character, from this list:

{ingredients_list}

CRITICAL: You MUST NOT modify, abbreviate, or paraphrase any ingredient names.
If you cannot find a suitable match in the MyNetDiary list for a visible ingredient,
choose the closest available option or omit that ingredient rather than creating a custom name.
ABSOLUTELY NO custom ingredient names are allowed - ONLY exact copies from the list above.
"""

    @classmethod
    def get_mynetdiary_ingredients_list_only(cls, exclude_uncooked: bool = True) -> str:
        """MyNetDiary食材名リストのみ（制約指示なし）をElasticsearchから動的取得

        Args:
            exclude_uncooked: uncooked食材を除外するかどうか（デフォルト: True）

        Returns:
            str: 食材リストのみ

        Raises:
            RuntimeError: Elasticsearch取得失敗時
        """
        provider = cls._get_provider()
        return provider.get_ingredient_list_for_prompt(exclude_uncooked=exclude_uncooked)

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

    @classmethod
    def get_dish_decomposition_rule(cls) -> str:
        """料理分解ルール（画像・音声共通）"""
        return """
DISH DECOMPOSITION RULE:
When you encounter dish names (e.g., "Pepperoni Pizza", "Chicken Sandwich", "Beef Stew"), you MUST break them down into their constituent ingredients.
• Do NOT treat dish names as single ingredients
• Break down each dish into individual ingredients that can be found in the MyNetDiary list
• For complex dishes, identify all main components (proteins, carbs, fats, sauces, toppings, etc.)
• Each ingredient must be separately listed with its own weight estimate
• Example: "Pepperoni Pizza" → Pizza dough, Tomato sauce, Mozzarella cheese, Pepperoni (pork/beef)
"""

    @classmethod
    def get_nutritional_completeness_requirements(cls) -> str:
        """栄養完全性要件（画像・音声共通）"""
        return """
NUTRITIONAL COMPLETENESS REQUIREMENTS:
For EACH dish, list ALL PRIMARY INGREDIENTS that materially contribute to nutrition calculations:
• Include all protein sources, carbohydrate sources, fat sources
• Include cooking oils, sauces, dressings, and condiments
• Include toppings and garnishes that add significant calories
• The goal is to capture every ingredient that affects total calories or macro-nutrients
• This exhaustive ingredient list is critical for accurate nutrition calculation
• ALL ingredient names MUST be selected from the MyNetDiary list provided above
"""

    @classmethod
    def get_weight_estimation_requirements(cls) -> str:
        """重量推定要件（画像・音声共通）"""
        return """
WEIGHT ESTIMATION REQUIREMENTS (MANDATORY):
For EACH ingredient, you MUST estimate the weight in grams (weight_g):
• This field is MANDATORY - the system will fail if any ingredient lacks weight_g
• Estimate realistic weights based on typical serving sizes
• For liquids: 1ml ≈ 1g for most beverages
• For solids: consider typical portions (e.g., 50-200g for main ingredients, 5-30g for seasonings)
• NEVER omit the weight_g field - it is required for every single ingredient
"""

    @classmethod
    def get_cooking_state_requirements(cls) -> str:
        """調理状態の考慮（画像・音声共通）"""
        return """
CRITICAL COOKING STATE CONSIDERATION:
For pasta, rice, grains, and legumes that absorb water during cooking:
• ALWAYS specify the cooking state in the ingredient_name (e.g., "pasta white cooked" vs "pasta white dry uncooked")
• Cooked pasta/rice weighs 2-3x more than dry due to water absorption
• Nutrition per gram is 2-3x LESS for cooked vs uncooked
• This distinction is CRITICAL - getting this wrong causes 200-300% calorie errors
• When estimating weight, ensure it matches the cooking state specified in the ingredient name
"""
