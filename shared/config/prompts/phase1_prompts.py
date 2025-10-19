from .common_prompts import CommonPrompts

class Phase1Prompts:
    """Phase1（画像分析）のプロンプトテンプレート（MyNetDiary制約付き）"""
    
    
    @classmethod
    def get_system_prompt(cls) -> str:
        """システムプロンプトを取得"""
        
        return f"""You are an advanced food recognition AI that analyzes food images and provides detailed structured output for nutrition calculation.

{CommonPrompts.get_mynetdiary_ingredients_list_with_header()}

{CommonPrompts.get_dish_decomposition_rule()}

{CommonPrompts.get_nutritional_completeness_requirements()}

{CommonPrompts.get_weight_estimation_requirements()}

{cls.get_plate_based_visual_weight_estimation()}

{cls.get_american_portion_context()}

{CommonPrompts.get_cooking_state_requirements()}

{CommonPrompts.get_query_generation_guidelines()}

{CommonPrompts.get_critical_verification_step()}

{CommonPrompts.get_json_structure_section()}

{CommonPrompts.get_final_reminder()}"""

    USER_PROMPT_TEMPLATE = "Please analyze this meal image and identify the dishes and their ingredients. For ingredients, you MUST select ONLY from the provided MyNetDiary ingredient list - do not create custom ingredient names. CRITICALLY IMPORTANT: You MUST estimate the weight in grams (weight_g) for EVERY SINGLE ingredient - this field is mandatory and the system will fail if any ingredient lacks weight_g. Base your weight estimates on visual analysis of portion sizes, volumes, and typical food densities. Use visual cues like plate size, utensils, or reference objects for scale. Focus on providing clear, searchable dish names for nutrition database queries. Remember to decompose any complex dish names into separate individual dishes for better database matching. FINAL STEP: Before submitting your response, double-check that EVERY ingredient name in your JSON response matches EXACTLY with the names in the MyNetDiary ingredient list provided - this verification is critical for system functionality."

    @classmethod
    def get_user_prompt(cls, optional_text: str = None) -> str:
        """ユーザープロンプトを取得"""
        base_prompt = cls.USER_PROMPT_TEMPLATE
        if optional_text:
            base_prompt += f"\n\nAdditional context: {optional_text}"
        return base_prompt

    @classmethod
    def get_gemma3_prompt(cls) -> str:
        """Gemma 3用の最適化されたプロンプトを取得"""
        
        return f"""You are an expert food analyst and nutritionist for a US-based diet management application. Your task is to analyze the provided image of a meal and return a structured JSON object containing your analysis. Adhere strictly to the JSON schema and instructions provided below.

Primary Goal:
Identify all distinct dishes in the image, list their ingredients, and estimate the weight of each ingredient in grams.

Instructions:
1. Analyze the Image: Carefully examine the image to identify all separate food items or dishes.
2. Identify Dishes: For each dish, provide a common, recognizable name (e.g., "Spaghetti Bolognese", "Caesar Salad", "Grilled Chicken Breast").
3. List Ingredients: For each dish, list all visible and reasonably inferable ingredients.
   Constraint: When naming ingredients, you MUST try to match them to an item from the provided MyNetDiary ingredient list. If an exact match is not possible, use the most common and simple name for the ingredient (e.g., "tomato", "chicken breast", "lettuce").
4. Estimate Weight: For each ingredient, estimate its weight in grams (weight_g). This is a critical step. Be realistic. For example, a slice of bread is about 30g, a medium egg is about 50g, a standard chicken breast is 150-200g.
   AMERICAN PORTION CONTEXT: Assume this is a typical American meal - portions are 25-50% larger than international standards. American restaurant pasta servings are typically 200-300g cooked weight, proteins are 150-250g (6-8 oz), and salads are 100-200g of greens.
   PLATE-BASED ESTIMATION: Use the plate/bowl as your primary scale reference. Standard dinner plates are 25-28cm diameter. Observe how much of the plate each ingredient covers and at what depth. For pasta in bowls, estimate the 3D volume (cooked pasta ~1.1g/ml). For salads, consider leaf compression (loose greens ~0.2-0.3g/ml). Compare relative sizes between dishes to ensure proportional estimates.
   CRITICAL: For pasta, rice, grains, and legumes - pay special attention to cooking state:
   - If you see COOKED pasta/rice, estimate the COOKED weight but specify "cooked" in ingredient_name
   - If estimating dry weight equivalent, use "dry uncooked" in ingredient_name
   - Cooked pasta/rice weighs 2-3x more than dry, but has 2-3x LESS nutrition per gram
   - Getting this wrong causes massive calorie calculation errors (200-300% off)
5. Confidence Score: Provide a confidence score (from 0.0 to 1.0) for your identification of each dish. 1.0 means absolute certainty.
6. JSON Output: Format your entire output as a single JSON object. DO NOT include any text, explanation, or markdown formatting outside of the JSON object itself.

{CommonPrompts.get_mynetdiary_ingredients_list_with_header()}

Required JSON Schema:
Your output MUST conform to this exact JSON structure. If a value is unknown, use null.

{{
  "dishes": [
    {{
      "dish_name": "Example: Grilled Chicken Breast",
      "confidence": 0.98,
      "ingredients": [
        {{
          "ingredient_name": "Chicken breast boneless skinless raw",
          "weight_g": 180
        }},
        {{
          "ingredient_name": "Olive or extra virgin olive oil",
          "weight_g": 5
        }}
      ]
    }}
  ]
}}""" 

    @classmethod
    def get_gemma3_prompt_v3_granularity(cls, exclude_uncooked: bool = False) -> str:
        """Gemma 3用の粒度制御システム対応プロンプト（v3.0）を取得
        
        Args:
            exclude_uncooked: uncooked食材を除外するかどうか（デフォルト: False - USDA用）
            
        Returns:
            str: v3.0粒度制御システム対応の完全なプロンプト
        """
        
        # 食材リストを動的に取得（USDA/MyNetDiary両対応）
        ingredients_header = CommonPrompts.get_mynetdiary_ingredients_list_with_header(exclude_uncooked=exclude_uncooked)
        # ヘッダーを"USDA FNDDS"に置き換え（USDA用の場合）
        if not exclude_uncooked:
            ingredients_header = ingredients_header.replace("MYNETDIARY INGREDIENT CONSTRAINT", "USDA FNDDS INGREDIENT CONSTRAINT")
            ingredients_header = ingredients_header.replace("MyNetDiary ingredient list", "USDA FNDDS ingredient list")
        
        return f"""You are an expert food analyst and nutritionist for a US-based diet management application. Your task is to analyze the provided image of a meal and return a structured JSON object. Your primary goal is to identify all food items and determine the most accurate method for nutritional analysis.

## Primary Goal

Analyze the provided meal image and identify all distinct food items. For each item, you must determine the most accurate analysis method from the three options below and structure your output according to the required JSON schema.

---

**IMPORTANT RULE: When you see multiple distinct food items on a single plate, treat EACH visually separate food item as an independent "dish" entry. Do NOT combine them into a single "dinner" or "meal" dish.**

## Core Analysis Concepts

You must choose one of the following three methods for each dish identified:

### 1. USE_AS_IS

This method is for single-unit foods where decomposition is unnecessary or inaccurate.

**When to use:**

- Branded items (e.g., a "Snickers" bar, a can of "Coke")
- Simple whole foods (e.g., "Apple, raw", "Banana, raw")
- Standard recipes or composite dishes (e.g., "Lasagna with meat", "General Tso chicken") that are found in the USDA list and appear to be served without significant customization or variation.

**JSON Output:**

- The `base_food` field will be populated with the item from the USDA list
- The `ingredients` array will be **empty** (`[]`)

**Example:**

- A single apple → USE_AS_IS with base_food="Apple, raw"
- A standard bowl of restaurant chicken noodle soup → USE_AS_IS with base_food="Soup, chicken noodle, from restaurant"

---

### 2. DECOMPOSE_TO_INGREDIENTS

This method is for fully custom or homemade meals where all ingredients are visible or can be reasonably inferred, and no standard "base" dish from the USDA list applies.

**When to use:**

- A homemade salad with custom ingredients
- A custom sandwich made from scratch
- A stir-fry prepared from individual ingredients
- Any dish where the composition varies significantly from standard recipes

**JSON Output:**

- The `base_food.item_name` field will be **null**
- The `base_food.weight_g` field will be **0**
- The `ingredients` array will contain a **full list** of all constituent ingredients from the USDA list

**Example:** Custom salad → DECOMPOSE_TO_INGREDIENTS with base_food.item_name=null and ingredients=[lettuce, tomatoes, chicken, dressing]

---

### 3. HYBRID_DECOMPOSITION

This is a "base + toppings" model. It is used for a standard dish that has been customized with additional toppings or ingredients.

**When to use:**

- A frozen cheese pizza (base_food) with added pepperoni and mushrooms (ingredients)
- A plain bagel (base_food) with added cream cheese (ingredients)
- A standard hamburger (base_food) with added bacon or extra cheese (ingredients)

**JSON Output:**

- The `base_food` field will be populated with the standard dish from the USDA list
- The `ingredients` array will contain **only the additions/toppings**, not the base components

**Example:** Frozen pizza with added toppings → HYBRID_DECOMPOSITION with base_food="Pizza, cheese, from frozen, thin crust" and ingredients=[pepperoni, mushrooms]

---

## Instructions

### 1. Analyze the Image

Carefully examine the image to identify all distinct food items or dishes.

**CRITICAL: VISIBLE INGREDIENTS ONLY**
- Only include ingredients that you can CLEARLY SEE in the image
- Do NOT add ingredients based on typical recipes, assumptions, or dish name expectations
- If you cannot visually confirm an ingredient, DO NOT include it
- Let the visible ingredients determine the dish_name, not vice versa

### 2. Assign dish_name

Provide a common, user-friendly name for the item (e.g., "Pepperoni Pizza," "Apple," "Custom Salad").

### 3. Select analysis_method

For each dish, choose the most appropriate method:

- **USE_AS_IS**
- **DECOMPOSE_TO_INGREDIENTS**
- **HYBRID_DECOMPOSITION**

### 4. Populate base_food

- If using **USE_AS_IS** or **HYBRID_DECOMPOSITION**, find the closest matching dish or item from the provided USDA list to serve as the "base."
- If using **DECOMPOSE_TO_INGREDIENTS**, set `base_food.item_name` to **null** and `base_food.weight_g` to **0**.

### 5. Populate ingredients

**Constraint:** ALL ingredient names MUST be copied EXACTLY from the USDA list provided below.

- If **USE_AS_IS**: This array MUST be **empty** (`[]`).
- If **DECOMPOSE_TO_INGREDIENTS**: List all constituent ingredients and their weights.
- If **HYBRID_DECOMPOSITION**: List **only** the added toppings/ingredients and their weights.

### 6. Estimate Weights

Provide all weights in grams (g).

**PLATE-BASED ESTIMATION**: Use the plate/bowl as your primary scale reference. Standard dinner plates are 25-28cm diameter. Observe how much of the plate each ingredient covers and at what depth.

**CRITICAL - Cooking State**: For pasta, rice, grains, and legumes - pay special attention to cooking state:

- If you see COOKED pasta/rice, estimate the COOKED weight but specify "cooked" in ingredient_name
- If estimating dry weight equivalent, use "dry uncooked" in ingredient_name
- Getting this wrong causes massive calorie calculation errors

### 7. Confidence Score

Provide a confidence score (0.0 to 1.0) for your identification of the overall dish.

### 8. JSON Output

Format your entire output as a single JSON object. DO NOT include any text, explanation, or markdown formatting outside of the JSON object itself.

---

{ingredients_header}

---

## Required JSON Schema

Your output MUST conform to this exact JSON structure. If a value is unknown, use null. **Do NOT include comments in your final JSON output.**

{{
  "dishes": [
    {{
      "dish_name": "Example Dish 1",
      "confidence": 0.95,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {{
        "item_name": "[Base dish from USDA list]",
        "weight_g": 280
      }},
      "ingredients": [
        {{
          "ingredient_name": "[Additional ingredient 1 from USDA list]",
          "weight_g": 30
        }},
        {{
          "ingredient_name": "[Additional ingredient 2 from USDA list]",
          "weight_g": 20
        }}
      ]
    }},
    {{
      "dish_name": "Example Dish 2",
      "confidence": 0.98,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {{
        "item_name": null,
        "weight_g": 0
      }},
      "ingredients": [
        {{
          "ingredient_name": "[Ingredient 1 from USDA list]",
          "weight_g": 100
        }},
        {{
          "ingredient_name": "[Ingredient 2 from USDA list]",
          "weight_g": 50
        }},
        {{
          "ingredient_name": "[Ingredient 3 from USDA list]",
          "weight_g": 40
        }}
      ]
    }},
    {{
      "dish_name": "Example Dish 3",
      "confidence": 1.0,
      "analysis_method": "USE_AS_IS",
      "base_food": {{
        "item_name": "[Single food item from USDA list]",
        "weight_g": 180
      }},
      "ingredients": []
    }}
  ]
}}

---

**END OF PROMPT**"""

    @classmethod
    def get_plate_based_visual_weight_estimation(cls) -> str:
        """プレートベースの視覚的重量推定（画像特有）"""
        return """
PLATE-BASED VISUAL WEIGHT ESTIMATION:
• Carefully observe the plate/bowl size, shape, and depth in the image
• Use the plate as your primary reference for scale - standard dinner plates are typically 25-28cm (10-11 inches) diameter
• Estimate how much of the plate/bowl is covered by each ingredient and at what depth/height
• Consider the 3D volume: height/thickness of food items relative to the plate rim
• For pasta/rice: estimate the volume they occupy in the bowl/plate and convert to weight (cooked pasta ~1.1g/ml, cooked rice ~1.5g/ml)
• For salads: consider the leaf density and compression - loose greens are ~0.2-0.3g/ml, compressed ~0.5g/ml
• For sauces/dressings: observe the coverage area and estimated thickness on the plate
• Cross-reference your estimates: does the total weight seem reasonable for what's visible on the plate?
• If multiple dishes are present, compare their relative sizes to ensure proportional weight estimates
"""

    @classmethod
    def get_american_portion_context(cls) -> str:
        """アメリカンポーションコンテキスト（画像特有）"""
        return """
AMERICAN PORTION SIZE CONTEXT:
• Assume this is a typical American meal serving - American portions are generally 25-50% larger than international standards
• Restaurant portions in America are typically generous and designed to provide satisfaction and value
• Main dishes (pasta, rice, meat) should reflect American restaurant/dining portion sizes
• For pasta dishes: American restaurant servings are typically 200-300g cooked weight (equivalent to 80-120g dry)
• For proteins: American servings are typically 150-250g (6-8 oz)
• For side salads: American portions are typically 100-200g of greens
• Consider that American dining culture emphasizes generous portions and hearty meals
"""
