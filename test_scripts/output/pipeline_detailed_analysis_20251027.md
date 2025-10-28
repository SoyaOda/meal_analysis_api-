# 30%以上カロリー誤差の詳細Pipeline分析レポート

**生成日時**: 2025年10月27日 14:51:40
**テスト画像総数**: 50

## 📊 高誤差画像サマリー

- **30%以上誤差の画像総数**: 29
- **全3プロンプトで30%以上誤差**: 3件

### プロンプト別30%以上誤差件数

- **v6_balanced**: 8件
- **v6_corrected**: 11件
- **v6_enhanced**: 21件

## 🔴 Critical: 全プロンプトで30%以上誤差の画像

### 画像: test_food25.jpg

#### 各プロンプトのエラー率

| プロンプト | 予測カロリー | ラベルカロリー | 誤差率 |
|-----------|------------|-------------|--------|
| v6_balanced | 1047.3 kcal | 748.1 kcal | +40.0% |
| v6_corrected | 1367.6 kcal | 748.1 kcal | +82.8% |
| v6_enhanced | 1859.4 kcal | 748.1 kcal | +148.5% |

#### Pipeline分析: v6_balanced

**ラベルアイテム（正解データ）:**

1. **main_food**: hot dog with bun - 120g (Cal: 348.0, Pro: 13.2g, Fat: 19.2g, Carbs: 28.8g)
2. **extra**: beef chili - 90g (Cal: 105.3, Pro: 6.6g, Fat: 3.4g, Carbs: 11.3g)
3. **extra**: cheddar cheese - 20g (Cal: 80.4, Pro: 5.0g, Fat: 6.6g, Carbs: 0.3g)
4. **main_food**: potato chips - 40g (Cal: 214.4, Pro: 2.8g, Fat: 14.0g, Carbs: 21.2g)

**ラベル総重量**: 270g

**栄養素比較:**

| 栄養素 | 予測値 | ラベル値 | 誤差 |
|--------|--------|----------|------|
| calories | 1047.3 | 748.1 | +40.0% |
| protein_g | 45.1 | 27.6 | +63.4% |
| fat_g | 76.9 | 43.2 | +78.0% |
| carbs_g | 46.1 | 61.6 | -25.2% |

---

#### Pipeline分析: v6_corrected

**ラベルアイテム（正解データ）:**

1. **main_food**: hot dog with bun - 120g (Cal: 348.0, Pro: 13.2g, Fat: 19.2g, Carbs: 28.8g)
2. **extra**: beef chili - 90g (Cal: 105.3, Pro: 6.6g, Fat: 3.4g, Carbs: 11.3g)
3. **extra**: cheddar cheese - 20g (Cal: 80.4, Pro: 5.0g, Fat: 6.6g, Carbs: 0.3g)
4. **main_food**: potato chips - 40g (Cal: 214.4, Pro: 2.8g, Fat: 14.0g, Carbs: 21.2g)

**ラベル総重量**: 270g

**栄養素比較:**

| 栄養素 | 予測値 | ラベル値 | 誤差 |
|--------|--------|----------|------|
| calories | 1367.6 | 748.1 | +82.8% |
| protein_g | 41.9 | 27.6 | +51.8% |
| fat_g | 84.3 | 43.2 | +95.1% |
| carbs_g | 114.6 | 61.6 | +86.0% |

---

#### Pipeline分析: v6_enhanced

**ラベルアイテム（正解データ）:**

1. **main_food**: hot dog with bun - 120g (Cal: 348.0, Pro: 13.2g, Fat: 19.2g, Carbs: 28.8g)
2. **extra**: beef chili - 90g (Cal: 105.3, Pro: 6.6g, Fat: 3.4g, Carbs: 11.3g)
3. **extra**: cheddar cheese - 20g (Cal: 80.4, Pro: 5.0g, Fat: 6.6g, Carbs: 0.3g)
4. **main_food**: potato chips - 40g (Cal: 214.4, Pro: 2.8g, Fat: 14.0g, Carbs: 21.2g)

**ラベル総重量**: 270g

**栄養素比較:**

| 栄養素 | 予測値 | ラベル値 | 誤差 |
|--------|--------|----------|------|
| calories | 1859.4 | 748.1 | +148.5% |
| protein_g | 45.1 | 27.6 | +63.4% |
| fat_g | 111.4 | 43.2 | +157.9% |
| carbs_g | 174.8 | 61.6 | +183.8% |

---


### 画像: test_food3.jpg

#### 各プロンプトのエラー率

| プロンプト | 予測カロリー | ラベルカロリー | 誤差率 |
|-----------|------------|-------------|--------|
| v6_balanced | 570.5 kcal | 1000.5 kcal | -43.0% |
| v6_corrected | 615.7 kcal | 1000.5 kcal | -38.5% |
| v6_enhanced | 639.6 kcal | 1000.5 kcal | -36.1% |

#### Pipeline分析: v6_balanced

**ラベルアイテム（正解データ）:**

1. **main_food**: beef steak - 180g (Cal: 450.0, Pro: 46.8g, Fat: 30.6g, Carbs: 0.0g)
2. **extra**: tomato onion relish - 30g (Cal: 18.0, Pro: 0.3g, Fat: 0.6g, Carbs: 3.0g)
3. **main_food**: roasted potatoes - 220g (Cal: 330.0, Pro: 5.5g, Fat: 9.9g, Carbs: 59.4g)
4. **main_food**: asparagus - 130g (Cal: 32.5, Pro: 3.8g, Fat: 0.5g, Carbs: 6.0g)
5. **extra**: garlic aioli - 25g (Cal: 170.0, Pro: 0.3g, Fat: 18.8g, Carbs: 0.3g)

**ラベル総重量**: 585g

**栄養素比較:**

| 栄養素 | 予測値 | ラベル値 | 誤差 |
|--------|--------|----------|------|
| calories | 570.5 | 1000.5 | -43.0% |
| protein_g | 61.0 | 56.7 | +7.6% |
| fat_g | 26.5 | 60.4 | -56.1% |
| carbs_g | 23.5 | 68.7 | -65.8% |

---

#### Pipeline分析: v6_corrected

**ラベルアイテム（正解データ）:**

1. **main_food**: beef steak - 180g (Cal: 450.0, Pro: 46.8g, Fat: 30.6g, Carbs: 0.0g)
2. **extra**: tomato onion relish - 30g (Cal: 18.0, Pro: 0.3g, Fat: 0.6g, Carbs: 3.0g)
3. **main_food**: roasted potatoes - 220g (Cal: 330.0, Pro: 5.5g, Fat: 9.9g, Carbs: 59.4g)
4. **main_food**: asparagus - 130g (Cal: 32.5, Pro: 3.8g, Fat: 0.5g, Carbs: 6.0g)
5. **extra**: garlic aioli - 25g (Cal: 170.0, Pro: 0.3g, Fat: 18.8g, Carbs: 0.3g)

**ラベル総重量**: 585g

**栄養素比較:**

| 栄養素 | 予測値 | ラベル値 | 誤差 |
|--------|--------|----------|------|
| calories | 615.7 | 1000.5 | -38.5% |
| protein_g | 60.1 | 56.7 | +6.0% |
| fat_g | 20.8 | 60.4 | -65.6% |
| carbs_g | 45.4 | 68.7 | -33.9% |

---

#### Pipeline分析: v6_enhanced

**ラベルアイテム（正解データ）:**

1. **main_food**: beef steak - 180g (Cal: 450.0, Pro: 46.8g, Fat: 30.6g, Carbs: 0.0g)
2. **extra**: tomato onion relish - 30g (Cal: 18.0, Pro: 0.3g, Fat: 0.6g, Carbs: 3.0g)
3. **main_food**: roasted potatoes - 220g (Cal: 330.0, Pro: 5.5g, Fat: 9.9g, Carbs: 59.4g)
4. **main_food**: asparagus - 130g (Cal: 32.5, Pro: 3.8g, Fat: 0.5g, Carbs: 6.0g)
5. **extra**: garlic aioli - 25g (Cal: 170.0, Pro: 0.3g, Fat: 18.8g, Carbs: 0.3g)

**ラベル総重量**: 585g

**栄養素比較:**

| 栄養素 | 予測値 | ラベル値 | 誤差 |
|--------|--------|----------|------|
| calories | 639.6 | 1000.5 | -36.1% |
| protein_g | 30.4 | 56.7 | -46.4% |
| fat_g | 38.3 | 60.4 | -36.6% |
| carbs_g | 45.5 | 68.7 | -33.8% |

---


### 画像: test_food45.jpg

#### 各プロンプトのエラー率

| プロンプト | 予測カロリー | ラベルカロリー | 誤差率 |
|-----------|------------|-------------|--------|
| v6_balanced | 1422.4 kcal | 791.2 kcal | +79.8% |
| v6_corrected | 1534.5 kcal | 791.2 kcal | +93.9% |
| v6_enhanced | 1505.2 kcal | 791.2 kcal | +90.2% |

#### Pipeline分析: v6_balanced

**ラベルアイテム（正解データ）:**

1. **main_food**: prosciutto and mozzarella sandwich - 220g (Cal: 550.0, Pro: 26.4g, Fat: 24.2g, Carbs: 57.2g)
2. **main_food**: potato chips - 45g (Cal: 241.2, Pro: 3.1g, Fat: 15.8g, Carbs: 22.9g)

**ラベル総重量**: 265g

**栄養素比較:**

| 栄養素 | 予測値 | ラベル値 | 誤差 |
|--------|--------|----------|------|
| calories | 1422.4 | 791.2 | +79.8% |
| protein_g | 50.1 | 29.5 | +69.8% |
| fat_g | 68.7 | 40.0 | +71.8% |
| carbs_g | 157.6 | 80.1 | +96.8% |

---

#### Pipeline分析: v6_corrected

**ラベルアイテム（正解データ）:**

1. **main_food**: prosciutto and mozzarella sandwich - 220g (Cal: 550.0, Pro: 26.4g, Fat: 24.2g, Carbs: 57.2g)
2. **main_food**: potato chips - 45g (Cal: 241.2, Pro: 3.1g, Fat: 15.8g, Carbs: 22.9g)

**ラベル総重量**: 265g

**栄養素比較:**

| 栄養素 | 予測値 | ラベル値 | 誤差 |
|--------|--------|----------|------|
| calories | 1534.5 | 791.2 | +93.9% |
| protein_g | 54.8 | 29.5 | +85.8% |
| fat_g | 78.2 | 40.0 | +95.5% |
| carbs_g | 157.0 | 80.1 | +96.0% |

---

#### Pipeline分析: v6_enhanced

**ラベルアイテム（正解データ）:**

1. **main_food**: prosciutto and mozzarella sandwich - 220g (Cal: 550.0, Pro: 26.4g, Fat: 24.2g, Carbs: 57.2g)
2. **main_food**: potato chips - 45g (Cal: 241.2, Pro: 3.1g, Fat: 15.8g, Carbs: 22.9g)

**ラベル総重量**: 265g

**栄養素比較:**

| 栄養素 | 予測値 | ラベル値 | 誤差 |
|--------|--------|----------|------|
| calories | 1505.2 | 791.2 | +90.2% |
| protein_g | 39.8 | 29.5 | +34.9% |
| fat_g | 81.8 | 40.0 | +104.5% |
| carbs_g | 159.9 | 80.1 | +99.6% |

---


## 🟡 2プロンプトで30%以上誤差の画像

- **test_food24.jpg**: v6_balanced, v6_enhanced (平均誤差: 42.5%)
- **test_food31.jpg**: v6_balanced, v6_corrected (平均誤差: 47.4%)
- **test_food33.jpg**: v6_corrected, v6_enhanced (平均誤差: 61.6%)
- **test_food48.jpg**: v6_balanced, v6_enhanced (平均誤差: 48.3%)
- **test_food6.jpg**: v6_corrected, v6_enhanced (平均誤差: 53.6%)

## 🟢 1プロンプトのみ30%以上誤差の画像

### v6_balanced: 2件

- **test_food39.jpg**: -51.4%
- **test_food37.jpg**: +36.8%

### v6_corrected: 5件

- **test_food49.jpg**: +55.4%
- **test_food21.jpg**: +43.2%
- **test_food28.jpg**: -36.2%
- **test_food14.jpg**: -31.0%
- **test_food4.jpg**: +30.3%

### v6_enhanced: 14件

- **test_food19.jpg**: +90.4%
- **test_food18.jpg**: +69.8%
- **test_food40.jpg**: -67.2%
- **test_food44.jpg**: +55.8%
- **test_food9.jpg**: +50.3%
- **test_food13.jpg**: +47.4%
- **test_food47.jpg**: +44.7%
- **test_food27.jpg**: -43.5%
- **test_food8.jpg**: +41.8%
- **test_food17.jpg**: -41.4%
- **test_food36.jpg**: +40.5%
- **test_food50.jpg**: -34.1%
- **test_food38.jpg**: +32.5%
- **test_food7.jpg**: -30.7%
