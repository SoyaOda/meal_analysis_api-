# FNDDSデータベース食品カテゴリー分析レポート

## 📅 分析日時
2025-10-12

## 📊 分析結果サマリー

### 総食品数: **5,432件**

| カテゴリー | 件数 | 割合 |
|----------|------|------|
| **複合料理 (Composite Dishes)** | **3,829件** | **70.5%** |
| **基本食材 (Basic Ingredients)** | **1,433件** | **26.4%** |
| **調理済み食材 (Prepared Ingredients)** | **170件** | **3.1%** |
| 分類不能 (Unknown) | 0件 | 0.0% |

---

## 🔍 各カテゴリーの定義

### 1. 複合料理 (Composite Dishes) - 3,829件 (70.5%)

**定義**: `inputFoods`に2つ以上の材料が含まれている食品

**特徴**:
- 平均材料数: **4.4種類**
- 最小材料数: 2種類
- 最大材料数: 20種類

**材料数別分布（上位10）**:
```
 2種類: 1,039件
 3種類:   834件
 4種類:   577件
 5種類:   396件
 6種類:   291件
 7種類:   221件
 8種類:   142件
 9種類:    82件
10種類:    68件
11種類:    59件
```

**サンプル例**:
- Oat milk (8種類の材料)
- Soy milk, chocolate (3種類の材料)
- Caesar salad, with romaine, no dressing
- Beef and vegetable stew
- Chicken noodle soup
- Pizza, cheese
- Yogurt, low fat milk, plain (2種類の材料)

**注意事項**:
- "Milk, NFS"のような単純な食品でも、FNDDSのデータ構造上、inputFoodsに複数のエントリーがある場合は複合料理に分類される
- これは、FNDDSが栄養計算のためにレシピ情報を詳細に保持しているため

### 2. 基本食材 (Basic Ingredients) - 1,433件 (26.4%)

**定義**:
- `inputFoods`がない、または1つのみ
- 調理方法を示すキーワードが含まれていない
- 生・未加工の食材

**サンプル例**:
- Milk, whole
- Milk, reduced fat (2%)
- Milk, fat free (skim)
- Buttermilk
- Goat milk
- Milk, evaporated, whole
- Milk, condensed, sweetened
- Eggs, raw
- Chicken breast, skinless, raw
- Broccoli, raw

**特徴**:
- 主に生の食材
- 加工度が低い
- 単一の食品

### 3. 調理済み食材 (Prepared Ingredients) - 170件 (3.1%)

**定義**:
- `inputFoods`が1つのみ（単一材料）
- 調理方法を示すキーワードが含まれている
  - boiled, fried, baked, roasted, grilled, steamed, cooked, prepared, etc.

**サンプル例**:
- Beef, bacon, cooked
- Canadian bacon, cooked
- Pork bacon, smoked or cured, cooked
- Chicken breast, baked or broiled, skin eaten, from pre-cooked
- Chicken drumstick, baked or broiled, skin not eaten, from pre-cooked
- Mozzarella sticks, breaded, baked, or fried
- Pork, pig's feet, pickled

**特徴**:
- 単一食材だが調理済み
- ベーコン、調理済み肉類が多い
- "cooked", "baked", "fried"などの調理方法が明記されている

---

## 📈 分析からわかること

### 1. FNDDSは複合料理が主体
- **70.5%が複合料理**であり、FNDDSは実際の食事で摂取される料理を重視している
- SR Legacyの28.7%と比較すると、より実用的な食事データベース

### 2. レシピ情報の詳細さ
- 平均4.4種類の材料が含まれる複合料理が中心
- 最大20種類もの材料を含む複雑な料理も存在

### 3. 基本食材も豊富
- 26.4%（1,433件）の基本食材が含まれる
- 生の肉、野菜、果物、乳製品など

### 4. 調理済み食材は少数
- 3.1%（170件）のみ
- 主にベーコンなどの加工肉類

---

## 🎯 search_name/description生成への影響

### 複合料理の場合
- **inputFoodsから主要材料を抽出**する必要がある
- 例: "Caesar salad, with romaine, no dressing"
  - search_name: "Caesar salad"
  - description: "romaine, no dressing"

### 基本食材の場合
- **シンプルな名称変換**で対応可能
- 例: "Milk, reduced fat (2%)"
  - search_name: "Milk"
  - description: "reduced fat, 2%"

### 調理済み食材の場合
- **調理方法をdescriptionに移動**
- 例: "Beef, bacon, cooked"
  - search_name: "Beef bacon"
  - description: "cooked"

---

## 💡 LLMベース生成の推奨理由

1. **複合料理の複雑性**: 70.5%が複合料理で、ルールベースでは対応困難
2. **材料数の多様性**: 2種類〜20種類まで多様
3. **文脈理解の必要性**: "or"が調理方法の選択肢なのか、代替名なのかの判断
4. **既存インフラ**: DeepInfraService実装済み

---

## 📝 次のステップ

1. ✅ **カテゴリー分析完了**
2. ⏳ **LLMベースのsearch_name/description生成プロトタイプ作成**
3. ⏳ **10件テストで品質評価**
4. ⏳ **全5,432件をバッチ処理**

---

## 📂 関連ファイル

- **FNDDSデータ**: `/Users/odasoya/meal_analysis_api_2/usda_database/surveyDownload.json`
- **分析スクリプト**: `/tmp/analyze_fndds_food_categories.py`
- **実現可能性レポート**: `/tmp/deepinfra_feasibility_report.md`
