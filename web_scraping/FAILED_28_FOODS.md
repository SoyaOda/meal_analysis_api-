# 28失敗食材リスト

## 📊 概要

**失敗理由:** `insufficient_serving`（有効なserving数不足: 0個）

**原因:** 生データ（comprehensive_food_collection_all_20251001_124446.json）のserving_optionsに、HTML/CSS/JavaScriptゴミのみで有効なservingデータが含まれていない。

**総数:** 28食材

---

## 📋 カテゴリ別リスト

### 🌾 Grains & Grain Products (1食材)
1. Cornstarch, cup 488cals

### 🧂 Spices & Herbs (5食材)
2. Baker's yeast active dry, tbsp 39cals
3. Baker's yeast compressed, cake (0.6 oz) 18cals
4. Cardamom, tbsp, ground 18cals
5. Paprika, tbsp 19cals
6. Za'atar or za'atar spice blend, tsp 0cals

### 🧂 Seasonings (2食材)
7. Salt, cup 0cals
8. Sea salt iodized, gram 0cals

### 🐟 Fish & Seafood (1食材)
9. Sea bass mixed species raw, fillet 125cals

### 🫘 Beans & Peas (2食材)
10. Hummus, cup 583cals
11. Natto, cup 369cals

### 🥛 Dairy & Substitutes (1食材)
12. Goat's milk, cup 168cals

### 🥫 Condiments, Dressings & Sauces (2食材)
13. Guacamole, serving 64cals
14. Salsa, cup 75cals

### 🍯 Sweets & Sweeteners (3食材)
15. Honey, cup 1,031cals
16. Jellies, 1 tbsp 58cals
17. Molasses, cup 977cals

### 🍷 Beverages (5食材)
18. Champagne, serving 82cals
19. Cognac, serving 231cals
20. Liqueur, serving 284cals
21. Martini, serving 188cals
22. Water, cup 0cals

### 🍉 Fruit (1食材)
23. Watermelon, cup, balls 46cals

### 🌰 Nuts & Seeds (5食材)
24. Flaxseeds, cup, whole 897cals
25. Walnuts dry roasted with salt, oz 182cals
26. Walnuts glazed, oz 142cals
27. Walnuts raw, cup, chopped 765cals
28. Watermelon seed kernels (shelled) dried, cup 602cals

---

## 🔧 対策オプション

### オプション1: 再スクレイピング
バックグラウンドで実行中の`retry_failed_foods_main.py`が対応中の可能性あり。

**確認方法:**
```bash
# プロセス状態確認
ps aux | grep retry_failed

# 最新の収集データ確認
ls -lt data/comprehensive*.json | head -5
```

### オプション2: 手動食材として追加
Stemmed DBから100g栄養情報を取得して手動で追加。

**手順:**
1. `/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed.json`から該当食材の100g栄養を検索
2. 手動食材フォーマットに変換
3. `manual_foods/`に追加

### オプション3: serving_optionsから代替計算
nutrition_factsと組み合わせて100g栄養を推定。

---

## 📈 優先順位

### 高優先度（よく使用される食材）
- ✅ **Water** - 最重要（0カロリーなので手動追加が容易）
- ✅ **Salt** - 調味料として重要
- ✅ **Honey** - 甘味料として一般的
- ✅ **Cornstarch** - 料理によく使用

### 中優先度（一般的な食材）
- Goat's milk
- Hummus
- Salsa
- Guacamole
- Watermelon

### 低優先度（特殊な食材）
- Za'atar or za'atar spice blend
- Baker's yeast active/compressed
- Natto
- Watermelon seed kernels
- アルコール飲料（Champagne, Cognac, Liqueur, Martini）

---

## 📝 次のアクション

1. ✅ バックグラウンドretryプロセスの状態確認
2. ✅ 高優先度4食材の手動追加（Water, Salt, Honey, Cornstarch）
3. ✅ 中優先度食材の再スクレイピング結果待ち
4. ✅ 低優先度食材は必要に応じて対応

---

**作成日:** 2025-10-03
**最終更新:** 2025-10-03
