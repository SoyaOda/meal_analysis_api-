# USDA食品マッピング生成プロンプト v3.0 - 包括版

## 🎯 ミッション

未マップのUSDA食品（Survey FNDDS: 4,290個、Foundation Food: 84個）から、実用的で効率的なマッピングを生成する。

## 📊 現状分析

### マッピング済み
- **487個**の汎用食品カテゴリがマッピング済み
- 基本食材と一般的な料理をカバー

### 未マップの内訳
- **79%**のSurvey FNDDS食品が未マップ
- 主に以下のタイプ：
  - 具体的な料理名（Meat loaf, Caesar salad等）
  - ブランド別商品（McDonald's, Burger King等）
  - 調理法別バリエーション（fried, grilled, baked）
  - ソース・調味料別（with cheese sauce, with gravy）
  - 栄養調整版（fat free, light, reduced sodium）

## 🔧 マッピング戦略

### 1. 優先順位の原則

#### 高優先度（必ずマッピング）
- **頻出食品**: レストラン、家庭料理でよく見る
- **視覚的に特徴的**: 写真で明確に識別可能
- **栄養的に重要**: カロリー/栄養素が大きく異なる

#### 低優先度（除外対象）
- Baby/Toddler food（91個）
- 学校給食専用品
- WIC/USDA commodity foods
- 極めて特殊な地域料理
- ブランド固有の細かいバリエーション

### 2. 統合ルール

#### 積極的統合
```
例: Meat loaf varieties → "meat_loaf"
- Meat loaf made with beef
- Meat loaf made with beef and pork
- Meat loaf made with turkey
→ 全て"meat_loaf"に統合（肉種の違いは視覚的に判別困難）
```

#### 条件付き統合
```
例: Caesar salad varieties → "caesar_salad"
- Caesar salad, with romaine, no dressing
- Chicken caesar salad
- Caesar salad with shrimp
→ 基本は"caesar_salad"、チキン/シュリンプは視覚的に判別可能なら分離も検討
```

#### 分離維持
```
例: Pizza types
- Pizza (cheese) → "pizza"
- Pizza rolls → "pizza_rolls"（形状が全く異なる）
- Dessert pizza → "dessert_pizza"（デザート系は別カテゴリ）
```

### 3. 命名規則

#### キー名（JSON key）
- 小文字、アンダースコア区切り
- 例: `meat_loaf`, `caesar_salad`, `french_fries`

#### display_name
- 自然な英語表記、タイトルケース
- 例: "Meat loaf", "Caesar salad", "French fries"

#### default_usda選定
- 最も一般的/代表的なバリエーション
- NFSがある場合は優先（汎用的）
- 無い場合は最もシンプルな名称

### 4. カテゴリ設定

既存カテゴリを優先使用:
- `meat_dishes` - 肉料理全般
- `salads` - サラダ類
- `sandwiches` - サンドイッチ類
- `mexican` - メキシコ料理
- `asian` - アジア料理
- `italian` - イタリア料理
- `indian` - インド料理
- `breakfast` - 朝食系
- `desserts` - デザート
- `beverages` - 飲み物
- `snacks` - スナック類
- `seafood` - シーフード
- `soups_stews` - スープ・シチュー
- `potato_dishes` - じゃがいも料理
- `mixed_dishes` - 複合料理

## 📝 詳細マッピング例

```json
{
  "meat_loaf": {
    "display_name": "Meat loaf",
    "category": "meat_dishes",
    "spec2_rule": "統合（汎化）",
    "spec2_reason": "肉種の違いは視覚的に判別困難、栄養価も類似",
    "default_usda": {
      "name": "Meat loaf made with beef",
      "database": "survey_fndds",
      "reason": "最も一般的な牛肉ベース"
    },
    "all_usda_mappings": [
      {"name": "Meat loaf made with beef", "database": "survey_fndds", "specificity": "specific"},
      {"name": "Meat loaf made with beef and pork", "database": "survey_fndds", "specificity": "specific"},
      {"name": "Meat loaf made with beef, veal and pork", "database": "survey_fndds", "specificity": "specific"},
      {"name": "Meat loaf made with turkey", "database": "survey_fndds", "specificity": "specific"},
      {"name": "Meat loaf dinner, NFS, frozen meal", "database": "survey_fndds", "specificity": "generic"}
    ],
    "aliases": ["meatloaf", "meat loaf", "ground meat loaf"],
    "visual_hints": ["loaf shaped", "brown exterior", "sliced", "ground meat texture", "often with glaze"],
    "is_new_mapping": true,
    "data_sources": ["survey_fndds"],
    "nutritional_variance": "low"  // 栄養価のばらつき: low/medium/high
  },

  "caesar_salad": {
    "display_name": "Caesar salad",
    "category": "salads",
    "spec2_rule": "統合（汎化）",
    "spec2_reason": "基本構成は同じ、トッピングの有無を統合",
    "default_usda": {
      "name": "Caesar salad, with romaine, no dressing",
      "database": "survey_fndds",
      "reason": "ドレッシング別添えを想定した基本形"
    },
    "all_usda_mappings": [
      {"name": "Caesar salad, with romaine, no dressing", "database": "survey_fndds", "specificity": "generic"},
      {"name": "Caesar dressing", "database": "survey_fndds", "specificity": "component"},
      {"name": "Chicken or turkey caesar garden salad, chicken and/or turkey, lettuce, tomato, cheese, no dressing",
       "database": "survey_fndds", "specificity": "specific"}
    ],
    "aliases": ["caesar", "caesar salad", "chicken caesar", "romaine salad"],
    "visual_hints": ["romaine lettuce", "parmesan shavings", "croutons", "creamy white dressing", "anchovies optional"],
    "is_new_mapping": true,
    "common_additions": ["grilled chicken", "shrimp", "salmon"],
    "nutritional_variance": "medium"
  },

  "bibimbap": {
    "display_name": "Bibimbap",
    "category": "asian",
    "spec2_rule": "維持",
    "spec2_reason": "韓国の代表的料理、視覚的に特徴的",
    "default_usda": {
      "name": "Bibimbap, Korean",
      "database": "survey_fndds",
      "reason": "韓国の混ぜご飯料理"
    },
    "all_usda_mappings": [
      {"name": "Bibimbap, Korean", "database": "survey_fndds", "specificity": "specific"}
    ],
    "aliases": ["bibimbap", "korean mixed rice", "비빔밥"],
    "visual_hints": ["bowl presentation", "colorful vegetables arranged", "fried egg on top", "rice base", "gochujang sauce"],
    "is_new_mapping": true,
    "cultural_cuisine": "Korean",
    "nutritional_variance": "medium"
  }
}
```

## 🎯 生成対象食品（カテゴリ別）


### Meat loaf varieties (13個)

```
1. Meat loaf dinner, NFS, frozen meal
2. Meat loaf made with beef
3. Meat loaf made with beef and pork
4. Meat loaf made with beef and pork, with tomato-based sauce
5. Meat loaf made with beef, veal and pork
6. Meat loaf made with beef, with tomato-based sauce
7. Meat loaf made with chicken or turkey
8. Meat loaf made with chicken or turkey, with tomato-based sauce
9. Meat loaf made with ham
10. Meat loaf made with venison/deer
11. Meat loaf with potatoes, vegetable, frozen meal
12. Meat loaf, NS as to type of meat
13. Meat loaf, Puerto Rican style
```

### Caesar varieties (6個)

```
1. Caesar dressing
2. Caesar dressing, fat free
3. Caesar dressing, light
4. Caesar salad, with romaine, no dressing
5. Chicken or turkey caesar garden salad, chicken and/or turkey, lettuce, tomato, cheese, no dressing
6. Chicken or turkey, breaded, fried, caesar garden salad, chicken and/or turkey, lettuce, tomatoes, cheese, no dressing
```

### Pizza varieties (66個)

```
1. Breakfast pizza with egg
2. Mexican pizza
3. Pizza with beans and vegetables, thick crust
4. Pizza with beans and vegetables, thin crust
5. Pizza with cheese and extra vegetables, medium crust
6. Pizza with cheese and extra vegetables, thick crust
7. Pizza with cheese and extra vegetables, thin crust
8. Pizza with extra meat and extra vegetables, medium crust
9. Pizza with extra meat and extra vegetables, thick crust
10. Pizza with extra meat and extra vegetables, thin crust
11. Pizza with extra meat, medium crust
12. Pizza with extra meat, thick crust
13. Pizza with extra meat, thin crust
14. Pizza with meat and fruit, medium crust
15. Pizza with meat and fruit, thick crust
16. Pizza with meat and fruit, thin crust
17. Pizza with meat and vegetables, from frozen, medium crust
18. Pizza with meat and vegetables, from frozen, thick crust
19. Pizza with meat and vegetables, from frozen, thin crust
20. Pizza with meat and vegetables, from restaurant or fast food, thick crust
21. Pizza with meat and vegetables, from restaurant or fast food, thin crust
22. Pizza with meat other than pepperoni, from frozen, medium crust
23. Pizza with meat other than pepperoni, from frozen, thick crust
24. Pizza with meat other than pepperoni, from frozen, thin crust
25. Pizza with meat other than pepperoni, from restaurant or fast food, NS as to type of crust
26. Pizza with meat other than pepperoni, from restaurant or fast food, medium crust
27. Pizza with meat other than pepperoni, from restaurant or fast food, thick crust
28. Pizza with meat other than pepperoni, from restaurant or fast food, thin crust
29. Pizza with pepperoni, from frozen, medium crust
30. Pizza with pepperoni, from frozen, thick crust

... 他 36個
```

### Burger varieties (50個)

```
1. Cheese, Limburger
2. Cheeseburger slider
3. Cheeseburger slider, from fast food
4. Cheeseburger, NFS
5. Cheeseburger, from fast food, 1 large patty
6. Cheeseburger, from fast food, 1 medium patty
7. Cheeseburger, from fast food, 1 small patty
8. Cheeseburger, on wheat bun, 1 large patty
9. Cheeseburger, on wheat bun, 1 medium patty
10. Cheeseburger, on wheat bun, 1 small patty
11. Cheeseburger, on white bun, 1 large patty
12. Cheeseburger, on white bun, 1 medium patty
13. Cheeseburger, on white bun, 1 small patty
14. Chiliburger, with or without cheese, on bun
15. Double cheeseburger, from fast food, 2 large patties
16. Double cheeseburger, from fast food, 2 small patties
17. Double cheeseburger, on wheat bun, 2 large patties
18. Double cheeseburger, on wheat bun, 2 medium patties
19. Double cheeseburger, on wheat bun, 2 small patties
20. Double cheeseburger, on white bun, 2 large patties

... 他 30個
```

### Taco/Mexican (74個)

```
1. Beef taco filling: beef, cheese, tomato, taco sauce
2. Burrito bowl, NFS
3. Burrito bowl, beef or pork
4. Burrito bowl, beef or pork, with beans
5. Burrito bowl, beef or pork, with beans and rice
6. Burrito bowl, beef or pork, with rice
7. Burrito bowl, chicken
8. Burrito bowl, chicken, with beans
9. Burrito bowl, chicken, with beans and rice
10. Burrito bowl, chicken, with rice
11. Burrito bowl, with beans
12. Burrito, NFS
13. Burrito, beef, cheese
14. Burrito, beef, with beans and rice, cheese
15. Burrito, beef, with beans, cheese
16. Burrito, beef, with rice, cheese
17. Burrito, cheese only
18. Burrito, chicken, cheese
19. Burrito, chicken, with beans and rice, cheese
20. Burrito, chicken, with beans, cheese

... 他 54個
```

### Asian dishes (42個)

```
1. Asian chicken or turkey garden salad with crispy noodles, chicken and/or turkey, lettuce, fruit, nuts, crispy noodles, no dressing
2. Asian chicken or turkey garden salad, chicken and/or turkey, lettuce, fruit, nuts, no dressing
3. Beef chow mein or chop suey with noodles
4. Beef chow mein or chop suey, no noodles
5. Bibimbap, Korean
6. Broccoli, Chinese, cooked
7. Broccoli, chinese, raw
8. Cabbage, Chinese, cooked, fat added
9. Cabbage, Chinese, cooked, no added fat
10. Cabbage, Chinese, raw
11. Chicken or turkey chow mein or chop suey with noodles
12. Chicken or turkey chow mein or chop suey, no noodles
13. Chow mein or chop suey, various types of meat, with noodles
14. Cookie, tea, Japanese
15. Hot Thai sauce
16. Korean dressing or marinade
17. Kung Pao beef
18. Kung Pao pork
19. Kung Pao shrimp
20. Kung pao chicken

... 他 22個
```

### Italian dishes (167個)

```
1. Bread, Italian, Grecian, Armenian
2. Bread, Italian, Grecian, Armenian, toasted
3. Breadsticks, soft, with parmesan cheese, fast food / restaurant
4. Cheese, Parmesan, dry grated
5. Cheese, Parmesan, dry grated, fat free
6. Cheese, Parmesan, dry grated, reduced fat
7. Cheese, Parmesan, hard
8. Chicken or turkey salad, made with Italian dressing
9. Chicken or turkey salad, made with light Italian dressing
10. Creamy Italian dressing
11. Creamy Italian dressing, fat free
12. Creamy Italian dressing, light
13. Egg salad, made with Italian dressing
14. Egg salad, made with light Italian dressing
15. Garlic bread, with parmesan cheese, from fast food / restaurant
16. Garlic bread, with parmesan cheese, from frozen
17. Italian dressing, fat free
18. Italian dressing, light
19. Italian sausage
20. Lasagna with chicken or turkey

... 他 147個
```

### Indian dishes (14個)

```
1. Barfi or Burfi, Indian dessert
2. Beef curry
3. Biryani with chicken
4. Biryani with meat
5. Biryani with vegetables
6. Bread, naan
7. Cheese, paneer
8. Curry sauce
9. Firni, Indian pudding
10. Fish curry
11. Fish curry with rice
12. Lentil curry
13. Lentil curry with rice
14. Samosa
```

### Breakfast items (278個)

```
1. Bacon and tomato dressing
2. Bacon strip, meatless
3. Bacon, for use with vegetables
4. Beef sausage
5. Beef sausage with cheese
6. Beef, bacon, cooked
7. Beef, bacon, reduced sodium, cooked
8. Blood sausage
9. Breakfast bar, NFS
10. Breakfast bar, cereal crust with fruit filling, lowfat
11. Breakfast bar, date, with yogurt coating
12. Breakfast link, pattie, or slice, meatless
13. Breakfast meat as ingredient in omelet
14. Breakfast pastry, NFS
15. Breakfast tart
16. Breakfast tart, lowfat
17. Broccoli salad with cauliflower, cheese, bacon bits, and dressing
18. Canadian bacon, cooked
19. Cereal or Granola bar, NFS
20. Cereal or granola bar (General Mills Fiber One Chewy Bar)

... 他 258個
```

### Salad varieties (79個)

```
1. Apple salad with dressing
2. Bean salad, yellow and/or green string beans
3. Beef salad
4. Black bean salad
5. Broccoli slaw salad
6. Cabbage salad, NFS
7. Carrots, raw, salad
8. Carrots, raw, salad with apples
9. Chicken or turkey garden salad with cheese, chicken and/or turkey, cheese, lettuce and/or greens, tomato and/or carrots, other vegetables, no dressing
10. Chicken or turkey garden salad, chicken and/or turkey, other vegetables excluding tomato and carrots, no dressing
11. Chicken or turkey garden salad, chicken and/or turkey, tomato and/or carrots, other vegetables, no dressing
12. Chicken or turkey salad, made with any type of fat free dressing
13. Chicken or turkey salad, made with creamy dressing
14. Chicken or turkey salad, made with light creamy dressing
15. Chicken or turkey salad, made with light mayonnaise
16. Chicken or turkey salad, made with light mayonnaise-type salad dressing
17. Chicken or turkey, breaded, fried, garden salad with cheese, chicken and/or turkey, cheese, lettuce and/or greens, tomato and/or carrots, other vegetables, no dressing
18. Cobb salad, no dressing
19. Codfish salad, Puerto Rican style, Serenata
20. Egg salad, made with light creamy dressing

... 他 59個
```

### Soups and stews (112個)

```
1. Chicken breast, stewed, skin eaten
2. Chicken drumstick, stewed, skin eaten
3. Chicken drumstick, stewed, skin not eaten
4. Chicken leg, drumstick and thigh, stewed, skin eaten
5. Chicken leg, drumstick and thigh, stewed, skin not eaten
6. Chicken or turkey a la king with vegetables excluding carrorts, broccoli, and dark-green leafy; no potatoes, cream, white, or soup-based sauce
7. Chicken or turkey a la king with vegetables including carrots, broccoli, and/or dark-green leafy; no potatoes, cream, white, or soup-based sauce
8. Chicken thigh, stewed, skin eaten
9. Chicken thigh, stewed, skin not eaten
10. Chicken wing, stewed
11. Chicken, NS as to part, stewed, NS as to skin eaten
12. Chicken, NS as to part, stewed, skin eaten
13. Chicken, NS as to part, stewed, skin not eaten
14. Potato from Puerto Rican beef stew, with gravy
15. Rice with stewed beans, Puerto Rican style
16. Sambar, vegetable stew
17. Soup, French onion
18. Soup, Manhattan clam chowder
19. Soup, Matzo ball
20. Soup, NFS

... 他 92個
```

### Desserts and sweets (394個)

```
1. Apple pie filling
2. Banana pudding
3. Bean cake
4. Bean paste, sweetened
5. Beef with sweet and sour sauce
6. Blueberry pie filling
7. Bread, sweet potato
8. Bread, sweet potato, toasted
9. Cake made with glutinous rice
10. Cake made with glutinous rice and dried beans
11. Cake or cupcake, Black Forest
12. Cake or cupcake, German chocolate
13. Cake or cupcake, NFS
14. Cake or cupcake, apple
15. Cake or cupcake, banana
16. Cake or cupcake, carrot
17. Cake or cupcake, chocolate with chocolate icing, bakery
18. Cake or cupcake, chocolate with chocolate icing, from mix
19. Cake or cupcake, chocolate with white icing, bakery
20. Cake or cupcake, chocolate with white icing, from mix

... 他 374個
```

### Beverages (382個)

```
1. Alcoholic coffee drink
2. Beef steak with onions, Puerto Rican style
3. Beef, steak, T-bone,  lean and fat eaten
4. Beef, steak, T-bone, lean only eaten
5. Beef, steak, chuck
6. Beef, steak, country fried
7. Beef, steak, cube
8. Beef, steak, flank
9. Beef, steak, ribeye, lean and fat eaten
10. Beef, steak, ribeye, lean only eaten
11. Beef, steak, round
12. Beef, steak, sirloin, lean and fat eaten
13. Beef, steak, sirloin, lean only eaten
14. Beef, steak, strip, NS as to fat eaten
15. Beef, steak, strip, lean and fat eaten
16. Beef, steak, strip, lean only eaten
17. Beef, steak, tenderloin
18. Beet juice
19. Blackberry juice, 100%
20. Blueberry juice

... 他 362個
```

### Seafood dishes (69個)

```
1. Biscayne codfish, Puerto Rican style
2. Calamari, cooked
3. Codfish with starchy vegetables, Puerto Rican style
4. Congee, with meat, poultry, and/or seafood, and vegetables
5. Crab, soft shell
6. Crayfish, cooked
7. Fish timbale or mousse
8. Fish, NFS
9. Fish, anchovy
10. Fish, bass, NFS
11. Fish, canned
12. Fish, carp
13. Fish, catfish, NFS
14. Fish, cod, NFS
15. Fish, cooked, as ingredient
16. Fish, croaker
17. Fish, eel
18. Fish, flounder, NFS
19. Fish, haddock, NFS
20. Fish, halibut

... 他 49個
```

### Mixed dishes with meat (43個)

```
1. Beef and vegetables, Hawaiian style
2. Beef shish kabob with vegetables, excluding potatoes
3. Beef stroganoff with noodles
4. Beef with spaetzle or rice, vegetable, frozen meal
5. Beef with vegetable, diet frozen meal
6. Beef, for use with vegetables
7. Beef, ground, with egg and onion
8. Chicken and vegetable entree with noodles, diet frozen meal
9. Chicken and vegetable entree with rice, diet frozen meal
10. Chicken and vegetables au gratin with rice, diet frozen entree
11. Chicken leg, drumstick and thigh, NS as to cooking method, skin eaten
12. Chicken leg, drumstick and thigh, NS as to cooking method, skin not eaten
13. Chicken leg, drumstick and thigh, rotisserie, skin eaten
14. Chicken leg, drumstick and thigh, rotisserie, skin not eaten
15. Chicken leg, drumstick and thigh, sauteed, skin eaten
16. Chicken leg, drumstick and thigh, sauteed, skin not eaten
17. Chicken or turkey creole, without rice
18. Chicken or turkey shish kabob with vegetables, excluding potatoes
19. Chicken or turkey with dumplings
20. Chicken or turkey with stuffing

... 他 23個
```

### Fried foods (83個)

```
1. Bread, dough, fried
2. Calamari, fried
3. Chicken breast, fried, coated, skin / coating eaten, from raw
4. Chicken breast, fried, coated, skin / coating not eaten, from fast food / restaurant
5. Chicken breast, fried, coated, skin / coating not eaten, from pre-cooked
6. Chicken breast, fried, coated, skin / coating not eaten, from raw
7. Chicken drumstick, fried, coated, prepared skinless, coating eaten, from raw
8. Chicken drumstick, fried, coated, skin / coating eaten, from raw
9. Chicken drumstick, fried, coated, skin / coating not eaten, from fast food / restaurant
10. Chicken drumstick, fried, coated, skin / coating not eaten, from pre-cooked
11. Chicken drumstick, fried, coated, skin / coating not eaten, from raw
12. Chicken leg, drumstick and thigh, fried, coated, skin / coating not eaten
13. Chicken thigh, fried, coated, prepared skinless, coating eaten, from raw
14. Chicken thigh, fried, coated, skin / coating eaten, from pre-cooked
15. Chicken thigh, fried, coated, skin / coating eaten, from raw
16. Chicken thigh, fried, coated, skin / coating not eaten, from fast food
17. Chicken thigh, fried, coated, skin / coating not eaten, from pre-cooked
18. Chicken thigh, fried, coated, skin / coating not eaten, from raw
19. Chicken thigh, fried, coated, skin / coating not eaten, from restaurant
20. Chicken wing, fried, coated, from pre-cooked

... 他 63個
```

### Grilled/BBQ (50個)

```
1. Cashews, honey roasted
2. Cashews, unroasted
3. Chicken breast, baked, broiled, or roasted, skin eaten, from raw
4. Chicken drumstick, baked, broiled, or roasted, skin not eaten, from raw
5. Chicken fillet, grilled
6. Chicken thigh, baked, broiled, or roasted, skin not eaten, from raw
7. Chicken, NS as to part, baked, broiled, or roasted, NS as to skin eaten
8. Chicken, NS as to part, baked, broiled, or roasted, skin eaten
9. Chicken, NS as to part, baked, broiled, or roasted, skin not eaten
10. Chicken, chicken roll, roasted
11. Cornish game hen, roasted, skin eaten
12. Cornish game hen, roasted, skin not eaten
13. Duck, roasted, skin eaten
14. Duck, roasted, skin not eaten
15. Fish, bass, grilled
16. Fish, catfish, grilled
17. Fish, cod, grilled
18. Fish, flounder, grilled
19. Fish, haddock, grilled
20. Fish, mackerel, grilled

... 他 30個
```

### Sauces and condiments (422個)

```
1. Barbecue beef, no sauce
2. Barbecue pork, no sauce
3. Barbecue sauce
4. Bean dip, made with refried beans
5. Beef and macaroni with cheese sauce
6. Beef and potatoes with cheese sauce
7. Beef and potatoes with cream sauce, white sauce or mushroom sauce
8. Beef and potatoes, no sauce
9. Beef and rice with cheese sauce
10. Beef and rice with cream sauce
11. Beef and vegetables excluding carrots, broccoli, and dark-green leafy; no potatoes, gravy
12. Beef and vegetables excluding carrots, broccoli, and dark-green leafy; no potatoes, no sauce
13. Beef and vegetables excluding carrots, broccoli, and dark-green leafy; no potatoes, soy-based sauce
14. Beef and vegetables including carrots, broccoli, and/or dark-green leafy; no potatoes, gravy
15. Beef and vegetables including carrots, broccoli, and/or dark-green leafy; no potatoes, no sauce
16. Beef and vegetables including carrots, broccoli, and/or dark-green leafy; no potatoes, soy-based sauce
17. Beef rolls, stuffed with vegetables or meat mixture, tomato-based sauce
18. Beef with cream or white sauce
19. Beef with gravy
20. Beef with mushroom sauce

... 他 402個
```

### Snacks (148個)

```
1. Bagel chips
2. Bagel, wheat, with fruit and nuts
3. Bean chips
4. Brazil nuts
5. Bread, reduced calorie and/or high fiber, white or NFS, with fruit and/or nuts
6. Bread, reduced calorie and/or high fiber, white or NFS, with fruit and/or nuts, toasted
7. Cheese flavored corn snacks
8. Cheese flavored corn snacks (Cheetos)
9. Cheese flavored corn snacks, reduced fat
10. Chestnuts
11. Chips, rice
12. Corn nuts
13. Crackers, Cuban
14. Crackers, NFS
15. Crackers, butter (Ritz)
16. Crackers, butter, flavored
17. Crackers, butter, plain
18. Crackers, butter, reduced fat
19. Crackers, butter, reduced sodium
20. Crackers, cheese

... 他 128個
```

### Restaurant brands (11個)

```
1. Big Mac (McDonalds)
2. Cheeseburger (Burger King)
3. Cheeseburger (McDonalds)
4. Chipotle dip, light
5. Chipotle dip, regular
6. Chipotle dip, yogurt based
7. Hamburger (Burger King)
8. Hamburger (McDonalds)
9. McDouble (McDonalds)
10. Quarter Pounder (McDonalds)
11. Quarter Pounder with cheese (McDonalds)
```

### Other foods (1100個)

```
1. Almond chicken
2. Almond paste
3. Ambrosia
4. Animal fat or drippings
5. Anisette toast
6. Armadillo
7. Asparagus, canned, cooked with butter or margarine
8. Asparagus, canned, cooked with oil
9. Asparagus, canned, cooked, fat added, NS as to fat type
10. Asparagus, fresh, cooked with butter or margarine
11. Asparagus, fresh, cooked with oil
12. Asparagus, fresh, cooked, fat added, NS as to fat type
13. Asparagus, frozen, cooked with butter or margarine
14. Asparagus, frozen, cooked with oil
15. Asparagus, frozen, cooked, fat added, NS as to fat type
16. Bacalaitos fritos
17. Bagel, multigrain, with raisins
18. Bagel, pumpernickel
19. Bagel, wheat
20. Bagel, wheat bran

... 他 1080個
```


## 📋 生成ガイドライン

### 必須フィールド
- `display_name`: ユーザー表示用の自然な名称
- `category`: 既存カテゴリから選択
- `spec2_rule`: "統合（汎化）"、"維持"、"分離"のいずれか
- `spec2_reason`: 判断理由を簡潔に
- `default_usda`: 最も代表的なUSDA名
- `all_usda_mappings`: 全ての関連USDA名をリスト化
- `aliases`: 検索用の別名
- `visual_hints`: 画像認識の手がかり

### オプションフィールド
- `is_new_mapping`: true（新規マッピング）
- `nutritional_variance`: "low"/"medium"/"high"
- `common_additions`: よくあるトッピング/追加食材
- `cultural_cuisine`: 料理の文化圏
- `preparation_method`: 主な調理法

### 生成のコツ
1. **1つのキーに多くのバリエーションをまとめる**
   - 視覚的に似ているものは積極統合
   - all_usda_mappingsを充実させる

2. **実用性を重視**
   - レストランメニューでよく見るものを優先
   - 家庭料理の定番を押さえる

3. **画像認識を意識**
   - visual_hintsは具体的に
   - 色、形、質感、盛り付けを記述

4. **栄養価の違いを考慮**
   - 大きく異なる場合は分離も検討
   - nutritional_varianceで示す

## 📦 期待する出力

1. **JSONマッピング**: 上記形式で50-100個程度の新規マッピング
2. **除外リスト**: マッピング不要と判断した食品とその理由
3. **統合提案**: 既存マッピングと統合可能な項目があれば提案

優先的に以下をマッピング:
- Meat loaf全バリエーション
- Caesar salad全バリエーション
- 主要なpizza種類（dessert pizza除く）
- 一般的なsandwich類
- 代表的なethnic dishes
- 頻出するmixed dishes

生成開始してください。
