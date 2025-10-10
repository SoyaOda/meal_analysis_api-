# 🔍 デフォルト単位・カロリー不一致食材レポート

Manual Templatesのデフォルト単位とカロリーが【Serving情報】と不一致な186件の詳細レポートです。

---

## 📊 サマリー

| 不一致タイプ | 件数 | 説明 |
|------------|------|------|
| カロリー不一致 | 4件 | デフォルト単位はServing情報に存在するが、カロリーが異なる |
| 単位が見つからない | 181件 | デフォルト単位がServing情報に完全一致しない |
| セクション不明 | 1件 | Serving情報セクションが見つからない |
| **合計** | **186件** | |

---

## 1️⃣ カロリー不一致（4件）

デフォルト単位はServing情報に存在するが、カロリーが異なる食材です。

### 1. Chicken thigh meat and skin raw (yield from 1 lb ready-to-cook chicken)

**カテゴリ**: Poultry

**ファイル**: `poultry_manual_input.txt`

**番号**: 11

**タイトル行**:
- `Chicken thigh meat and skin raw, thigh, bone removed (yield from 1 lb ready-to-cook chicken)`
- `126cals`

**デフォルト情報**:
- 単位: `thigh, bone removed`
- カロリー: `126cals`

**Serving情報の該当行**:
- `thigh, bone removed 208cals / 94 g`
- カロリー: `208cals`

**問題**:
- デフォルトカロリー（`126cals`）とServing情報のカロリー（`208cals`）が不一致

**全Serving情報**:
```
gram 2cals / 1 g
thigh, bone removed 208cals / 94 g
oz 63cals / 28.3 g
thigh, bone removed (yield from 1 lb ready-to-cook chicken) 126cals / 57 g
```

---

### 2. Chicken thigh meat only raw (yield from 1 lb ready-to-cook chicken)

**カテゴリ**: Poultry

**ファイル**: `poultry_manual_input.txt`

**番号**: 12

**タイトル行**:
- `Chicken thigh meat only raw, thigh, bone and skin removed (yield from 1 lb ready-to-cook chicken)`
- `50cals`

**デフォルト情報**:
- 単位: `thigh, bone and skin removed`
- カロリー: `50cals`

**Serving情報の該当行**:
- `thigh, bone and skin removed 83cals / 69 g`
- カロリー: `83cals`

**問題**:
- デフォルトカロリー（`50cals`）とServing情報のカロリー（`83cals`）が不一致

**全Serving情報**:
```
gram 1cals / 1 g
oz 34cals / 28.3 g
thigh, bone and skin removed 83cals / 69 g
thigh, bone and skin removed (yield from 1 lb ready-to-cook chicken) 50cals / 41 g
```

---

### 3. Chicken wing meat and skin raw (yield from 1 lb ready-to-cook chicken)

**カテゴリ**: Poultry

**ファイル**: `poultry_manual_input.txt`

**番号**: 14

**タイトル行**:
- `Chicken wing meat and skin raw, wing, bone removed (yield from 1 lb ready-to-cook chicken)`
- `55cals`

**デフォルト情報**:
- 単位: `wing, bone removed`
- カロリー: `55cals`

**Serving情報の該当行**:
- `wing, bone removed 94cals / 49 g`
- カロリー: `94cals`

**問題**:
- デフォルトカロリー（`55cals`）とServing情報のカロリー（`94cals`）が不一致

**全Serving情報**:
```
wing, bone removed 94cals / 49 g
gram 2cals / 1 g
wing, bone removed (yield from 1 lb ready-to-cook chicken) 55cals / 29 g
oz 54cals / 28.3 g
```

---

### 4. Chicken broth or bouillon dry powder (8 fl oz)

**カテゴリ**: Stocks and Gravy

**ファイル**: `stocks_and_gravy_manual_input.txt`

**番号**: 11

**タイトル行**:
- `Chicken broth or bouillon dry powder, cup (8 fl oz)`
- `21cals`

**デフォルト情報**:
- 単位: `cup`
- カロリー: `21cals`

**Serving情報の該当行**:
- `cup 256cals / 96 g`
- カロリー: `256cals`

**問題**:
- デフォルトカロリー（`21cals`）とServing情報のカロリー（`256cals`）が不一致

**全Serving情報**:
```
cup (8 fl oz) 21cals / 8 g
tsp 5cals / 2 g
cube 11cals / 4 g
tablespoon 16cals / 6 g
gram 3cals / 1 g
packet (6 fl oz prepared) 16cals / 6 g
ml 1cals / 0.4 g
fl oz 32cals / 12 g
portion, amount of dry mix to make 8 fl oz prepared 21cals / 8 g
oz 76cals / 28.3 g
cup 256cals / 96 g
lb 1,211cals / 453.6 g
```

---

## 2️⃣ セクション不明（1件）

【Serving情報】セクションが見つからない食材です。

### 1. Cashews dry roasted with salt

**カテゴリ**: Nuts & Seeds

**ファイル**: `nuts_and_seeds_manual_input.txt`

**番号**: 12

**タイトル行**:
- `Cashews dry roasted with salt, cup, halves and whole`
- `786cals`

**問題**:
- マニュアルファイル内で該当セクションが見つかりませんでした
- 正規表現パターンとのミスマッチの可能性

---

## 3️⃣ 単位が見つからない（181件）

デフォルト単位がServing情報に完全一致しない食材です。

**主なパターン**:
- デフォルト単位が `cup` だが、Serving情報には `0.5 cup`, `0.33 cup` などの分数表記のみ
- デフォルト単位が `block` だが、Serving情報には `0.2 block`, `0.25 block` などのみ
- デフォルト単位が `fl oz` だが、Serving情報には `12 fl oz` などの数量付きのみ

### カテゴリ別内訳（18カテゴリ）

| カテゴリ | 件数 |
|---------|------|
| Beans & Peas | 9件 |
| Beverages | 3件 |
| Breads & Rolls | 9件 |
| Cheese | 7件 |
| Condiments, Dressings & Sauces | 8件 |
| Dairy, Dairy Substitutes & Egg | 11件 |
| Fish & Seafood | 22件 |
| Fruit - canned, dried, or juice | 2件 |
| Fruit - raw or frozen | 4件 |
| Grains & Grain Products | 11件 |
| Meats | 15件 |
| Nuts & Seeds | 5件 |
| Poultry | 11件 |
| Spices & Herbs | 10件 |
| Stocks and Gravy | 4件 |
| Sweets & Sweeteners | 11件 |
| Vegetables - canned, dried, or juice | 4件 |
| Vegetables - raw, frozen, or cooked | 35件 |

### Beans & Peas（9件）

#### 1. Black beans canned no salt added

**デフォルト単位**: `cup`

**デフォルトカロリー**: `220cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup 110cals / 130 g
gram 1cals / 1 g
oz 24cals / 28.3 g
tablespoon 14cals / 16.3 g
fl oz 28cals / 32.5 g
```

#### 2. Cannellini or white kidney beans canned no salt added

**デフォルト単位**: `cup`

**デフォルトカロリー**: `200cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup 100cals / 130 g
gram 1cals / 1 g
oz 22cals / 28.3 g
tablespoon 13cals / 16.3 g
fl oz 25cals / 32.5 g
```

#### 3. Edamame dry roasted

**デフォルト単位**: `cup`

**デフォルトカロリー**: `391cals`

**Serving情報の単位（最初の5件）**:
```
0.33 cup 129cals / 29.7 g
gram 4cals / 1 g
tablespoon 24cals / 5.6 g
oz 123cals / 28.3 g
teaspoon 8cals / 1.9 g
```

#### 4. Tofu extra firm made with nigari

**デフォルト単位**: `block`

**デフォルトカロリー**: `378cals`

**Serving情報の単位（最初の5件）**:
```
0.2 block 76cals / 91 g
oz 24cals / 28.3 g
gram 1cals / 1 g
lb 376cals / 453.6 g
```

#### 5. Tofu firm made with calcium sulfate

**デフォルト単位**: `cup`

**デフォルトカロリー**: `363cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
0.25 block 117cals / 81 g
oz 41cals / 28.3 g
0.5 cup 181cals / 126 g
tablespoon 23cals / 15.8 g
```

#### 6. Tofu firm made with nigari

**デフォルト単位**: `cup`

**デフォルトカロリー**: `197cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
oz 22cals / 28.3 g
0.5 cup 98cals / 126 g
0.25 block 63cals / 81 g
tablespoon 12cals / 15.8 g
```

#### 7. Tofu regular made with calcium sulfate

**デフォルト単位**: `cup`

**デフォルトカロリー**: `188cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
0.25 block 88cals / 116 g
0.5 cup 94cals / 124 g
oz 22cals / 28.3 g
tablespoon 12cals / 15.5 g
```

#### 8. Tofu soft made with nigari (1/2" cubes)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `151cals`

**Serving情報の単位（最初の5件）**:
```
cup (1/2" cubes) 151cals / 248 g
gram 1cals / 1 g
0.25 block 71cals / 116 g
0.2 block 57cals / 92.8 g
oz 17cals / 28.3 g
```

#### 9. Tofu soft silken

**デフォルト単位**: `block`

**デフォルトカロリー**: `210cals`

**Serving情報の単位（最初の5件）**:
```
0.2 block 42cals / 85 g
gram 0cals / 1 g
oz 14cals / 28.3 g
lb 224cals / 453.6 g
```

---

### Beverages（3件）

#### 1. Beer 7.7% ABV

**デフォルト単位**: `fl oz`

**デフォルトカロリー**: `19cals`

**Serving情報の単位（最初の5件）**:
```
12 fl oz 222cals / 362 g
ml 1cals / 1 g
cup 148cals / 241.3 g
oz 17cals / 28.3 g
gram 1cals / 1 g
```

#### 2. Hard seltzer lemonade 5% ABV

**デフォルト単位**: `fl oz`

**デフォルトカロリー**: `8cals`

**Serving情報の単位（最初の5件）**:
```
12 fl oz 100cals / 355 g
ml 0cals / 1 g
cup 67cals / 236.7 g
oz 8cals / 28.3 g
gram 0cals / 1 g
```

#### 3. Tea black regular instant powder unsweetened

**デフォルト単位**: `1 tsp`

**デフォルトカロリー**: `2cals`

**Serving情報の単位（最初の5件）**:
```
tsp 2cals / 0.7 g
gram 3cals / 1 g
oz 89cals / 28.3 g
lb 1,429cals / 453.6 g
```

---

### Breads & Rolls（9件）

#### 1. Bagel plain onion poppy or sesame (2-1/2" dia)

**デフォルト単位**: `bagel, mini`

**デフォルトカロリー**: `72cals`

**Serving情報の単位（最初の5件）**:
```
medium bagel (3-1/2" to 4" dia) 289cals / 105 g
large bagel (4-1/2" dia) 360cals / 131 g
gram 3cals / 1 g
small bagel (3" dia) 190cals / 69 g
bagel, mini (2-1/2" dia) 72cals / 26 g
```

#### 2. Bread crumbs panko

**デフォルト単位**: `cup`

**デフォルトカロリー**: `200cals`

**Serving情報の単位（最初の5件）**:
```
tablespoon 13cals / 3.8 g
0.5 cup 100cals / 30 g
gram 3cals / 1 g
teaspoon 4cals / 1.3 g
oz 94cals / 28.3 g
```

#### 3. Bread crumbs whole wheat dry grated

**デフォルト単位**: `cup`

**デフォルトカロリー**: `415cals`

**Serving情報の単位（最初の5件）**:
```
gram 3cals / 1 g
0.25 cup 104cals / 30 g
oz 98cals / 28.3 g
tablespoon 26cals / 7.5 g
teaspoon 9cals / 2.5 g
```

#### 4. Crispbread multigrain

**デフォルト単位**: `stick`

**デフォルトカロリー**: `34cals`

**Serving情報の単位（最初の5件）**:
```
2 stick 68cals / 20 g
2 slice 68cals / 20 g
gram 3cals / 1 g
oz 96cals / 28.3 g
lb 1,542cals / 453.6 g
```

#### 5. French vienna or sourdough bread (2" x 2-1/2" x 1-3/4")

**デフォルト単位**: `slice, small`

**デフォルトカロリー**: `87cals`

**Serving情報の単位（最初の5件）**:
```
slice, small (2" x 2-1/2" x 1-3/4") 87cals / 32 g
gram 3cals / 1 g
slice, medium (4" x 2-1/2" x 1-3/4") 174cals / 64 g
oz 77cals / 28.3 g
slice, large (6" x 2-1/2" x 1-3/4") 261cals / 96 g
```

#### 6. Pita white (6-1/2" dia)

**デフォルト単位**: `pita, large`

**デフォルトカロリー**: `165cals`

**Serving情報の単位（最初の5件）**:
```
pita, large (6-1/2" dia) 165cals / 60 g
pita, small (4" dia) 77cals / 28 g
gram 3cals / 1 g
oz 78cals / 28.3 g
lb 1,247cals / 453.6 g
```

#### 7. Pita whole wheat (6-1/2" dia)

**デフォルト単位**: `pita, large`

**デフォルトカロリー**: `168cals`

**Serving情報の単位（最初の5件）**:
```
pita, large (6-1/2" dia) 168cals / 64 g
pita, small (4" dia) 73cals / 28 g
gram 3cals / 1 g
oz 74cals / 28.3 g
lb 1,188cals / 453.6 g
```

#### 8. Rolls dinner white (foot long frankfurter roll)

**デフォルト単位**: `roll`

**デフォルトカロリー**: `267cals`

**Serving情報の単位（最初の5件）**:
```
roll (1 oz) 87cals / 28 g
roll (pan, dinner, or small roll) (2" square, 2" high) 87cals / 28 g
gram 3cals / 1 g
roll (hamburger, frankfurter, onion roll, bun, large roll) 133cals / 43 g
oz 88cals / 28.3 g
```

#### 9. Rolls dinner whole wheat (hamburger, frankfurter roll)

**デフォルト単位**: `roll`

**デフォルトカロリー**: `108cals`

**Serving情報の単位（最初の5件）**:
```
roll (1 oz) 71cals / 28 g
medium (2-1/2" dia) 91cals / 36 g
gram 3cals / 1 g
roll (hamburger, frankfurter roll) 108cals / 43 g
roll (small submarine, hoagie roll) 164cals / 65 g
```

---

### Cheese（7件）

#### 1. Cottage cheese low fat 1% milkfat (not packed)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `163cals`

**Serving情報の単位（最初の5件）**:
```
cup (not packed) 163cals / 226 g
gram 1cals / 1 g
4 oz 82cals / 113.4 g
lb 327cals / 453.6 g
```

#### 2. Cottage cheese whole 4% milkfat

**デフォルト単位**: `oz`

**デフォルトカロリー**: `28cals`

**Serving情報の単位（最初の5件）**:
```
cup, small curd (not packed) 221cals / 225 g
gram 1cals / 1 g
4 oz 111cals / 113.4 g
cup, large curd (not packed) 206cals / 210 g
lb 445cals / 453.6 g
```

#### 3. Mexican blend cheese

**デフォルト単位**: `cup shredded`

**デフォルトカロリー**: `451cals`

**Serving情報の単位（最初の5件）**:
```
0.25 cup shredded 113cals / 28 g
oz 114cals / 28.3 g
gram 4cals / 1 g
lb 1,828cals / 453.6 g
```

#### 4. Queso cotija cheese

**デフォルト単位**: `tsp`

**デフォルトカロリー**: `10cals`

**Serving情報の単位（最初の5件）**:
```
tablespoon 30cals / 7.5 g
gram 4cals / 1 g
oz 114cals / 28.3 g
2 tsp 20cals / 5 g
cup 484cals / 120 g
```

#### 5. Ricotta cheese nonfat

**デフォルト単位**: `cup`

**デフォルトカロリー**: `165cals`

**Serving情報の単位（最初の5件）**:
```
tablespoon 10cals / 15.5 g
0.25 cup 41cals / 62 g
gram 1cals / 1 g
oz 19cals / 28.3 g
teaspoon 3cals / 5.2 g
```

#### 6. Vegan mozzarella cheese shredded

**デフォルト単位**: `cup`

**デフォルトカロリー**: `360cals`

**Serving情報の単位（最初の5件）**:
```
0.25 cup 90cals / 28 g
gram 3cals / 1 g
tablespoon 23cals / 7 g
oz 91cals / 28.3 g
teaspoon 8cals / 2.3 g
```

#### 7. Vegan parmesan cheese

**デフォルト単位**: `cup`

**デフォルトカロリー**: `400cals`

**Serving情報の単位（最初の5件）**:
```
0.25 cup 100cals / 28 g
tablespoon 25cals / 7 g
gram 4cals / 1 g
teaspoon 8cals / 2.3 g
oz 101cals / 28.3 g
```

---

### Condiments, Dressings & Sauces（8件）

#### 1. Cocktail sauce

**デフォルト単位**: `cup`

**デフォルトカロリー**: `266cals`

**Serving情報の単位（最初の5件）**:
```
tablespoon 17cals / 15 g
teaspoon 6cals / 5 g
0.25 cup 66cals / 60 g
gram 1cals / 1 g
oz 31cals / 28.3 g
```

#### 2. Coconut aminos

**デフォルト単位**: `cup`

**デフォルトカロリー**: `266cals`

**Serving情報の単位（最初の5件）**:
```
tablespoon 17cals / 15 g
teaspoon 6cals / 5 g
0.25 cup 66cals / 60 g
gram 1cals / 1 g
oz 31cals / 28.3 g
```

#### 3. Pesto prepared refrigerated

**デフォルト単位**: `cup`

**デフォルトカロリー**: `1,053cals`

**Serving情報の単位（最初の5件）**:
```
tablespoon 66cals / 15.8 g
teaspoon 22cals / 5.3 g
gram 4cals / 1 g
oz 119cals / 28.3 g
0.25 cup 263cals / 63 g
```

#### 4. Rice vinegar

**デフォルト単位**: `ml`

**デフォルトカロリー**: `0cals`

**Serving情報の単位（最初の5件）**:
```
tablespoon 2cals / 11 g
teaspoon 1cals / 3.7 g
15 ml 2cals / 11 g
gram 0cals / 1 g
cup 32cals / 176 g
```

#### 5. Salad dressing Greek

**デフォルト単位**: `tbsp`

**デフォルトカロリー**: `65cals`

**Serving情報の単位（最初の5件）**:
```
2 tbsp 130cals / 30 g
teaspoon 22cals / 5 g
oz 123cals / 28.3 g
gram 4cals / 1 g
cup 1,040cals / 240 g
```

#### 6. Salsa verde

**デフォルト単位**: `tbsp`

**デフォルトカロリー**: `5cals`

**Serving情報の単位（最初の5件）**:
```
2 tbsp 10cals / 30 g
cup 77cals / 240 g
oz 9cals / 28.3 g
gram 0cals / 1 g
teaspoon 2cals / 5 g
```

#### 7. Steak sauce

**デフォルト単位**: `tbsp`

**デフォルトカロリー**: `16cals`

**Serving情報の単位（最初の5件）**:
```
2 tbsp 32cals / 34 g
gram 1cals / 1 g
teaspoon 5cals / 5.7 g
cup 258cals / 272 g
ml 1cals / 1.1 g
```

#### 8. Thai peanut sauce

**デフォルト単位**: `tbsp`

**デフォルトカロリー**: `40cals`

**Serving情報の単位（最初の5件）**:
```
2 tbsp 80cals / 25 g
cup 640cals / 200 g
oz 91cals / 28.3 g
gram 3cals / 1 g
teaspoon 13cals / 4.2 g
```

---

### Dairy, Dairy Substitutes & Egg（11件）

#### 1. Coconut yogurt plain unsweetened fortified

**デフォルト単位**: `cup`

**デフォルトカロリー**: `120cals`

**Serving情報の単位（最初の5件）**:
```
0.75 cup 90cals / 170 g
tablespoon 8cals / 14.2 g
gram 1cals / 1 g
teaspoon 3cals / 4.7 g
oz 15cals / 28.3 g
```

#### 2. Egg replacer

**デフォルト単位**: `tsp`

**デフォルトカロリー**: `10cals`

**Serving情報の単位（最初の5件）**:
```
tablespoon 30cals / 8 g
1.5 tsp 15cals / 4 g
gram 4cals / 1 g
oz 106cals / 28.3 g
cup 480cals / 128 g
```

#### 3. Flax milk unsweetened fortified

**デフォルト単位**: `ml`

**デフォルトカロリー**: `0cals`

**Serving情報の単位（最初の5件）**:
```
cup 25cals / 245 g
oz 3cals / 28.3 g
fl oz 3cals / 30.6 g
tablespoon 2cals / 15.3 g
gram 0cals / 1 g
```

#### 4. Greek yogurt plain low fat (7 oz)

**デフォルト単位**: `container`

**デフォルトカロリー**: `153cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
container (7 oz) 153cals / 200 g
oz 22cals / 28.3 g
cup 188cals / 245 g
tablespoon 12cals / 15.3 g
```

#### 5. Greek yogurt vanilla nonfat

**デフォルト単位**: `cup`

**デフォルトカロリー**: `174cals`

**Serving情報の単位（最初の5件）**:
```
0.75 cup 130cals / 170 g
gram 1cals / 1 g
tablespoon 11cals / 14.2 g
oz 22cals / 28.3 g
teaspoon 4cals / 4.7 g
```

#### 6. Rice milk unsweetened fortified

**デフォルト単位**: `ml`

**デフォルトカロリー**: `0cals`

**Serving情報の単位（最初の5件）**:
```
cup 70cals / 245 g
240 ml 70cals / 245 g
oz 8cals / 28.3 g
fl oz 9cals / 30.6 g
gram 0cals / 1 g
```

#### 7. Soy milk unsweetened high protein

**デフォルト単位**: `fl oz`

**デフォルトカロリー**: `16cals`

**Serving情報の単位（最初の5件）**:
```
ml 1cals / 0.9 g
cup 130cals / 226.8 g
8 fl oz 130cals / 226.8 g
gram 1cals / 1 g
tablespoon 8cals / 14.2 g
```

#### 8. Soy yogurt plain fortified

**デフォルト単位**: `cup`

**デフォルトカロリー**: `147cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
0.75 cup 110cals / 170 g
tablespoon 9cals / 14.2 g
oz 18cals / 28.3 g
ml 1cals / 0.9 g
```

#### 9. Yogurt plain fat free or nonfat (8 fl oz)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `137cals`

**Serving情報の単位（最初の5件）**:
```
cup (8 fl oz) 137cals / 245 g
gram 1cals / 1 g
oz 16cals / 28.3 g
0.5 container (4 oz) 63cals / 113 g
container (8 oz) 127cals / 227 g
```

#### 10. Yogurt plain low fat (8 fl oz)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `154cals`

**Serving情報の単位（最初の5件）**:
```
cup (8 fl oz) 154cals / 245 g
gram 1cals / 1 g
oz 18cals / 28.3 g
0.5 container (4 oz) 71cals / 113 g
container (8 oz) 143cals / 227 g
```

#### 11. Yogurt plain whole milk (8 fl oz)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `149cals`

**Serving情報の単位（最初の5件）**:
```
cup (8 fl oz) 149cals / 245 g
gram 1cals / 1 g
oz 17cals / 28.3 g
0.5 container (4 oz) 69cals / 113 g
container (8 oz) 138cals / 227 g
```

---

### Fish & Seafood（22件）

#### 1. Anchovy raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `37cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
3 oz 111cals / 85 g
lb 594cals / 453.6 g
```

#### 2. Clams cooked moist heat

**デフォルト単位**: `oz`

**デフォルトカロリー**: `40cals`

**Serving情報の単位（最初の5件）**:
```
20 small 270cals / 190 g
gram 1cals / 1 g
3 oz 121cals / 85 g
lb 644cals / 453.6 g
```

#### 3. Clams raw (with liquid and clams)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `195cals`

**Serving情報の単位（最初の5件）**:
```
small 8cals / 9 g
medium 12cals / 14.5 g
gram 1cals / 1 g
large 17cals / 20 g
cup (with liquid and clams) 195cals / 227 g
```

#### 4. Crab Dungeness raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `24cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 71cals / 85 g
crab 135cals / 163 g
gram 1cals / 1 g
lb 376cals / 453.6 g
```

#### 5. Crab blue raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `25cals`

**Serving情報の単位（最初の5件）**:
```
crab 18cals / 21 g
3 oz 74cals / 85 g
gram 1cals / 1 g
lb 395cals / 453.6 g
```

#### 6. Crab queen or snow raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `24cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 71cals / 85 g
gram 1cals / 1 g
lb 376cals / 453.6 g
```

#### 7. Halibut raw

**デフォルト単位**: `fillet`

**デフォルトカロリー**: `371cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 77cals / 85 g
gram 1cals / 1 g
0.5 fillet 186cals / 204 g
lb 413cals / 453.6 g
```

#### 8. Octopus raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `23cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
3 oz 70cals / 85 g
lb 372cals / 453.6 g
```

#### 9. Oyster eastern farmed raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `17cals`

**Serving情報の単位（最初の5件）**:
```
6 medium 50cals / 84 g
3 oz 50cals / 85 g
gram 1cals / 1 g
lb 268cals / 453.6 g
```

#### 10. Oyster eastern wild cooked moist heat

**デフォルト単位**: `oz`

**デフォルトカロリー**: `29cals`

**Serving情報の単位（最初の5件）**:
```
6 medium 43cals / 42 g
gram 1cals / 1 g
3 oz 87cals / 85 g
lb 463cals / 453.6 g
```

#### 11. Pollock Atlantic cooked dry heat

**デフォルト単位**: `fillet`

**デフォルトカロリー**: `356cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 100cals / 85 g
gram 1cals / 1 g
0.5 fillet 178cals / 151 g
lb 535cals / 453.6 g
```

#### 12. Pollock Atlantic raw

**デフォルト単位**: `fillet`

**デフォルトカロリー**: `355cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 78cals / 85 g
gram 1cals / 1 g
0.5 fillet 178cals / 193 g
lb 417cals / 453.6 g
```

#### 13. Salmon Atlantic wild cooked dry heat

**デフォルト単位**: `fillet`

**デフォルトカロリー**: `561cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 155cals / 85 g
gram 2cals / 1 g
0.5 fillet 280cals / 154 g
lb 826cals / 453.6 g
```

#### 14. Salmon Atlantic wild raw

**デフォルト単位**: `fillet`

**デフォルトカロリー**: `562cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 121cals / 85 g
gram 1cals / 1 g
0.5 fillet 281cals / 198 g
lb 644cals / 453.6 g
```

#### 15. Salmon atlantic farmed raw

**デフォルト単位**: `fillet`

**デフォルトカロリー**: `824cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 177cals / 85 g
gram 2cals / 1 g
0.5 fillet 412cals / 198 g
lb 943cals / 453.6 g
```

#### 16. Salmon chinook raw

**デフォルト単位**: `fillet`

**デフォルトカロリー**: `709cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 152cals / 85 g
gram 2cals / 1 g
0.5 fillet 354cals / 198 g
lb 812cals / 453.6 g
```

#### 17. Salmon pink cooked dry heat

**デフォルト単位**: `fillet`

**デフォルトカロリー**: `379cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 130cals / 85 g
gram 2cals / 1 g
0.5 fillet 190cals / 124 g
lb 694cals / 453.6 g
```

#### 18. Salmon pink raw

**デフォルト単位**: `fillet`

**デフォルトカロリー**: `404cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
3 oz 108cals / 85 g
0.5 fillet 202cals / 159 g
lb 576cals / 453.6 g
```

#### 19. Shrimp raw frozen medium peeled and deveined tail off

**デフォルト単位**: `oz`

**デフォルトカロリー**: `42cals`

**Serving情報の単位（最初の5件）**:
```
4 oz 170cals / 113.4 g
gram 1cals / 1 g
lb 680cals / 453.6 g
```

#### 20. Surimi imitation crab

**デフォルト単位**: `oz`

**デフォルトカロリー**: `27cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 81cals / 85 g
gram 1cals / 1 g
lb 431cals / 453.6 g
```

#### 21. Tuna bluefin raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `41cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 122cals / 85 g
gram 1cals / 1 g
lb 653cals / 453.6 g
```

#### 22. Tuna yellowfin cooked dry heat

**デフォルト単位**: `oz`

**デフォルトカロリー**: `37cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 111cals / 85 g
gram 1cals / 1 g
lb 590cals / 453.6 g
```

---

### Fruit - canned, dried, or juice（2件）

#### 1. Cherries tart sweetened dried

**デフォルト単位**: `cup`

**デフォルトカロリー**: `542cals`

**Serving情報の単位（最初の5件）**:
```
tablespoon 34cals / 10 g
0.25 cup 136cals / 40 g
gram 3cals / 1 g
teaspoon 11cals / 3.3 g
oz 96cals / 28.3 g
```

#### 2. Cranberries sweetened dried

**デフォルト単位**: `cup`

**デフォルトカロリー**: `373cals`

**Serving情報の単位（最初の5件）**:
```
tablespoon 23cals / 7.6 g
gram 3cals / 1 g
0.33 cup 123cals / 40 g
teaspoon 8cals / 2.5 g
oz 87cals / 28.3 g
```

---

### Fruit - raw or frozen（4件）

#### 1. Figs raw (2-1/2" dia)

**デフォルト単位**: `large`

**デフォルトカロリー**: `47cals`

**Serving情報の単位（最初の5件）**:
```
small (1-1/2" dia) 30cals / 40 g
medium (2-1/4" dia) 37cals / 50 g
gram 1cals / 1 g
large (2-1/2" dia) 47cals / 64 g
oz 21cals / 28.3 g
```

#### 2. Limes raw (2" dia)

**デフォルト単位**: `fruit`

**デフォルトカロリー**: `20cals`

**Serving情報の単位（最初の5件）**:
```
fruit (2" dia) 20cals / 67 g
gram 0cals / 1 g
oz 9cals / 28.3 g
serving 20cals / 67 g
lb 136cals / 453.6 g
```

#### 3. Persimmons Japanese raw (2-1/2" dia)

**デフォルト単位**: `fruit`

**デフォルトカロリー**: `118cals`

**Serving情報の単位（最初の5件）**:
```
fruit (2-1/2" dia) 118cals / 168 g
gram 1cals / 1 g
oz 20cals / 28.3 g
lb 318cals / 453.6 g
```

#### 4. Pomegranates raw (3-3/8" dia)

**デフォルト単位**: `pomegranate`

**デフォルトカロリー**: `128cals`

**Serving情報の単位（最初の5件）**:
```
pomegranate (3-3/8" dia) 128cals / 154 g
oz 24cals / 28.3 g
gram 1cals / 1 g
lb 376cals / 453.6 g
```

---

### Grains & Grain Products（11件）

#### 1. Chickpea or garbanzo bean flour

**デフォルト単位**: `cup`

**デフォルトカロリー**: `480cals`

**Serving情報の単位（最初の5件）**:
```
0.25 cup 120cals / 30 g
tablespoon 30cals / 7.5 g
gram 4cals / 1 g
oz 113cals / 28.3 g
teaspoon 10cals / 2.5 g
```

#### 2. Crackers gluten free multiseed and multigrains

**デフォルト単位**: `cracker`

**デフォルトカロリー**: `9cals`

**Serving情報の単位（最初の5件）**:
```
3 crackers 28cals / 6.1 g
gram 5cals / 1 g
oz 128cals / 28.3 g
lb 2,055cals / 453.6 g
```

#### 3. Flour gluten free all purpose

**デフォルト単位**: `cup`

**デフォルトカロリー**: `490cals`

**Serving情報の単位（最初の5件）**:
```
0.25 cup 122cals / 34 g
gram 4cals / 1 g
tablespoon 31cals / 8.5 g
teaspoon 10cals / 2.8 g
oz 102cals / 28.3 g
```

#### 4. Flour whole wheat pastry

**デフォルト単位**: `cup`

**デフォルトカロリー**: `440cals`

**Serving情報の単位（最初の5件）**:
```
0.25 cup 110cals / 30 g
gram 4cals / 1 g
tablespoon 28cals / 7.5 g
oz 104cals / 28.3 g
teaspoon 9cals / 2.5 g
```

#### 5. Muesli dry uncooked

**デフォルト単位**: `cup`

**デフォルトカロリー**: `560cals`

**Serving情報の単位（最初の5件）**:
```
0.25 cup 140cals / 35 g
gram 4cals / 1 g
tablespoon 35cals / 8.8 g
teaspoon 12cals / 2.9 g
oz 113cals / 28.3 g
```

#### 6. Noodles Japanese soba dry uncooked

**デフォルト単位**: `oz`

**デフォルトカロリー**: `95cals`

**Serving情報の単位（最初の5件）**:
```
gram 3cals / 1 g
2 oz 191cals / 56.7 g
lb 1,524cals / 453.6 g
```

#### 7. Pasta white dry uncooked

**デフォルト単位**: `oz`

**デフォルトカロリー**: `105cals`

**Serving情報の単位（最初の5件）**:
```
gram 4cals / 1 g
2 oz 210cals / 56.7 g
cup elbows 453cals / 122 g
cup shells 237cals / 64 g
cup penne 352cals / 95 g
```

#### 8. Pasta whole wheat dry uncooked

**デフォルト単位**: `oz`

**デフォルトカロリー**: `100cals`

**Serving情報の単位（最初の5件）**:
```
gram 4cals / 1 g
2 oz 200cals / 56.7 g
cup elbows 429cals / 122 g
cup rotini 338cals / 96 g
cup spaghetti 320cals / 91 g
```

#### 9. Polenta dry uncooked

**デフォルト単位**: `cup`

**デフォルトカロリー**: `440cals`

**Serving情報の単位（最初の5件）**:
```
0.25 cup 110cals / 30 g
gram 4cals / 1 g
tablespoon 28cals / 7.5 g
oz 104cals / 28.3 g
ml 2cals / 0.5 g
```

#### 10. Polenta precooked tubes

**デフォルト単位**: `half-inch slice`

**デフォルトカロリー**: `35cals`

**Serving情報の単位（最初の5件）**:
```
2 half-inch slices 70cals / 100 g
gram 1cals / 1 g
oz 20cals / 28.3 g
lb 318cals / 453.6 g
```

#### 11. Shirataki noodles

**デフォルト単位**: `package`

**デフォルトカロリー**: `10cals`

**Serving情報の単位（最初の5件）**:
```
0.5 package 5cals / 85 g
gram 0cals / 1 g
oz 2cals / 28.3 g
lb 27cals / 453.6 g
```

---

### Meats（15件）

#### 1. Beef chuck short ribs boneless lean and fat trimmed to 0" fat raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `67cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 200cals / 85 g
gram 2cals / 1 g
piece 1,015cals / 432 g
lb 1,066cals / 453.6 g
```

#### 2. Beef ground 97% lean 3% fat raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `34cals`

**Serving情報の単位（最初の5件）**:
```
4 oz 137cals / 113.4 g
gram 1cals / 1 g
lb 549cals / 453.6 g
```

#### 3. Beef ribeye steak bone-in lean and trimmed to 1/8" fat all grades raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `47cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 141cals / 85 g
gram 2cals / 1 g
steak 767cals / 462 g
roast 4,361cals / 2,627 g
lb 753cals / 453.6 g
```

#### 4. Beef ribeye steak boneless lean and trimmed to 1/8" fat all grades raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `69cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 208cals / 85 g
gram 2cals / 1 g
steak 881cals / 361 g
roast 5,258cals / 2,155 g
lb 1,107cals / 453.6 g
```

#### 5. Beef round top steak boneless lean and trimmed to 0" fat all grades raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `35cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 105cals / 85 g
gram 1cals / 1 g
steak 427cals / 344 g
lb 562cals / 453.6 g
```

#### 6. Beef tenderloin boneless lean meat only cooked roasted

**デフォルト単位**: `oz`

**デフォルトカロリー**: `50cals`

**Serving情報の単位（最初の5件）**:
```
gram 2cals / 1 g
3 oz 151cals / 85 g
roast 851cals / 481 g
lb 803cals / 453.6 g
```

#### 7. Lamb leg boneless lean and fat trimmed to 1/8" fat

**デフォルト単位**: `oz`

**デフォルトカロリー**: `53cals`

**Serving情報の単位（最初の5件）**:
```
4 oz 212cals / 113.4 g
gram 2cals / 1 g
leg bottom, boneless 1,849cals / 989 g
lb 848cals / 453.6 g
```

#### 8. Pork bacon Canadian unprepared (6 oz)

**デフォルト単位**: `package`

**デフォルトカロリー**: `187cals`

**Serving情報の単位（最初の5件）**:
```
2 slices (6 per 6-oz pkg.) 63cals / 57 g
gram 1cals / 1 g
oz 31cals / 28.3 g
package (6 oz) 187cals / 170 g
lb 499cals / 453.6 g
```

#### 9. Pork ground 84% lean 16% fat raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `62cals`

**Serving情報の単位（最初の5件）**:
```
4 oz 247cals / 113.4 g
gram 2cals / 1 g
lb 989cals / 453.6 g
```

#### 10. Pork sausage Polish (10" long x 1-1/4" dia)

**デフォルト単位**: `sausage`

**デフォルトカロリー**: `780cals`

**Serving情報の単位（最初の5件）**:
```
oz 97cals / 28.3 g
gram 3cals / 1 g
sausage (10" long x 1-1/4" dia) 780cals / 227 g
lb 1,559cals / 453.6 g
```

#### 11. Pork sausage chorizo link or ground raw (4" long)

**デフォルト単位**: `link`

**デフォルトカロリー**: `178cals`

**Serving情報の単位（最初の5件）**:
```
link (4" long) 178cals / 60 g
oz 84cals / 28.3 g
gram 3cals / 1 g
lb 1,346cals / 453.6 g
```

#### 12. Pork shoulder boneless lean and fat raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `36cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
3 oz 108cals / 85 g
piece 546cals / 430 g
lb 576cals / 453.6 g
```

#### 13. Pork tenderloin lean meat and fat raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `32cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
3 oz 97cals / 85 g
roast 612cals / 537 g
lb 517cals / 453.6 g
```

#### 14. Veal cutlet boneless raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `30cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
3 oz 91cals / 85 g
cutlet 59cals / 55 g
serving 121cals / 113 g
lb 485cals / 453.6 g
```

#### 15. Veal or calf liver cooked pan fried (yield from 99g raw liver)

**デフォルト単位**: `slice`

**デフォルトカロリー**: `129cals`

**Serving情報の単位（最初の5件）**:
```
gram 2cals / 1 g
oz 55cals / 28.3 g
slice (yield from 99g raw liver) 129cals / 67 g
lb 875cals / 453.6 g
```

---

### Nuts & Seeds（5件）

#### 1. Brazil nuts or brazilnuts (32 kernels)

**デフォルト単位**: `cup shelled`

**デフォルトカロリー**: `923cals`

**Serving情報の単位（最初の5件）**:
```
gram 7cals / 1 g
oz (6-8 kernels) 185cals / 28 g
oz 187cals / 28.3 g
cup shelled (32 kernels) 923cals / 140 g
lb 2,989cals / 453.6 g
```

#### 2. Coconut flour

**デフォルト単位**: `tbsp`

**デフォルトカロリー**: `30cals`

**Serving情報の単位（最初の5件）**:
```
2 tbsp 60cals / 14 g
gram 4cals / 1 g
cup 480cals / 112 g
teaspoon 10cals / 2.3 g
oz 122cals / 28.3 g
```

#### 3. Coconut milk canned light

**デフォルト単位**: `cup`

**デフォルトカロリー**: `152cals`

**Serving情報の単位（最初の5件）**:
```
0.33 cup 50cals / 75 g
ml 1cals / 0.9 g
tablespoon 9cals / 14.2 g
gram 1cals / 1 g
oz 19cals / 28.3 g
```

#### 4. Coconut shredded unsweetened packaged

**デフォルト単位**: `tbsp`

**デフォルトカロリー**: `33cals`

**Serving情報の単位（最初の5件）**:
```
3 tbsp 100cals / 15 g
gram 7cals / 1 g
teaspoon 11cals / 1.7 g
cup 533cals / 80 g
oz 189cals / 28.3 g
```

#### 5. Hemp seeds shelled or hulled

**デフォルト単位**: `tbsp`

**デフォルトカロリー**: `55cals`

**Serving情報の単位（最初の5件）**:
```
3 tbsp 166cals / 30 g
teaspoon 18cals / 3.3 g
gram 6cals / 1 g
cup 885cals / 160 g
oz 157cals / 28.3 g
```

---

### Poultry（11件）

#### 1. Chicken breast baked boneless skinless (yield from 1 lb ready-to-cook chicken)

**デフォルト単位**: `unit`

**デフォルトカロリー**: `97cals`

**Serving情報の単位（最初の5件）**:
```
oz 53cals / 28.3 g
0.5 breast 161cals / 86 g
gram 2cals / 1 g
unit (yield from 1 lb ready-to-cook chicken) 97cals / 52 g
```

#### 2. Chicken breast boneless skinless raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `31cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
3 oz 92cals / 85 g
breast large 255cals / 236 g
piece 284cals / 263 g
breast medium 184cals / 170 g
```

#### 3. Chicken breast grilled boneless skinless

**デフォルト単位**: `oz`

**デフォルトカロリー**: `42cals`

**Serving情報の単位（最初の5件）**:
```
3 oz 126cals / 85 g
gram 1cals / 1 g
piece 284cals / 192 g
lb 671cals / 453.6 g
```

#### 4. Chicken giblets raw (yield from 1 lb ready-to-cook chicken)

**デフォルト単位**: `unit`

**デフォルトカロリー**: `29cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
unit (yield from 1 lb ready-to-cook chicken) 29cals / 23 g
giblets 93cals / 75 g
oz 35cals / 28.3 g
```

#### 5. Chicken ground raw

**デフォルト単位**: `oz crumbled`

**デフォルトカロリー**: `40cals`

**Serving情報の単位（最初の5件）**:
```
4 oz crumbled 160cals / 112 g
gram 1cals / 1 g
oz 41cals / 28.3 g
lb 649cals / 453.6 g
```

#### 6. Chicken liver all classes cooked simmered (cooked, yield from 400g raw liver)

**デフォルト単位**: `container`

**デフォルトカロリー**: `428cals`

**Serving情報の単位（最初の5件）**:
```
gram 2cals / 1 g
oz 47cals / 28.3 g
container (cooked, yield from 400g raw liver) 428cals / 256 g
lb 758cals / 453.6 g
```

#### 7. Chicken whole meat and skin raw (yield from 1 lb ready-to-cook chicken)

**デフォルト単位**: `unit`

**デフォルトカロリー**: `660cals`

**Serving情報の単位（最初の5件）**:
```
gram 2cals / 1 g
unit (yield from 1 lb ready-to-cook chicken) 660cals / 276 g
oz 68cals / 28.3 g
0.5 chicken, bone removed 1,099cals / 460 g
```

#### 8. Duck meat only raw (yield from 1 lb ready-to-cook duck)

**デフォルト単位**: `unit`

**デフォルトカロリー**: `185cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
oz 38cals / 28.3 g
0.5 duck 409cals / 303 g
unit (yield from 1 lb ready-to-cook duck) 185cals / 137 g
```

#### 9. Duck wild meat and skin raw (yield from 1 lb ready-to-cook duck)

**デフォルト単位**: `unit`

**デフォルトカロリー**: `504cals`

**Serving情報の単位（最初の5件）**:
```
gram 2cals / 1 g
oz 60cals / 28.3 g
0.5 duck 570cals / 270 g
unit (yield from 1 lb ready-to-cook duck) 504cals / 239 g
```

#### 10. Turkey drumstick meat and skin raw

**デフォルト単位**: `oz`

**デフォルトカロリー**: `40cals`

**Serving情報の単位（最初の5件）**:
```
drumstick 502cals / 356 g
gram 1cals / 1 g
3 oz 120cals / 85 g
lb 640cals / 453.6 g
```

#### 11. Turkey ground 85% lean 5% fat raw (cooked from 4 oz raw)

**デフォルト単位**: `patty`

**デフォルトカロリー**: `153cals`

**Serving情報の単位（最初の5件）**:
```
oz 51cals / 28.3 g
gram 2cals / 1 g
lb 815cals / 453 g
patty (cooked from 4 oz raw) 153cals / 85 g
```

---

### Spices & Herbs（10件）

#### 1. Baker's yeast compressed (0.6 oz)

**デフォルト単位**: `cake`

**デフォルトカロリー**: `18cals`

**Serving情報の単位（最初の5件）**:
```
cake (0.6 oz) 18cals / 17 g
gram 1cals / 1 g
oz 30cals / 28.3 g
lb 476cals / 453.6 g
```

#### 2. Basil fresh or raw herb

**デフォルト単位**: `tbsp`

**デフォルトカロリー**: `1cals`

**Serving情報の単位（最初の5件）**:
```
5 leaves 1cals / 2.5 g
gram 0cals / 1 g
2 tbsp 1cals / 5.3 g
cup 10cals / 42.4 g
oz 7cals / 28.3 g
```

#### 3. Cilantro or coriander leaves fresh or raw herb

**デフォルト単位**: `cup`

**デフォルトカロリー**: `4cals`

**Serving情報の単位（最初の5件）**:
```
9 sprigs 5cals / 20 g
gram 0cals / 1 g
0.25 cup 1cals / 4 g
tablespoon 0cals / 1 g
oz 7cals / 28.3 g
```

#### 4. Everything bagel seasoning by stonemill

**デフォルト単位**: `teaspoon`

**デフォルトカロリー**: `20cals`

**Serving情報の単位（最初の5件）**:
```
0.25 teaspoon 5cals / 1 g
tablespoon 60cals / 12 g
gram 5cals / 1 g
ml 4cals / 0.8 g
oz 142cals / 28.3 g
```

#### 5. Everything bagel seasoning salt free

**デフォルト単位**: `teaspoon`

**デフォルトカロリー**: `20cals`

**Serving情報の単位（最初の5件）**:
```
0.25 teaspoon 5cals / 0.9 g
tablespoon 60cals / 10.8 g
oz 157cals / 28.3 g
gram 6cals / 1 g
ml 4cals / 0.7 g
```

#### 6. Fajita seasoning mix

**デフォルト単位**: `tsp`

**デフォルトカロリー**: `8cals`

**Serving情報の単位（最初の5件）**:
```
2 tsp 15cals / 4 g
tablespoon 23cals / 6 g
gram 4cals / 1 g
oz 106cals / 28.3 g
cup 360cals / 96 g
```

#### 7. Kosher salt

**デフォルト単位**: `tsp`

**デフォルトカロリー**: `0cals`

**Serving情報の単位（最初の5件）**:
```
0.12 tsp 0cals / 1 g
dash 0cals / 0.4 g
gram 0cals / 1 g
tablespoon 0cals / 25 g
ml 0cals / 1.7 g
```

#### 8. Lemon pepper seasoning

**デフォルト単位**: `tsp`

**デフォルトカロリー**: `9cals`

**Serving情報の単位（最初の5件）**:
```
0.25 tsp 2cals / 1.2 g
tablespoon 26cals / 14.4 g
gram 2cals / 1 g
oz 50cals / 28.3 g
ml 2cals / 1 g
```

#### 9. Mint fresh or raw herb

**デフォルト単位**: `tbsp`

**デフォルトカロリー**: `2cals`

**Serving情報の単位（最初の5件）**:
```
2 tbsp 5cals / 11.4 g
gram 0cals / 1 g
cup 40cals / 91.2 g
teaspoon 1cals / 1.9 g
oz 12cals / 28.3 g
```

#### 10. Spices dry taco seasoning mix

**デフォルト単位**: `tsp`

**デフォルトカロリー**: `8cals`

**Serving情報の単位（最初の5件）**:
```
2 tsp 17cals / 5.7 g
tablespoon 25cals / 8.6 g
gram 3cals / 1 g
oz 83cals / 28.3 g
cup 402cals / 136.8 g
```

---

### Stocks and Gravy（4件）

#### 1. Beef broth or bouillon dry powder (8 fl oz)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `17cals`

**Serving情報の単位（最初の5件）**:
```
cup (8 fl oz) 17cals / 8 g
cube 8cals / 3.6 g
gram 2cals / 1 g
packet 13cals / 6 g
oz 60cals / 28.3 g
```

#### 2. Beef broth or bouillon prepared from dry powder (8 fl oz)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `7cals`

**Serving情報の単位（最初の5件）**:
```
cup (8 fl oz) 7cals / 244 g
fl oz (prepared) 1cals / 30.5 g
packet (6 fl oz prepared) 5cals / 183 g
oz 1cals / 28.3 g
gram 0cals / 1 g
```

#### 3. Chicken broth dry cubes (8 fl oz)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `13cals`

**Serving情報の単位（最初の5件）**:
```
cube 10cals / 4.8 g
cup (8 fl oz) 13cals / 6.4 g
gram 2cals / 1 g
oz 56cals / 28.3 g
lb 898cals / 453.6 g
```

#### 4. Chicken broth prepared from dry cubes (8 fl oz)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `12cals`

**Serving情報の単位（最初の5件）**:
```
cube (6 fl oz prepared) 9cals / 182 g
cup (8 fl oz) 12cals / 243 g
gram 0cals / 1 g
oz 1cals / 28.3 g
lb 23cals / 453.6 g
```

---

### Sweets & Sweeteners（11件）

#### 1. Erythritol sweetener granular

**デフォルト単位**: `cup`

**デフォルトカロリー**: `0cals`

**Serving情報の単位（最初の5件）**:
```
teaspoon 0cals / 4 g
tablespoon 0cals / 12 g
gram 0cals / 1 g
0.5 cup 0cals / 96 g
ml 0cals / 0.8 g
```

#### 2. Ice cream chocolate (3.5 fl oz)

**デフォルト単位**: `individual`

**デフォルトカロリー**: `125cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup (4 fl oz) 143cals / 66 g
gram 2cals / 1 g
individual (3.5 fl oz) 125cals / 58 g
oz 61cals / 28.3 g
lb 980cals / 453.6 g
```

#### 3. Ice cream strawberry (3.5 fl oz)

**デフォルト単位**: `individual`

**デフォルトカロリー**: `111cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup (4 fl oz) 127cals / 66 g
gram 2cals / 1 g
individual (3.5 fl oz) 111cals / 58 g
oz 54cals / 28.3 g
lb 871cals / 453.6 g
```

#### 4. Ice cream vanilla

**デフォルト単位**: `cup`

**デフォルトカロリー**: `298cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup 149cals / 72 g
gram 2cals / 1 g
tablespoon 19cals / 9 g
oz 59cals / 28.3 g
ml 1cals / 0.6 g
```

#### 5. Jellies

**デフォルト単位**: `1 tbsp`

**デフォルトカロリー**: `58cals`

**Serving情報の単位（最初の5件）**:
```
tbsp 58cals / 21 g
packet (0.5 oz) 39cals / 14 g
gram 3cals / 1 g
oz 79cals / 28.3 g
lb 1,261cals / 453.6 g
```

#### 6. Noncaloric sweetener Sweet n Low or saccharin (pink packet)

**デフォルト単位**: `1 packet`

**デフォルトカロリー**: `4cals`

**Serving情報の単位（最初の5件）**:
```
packet 4cals / 1 g
gram 4cals / 1 g
packet sugar twin 3cals / 0.8 g
oz 102cals / 28.3 g
lb 1,633cals / 453.6 g
```

#### 7. Nougat

**デフォルト単位**: `piece`

**デフォルトカロリー**: `32cals`

**Serving情報の単位（最初の5件）**:
```
4 piece 128cals / 32.8 g
oz 111cals / 28.3 g
gram 4cals / 1 g
lb 1,772cals / 453.6 g
```

#### 8. Nougat with nuts, homemade

**デフォルト単位**: `piece`

**デフォルトカロリー**: `65cals`

**Serving情報の単位（最初の5件）**:
```
2 piece 129cals / 28 g
oz 131cals / 28.3 g
gram 5cals / 1 g
lb 2,098cals / 453.6 g
```

#### 9. Nougat, homemade

**デフォルト単位**: `piece`

**デフォルトカロリー**: `49cals`

**Serving情報の単位（最初の5件）**:
```
2 piece 97cals / 28 g
oz 98cals / 28.3 g
gram 3cals / 1 g
lb 1,573cals / 453.6 g
```

#### 10. Pie filling apple canned (21 oz)

**デフォルト単位**: `can`

**デフォルトカロリー**: `595cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
oz 28cals / 28.3 g
0.12 can 74cals / 74 g
can (21 oz) 595cals / 595 g
lb 454cals / 453.6 g
```

#### 11. Pie filling cherry canned (21 oz)

**デフォルト単位**: `can`

**デフォルトカロリー**: `684cals`

**Serving情報の単位（最初の5件）**:
```
0.12 can 85cals / 74 g
oz 33cals / 28.3 g
gram 1cals / 1 g
can (21 oz) 684cals / 595 g
lb 522cals / 453.6 g
```

---

### Vegetables - canned, dried, or juice（4件）

#### 1. Corn sweet yellow canned no salt added

**デフォルト単位**: `cup`

**デフォルトカロリー**: `166cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup 83cals / 105 g
gram 1cals / 1 g
tablespoon 10cals / 13.1 g
oz 22cals / 28.3 g
can (303 x 406) 269cals / 340 g
```

#### 2. Peppers hot pickled canned

**デフォルト単位**: `cup drained`

**デフォルトカロリー**: `30cals`

**Serving情報の単位（最初の5件）**:
```
oz 6cals / 28.3 g
gram 0cals / 1 g
0.25 cup drained 7cals / 34 g
lb 100cals / 453.6 g
```

#### 3. Tomato paste canned

**デフォルト単位**: `cup`

**デフォルトカロリー**: `215cals`

**Serving情報の単位（最初の5件）**:
```
tablespoon 13cals / 16.4 g
gram 1cals / 1 g
teaspoon 4cals / 5.5 g
can (6 oz) 139cals / 170 g
0.5 cup 107cals / 131 g
```

#### 4. Tomatoes crushed canned no salt added

**デフォルト単位**: `oz`

**デフォルトカロリー**: `9cals`

**Serving情報の単位（最初の5件）**:
```
14 oz 127cals / 396.9 g
gram 0cals / 1 g
lb 145cals / 453.6 g
```

---

### Vegetables - raw, frozen, or cooked（35件）

#### 1. Asparagus boiled with salt

**デフォルト単位**: `cup`

**デフォルトカロリー**: `40cals`

**Serving情報の単位（最初の5件）**:
```
4 spears (1/2" base) 13cals / 60 g
gram 0cals / 1 g
0.5 cup 20cals / 90 g
oz 6cals / 28.3 g
tablespoon 2cals / 11.3 g
```

#### 2. Asparagus boiled without salt

**デフォルト単位**: `cup`

**デフォルトカロリー**: `40cals`

**Serving情報の単位（最初の5件）**:
```
4 spears (1/2" base) 13cals / 60 g
gram 0cals / 1 g
0.5 cup 20cals / 90 g
oz 6cals / 28.3 g
fl oz 5cals / 22.5 g
```

#### 3. Asparagus steameds (1/2" base)

**デフォルト単位**: `spear`

**デフォルトカロリー**: `3cals`

**Serving情報の単位（最初の5件）**:
```
10 spears (1/2" base) 33cals / 150 g
gram 0cals / 1 g
oz 6cals / 28.3 g
lb 100cals / 453.6 g
```

#### 4. Broccoli boiled without salt (11"-12" long)

**デフォルト単位**: `stalk, large`

**デフォルトカロリー**: `98cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup, chopped 27cals / 78 g
gram 0cals / 1 g
oz 10cals / 28.3 g
serving 30cals / 87 g
stalk, small (5" long) 49cals / 140 g
```

#### 5. Broccoli roasted without salt

**デフォルト単位**: `serving`

**デフォルトカロリー**: `88cals`

**Serving情報の単位（最初の5件）**:
```
4 serving 351cals / 280 g
oz 36cals / 28.3 g
gram 1cals / 1 g
lb 569cals / 453.6 g
```

#### 6. Broccolini raw

**デフォルト単位**: `cup chopped raw`

**デフォルトカロリー**: `20cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup chopped raw 10cals / 36 g
gram 0cals / 1 g
oz 8cals / 28.3 g
lb 126cals / 453.6 g
```

#### 7. Brussels sprouts frozen unprepared (10 oz)

**デフォルト単位**: `package`

**デフォルトカロリー**: `116cals`

**Serving情報の単位（最初の5件）**:
```
gram 0cals / 1 g
package (10 oz) 116cals / 284 g
oz 12cals / 28.3 g
package (2 lb) 372cals / 907 g
```

#### 8. Cauliflower boiled without salt (1" pieces)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `29cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup (1" pieces) 14cals / 62 g
gram 0cals / 1 g
3 flowerets 12cals / 54 g
oz 7cals / 28.3 g
lb 104cals / 453.6 g
```

#### 9. Cauliflower frozen unprepared (10 oz)

**デフォルト単位**: `package`

**デフォルトカロリー**: `68cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup (1" pieces) 16cals / 66 g
gram 0cals / 1 g
oz 7cals / 28.3 g
package (10 oz) 68cals / 284 g
lb 109cals / 453.6 g
```

#### 10. Cauliflower steamed (1" pieces)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `29cals`

**Serving情報の単位（最初の5件）**:
```
1.5 cup (1" pieces) 43cals / 186 g
gram 0cals / 1 g
oz 7cals / 28.3 g
lb 105cals / 453.6 g
```

#### 11. Chayote fruit or mirliton squash raw (1" pieces)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `25cals`

**Serving情報の単位（最初の5件）**:
```
cup (1" pieces) 25cals / 132 g
gram 0cals / 1 g
chayote (5-3/4") 39cals / 203 g
oz 5cals / 28.3 g
lb 86cals / 453.6 g
```

#### 12. Corn sweet white raw (5-1/2" to 6-1/2" long)

**デフォルト単位**: `ear, small`

**デフォルトカロリー**: `63cals`

**Serving情報の単位（最初の5件）**:
```
cup 132cals / 154 g
ear, medium (6-3/4" to 7-1/2" long) 77cals / 90 g
gram 1cals / 1 g
ear, large (7-3/4" to 9" long) 123cals / 143 g
ear, small (5-1/2" to 6-1/2" long) 63cals / 73 g
```

#### 13. Corn sweet yellow boiled without salt (5-1/2" to 6-1/2" long)

**デフォルト単位**: `ear, small`

**デフォルトカロリー**: `85cals`

**Serving情報の単位（最初の5件）**:
```
cup cut 157cals / 164 g
gram 1cals / 1 g
ear, medium (6-3/4" to 7-1/2" long) 99cals / 103 g
ear, large (7-3/4" to 9" long) 113cals / 118 g
ear, small (5-1/2" to 6-1/2" long) 85cals / 89 g
```

#### 14. Corn sweet yellow frozen kernels unprepared

**デフォルト単位**: `cup`

**デフォルトカロリー**: `144cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup 72cals / 82 g
gram 1cals / 1 g
tablespoon 9cals / 10.3 g
oz 25cals / 28.3 g
fl oz 18cals / 20.5 g
```

#### 15. Corn sweet yellow raw (5-1/2" to 6-1/2" long)

**デフォルト単位**: `ear, small`

**デフォルトカロリー**: `63cals`

**Serving情報の単位（最初の5件）**:
```
cup 132cals / 154 g
gram 1cals / 1 g
ear, medium (6-3/4" to 7-1/2" long) 77cals / 90 g
tablespoon 8cals / 9.6 g
ear, small (5-1/2" to 6-1/2" long) 63cals / 73 g
```

#### 16. Cucumber with peel raw

**デフォルト単位**: `cup slices`

**デフォルトカロリー**: `16cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup slices 8cals / 52 g
gram 0cals / 1 g
cucumber (8-1/4") 45cals / 301 g
slice 1cals / 8 g
oz 4cals / 28.3 g
```

#### 17. Eggplant boiled without salt (1" cubes)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `35cals`

**Serving情報の単位（最初の5件）**:
```
cup (1" cubes) 35cals / 99 g
gram 0cals / 1 g
oz 10cals / 28.3 g
lb 159cals / 453.6 g
```

#### 18. Green peas frozen boiled without salt (10 oz) yields

**デフォルト単位**: `package`

**デフォルトカロリー**: `197cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup 62cals / 80 g
gram 1cals / 1 g
tablespoon 8cals / 10 g
oz 22cals / 28.3 g
fl oz 16cals / 20 g
```

#### 19. Green peas frozen unprepared

**デフォルト単位**: `cup`

**デフォルトカロリー**: `111cals`

**Serving情報の単位（最初の5件）**:
```
0.5 cup 55cals / 72 g
gram 1cals / 1 g
tablespoon 7cals / 9 g
oz 22cals / 28.3 g
fl oz 14cals / 18 g
```

#### 20. Okra frozen unprepared (10 oz)

**デフォルト単位**: `package`

**デフォルトカロリー**: `85cals`

**Serving情報の単位（最初の5件）**:
```
gram 0cals / 1 g
oz 9cals / 28.3 g
package (10 oz) 85cals / 284 g
package (3 lb) 408cals / 1,361 g
```

#### 21. Onions frozen chopped unprepared (10 oz)

**デフォルト単位**: `package`

**デフォルトカロリー**: `82cals`

**Serving情報の単位（最初の5件）**:
```
gram 0cals / 1 g
oz 8cals / 28.3 g
package (10 oz) 82cals / 284 g
lb 132cals / 453.6 g
```

#### 22. Parsnips boiled without salt

**デフォルト単位**: `cup slices`

**デフォルトカロリー**: `111cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
parsnip (9" long) 114cals / 160 g
0.5 cup slices 55cals / 78 g
oz 20cals / 28.3 g
lb 322cals / 453.6 g
```

#### 23. Peppers sweet yellow raw (3-3/4" long, 3" dia)

**デフォルト単位**: `pepper, large`

**デフォルトカロリー**: `50cals`

**Serving情報の単位（最初の5件）**:
```
pepper, large (3-3/4" long, 3" dia) 50cals / 186 g
gram 0cals / 1 g
10 strips 14cals / 52 g
oz 8cals / 28.3 g
lb 122cals / 453.6 g
```

#### 24. Potatoes baked with skin without salt (3" to 4-1/4" dia)

**デフォルト単位**: `potato large`

**デフォルトカロリー**: `278cals`

**Serving情報の単位（最初の5件）**:
```
potato medium (2-1/4" to 3-1/4" dia.) 161cals / 173 g
gram 1cals / 1 g
potato small (1-3/4" to 2-1/2" dia.) 128cals / 138 g
oz 26cals / 28.3 g
potato large (3" to 4-1/4" dia) 278cals / 299 g
```

#### 25. Potatoes boiled with skin without salt

**デフォルト単位**: `cup`

**デフォルトカロリー**: `136cals`

**Serving情報の単位（最初の5件）**:
```
potato (2-1/2" dia, sphere) 118cals / 136 g
gram 1cals / 1 g
0.5 cup 68cals / 78 g
oz 25cals / 28.3 g
tablespoon 8cals / 9.8 g
```

#### 26. Potatoes hashed brown frozen plain prepared (approx 3" x 1-1/2" x 1/2")

**デフォルト単位**: `patty, oval`

**デフォルトカロリー**: `65cals`

**Serving情報の単位（最初の5件）**:
```
patty, oval (approx 3" x 1-1/2" x 1/2") 65cals / 29 g
0.5 cup 176cals / 78 g
gram 2cals / 1 g
oz 64cals / 28.3 g
fl oz 44cals / 19.5 g
```

#### 27. Potatoes with skin raw (3" to 4-1/4" dia)

**デフォルト単位**: `potato large`

**デフォルトカロリー**: `284cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
potato medium (2-1/4" to 3-1/4" dia) 164cals / 213 g
0.5 cup, diced 58cals / 75 g
potato small (1-3/4" to 2-1/2" dia) 131cals / 170 g
oz 22cals / 28.3 g
```

#### 28. Pumpkin raw (1" cubes)

**デフォルト単位**: `cup`

**デフォルトカロリー**: `30cals`

**Serving情報の単位（最初の5件）**:
```
gram 0cals / 1 g
cup (1" cubes) 30cals / 116 g
oz 7cals / 28.3 g
lb 118cals / 453.6 g
```

#### 29. Radishes oriental raw (7" long)

**デフォルト単位**: `radish`

**デフォルトカロリー**: `61cals`

**Serving情報の単位（最初の5件）**:
```
gram 0cals / 1 g
oz 5cals / 28.3 g
radish (7" long) 61cals / 338 g
lb 82cals / 453.6 g
```

#### 30. Red potatoes with skin raw (3" to 4-1/4" dia)

**デフォルト単位**: `potato large`

**デフォルトカロリー**: `258cals`

**Serving情報の単位（最初の5件）**:
```
potato medium (2-1/4" to 3-1/4" dia) 149cals / 213 g
gram 1cals / 1 g
oz 20cals / 28.3 g
0.5 cup diced 53cals / 75 g
potato small (1-3/4" to 2-1/4" dia) 119cals / 170 g
```

#### 31. Russet potatoes with skin raw (1-3/4" to 2-1/4" dia)

**デフォルト単位**: `potato small`

**デフォルトカロリー**: `134cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
potato medium (2-1/4" to 3-1/4" dia) 168cals / 213 g
oz 22cals / 28.3 g
potato small (1-3/4" to 2-1/4" dia) 134cals / 170 g
0.5 cup, diced 59cals / 75 g
```

#### 32. Seaweed kelp raw

**デフォルト単位**: `tbsp`

**デフォルトカロリー**: `2cals`

**Serving情報の単位（最初の5件）**:
```
gram 0cals / 1 g
cup 34cals / 80 g
teaspoon 1cals / 1.7 g
2 tbsp 4cals / 10 g
oz 12cals / 28.3 g
```

#### 33. Seaweed laver raws

**デフォルト単位**: `sheet`

**デフォルトカロリー**: `1cals`

**Serving情報の単位（最初の5件）**:
```
10 sheets 9cals / 26 g
gram 0cals / 1 g
2 tbsp 4cals / 10 g
cup 28cals / 80 g
oz 10cals / 28.3 g
```

#### 34. Seaweed wakame raw

**デフォルト単位**: `tbsp`

**デフォルトカロリー**: `2cals`

**Serving情報の単位（最初の5件）**:
```
2 tbsp 5cals / 10 g
gram 0cals / 1 g
cup 36cals / 80 g
oz 13cals / 28.3 g
teaspoon 1cals / 1.7 g
```

#### 35. Squash butternut frozen unprepared (12 oz)

**デフォルト単位**: `package`

**デフォルトカロリー**: `194cals`

**Serving情報の単位（最初の5件）**:
```
gram 1cals / 1 g
oz 16cals / 28.3 g
package (12 oz) 194cals / 340 g
package (4 lb) 1,034cals / 1,814 g
```

---

## 📈 パターン分析

### デフォルト単位別の不一致件数

| デフォルト単位 | 件数 | 例 |
|--------------|------|-----|
| `cup` | 50件 | Black beans canned no salt added |
| `oz` | 31件 | Cottage cheese whole 4% milkfat |
| `tbsp` | 11件 | Salad dressing Greek |
| `fillet` | 9件 | Halibut raw |
| `package` | 8件 | Shirataki noodles |
| `tsp` | 6件 | Queso cotija cheese |
| `unit` | 5件 | Chicken breast baked boneless skinless (yield from 1 lb ready-to-cook chicken) |
| `fl oz` | 3件 | Beer 7.7% ABV |
| `ml` | 3件 | Rice vinegar |
| `piece` | 3件 | Nougat |

---

## ✅ 推奨対処

### カロリー不一致（4件）

これらはマニュアルスクレイピングの際のデータ誤りの可能性があります：
- 再度MyNetDiaryから正しいデータをスクレイピング
- または栄養情報のServing SizeとCaloriesを正として使用

### 単位が見つからない（181件）

これらはMyNetDiaryのデフォルト単位とServing情報の表記揺れです：

**対処方法**:
1. **部分一致検索**: デフォルト単位 `cup` で Serving情報の `0.5 cup` などを検索
2. **数学的計算**: `0.5 cup 110cals` から `cup 220cals` を算出
3. **栄養情報のServing Sizeを正とする**: 栄養情報の単位とカロリーを使用

### セクション不明（1件）

- ファイル内容を直接確認して修正
