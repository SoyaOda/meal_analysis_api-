# USDA食品マッピング生成プロンプト v2.0

## 🎯 命令

以下の未マップUSDA食品に対して、実用的なマッピングを生成してください。

### 重要な前提条件
1. **用途**: AIが画像から食品を識別 → 栄養データベースと照合 → 栄養価計算
2. **優先順位**:
   - 視覚的に識別可能で頻出する食品を優先
   - 特殊な調理法や細かいバリエーションは統合
   - ブランド固有の商品は除外またはgeneric版に統合

## 📋 マッピング生成方針（改良版）

### 1. 統合の原則
- **視覚的類似性**: 写真で区別困難なものは統合
- **栄養的類似性**: 栄養価が近似するものは統合
- **実用性**: 一般的な食事シーンで頻出するものを優先

### 2. カテゴリ別の処理方針

#### Beverages（飲料）
- アルコール度数の違いは統合（例: beer → Beer）
- フレーバーの違いは基本統合（例: flavored water → Water）
- 主要な果汁飲料は独立維持（Orange juice, Apple juice等）

#### Restaurant/Fast Food
- ブランド名を除去して汎用化（例: "McDonald's burger" → "Hamburger"）
- 主要チェーン固有のメニューは除外または最も近い汎用カテゴリに統合

#### Ethnic Dishes（各国料理）
- 代表的な料理は独立カテゴリ（例: Pad Thai, Tandoori chicken）
- 細かいバリエーションは統合（例: various curry types → "Curry"）
- 視覚的に特徴的な料理を優先

#### Mixed Dishes（複合料理）
- 主材料で分類（例: "Beef and rice" → beef_dishesカテゴリ）
- ソースの違いは基本統合（with gravy/with sauce → 統一）
- "NFS"や"NS as to"表記は除去

#### Desserts
- 主要なデザートタイプごとに分類
- フレーバーバリエーションは限定的に（chocolate, vanilla程度）
- トッピングの有無は統合

### 3. 除外基準
以下は**マッピング不要**:
- Baby/Toddler food全般
- 学校給食専用メニュー（School lunch specific）
- WIC/USDA commodity foods
- 栄養補助食品（Supplement drinks等）
- 極めて特殊な地域料理

### 4. 命名規則
- NFSやNS表記を削除
- 調理法は主要なもののみ（fried, grilled, baked）
- 括弧内の詳細は基本削除
- display_nameは自然な英語表記

## 📝 マッピング例（改良版）

```json
{
  "meat_loaf": {
    "display_name": "Meat loaf",
    "category": "meat_dishes",
    "spec2_rule": "統合（汎化）",
    "spec2_reason": "牛肉・豚肉等の違いは視覚的に判別困難",
    "default_usda": {
      "name": "Meat loaf made with beef",
      "database": "survey_fndds",
      "reason": "最も一般的な牛肉ベースのミートローフ"
    },
    "all_usda_mappings": [
      {
        "name": "Meat loaf made with beef",
        "database": "survey_fndds",
        "specificity": "specific"
      },
      {
        "name": "Meat loaf made with beef and pork",
        "database": "survey_fndds",
        "specificity": "specific"
      },
      {
        "name": "Meat loaf made with beef, veal and pork",
        "database": "survey_fndds",
        "specificity": "specific"
      },
      {
        "name": "Meat loaf dinner, NFS, frozen meal",
        "database": "survey_fndds",
        "specificity": "generic"
      }
    ],
    "aliases": ["meatloaf", "meat loaf", "ground meat loaf"],
    "visual_hints": ["loaf shaped", "brown", "sliced", "ground meat texture"]
  },

  "caesar_salad": {
    "display_name": "Caesar salad",
    "category": "salads",
    "spec2_rule": "統合（汎化）",
    "spec2_reason": "ドレッシングの有無やトッピングの違いを統合",
    "default_usda": {
      "name": "Caesar salad, with romaine, no dressing",
      "database": "survey_fndds",
      "reason": "基本的なシーザーサラダ（ドレッシング別添え想定）"
    },
    "all_usda_mappings": [
      {
        "name": "Caesar salad, with romaine, no dressing",
        "database": "survey_fndds",
        "specificity": "generic"
      },
      {
        "name": "Chicken or turkey caesar garden salad, chicken and/or turkey, lettuce, tomato, cheese, no dressing",
        "database": "survey_fndds",
        "specificity": "specific"
      }
    ],
    "aliases": ["caesar", "caesar salad", "chicken caesar"],
    "visual_hints": ["romaine lettuce", "parmesan", "croutons", "creamy dressing"]
  },

  "french_fries": {
    "display_name": "French fries",
    "category": "potato_dishes",
    "spec2_rule": "統合（汎化）",
    "spec2_reason": "調理法や味付けの違いは視覚的に判別困難",
    "default_usda": {
      "name": "French fries, from fresh, deep fried",
      "database": "survey_fndds",
      "reason": "最も一般的なフライドポテト"
    },
    "all_usda_mappings": [
      {
        "name": "French fries, from fresh, deep fried",
        "database": "survey_fndds",
        "specificity": "generic"
      },
      {
        "name": "French fries, from frozen, deep fried",
        "database": "survey_fndds",
        "specificity": "specific"
      },
      {
        "name": "French fries, from frozen, oven baked",
        "database": "survey_fndds",
        "specificity": "specific"
      },
      {
        "name": "French fries, seasoned",
        "database": "survey_fndds",
        "specificity": "specific"
      }
    ],
    "aliases": ["fries", "french fries", "potato fries", "chips"],
    "visual_hints": ["golden", "crispy", "stick shaped", "fried potato"]
  }
}
```

## 🎯 生成対象食品リスト

以下のカテゴリの食品についてマッピングを生成してください：


### Beverages
```
Alcoholic coffee drink
Beef, steak, T-bone,  lean and fat eaten
Beef, steak, T-bone, lean only eaten
Beef, steak, chuck
Beef, steak, country fried
Beef, steak, cube
Beef, steak, flank
Beef, steak, ribeye, lean and fat eaten
Beef, steak, ribeye, lean only eaten
Beef, steak, round
```

### Breakfast
```
Breakfast bar, NFS
Breakfast bar, cereal crust with fruit filling, lowfat
Breakfast bar, date, with yogurt coating
Breakfast link, pattie, or slice, meatless
Breakfast meat as ingredient in omelet
Breakfast pastry, NFS
Breakfast pizza with egg
Breakfast tart
Breakfast tart, lowfat
Cereal or Granola bar, NFS
```

### Condiments
```
Bacon and tomato dressing
Barbecue beef, no sauce
Barbecue pork, no sauce
Barbecue sauce
Beef and macaroni with cheese sauce
Beef and potatoes with cheese sauce
Beef and potatoes with cream sauce, white sauce or mushroom sauce
Beef and potatoes, no sauce
Beef and rice with cheese sauce
Beef and rice with cream sauce
```

### Desserts
```
Apple pie filling
Banana pudding
Bean cake
Blueberry pie filling
Cake made with glutinous rice
Cake made with glutinous rice and dried beans
Cake or cupcake, Black Forest
Cake or cupcake, German chocolate
Cake or cupcake, NFS
Cake or cupcake, apple
```

### Ethnic dishes
```
Barfi or Burfi, Indian dessert
Beef steak with onions, Puerto Rican style
Bibimbap, Korean
Biscayne codfish, Puerto Rican style
Bread, Italian, Grecian, Armenian
Bread, Italian, Grecian, Armenian, toasted
Bread, Spanish coffee
Bread, lard, Puerto Rican style
Bread, lard, toasted, Puerto Rican style
Bread, native, water, Puerto Rican style
```

### Mixed dishes
```
Apple salad with dressing
Asian chicken or turkey garden salad with crispy noodles, chicken and/or turkey, lettuce, fruit, nuts, crispy noodles, no dressing
Asian chicken or turkey garden salad, chicken and/or turkey, lettuce, fruit, nuts, no dressing
Bean salad, yellow and/or green string beans
Beef salad
Black bean salad
Broccoli casserole with noodles
Broccoli casserole with rice
Broccoli salad with cauliflower, cheese, bacon bits, and dressing
Broccoli slaw salad
```

### NFS/NS
```
Asparagus, canned, cooked, fat added, NS as to fat type
Asparagus, fresh, cooked, fat added, NS as to fat type
Asparagus, frozen, cooked, fat added, NS as to fat type
Beans with meat, NS as to type
Beans, NFS
Beans, from canned, NS as to type, fat added
Beans, from canned, NS as to type, no added fat
Beans, from dried, NS as to type, fat added
Beans, from dried, NS as to type, no added fat
Beans, from fast food / restaurant, NS as to type
```

### Other
```
Almond chicken
Almond paste
Ambrosia
Animal fat or drippings
Anisette toast
Armadillo
Asparagus, canned, cooked with oil
Asparagus, fresh, cooked with oil
Asparagus, frozen, cooked with oil
Bacalaitos fritos
```

### Restaurant/Brand
```
Big Mac (McDonalds)
Cheeseburger (Burger King)
Cheeseburger (McDonalds)
Chipotle dip, light
Chipotle dip, regular
Chipotle dip, yogurt based
Hamburger (Burger King)
Hamburger (McDonalds)
McDouble (McDonalds)
Quarter Pounder (McDonalds)
```

### School/Institutional
```
Bacon biscuit sandwich
Bacon, for use on a sandwich
Bacon, lettuce, tomato sandwich on wheat
Bacon, lettuce, tomato sandwich on white
Barbecue beef sandwich, on wheat bun
Barbecue beef sandwich, on white bun
Barbecue chicken sandwich, on wheat bun
Barbecue chicken sandwich, on white bun
Barbecue pork sandwich, on wheat bun
Barbecue pork sandwich, on white bun
```

### Snacks
```
Bagel chips
Bagel, wheat, with fruit and nuts
Bean chips
Brazil nuts
Bread, reduced calorie and/or high fiber, white or NFS, with fruit and/or nuts
Bread, reduced calorie and/or high fiber, white or NFS, with fruit and/or nuts, toasted
Chestnuts
Chips, rice
Corn nuts
Crackers, Cuban
```

### Specific preparations
```
Bean dip, made with refried beans
Bread, dough, fried
Calamari, fried
Cashews, honey roasted
Cashews, unroasted
Chicken breast, baked or broiled, skin eaten, from fast food / restaurant
Chicken breast, baked or broiled, skin eaten, from pre-cooked
Chicken breast, baked or broiled, skin not eaten, from fast food / restaurant
Chicken breast, baked or broiled, skin not eaten, from pre-cooked
Chicken breast, baked, broiled, or roasted with marinade, skin eaten, from raw
```

### With additions
```
Asparagus, canned, cooked with butter or margarine
Asparagus, fresh, cooked with butter or margarine
Asparagus, frozen, cooked with butter or margarine
Beef sausage with cheese
Beef with gravy
Beef, sliced, with gravy, potatoes, vegetable, frozen meal
Biscuit with gravy
Bratwurst, with cheese
Broccoli, fresh, cooked with butter or margarine
Broccoli, frozen, cooked with butter or margarine
```


## 📌 生成時の注意事項

1. **全ての食品を無理にマッピングしない**
   - 特殊すぎる項目は除外してOK
   - 実用性の低い項目はスキップ

2. **統合を積極的に**
   - 似た食品は1つのキーにまとめる
   - all_usda_mappingsに複数のバリエーションを含める

3. **カテゴリの適切な設定**
   - 既存カテゴリを参考に
   - 新規カテゴリは慎重に

4. **視覚的特徴を重視**
   - visual_hintsは具体的に
   - 写真で識別可能な特徴を列挙

5. **データベース指定**
   - 基本は "survey_fndds"
   - Foundation Foodは特別な場合のみ

生成形式：
- JSON形式で出力
- インデント：2スペース
- 日本語コメント可

マッピング不要と判断した食品は、理由とともに別途リストアップしてください。
