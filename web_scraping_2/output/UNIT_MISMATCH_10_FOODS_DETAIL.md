# 🔍 単位不一致10食材の詳細レポート

タイトル行の単位と栄養情報の単位が異なる10食材の詳細情報です。

---

## 📊 サマリー

| # | 食材名 | カテゴリ | タイトル単位 | 栄養情報単位 |
|---|--------|---------|------------|------------|
| 1 | Gimlet cocktail | Beverages | serving | fl oz |
| 2 | Ice cubes | Beverages | cube | cup |
| 3 | Reduced fat mayonnaise with olive oil by great value | Condiments, Dressings & Sauces | tbsp | ml |
| 4 | Vinegar cider | Condiments, Dressings & Sauces | cup | tbsp |
| 5 | Almond yogurt plain | Dairy, Dairy Substitutes & Egg | oz | container |
| 6 | Safflower oil high linoleic content over 70% | Fats & Oils | cup | tbsp |
| 7 | Vegetable cooking spray oil, sprays | Fats & Oils | about 1/3 second each spray | spray, about 1/3 second each spray |
| 8 | Sea salt non-iodized | Spices & Herbs | tsp | tbsp |
| 9 | Chicken broth reduced sodium canned | Stocks and Gravy | cup | tbsp |
| 10 | Olives kalamata pitted | Vegetables - canned, dried, or juice | olives | 4 olives |

---

## 1. Gimlet cocktail

**カテゴリ**: Beverages

**ファイル**: `beverages_manual_input.txt`

**番号**: 23

### 📝 タイトル行

```
23. Gimlet cocktail, serving
174cals
```

**タイトル行の解析**:

- **食材名**: `Gimlet cocktail`
- **デフォルト単位**: `serving`
- **デフォルトカロリー**: `174cals`

### 🍽️ Serving情報

```
Select Serving
fl oz 64cals / 27.8 g
ml 2cals / 0.9 g
jigger 1.5 fl oz 97cals / 42 g
gram 2cals / 1 g
oz 65cals / 28.3 g
cup 514cals / 222.4 g
tablespoon 32cals / 13.9 g
teaspoon 11cals / 4.6 g
lb 1,048cals / 453.6 g
```

### 📊 栄養情報

```
Serving Size: fl oz (28g)
Calories: 64
```

**栄養情報の解析**:

- **Serving Size単位**: `fl oz`
- **カロリー**: `64cals`

### ⚠️ 問題点

**タイトル単位 `serving` と 栄養情報単位 `fl oz` が不一致**

### 💡 推奨対処

- 栄養情報の `fl oz` を正しい単位として採用
- タイトル行を `Gimlet cocktail, fl oz` に修正

---

## 2. Ice cubes

**カテゴリ**: Beverages

**ファイル**: `beverages_manual_input.txt`

**番号**: 28

### 📝 タイトル行

```
28. Ice cubes, cube
0cals
```

**タイトル行の解析**:

- **食材名**: `Ice cubes`
- **デフォルト単位**: `cube`
- **デフォルトカロリー**: `0cals`

### 🍽️ Serving情報

```
Select Serving
cube 0cals / 28 g
gram 0cals / 1 g
oz 0cals / 28.3 g
cup 0cals / 136 g
ml 0cals / 0.6 g
fl oz 0cals / 17 g
teaspoon 0cals / 2.8 g
tablespoon 0cals / 8.5 g
lb 0cals / 453.6 g
```

### 📊 栄養情報

```
```

**栄養情報の解析**:

- **Serving Size単位**: `cup`

### ⚠️ 問題点

**タイトル単位 `cube` と 栄養情報単位 `cup` が不一致**

### 💡 推奨対処

- 栄養情報の `cup` を正しい単位として採用
- タイトル行を `Ice cubes, cup` に修正

---

## 3. Reduced fat mayonnaise with olive oil by great value

**カテゴリ**: Condiments, Dressings & Sauces

**ファイル**: `condiments_dressings_and_sauces_manual_input.txt`

**番号**: 36

### 📝 タイトル行

```
36. Reduced fat mayonnaise with olive oil by great value, tbsp
60cals
```

**タイトル行の解析**:

- **食材名**: `Reduced fat mayonnaise with olive oil by great value`
- **デフォルト単位**: `tbsp`
- **デフォルトカロリー**: `60cals`

### 🍽️ Serving情報

```
Select Serving
tbsp 60cals / 15 g
teaspoon 20cals / 5 g
gram 4cals / 1 g
oz 113cals / 28.3 g
cup 928cals / 232 g
ml 4cals / 1 g
fl oz 120cals / 30 g
lb 1,814cals / 453.6 g


【栄養情報Nutrition Facts	grade
B-
Serving Size	tbsp (15g)
Amount per serving
Calories	60cals
% Daily Value*
Total Fat 6g	9%
Saturated Fat 1g	5%
Trans Fat 0g	
Monounsaturated Fat 2g	
Polyunsaturated Fat 3g	
Total Carbs 1g	0%
Net Carbs 1g	
Dietary Fiber 0g	0%
Total Sugars 0g	
Added Sugars 0g	0%
Protein 0g	0%
Cholesterol 5mg	2%
Sod
...
```

### 📊 栄養情報

```
Serving Size: ml (1g)
Calories: 0
```

**栄養情報の解析**:

- **Serving Size単位**: `ml`
- **カロリー**: `0cals`

### ⚠️ 問題点

**タイトル単位 `tbsp` と 栄養情報単位 `ml` が不一致**

### 💡 推奨対処

- 栄養情報の `ml` を正しい単位として採用
- タイトル行を `Reduced fat mayonnaise with olive oil by great value, ml` に修正

---

## 4. Vinegar cider

**カテゴリ**: Condiments, Dressings & Sauces

**ファイル**: `condiments_dressings_and_sauces_manual_input.txt`

**番号**: 71

### 📝 タイトル行

```
71. Vinegar cider, cup
50cals
```

**タイトル行の解析**:

- **食材名**: `Vinegar cider`
- **デフォルト単位**: `cup`
- **デフォルトカロリー**: `50cals`

### 🍽️ Serving情報

```
Select Serving
tbsp 50cals / 14 g
teaspoon 17cals / 4.7 g
gram 4cals / 1 g
oz 101cals / 28.3 g
ml 3cals / 0.9 g
fl oz 100cals / 28 g
cup 800cals / 224 g
lb 1,620cals / 453.6 g
```

### 📊 栄養情報

```
Serving Size: tbsp (14g)
Calories: 50
```

**栄養情報の解析**:

- **Serving Size単位**: `tbsp`
- **カロリー**: `50cals`

### ⚠️ 問題点

**タイトル単位 `cup` と 栄養情報単位 `tbsp` が不一致**

### 💡 推奨対処

- 栄養情報の `tbsp` を正しい単位として採用
- タイトル行を `Vinegar cider, tbsp` に修正

---

## 5. Almond yogurt plain

**カテゴリ**: Dairy, Dairy Substitutes & Egg

**ファイル**: `dairy_dairy_substitutes_and_egg_manual_input.txt`

**番号**: 2

### 📝 タイトル行

```
2. Almond yogurt plain, oz
26cals
```

**タイトル行の解析**:

- **食材名**: `Almond yogurt plain`
- **デフォルト単位**: `oz`
- **デフォルトカロリー**: `26cals`

### 🍽️ Serving情報

```
Select Serving
container 140cals / 150 g
gram 1cals / 1 g
oz 26cals / 28.3 g
lb 423cals / 453.6 g
```

### 📊 栄養情報

```
Serving Size: container (150g)
Calories: 140
```

**栄養情報の解析**:

- **Serving Size単位**: `container`
- **カロリー**: `140cals`

### ⚠️ 問題点

**タイトル単位 `oz` と 栄養情報単位 `container` が不一致**

### 💡 推奨対処

- マニュアルで確認して正しい単位を選択

---

## 6. Safflower oil high linoleic content over 70%

**カテゴリ**: Fats & Oils

**ファイル**: `fats_and_oils_manual_input.txt`

**番号**: 20

### 📝 タイトル行

```
20. Safflower oil high linoleic content over 70%, cup
1,927cals
```

**タイトル行の解析**:

- **食材名**: `Safflower oil high linoleic content over 70%`
- **デフォルト単位**: `cup`
- **デフォルトカロリー**: `1,927cals`

### 🍽️ Serving情報

```
Select Serving
tbsp 124cals / 14 g
tsp 40cals / 4.5 g
gram 9cals / 1 g
ml 8cals / 0.9 g
cup 1,927cals / 218 g
oz 251cals / 28.3 g
fl oz 248cals / 28 g
lb 4,010cals / 453.6 g
```

### 📊 栄養情報

```
Serving Size: tbsp (14g)
Calories: 124
```

**栄養情報の解析**:

- **Serving Size単位**: `tbsp`
- **カロリー**: `124cals`

### ⚠️ 問題点

**タイトル単位 `cup` と 栄養情報単位 `tbsp` が不一致**

### 💡 推奨対処

- 栄養情報の `tbsp` を正しい単位として採用
- タイトル行を `Safflower oil high linoleic content over 70%, tbsp` に修正

---

## 7. Vegetable cooking spray oil, sprays

**カテゴリ**: Fats & Oils

**ファイル**: `fats_and_oils_manual_input.txt`

**番号**: 26

### 📝 タイトル行

```
26. Vegetable cooking spray oil, sprays, about 1/3 second each spray
2cals
```

**タイトル行の解析**:

- **食材名**: `Vegetable cooking spray oil, sprays`
- **デフォルト単位**: `about 1/3 second each spray`
- **デフォルトカロリー**: `2cals`

### 🍽️ Serving情報

```
Select Serving
sprays, about 1/3 second each spray 2cals / 0.3 g
gram 8cals / 1 g
oz 225cals / 28.3 g
lb 3,592cals / 453.6 g
```

### 📊 栄養情報

```
Serving Size: spray, about 1/3 second each spray (0g)
Calories: 2
```

**栄養情報の解析**:

- **Serving Size単位**: `spray, about 1/3 second each spray`
- **カロリー**: `2cals`

### ⚠️ 問題点

**タイトル単位 `about 1/3 second each spray` と 栄養情報単位 `spray, about 1/3 second each spray` が不一致**

### 💡 推奨対処

- タイトル行の単位フォーマットを栄養情報に合わせる
- `spray, about 1/3 second each spray` に統一

---

## 8. Sea salt non-iodized

**カテゴリ**: Spices & Herbs

**ファイル**: `spices_and_herbs_manual_input.txt`

**番号**: 61

### 📝 タイトル行

```
61. Sea salt non-iodized, tsp
0cals
```

**タイトル行の解析**:

- **食材名**: `Sea salt non-iodized`
- **デフォルト単位**: `tsp`
- **デフォルトカロリー**: `0cals`

### 🍽️ Serving情報

```
Select Serving
0.25 tsp 0cals / 1.5 g
dash 0cals / 0.4 g
gram 0cals / 1 g
oz 0cals / 28.3 g
tablespoon 0cals / 18 g
ml 0cals / 1.2 g
cup 0cals / 288 g
fl oz 0cals / 36 g
lb 0cals / 453.6 g
```

### 📊 栄養情報

```
```

**栄養情報の解析**:

- **Serving Size単位**: `tbsp`

### ⚠️ 問題点

**タイトル単位 `tsp` と 栄養情報単位 `tbsp` が不一致**

### 💡 推奨対処

- 栄養情報の `tbsp` を正しい単位として採用
- タイトル行を `Sea salt non-iodized, tbsp` に修正

---

## 9. Chicken broth reduced sodium canned

**カテゴリ**: Stocks and Gravy

**ファイル**: `stocks_and_gravy_manual_input.txt`

**番号**: 14

### 📝 タイトル行

```
14. Chicken broth reduced sodium canned, cup
17cals
```

**タイトル行の解析**:

- **食材名**: `Chicken broth reduced sodium canned`
- **デフォルト単位**: `cup`
- **デフォルトカロリー**: `17cals`

### 🍽️ Serving情報

```
Select Serving
tsp 6cals / 2.3 g
gram 2cals / 1 g
tbsp 17cals / 6.8 g
ml 1cals / 0.5 g
oz 70cals / 28.3 g
fl oz 34cals / 13.6 g
cup 269cals / 108.8 g
lb 1,120cals / 453.6 g
```

### 📊 栄養情報

```
Serving Size: tbsp (7g)
Calories: 17
```

**栄養情報の解析**:

- **Serving Size単位**: `tbsp`
- **カロリー**: `17cals`

### ⚠️ 問題点

**タイトル単位 `cup` と 栄養情報単位 `tbsp` が不一致**

### 💡 推奨対処

- 栄養情報の `tbsp` を正しい単位として採用
- タイトル行を `Chicken broth reduced sodium canned, tbsp` に修正

---

## 10. Olives kalamata pitted

**カテゴリ**: Vegetables - canned, dried, or juice

**ファイル**: `vegetables_-_canned_dried_or_juice_manual_input.txt`

**番号**: 11

### 📝 タイトル行

```
11. Olives kalamata pitted, olives
9cals
```

**タイトル行の解析**:

- **食材名**: `Olives kalamata pitted`
- **デフォルト単位**: `olives`
- **デフォルトカロリー**: `9cals`

### 🍽️ Serving情報

```
Select Serving
4 olives 35cals / 15 g
gram 2cals / 1 g
oz 66cals / 28.3 g
lb 1,058cals / 453.6 g
```

### 📊 栄養情報

```
Serving Size: 4 olives (15g)
Calories: 35
```

**栄養情報の解析**:

- **Serving Size単位**: `4 olives`
- **カロリー**: `35cals`

### ⚠️ 問題点

**タイトル単位 `olives` と 栄養情報単位 `4 olives` が不一致**

### 💡 推奨対処

- マニュアルで確認して正しい単位を選択

---

## 📈 カテゴリ別分析

### Beverages (2件)

| 食材名 | タイトル単位 | 栄養情報単位 |
|--------|------------|------------|
| Gimlet cocktail | serving | fl oz |
| Ice cubes | cube | cup |

### Condiments, Dressings & Sauces (2件)

| 食材名 | タイトル単位 | 栄養情報単位 |
|--------|------------|------------|
| Reduced fat mayonnaise with olive oil by great value | tbsp | ml |
| Vinegar cider | cup | tbsp |

### Dairy, Dairy Substitutes & Egg (1件)

| 食材名 | タイトル単位 | 栄養情報単位 |
|--------|------------|------------|
| Almond yogurt plain | oz | container |

### Fats & Oils (2件)

| 食材名 | タイトル単位 | 栄養情報単位 |
|--------|------------|------------|
| Safflower oil high linoleic content over 70% | cup | tbsp |
| Vegetable cooking spray oil, sprays | about 1/3 second each spray | spray, about 1/3 second each spray |

### Spices & Herbs (1件)

| 食材名 | タイトル単位 | 栄養情報単位 |
|--------|------------|------------|
| Sea salt non-iodized | tsp | tbsp |

### Stocks and Gravy (1件)

| 食材名 | タイトル単位 | 栄養情報単位 |
|--------|------------|------------|
| Chicken broth reduced sodium canned | cup | tbsp |

### Vegetables - canned, dried, or juice (1件)

| 食材名 | タイトル単位 | 栄養情報単位 |
|--------|------------|------------|
| Olives kalamata pitted | olives | 4 olives |

---

## 🔍 問題パターン分析

### 容量単位の違い (大→小)

- Vinegar cider
- Safflower oil high linoleic content over 70%
- Chicken broth reduced sodium canned

### 容量単位の違い (小→大)

- Sea salt non-iodized

### 数量表現の違い

- Olives kalamata pitted

### 単位系の違い

- Reduced fat mayonnaise with olive oil by great value

### 表記形式の違い

- Gimlet cocktail
- Ice cubes
- Almond yogurt plain
- Vegetable cooking spray oil, sprays

---

## ✅ 推奨アクション

### 即座に修正すべき食材

以下の食材はタイトル行の単位を栄養情報に合わせて修正することを推奨:

| 食材名 | 現在のタイトル単位 | 修正後の単位 |
|--------|------------------|------------|
| Gimlet cocktail | serving | fl oz |
| Ice cubes | cube | cup |
| Reduced fat mayonnaise with olive oil by great value | tbsp | ml |
| Vinegar cider | cup | tbsp |
| Almond yogurt plain | oz | container |
| Safflower oil high linoleic content over 70% | cup | tbsp |
| Sea salt non-iodized | tsp | tbsp |
| Chicken broth reduced sodium canned | cup | tbsp |
