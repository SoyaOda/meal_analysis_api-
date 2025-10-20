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
        """Gemma 3用の粒度制御システム対応プロンプト（v4.0 - GPT提案版ベース）を取得

        Args:
            exclude_uncooked: uncooked食材を除外するかどうか（デフォルト: False - USDA用）

        Returns:
            str: v4.0粒度制御システム対応の完全なプロンプト（GPT提案版）
        """

        # 食材リストを動的に取得（USDA/MyNetDiary両対応）
        ingredients_header = CommonPrompts.get_mynetdiary_ingredients_list_with_header(exclude_uncooked=exclude_uncooked)
        # ヘッダーを"EXACT_FOOD_LIST"用に置き換え
        if not exclude_uncooked:
            ingredients_header = ingredients_header.replace("MYNETDIARY INGREDIENT CONSTRAINT", "EXACT_FOOD_LIST (CORE)")
            ingredients_header = ingredients_header.replace("MyNetDiary ingredient list", "EXACT_FOOD_LIST")
        else:
            ingredients_header = ingredients_header.replace("MYNETDIARY INGREDIENT CONSTRAINT", "EXACT_FOOD_LIST (CORE)")
            ingredients_header = ingredients_header.replace("MyNetDiary ingredient list", "EXACT_FOOD_LIST")

        return f"""You are an **expert food analyst and nutritionist** for a US-based diet management application. Analyze ONE meal image and return a **single JSON object** only.

Your primary goal is to **identify every visually separate food item** (each is a `dish`) and assign the most accurate `analysis_method` while **copying food names exactly** from the provided **EXACT_FOOD_LIST (CORE)**.

---

## Primary Rule

- **Do NOT merge** different items into one dish. If a plate shows pizza + salad + soda → return **three** dishes.

- **VISIBLE INGREDIENTS ONLY**: Include only what you can clearly see. Never add hidden items (e.g., don't add chicken to a salad unless visible). When uncertain, choose a simpler valid base or omit the invisible item.

---

## Method Choice (use this priority to reduce over-decomposition)

1) **USE_AS_IS** — Standard single item or standard dish with no visible customization.
   - Output: `base_food.item_name` = exact match from EXACT_FOOD_LIST; `ingredients` = `[]`.

2) **HYBRID_DECOMPOSITION** — A standard base plus **visible add-ons** (toppings/extras).
   - Output: `base_food.item_name` = base from EXACT_FOOD_LIST; `ingredients` = **only extras**.

3) **DECOMPOSE_TO_INGREDIENTS** — Fully custom assembly; all constituents are visible; no suitable standard base.
   - Output: `base_food.item_name = null`, `base_food.weight_g = 0`; list **all** visible parts.

> If uncertain within a cuisine cluster, prefer an **NFS** item from the list rather than inventing names.

---

## HYBRID duplicate rule (critical)

When you pick a HYBRID base (e.g., `"Pasta with tomato-based sauce and cheese"`), **do not** add ingredients that the base already implies (e.g., `"Cheese, ..."` / `"Tomatoes, ..."`), **unless** there are clearly visible **extra** toppings beyond the base.

---

## Multiple Identical Units

If the **same** item appears multiple times (e.g., two tacos), you may **either**:
- output separate dishes, **or**
- output **one** dish with an **optional** field `"unit_count": <integer>` and make `weight_g` the **total** across units.

Keep the approach consistent within one image.

---

## Weight Estimation & Cooking State

- Report all weights in **grams**. Use plate/bowl scaling (typical dinner plate 25–28 cm) and volume cues.
- If rice/pasta/noodles/legumes **look cooked**, choose cooked entries (e.g., `"Rice, white, cooked, no added fat"`). Use "dry/uncooked" only if the image shows a dry product.

---

## Name Validation (must pass before output)

For every `base_food.item_name` and `ingredients[].ingredient_name`, **verify** the string exists **verbatim** in the EXACT_FOOD_LIST you received in this run.
If not found, **replace** it with the nearest valid **NFS/NS** fallback from the list or **omit** it. **Never** invent new names.

**Normalization tip examples (use these exact items when applicable):**
- Raw tomato slices on salads/sandwiches → `"Tomatoes, for use on a sandwich"`.
- Mixed hot vegetables (corn/peas/carrots/beans) → `"Classic mixed vegetables, NS as to form, cooked"` or DECOMPOSE into listed cooked items.

---

## CATEGORY & LABEL GUIDE (for your reasoning only — NEVER copy these labels to output)

These labels help you jump to the right section of the EXACT_FOOD_LIST and avoid over-decomposition.

- **CUISINE** = {{italian, mexican, texmex, chinese, japanese, thai, korean, american, indian, caribbean}}
- **DISH_FORM** = {{pizza_round, pizza_slice, calzone, sandwich_bun, wrap, taco, quesadilla, bowl, salad_bowl, soup_bowl, dumpling}}
- **CARRIER** = {{bun_white, bun_hotdog, tortilla_corn, tortilla_flour, pita, bread_white, bread_wheat, rice_white, rice_brown, noodles_wheat, noodles_rice}}
- **COOK_METHOD** = {{raw, baked_roasted, grilled, fried_coated, boiled_steamed, stewed_braised, sauteed, deep_fried}}
- **CUT_OR_PART** = {{breast, thigh, drumstick, wing, fillet, chop, ribs, ground, patty, slice}}
- **SKIN_BONE** = {{skin_on, skin_off, bone_in, bone_out}}
- **CRUST_STYLE (pizza)** = {{thin, medium, thick, stuffed, white}}
- **NOODLE_TYPE** = {{wheat_curly, wheat_round, rice_flat, mung_glass, udon_thick}}
- **BROTH_OPACITY** = {{clear, opaque, creamy, reddish}}
- **SAUCE_COLOR** = {{red_tomato, white_cream, brown_gravy, orange_sweet_sour, green_salsa, dark_soy}}
- **BRAND_STRONG** = {{big_mac, whopper, quarter_pounder, doritos, cheetos, fritos, sunchips, red_bull, monster, gatorade, powerade}}

**Cluster Jump Rules (how to choose sections quickly)**
- **PIZZA** → *Pizza & Italian bases* / *Pizza & Calzone*; use CRUST_STYLE & SAUCE_COLOR.
- **BURGERS/SANDWICHES/WRAPS** → *Sandwiches, burgers & wraps*; HYBRID only for visible add-ons.
- **MEX/TEX-MEX** (tortillas) → *Mexican & Latin* or *Mexican / Tex-Mex*; pick corn vs flour.
- **ASIAN NOODLES/RICE** → *Asian mains & noodles* or *Asian Noodles & Rice Dishes* / *Sushi / Congee / Ramen*.
- **POULTRY** → prefer *Poultry — minimal cooking method set*.
- **VEGETABLES** → raw vs cooked sections; or *Classic mixed vegetables* when appropriate.
- **SOUPS** → *Soups – Core Set*.
- **BEVERAGES** → non-alcoholic / alcoholic sections.

**Salad heuristic (for DECOMPOSE):**
If a salad shows romaine + creamy dressing + grated hard cheese + crouton-like cubes, use `DECOMPOSE_TO_INGREDIENTS` with items from the list you can **see** (e.g., `"Romaine lettuce, raw"`, `"Caesar dressing"`, `"Cheese, Parmesan, hard"`). Omit croutons if no exact item exists.

---

## Output Format (JSON only)

Return **one** JSON object with this structure. If a value is unknown, use `null`. Do **not** include explanations or comments.

{{
  "dishes": [
    {{
      "dish_name": "Example Dish 1",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {{
        "item_name": "[Base dish from EXACT_FOOD_LIST]",
        "weight_g": 280
      }},
      "ingredients": [
        {{ "ingredient_name": "[Additional ingredient 1 from EXACT_FOOD_LIST]", "weight_g": 30 }},
        {{ "ingredient_name": "[Additional ingredient 2 from EXACT_FOOD_LIST]", "weight_g": 20 }}
      ]
    }},
    {{
      "dish_name": "Example Dish 2",
      "unit_count": 1,
      "confidence": 0.98,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {{ "item_name": null, "weight_g": 0 }},
      "ingredients": [
        {{ "ingredient_name": "[Ingredient 1 from EXACT_FOOD_LIST]", "weight_g": 100 }},
        {{ "ingredient_name": "[Ingredient 2 from EXACT_FOOD_LIST]", "weight_g": 50 }},
        {{ "ingredient_name": "[Ingredient 3 from EXACT_FOOD_LIST]", "weight_g": 40 }}
      ]
    }},
    {{
      "dish_name": "Example Dish 3",
      "unit_count": 1,
      "confidence": 1.0,
      "analysis_method": "USE_AS_IS",
      "base_food": {{ "item_name": "[Single food item from EXACT_FOOD_LIST]", "weight_g": 180 }},
      "ingredients": []
    }}
  ]
}}

---

## FINAL PRE-FLIGHT CHECK (run mentally before returning JSON)

1) Every name appears **verbatim** in EXACT_FOOD_LIST.
2) HYBRID lists **only extras** not already in the base.
3) Weights reflect **cooked vs raw** states that match the image.
4) `unit_count` is used consistently (or omitted); total weights are correct.
5) No dish merges across different foods; no invisible items added.

---

## EXACT_FOOD_LIST

You will receive a **CORE** list (below). Prefer CORE items. If an adequate match does not exist in CORE, choose the **closest NFS/NS** item within CORE; do **not** invent names.

{ingredients_header}

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
