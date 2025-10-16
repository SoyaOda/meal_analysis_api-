# LLMプロンプト改善実装ガイド

## 📅 作成日: 2025-10-15

## 🎯 目的

`split_ingredient_names_with_llm.py`のプロンプトを改善し、Word Query APIのTier Systemと完璧に連携する検索パターンを生成するための詳細な実装ガイドです。

---

## 📊 現状のプロンプト問題点（Stemming考慮）

### 現在のStemming実装
```python
# Word Query APIはPorter Stemmerを使用
def stem_query(query: str) -> str:
    # 小文字化 → 特殊文字除去 → 語幹化
    return stemmed_query

# 効果：
"breads" → "bread"  # 単複形統一
"toasted" → "toast"  # 時制統一
"french" → "french"  # 変化なし
```

### 問題1: 限定的なリスト生成ロジック（Stemmingでも解決不可）

**現在のルール:**
```python
# "or"がある場合のみリスト形式
"Chickpeas or garbanzo beans" → ["Chickpeas", "garbanzo beans"]  # ✅ OK
"Bread, French or Vienna" → ["French", "Vienna"]  # ❌ "Bread"が欠落
"Cookie, chocolate chip" → "Cookie"  # ⚠️ リストにならない
```

### 問題2: Stemming後も残る検索失敗

```json
// 現在の出力例
{
  "description": "Bread, French or Vienna, toasted",
  "search_name": ["French", "Vienna"],  // ❌ "Bread"がない
  "ai_description": "toasted"
}

// Stemming処理後の問題
ユーザー入力: "bread" → stem: "bread"
"French" → stem: "french"  // ❌ bread ≠ french
"Vienna" → stem: "vienna"  // ❌ bread ≠ vienna

結果: マッチしない（基本カテゴリ名が欠落）
```

**影響**: Stemmingがあってもユーザーが「bread」で検索してもヒットしない

---

## 🚀 改善されたプロンプト実装

### 完全版プロンプト

```python
def create_improved_splitting_prompt(recent_results: List[Dict] = None) -> str:
    """
    改善版：ユーザー検索パターンを網羅的に生成するプロンプト

    主な改善点:
    1. search_nameを常に配列形式で出力
    2. ユーザーの検索パターンを網羅的に生成
    3. 主要カテゴリを必ず含める
    4. Tier Systemとの完璧な連携
    """

    # 文脈セクション（継続性のため）
    context_section = ""
    if recent_results and len(recent_results) > 0:
        context_section = "\n\n📝 RECENT PROCESSING EXAMPLES:\n"
        context_section += "Use these for consistency in formatting and capitalization:\n\n"

        for i, result in enumerate(recent_results[-5:], 1):  # 最新5件で十分
            search_patterns = json.dumps(result['search_name'], ensure_ascii=False)
            context_section += f"{i}. \"{result['original_name']}\"\n"
            context_section += f"   → {search_patterns}\n\n"

    return f"""You are an advanced food search optimization AI specialized in generating comprehensive search patterns.

{context_section}
🎯 YOUR MISSION:
Transform food descriptions into exhaustive search pattern arrays that cover ALL possible ways users might search.

⚡ CRITICAL RULES:

1️⃣ **ALWAYS OUTPUT AS ARRAY**
   - search_name must ALWAYS be an array, even for simple items
   - Minimum 2 patterns, typically 3-6 patterns per food item

2️⃣ **PATTERN GENERATION FORMULA**
   For each food item, systematically generate:

   a) Main category (MANDATORY)
      → "Bread", "Cheese", "Cookie", "Topping"

   b) Category + specific type
      → "French bread", "Gouda cheese", "Chocolate cookie"

   c) Specific type alone
      → "French", "Gouda", "Chocolate chip"

   d) Category + preparation/state
      → "Toasted bread", "Melted cheese", "Frozen pizza"

   e) Common variations
      → Abbreviations, alternative names, colloquialisms

3️⃣ **CATEGORY EXTRACTION RULES**
   - First word/phrase before comma is usually the main category
   - Common compound categories should be recognized as units:
     * "White beans", "Black beans", "Green beans" → Category is the full compound
     * "Chicken breast", "Chicken thigh" → Category is the full compound
     * "Ice cream", "Sour cream" → Category is the full compound
   - Exception: Adjectives like "Baby", "Vegan", "Frozen" are modifiers, not categories
   - For "X, Y or Z" → Category is X, variants are Y and Z

4️⃣ **ai_description USAGE**
   Only include in ai_description what's NOT in search patterns:
   - Nutritional modifiers: "reduced calorie", "low fat", "high fiber"
     * Exception: When "and/or" is present with nutritional modifiers,
       include them in search patterns for better discoverability
   - Brand names
   - Detailed specifications not commonly searched
   - If everything important is in search_name → set to null

5️⃣ **AND/OR PATTERN HANDLING**
   When you see "and/or" in descriptions:
   - Generate patterns for BOTH options
   - Include combined patterns
   - Add common alternative terms users might search for
   - "and/or" means the item could have either property, or both

6️⃣ **DISPLAY NAME GENERATION (North American App)**
   Generate user-friendly display names for mobile app:

   a) display_name (REQUIRED):
      - 15-25 characters ideal, max 30
      - Use common American food terms
      - Focus on main identity
      - Smart abbreviations: PB = Peanut Butter, Mac = Macaroni, BBQ = Barbecue

   b) display_variant (OPTIONAL):
      - 5-15 characters
      - Only essential variants
      - Format examples: "Thin Crust", "Skinless", "No-Bake"

   c) display_badges (OPTIONAL):
      - Array of 0-3 short badges
      - Each badge: 3-8 characters
      - Priority order: Nutrition > Cooking > Source
      - Common badges:
        * Nutrition: "Diet", "Lite", "Fiber+", "Low-Na", "Protein"
        * Cooking: "No-Bake", "Toasted", "Grilled", "Raw"
        * Source: "Fast Food", "School", "Homemade"

7️⃣ **CONSUMPTION FREQUENCY (北米市場向け)**
   北米での一般的な摂取頻度を3段階で分類:

   consumption_frequency (必須): 摂取頻度カテゴリ
   frequency_score (必須): 並び替え用の数値スコア

   分類基準:
   - "common" (スコア: 3) - 週3回以上摂取される基本食材
     * Walmart、Costco、Krogerで通年入手可能
     * アメリカ人の70%以上が週に複数回消費
     * 例: bread, milk, chicken, coffee, eggs, cheese, rice

   - "moderate" (スコア: 2) - 週1-2回程度の一般的な食材
     * 一般的だが毎日ではない
     * 健康志向やグルメな選択肢
     * 例: salmon, avocado, quinoa, greek yogurt, berries

   - "rare" (スコア: 1) - 月1回以下、特別な機会の食材
     * 高価格帯（$20/lb以上）
     * エスニックまたは珍しい食材
     * 例: lobster, caviar, exotic fruits, specialty cheeses

   判断のヒント:
   - 生食用野菜・果物のraw → 頻度維持（cucumber, lettuce, apple等）
   - 調理前提食材のraw → 頻度を1段階下げる（肉、魚、豆、穀物）
   - ブランド名付き → 頻度を1段階上げる（一般流通品）
   - Fast food、Restaurant → "common"寄り
   - Homemade、From scratch → "moderate"寄り

   RAW食材の判断基準:
   - 🥗 サラダ野菜（生食一般的）→ 頻度維持
   - 🍎 果物（生食が標準）→ 頻度維持
   - 🥩 生肉・生魚 → rare（調理必須）
   - 🌾 生の穀物・豆 → 頻度-1（調理必須）

8️⃣ **EMOJI MAPPING FOR UI ENHANCEMENT**
   UI向け絵文字マッピング（前処理で自動追加）:

   NOTE: The emoji mapping is handled AUTOMATICALLY in preprocessing:
   - Each food item receives a category emoji based on its USDA category
   - 145 categories have been mapped to appropriate emojis
   - The preprocessor adds "category" and "category_emoji" fields
   - LLM does NOT need to generate emojis (they come from preprocessing)

   Example preprocessed input you'll receive:
   {
     "foodCode": "51107040",
     "description": "Bread, French or Vienna, toasted",
     "category": "Yeast breads",           // Added by preprocessor
     "category_emoji": "🍞",                // Added by preprocessor
     "foodNutrients": [...]
   }

   Category emoji examples (auto-assigned by preprocessor):
   - "Yeast breads" → "🍞"
   - "Cheese" → "🧀"
   - "Pizza" → "🍕"
   - "Ice cream" → "🍨"
   - "Chicken, whole pieces" → "🍗"
   - "Vegetables, fresh" → "🥦"
   - "Fruits" → "🍎"
   - "Beverages" → "🥤"
   - Default for unknown → "🍽️"

📚 COMPREHENSIVE EXAMPLES:

Example 1: "Bread, French or Vienna, toasted"
{{
  "search_name": [
    "Bread",                // Main category (MANDATORY)
    "French bread",         // Category + type
    "Vienna bread",         // Category + type
    "Toasted bread",        // Category + state
    "French",              // Type alone
    "Vienna",              // Type alone
    "French toast"         // Common confusion/variation
  ],
  "ai_description": null,   // All searchable terms are in search_name
  "consumption_frequency": "common",
  "frequency_score": 3
}}

Example 2: "Cheese, Gouda or Edam"
{{
  "search_name": [
    "Cheese",              // Main category
    "Gouda cheese",        // Category + type
    "Edam cheese",         // Category + type
    "Gouda",              // Type alone
    "Edam"                // Type alone
  ],
  "ai_description": null
}}

Example 3: "Cookie, chocolate chip"
{{
  "search_name": [
    "Cookie",                     // Main category
    "Chocolate chip cookie",      // Full name
    "Chocolate cookie",           // Alternative
    "Choc chip cookie",          // Common abbreviation
    "Chocolate chip"             // Ingredient alone
  ],
  "ai_description": null,
  "consumption_frequency": "common",  // Popular snack
  "frequency_score": 3
}}

Example 4: "Topping, chocolate"
{{
  "search_name": [
    "Topping",              // Main category
    "Chocolate topping",    // Category + type
    "Chocolate"            // Type alone
  ],
  "ai_description": null
}}

Example 5: "Bread, wheat, reduced calorie, high fiber"
{{
  "search_name": [
    "Bread",               // Main category
    "Wheat bread",         // Category + type
    "Whole wheat bread",   // Common variation
    "Wheat"               // Type alone
  ],
  "ai_description": "reduced calorie, high fiber"  // Nutritional specs
}}

Example 6: "Pizza, cheese, from restaurant or fast food"
{{
  "search_name": [
    "Pizza",               // Main category
    "Cheese pizza",        // Category + type
    "Pizza cheese"         // Alternative order
  ],
  "ai_description": "from restaurant, fast food"  // Source info
}}

Example 7: "Beans, black, boiled, with salt"
{{
  "search_name": [
    "Beans",               // Main category
    "Black beans",         // Category + type
    "Boiled beans",        // Category + preparation
    "Black"               // Sometimes searched alone
  ],
  "ai_description": "boiled, with salt"  // Preparation details
}}

Example 8: "Ice cream, vanilla, light"
{{
  "search_name": [
    "Ice cream",           // Main category (two words kept together)
    "Vanilla ice cream",   // Category + flavor
    "Vanilla"             // Flavor alone
  ],
  "ai_description": "light",  // Nutritional modifier
  "consumption_frequency": "common",  // Popular dessert
  "frequency_score": 3
}}

Example 9: "Lobster, steamed, with butter"
{{
  "search_name": [
    "Lobster",
    "Steamed lobster",
    "Lobster with butter"
  ],
  "ai_description": "with butter",
  "consumption_frequency": "rare",  // Expensive, special occasion
  "frequency_score": 1,
  "display_name": "Lobster",
  "display_variant": "Steamed",
  "display_badges": ["Premium"]
}}

Example 10: "White beans, boiled, NFS"
{{
  "search_name": [
    "White beans",         // Compound category kept together
    "Beans",              // General category
    "Boiled white beans", // Preparation + compound
    "Boiled beans",       // Preparation + general
    "White"              // Color alone (less common)
  ],
  "ai_description": "boiled, NFS"  // Don't worry about NFS, cleaned in post-processing
}}

Example 10: "Chicken breast, grilled"
{{
  "search_name": [
    "Chicken breast",     // Compound category kept together
    "Chicken",           // Main animal
    "Grilled chicken breast", // Preparation + compound
    "Grilled chicken",   // Preparation + main
    "Breast"            // Cut alone (for specific searches)
  ],
  "ai_description": "grilled"
}}

Example 11: "Bread, reduced calorie and/or high fiber, white"
{{
  "search_name": [
    "Bread",                    // Main category
    "White bread",              // Category + type
    "Reduced calorie bread",    // Category + option A
    "High fiber bread",         // Category + option B
    "Diet bread",              // Common alternative for reduced calorie
    "Low calorie bread",       // Alternative term
    "Light bread",             // Marketing term
    "Healthy bread",           // General search term
    "Whole grain bread"        // Common association with high fiber
  ],
  "ai_description": null      // All nutritional specs included in patterns
}}

Example 12: "Bread, with fruit and/or nuts"
{{
  "search_name": [
    "Bread",
    "Fruit bread",
    "Nut bread",
    "Fruit and nut bread",
    "Raisin bread",           // Common fruit bread
    "Walnut bread",           // Common nut bread
    "Banana bread"            // Another common fruit bread
  ],
  "ai_description": null
}}

Example 13: "Chicken or turkey and vegetables including carrots, broccoli, and/or dark-green leafy"
{{
  "search_name": [
    "Chicken and vegetables",
    "Turkey and vegetables",
    "Chicken vegetable",
    "Turkey vegetable",
    "Chicken",
    "Turkey",
    "Vegetable stir fry",
    "Chicken stir fry",
    "Turkey stir fry"
  ],
  "ai_description": "with carrots, broccoli, dark-green leafy vegetables",
  "display_name": "Chicken & Veggies",
  "display_variant": "Stir-fry Mix",
  "display_badges": []
}}

Example 14: "Cookie, marshmallow and peanut butter, with oat cereal, no bake"
{{
  "search_name": [
    "Cookie",
    "Marshmallow cookie",
    "Peanut butter cookie",
    "PB marshmallow cookie",
    "No bake cookie",
    "Oat cookie"
  ],
  "ai_description": null,
  "display_name": "PB Marshmallow Cookie",
  "display_variant": "No-Bake",
  "display_badges": ["Oats"]
}}

Example 15: "Pizza with pepperoni, from restaurant or fast food, thin crust"
{{
  "search_name": [
    "Pizza",
    "Pepperoni pizza",
    "Thin crust pizza",
    "Restaurant pizza",
    "Fast food pizza",
    "Pepperoni"
  ],
  "ai_description": "from restaurant or fast food",
  "display_name": "Pepperoni Pizza",
  "display_variant": "Thin Crust",
  "display_badges": ["Restaurant"]
}}

Example 16: "Chicken breast, rotisserie, skin not eaten"
{{
  "search_name": [
    "Chicken breast",
    "Chicken",
    "Rotisserie chicken",
    "Rotisserie chicken breast",
    "Skinless chicken",
    "Breast"
  ],
  "ai_description": null,
  "display_name": "Rotisserie Chicken",
  "display_variant": "Breast, Skinless",
  "display_badges": []
}}

Example 17: "Coffee, instant, decaffeinated, pre-lightened and pre-sweetened with sugar"
{{
  "search_name": [
    "Coffee",
    "Instant coffee",
    "Decaf coffee",
    "Decaffeinated coffee",
    "Sweet coffee",
    "Pre-sweetened coffee"
  ],
  "ai_description": "pre-lightened, pre-sweetened",
  "display_name": "Instant Coffee",
  "display_variant": "Decaf, Sweet",
  "display_badges": ["Pre-mix"]
}}

⚠️ COMMON MISTAKES TO AVOID:
- ❌ Missing the main category
- ❌ Only including specific variants
- ❌ Making search_name a string instead of array
- ❌ Including too much in ai_description

🎯 OUTPUT FORMAT:
{{
  "search_name": ["pattern1", "pattern2", ...],  // ALWAYS an array
  "ai_description": "modifiers" or null,          // Only non-searchable info
  "display_name": "User-friendly name",           // 15-30 chars for app display
  "display_variant": "Variant" or null,           // 5-15 chars, optional
  "display_badges": ["Badge1", "Badge2"] or [],   // 0-3 badges, 3-8 chars each
  "consumption_frequency": "common" | "moderate" | "rare",  // 摂取頻度
  "frequency_score": 3 | 2 | 1                    // 並び替え用スコア
}}

Remember: Your goal is to maximize searchability. Think "What would users type?" and include ALL those patterns."""
```

### 実装コード変更

```python
# split_ingredient_names_with_llm.py の修正箇所

# 1. プロンプト関数を置き換え（72行目から）
def create_splitting_prompt(recent_results: List[Dict] = None) -> str:
    # 上記の改善版プロンプトに置き換え
    pass

# 2. 結果検証関数を追加
def validate_search_patterns(result: Dict, original_description: str) -> Dict:
    """
    生成された検索パターンを検証・修正
    Stemming処理を考慮した検証ロジック
    """
    if not isinstance(result.get('search_name'), list):
        # 配列でない場合は配列に変換
        if isinstance(result['search_name'], str):
            result['search_name'] = [result['search_name']]
        else:
            result['search_name'] = []

    # 主要カテゴリの確認
    main_categories = [
        'Bread', 'Cheese', 'Cookie', 'Topping', 'Icing',
        'Pizza', 'Beans', 'Rice', 'Pasta', 'Meat', 'Fish',
        'Chicken', 'Beef', 'Pork', 'Vegetable', 'Fruit',
        'Milk', 'Yogurt', 'Butter', 'Oil', 'Sauce'
    ]

    desc_lower = original_description.lower()
    for category in main_categories:
        if category.lower() in desc_lower:
            # カテゴリが含まれているか確認
            has_category = any(
                category.lower() in pattern.lower()
                for pattern in result['search_name']
            )
            if not has_category:
                # 先頭に追加
                result['search_name'].insert(0, category)
                print(f"   ✅ カテゴリ '{category}' を追加")

    # and/orパターンの処理
    if "and/or" in original_description:
        # 栄養特性の場合
        if "reduced calorie" in original_description:
            ensure_patterns = ["diet", "low calorie", "light", "reduced calorie"]
            for pattern in ensure_patterns:
                if not any(pattern.lower() in p.lower() for p in result['search_name']):
                    result['search_name'].append(pattern)

        if "high fiber" in original_description:
            ensure_patterns = ["high fiber", "whole grain", "fiber"]
            for pattern in ensure_patterns:
                if not any(pattern.lower() in p.lower() for p in result['search_name']):
                    result['search_name'].append(pattern)

        # 材料の場合
        if "fruit and/or" in original_description:
            ensure_patterns = ["fruit", "with fruit"]
            for pattern in ensure_patterns:
                if not any(pattern.lower() in p.lower() for p in result['search_name']):
                    result['search_name'].append(pattern)

        if "nuts" in original_description:
            ensure_patterns = ["nut", "with nuts"]
            for pattern in ensure_patterns:
                if not any(pattern.lower() in p.lower() for p in result['search_name']):
                    result['search_name'].append(pattern)

    # Display name検証と調整
    if 'display_name' not in result or not result['display_name']:
        # Display nameが欠落している場合、自動生成
        base_name = original_description.split(',')[0].strip()
        result['display_name'] = base_name[:30]  # 最大30文字

    # Display name文字数検証
    if len(result['display_name']) > 30:
        result['display_name'] = result['display_name'][:30]
        print(f"   ⚠️ Display name truncated to 30 chars")

    # Display variant検証
    if 'display_variant' in result and result['display_variant']:
        if len(result['display_variant']) > 15:
            result['display_variant'] = result['display_variant'][:15]

    # Display badges検証
    if 'display_badges' not in result:
        result['display_badges'] = []
    elif len(result['display_badges']) > 3:
        # 最大3個のバッジに制限
        result['display_badges'] = result['display_badges'][:3]
        print(f"   ⚠️ Display badges limited to 3")

    # 重複削除（大文字小文字を区別）
    seen = set()
    unique_patterns = []
    for pattern in result['search_name']:
        if pattern not in seen:
            seen.add(pattern)
            unique_patterns.append(pattern)
    result['search_name'] = unique_patterns

    # 最低2パターン確保
    if len(result['search_name']) < 2:
        # 説明文から単語を抽出して追加
        words = original_description.split(',')[0].strip().split()
        if len(words) > 1:
            result['search_name'].append(' '.join(words))

    # Stemming効果のログ出力（デバッグ用）
    if DEBUG_MODE:
        print(f"   📊 Stemming効果予測:")
        for pattern in result['search_name']:
            stemmed = stem_query(pattern)
            print(f"      '{pattern}' → '{stemmed}'")

    return result

# 3. split_ingredient_name関数を修正（176行目）
async def split_ingredient_name(
    ingredient_name: str,
    api_key: str,
    client: AsyncOpenAI,
    recent_results: List[Dict] = None,
    max_retries: int = 3
) -> Optional[Dict]:
    # ... 既存のコード ...

    # JSONパース後に検証を追加
    result = json.loads(response_text)

    # 検証と修正
    result = validate_search_patterns(result, ingredient_name)

    return result

# 4. データ型定義（TypeScript版）
interface ImprovedFoodItem {
    // 既存フィールド
    foodCode: string;
    description: string;
    search_name: string[];         // 検索パターン配列
    ai_description: string | null;

    // 新規追加フィールド（北米アプリ向け）
    display_name: string;          // アプリ表示用名（15-30文字）
    display_variant?: string;      // バリエーション（5-15文字）
    display_badges?: string[];     // バッジ配列（0-3個、各3-8文字）

    // 栄養情報
    foodNutrients: NutrientInfo[];
}
```

---

## 📋 実装チェックリスト

### 事前準備
- [ ] 既存データのバックアップ作成
- [ ] DeepInfra APIキーの確認
- [ ] テスト環境の準備

### コード修正
- [ ] `create_splitting_prompt`関数の置き換え
- [ ] `validate_search_patterns`関数の追加
- [ ] `split_ingredient_name`関数への検証追加
- [ ] エラーハンドリングの強化

### テストケース
```python
test_cases = [
    # カテゴリが欠落しやすいケース
    ("Bread, French or Vienna, toasted",
     ["Bread", "French bread", "Vienna bread", ...]),

    ("Cheese, Gouda or Edam",
     ["Cheese", "Gouda cheese", "Edam cheese", ...]),

    ("Topping, chocolate",
     ["Topping", "Chocolate topping", "Chocolate"]),

    # 複雑なケース
    ("Cookie, chocolate chip, reduced fat",
     ["Cookie", "Chocolate chip cookie", ...]),

    ("Pizza, cheese, from frozen",
     ["Pizza", "Cheese pizza", ...]),

    # and/orパターンのケース
    ("Bread, reduced calorie and/or high fiber, white",
     ["Bread", "White bread", "Reduced calorie bread", "High fiber bread",
      "Diet bread", "Low calorie bread", "Light bread", "Healthy bread"]),

    ("Bread, with fruit and/or nuts",
     ["Bread", "Fruit bread", "Nut bread", "Fruit and nut bread",
      "Raisin bread", "Walnut bread"]),

    # Display name生成のケース
    ("Cookie, marshmallow and peanut butter, with oat cereal, no bake",
     {
         "search_name": ["Cookie", "Marshmallow cookie", "PB marshmallow cookie"],
         "display_name": "PB Marshmallow Cookie",
         "display_variant": "No-Bake",
         "display_badges": ["Oats"]
     }),

    ("Pizza with pepperoni, from restaurant or fast food, thin crust",
     {
         "search_name": ["Pizza", "Pepperoni pizza", "Thin crust pizza"],
         "display_name": "Pepperoni Pizza",
         "display_variant": "Thin Crust",
         "display_badges": ["Restaurant"]
     })
]
```

### 品質確認
- [ ] 問題のあった16件を優先的に再処理
- [ ] ランダムサンプル50件の手動確認
- [ ] 主要カテゴリの網羅率測定

---

## 🔧 段階的実装アプローチ

### Phase 1: 小規模テスト（推奨）

```bash
# 1. テスト用サブセットを作成
python scripts/create_test_subset.py --count=50

# 2. 新プロンプトでテスト実行
python scripts/split_ingredient_names_with_llm.py --test-mode

# 3. 結果の検証
python scripts/validate_search_patterns.py
```

### Phase 2: 問題ケースの修正

```python
# 問題のある16件のみを再処理
problem_food_codes = [
    "14105010",  # Cheese, Gouda or Edam
    "91304010",  # Topping, butterscotch or caramel
    "51107040",  # Bread, French or Vienna, toasted
    # ... 他13件
]

# 選択的再処理
for food_code in problem_food_codes:
    # 該当する食品のみ再処理
    pass
```

### Phase 3: 全データ再処理

```bash
# フル再処理（1,542件）
python scripts/split_ingredient_names_with_llm.py

# クリーニングと最終処理
python scripts/clean_and_finalize_usda_split_data.py

# 検証レポート生成
python scripts/generate_quality_report.py
```

---

## 📊 期待される改善効果（Stemming込み）

### Before/After 比較

| ケース | Before | After | Stemming貢献 |
|--------|--------|-------|-------------|
| **"bread"検索** | 8件ヒットせず | 全件Tier 1でヒット | パターン網羅が解決 |
| **"breads"検索** | 8件ヒットせず | 全件Tier 1でヒット | Stemming + パターン |
| **"cheese"検索** | 1件ヒットせず | 全件Tier 1でヒット | パターン網羅が解決 |
| **"topping"検索** | 5件ヒットせず | 全件Tier 1でヒット | パターン網羅が解決 |
| **"toppings"検索** | 5件ヒットせず | 全件Tier 1でヒット | Stemming + パターン |
| **平均パターン数** | 1.5個/食品 | 4-5個/食品 | - |
| **Tier 1マッチ率** | 60% | 90%以上 | 両方の相乗効果 |

### Stemming + 改善パターンの相乗効果

```
改善後のデータ:
search_name: ["Bread", "French bread", "Vienna bread", "Toasted bread"]

ユーザー入力パターンと結果:
---
"bread" → stem: "bread"
  → "Bread" → stem: "bread" ✅ Tier 1完全マッチ

"breads" → stem: "bread"
  → "Bread" → stem: "bread" ✅ Tier 1完全マッチ（単複形OK）

"french bread" → stem: "french bread"
  → "French bread" → stem: "french bread" ✅ Tier 1完全マッチ

"french breads" → stem: "french bread"
  → "French bread" → stem: "french bread" ✅ Tier 1完全マッチ（単複形OK）

"toasted breads" → stem: "toast bread"
  → "Toasted bread" → stem: "toast bread" ✅ Tier 1完全マッチ（時制+単複形OK）
```

### 検索体験の向上

```
ユーザー入力: "bread" / "breads" / "BREAD"
---
Before: 検索結果なし or 限定的
After: すべてのパン製品がTier 1でヒット（Stemming + パターン網羅）

ユーザー入力: "french bread" / "french breads" / "French Bread"
---
Before: "French"のみで部分マッチ（Tier 5）
After: "French bread"で完全マッチ（Tier 1、大文字小文字・単複形不問）
```

---

## ⚠️ 注意事項とトラブルシューティング

### 注意事項

1. **API制限**
   - DeepInfra APIのレート制限に注意
   - バッチサイズとディレイを適切に設定

2. **メモリ使用量**
   - search_name配列が大きくなるため、メモリ使用量が増加
   - 必要に応じてバッチサイズを調整

3. **後方互換性**
   - 既存のAPIクライアントが文字列形式を期待している可能性
   - 移行期間中は両形式をサポート

### トラブルシューティング

```python
# 問題: LLMが配列を返さない
if isinstance(result['search_name'], str):
    # 自動的に配列に変換
    result['search_name'] = [result['search_name']]

# 問題: 主要カテゴリが欠落
if not has_main_category(result['search_name']):
    # 自動的に抽出して追加
    category = extract_main_category(description)
    result['search_name'].insert(0, category)

# 問題: 重複パターン
result['search_name'] = list(dict.fromkeys(result['search_name']))
```

---

## 📈 メトリクス測定

### 測定コード

```python
def measure_improvement_metrics(old_data, new_data):
    """改善効果を測定"""
    metrics = {
        'avg_patterns_per_item': 0,
        'category_coverage': 0,
        'tier_1_potential': 0,
        'search_coverage': 0
    }

    # 平均パターン数
    total_patterns = sum(len(item['search_name']) for item in new_data)
    metrics['avg_patterns_per_item'] = total_patterns / len(new_data)

    # カテゴリカバレッジ
    categories = ['Bread', 'Cheese', 'Topping', 'Icing', ...]
    covered = 0
    for item in new_data:
        for category in categories:
            if any(category in pattern for pattern in item['search_name']):
                covered += 1
                break
    metrics['category_coverage'] = (covered / len(new_data)) * 100

    return metrics
```

---

## 🔧 後処理との連携（重要）

### 後処理で自動的に処理される項目

`clean_and_finalize_usda_split_data.py`が以下を自動処理するため、**プロンプトでは複雑な処理は不要**：

| 処理内容 | プロンプト側 | 後処理側 | 理由 |
|---------|-----------|---------|------|
| **NFS除去** | 不要 | ✅ 対応済み | 後処理で確実に削除 |
| **括弧処理** | 不要 | ✅ 対応済み | 正規表現で削除 |
| **NS as to** | 不要 | ✅ 対応済み | 該当食材を削除 |
| **ブランド名** | 不要 | ✅ 対応済み | brand_or_varietyに分離 |
| **"None"文字列** | 不要 | ✅ 対応済み | nullに変換 |

### 後処理コードの詳細

```python
def normalize_description(description: Optional[str]) -> Optional[str]:
    """
    descriptionフィールドの正規化（自動実行）
    """
    # 括弧とその内容を削除
    description = re.sub(r'\s*\([^)]*\)', '', description)

    # NFSを削除
    if description.endswith(", NFS"):
        description = description[:-5].strip()

    # 文字列"None"をNoneに変換
    if description.strip() == "None":
        return None
```

### プロンプトの設計方針

**シンプルさを優先し、複雑な処理は後処理に委ねる：**

1. **プロンプトはシンプルに**
   - 基本的な検索パターン生成に集中
   - 特殊文字処理は不要
   - NFSやNS as toの処理は不要

2. **複合語の基本ルールのみ追加**
   ```
   COMPOUND FOOD RULES:
   - "White beans", "Black beans" → Keep as compound
   - "Chicken breast", "Chicken thigh" → Keep as compound
   - "Ice cream", "Sour cream" → Keep as compound
   - But also generate patterns with individual parts
   ```

3. **検証関数は軽量に**
   - 主要カテゴリの確認程度
   - 複雑な処理は後処理に任せる

---

## 🎯 複合語パターンの特別な考慮

### 識別が必要な複合語カテゴリ

```python
compound_categories = [
    # 豆類
    'White beans', 'Black beans', 'Green beans', 'Navy beans',

    # 鶏肉部位
    'Chicken breast', 'Chicken thigh', 'Chicken wing', 'Chicken leg',

    # パン類
    'French bread', 'Wheat bread', 'White bread', 'Whole wheat bread',

    # クリーム類
    'Ice cream', 'Sour cream', 'Cream cheese', 'Whipped cream',

    # その他
    'French fries', 'Sweet potato', 'Green pepper', 'Bell pepper'
]
```

### 複合語の処理ルール

```python
# 例: "White beans, boiled"
search_patterns = [
    "White beans",        # 複合語全体（最重要）
    "Beans",             # 一般カテゴリ
    "Boiled white beans", # 状態 + 複合語
    "Boiled beans",      # 状態 + 一般カテゴリ
    "White"              # 単独（低優先度）
]

# 例: "Chicken breast, grilled"
search_patterns = [
    "Chicken breast",     # 複合語全体
    "Chicken",           # 主要部分
    "Grilled chicken breast", # 状態 + 複合語
    "Grilled chicken",   # 状態 + 主要部分
    "Breast"            # 部位単独
]
```

---

## 🔄 継続的改善サイクル

### 1. データ収集
```python
# ユーザーの検索ログを収集
search_logs = collect_search_logs()
failed_searches = analyze_failed_searches(search_logs)
```

### 2. パターン分析
```python
# よく使われる検索パターンを抽出
common_patterns = extract_common_patterns(search_logs)
missing_patterns = identify_missing_patterns(failed_searches)
```

### 3. プロンプト更新
```python
# 新しいパターンをプロンプトの例に追加
update_prompt_examples(common_patterns)
```

### 4. 再処理と検証
```python
# 更新されたプロンプトで再処理
reprocess_with_updated_prompt()
validate_improvements()
```

---

## 📚 関連ドキュメント

- [Word Query API改善プラン](./word_query_api_improvement_plan.md)
- [現在のプロンプト実装](../scripts/split_ingredient_names_with_llm.py)
- [問題分析レポート](../docs/search_name_comprehensive_issues_report.md)
- [Tier System仕様](../../apps/word_query_api/endpoints/nutrition_search.py)

---

## 📅 更新履歴

| 日付 | バージョン | 更新内容 |
|------|-----------|---------|
| 2025-10-15 | v1.0 | 初版作成 |
| 2025-10-15 | v1.1 | Stemming考慮の詳細と相乗効果を追記 |
| 2025-10-15 | v1.2 | and/orパターン処理方針を追加、Example 11-13を追加 |
| 2025-10-15 | v1.3 | 北米アプリ向けdisplay name生成ルール追加、Example 14-17を追加 |

---

## ✅ 最終確認事項

- [ ] プロンプトの文法とロジックの確認
- [ ] テストケースの網羅性確認
- [ ] エラーハンドリングの実装
- [ ] パフォーマンス測定の準備
- [ ] ロールバック計画の策定
- [ ] ドキュメントの完成度確認