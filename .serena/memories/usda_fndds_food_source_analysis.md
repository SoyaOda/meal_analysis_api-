# USDA FNDDS - 食品の入手先（Food Source）分析

## 📋 概要

USDA Survey (FNDDS) データでは、**同じ食品でも入手先（food source）によって異なるエントリ**が存在します。これは、食品がどこから入手されたかによって栄養成分が大きく異なるためです。

---

## 🔍 "from restaurant" と "from frozen" の違い

### 基本的な意味

| 表記 | 意味 | 例 |
|------|------|-----|
| **from restaurant / from fast food** | レストラン・ファストフード店で提供される食品 | Pizza, cheese, from restaurant or fast food, thin crust |
| **from frozen** | 店舗で購入した冷凍食品を家庭で調理したもの | Pizza, cheese, from frozen, thin crust |
| **from home recipe** | 家庭で材料から調理したもの | Bread, made from home recipe |
| **from school** | 学校給食で提供されるもの | Chicken tenders, from school lunch |

### なぜ対になっているのか？

NHANES（国民健康栄養調査）の「What We Eat in America」調査では、参加者が**24時間食事記録**を行います。その際、以下の情報を収集：

1. **何を食べたか**（食品の種類）
2. **どこで入手したか**（food source）
3. **どこで食べたか**（at home / away from home）

**重要**: 同じ食品でも、入手先によって栄養成分が異なるため、正確な栄養摂取量を把握するには入手先の区別が必須です。

---

## 📊 FNDDS データにおける入手先パターン

### 件数の内訳

| 入手先 | 件数 | 説明 |
|--------|------|------|
| **Restaurant/Fast Food** | 107件 | レストラン・ファストフードで提供 |
| **Home Recipe** | 49件 | 家庭で材料から調理 |
| **Frozen** | 30件 | 店舗で購入した冷凍食品 |
| **School** | 19件 | 学校給食 |

---

## 🍕 具体例：Pizza, cheese, thin crust

### 栄養成分の比較（100gあたり）

| 栄養素 | Restaurant/Fast Food版 | Frozen版 | 差異 |
|--------|----------------------|---------|------|
| **Food Code** | 58106220 | 58106200 | - |
| **Energy (kcal)** | 266 | 263 | -3 |
| **Protein (g)** | 11.4 | 11.9 | +0.5 |
| **Fat (g)** | 9.69 | 11.1 | +1.41 |
| **Carbohydrate (g)** | 33.3 | 28.8 | -4.5 |
| **Sodium (mg)** | 540 | 471 | -69 |

### 考察

- **レストラン版**: 炭水化物が多く、ナトリウムが高い
- **冷凍版**: 脂質がやや多いが、ナトリウムは低い

→ **レストランとメーカーの違い**:
  - レストランは味付けを濃くする傾向（ナトリウム↑）
  - 冷凍食品メーカーは長期保存を考慮した配合

---

## 🍗 具体例：Chicken Breast（鶏むね肉）

### 入手先による分類

| Food Code | Description | 入手先 |
|-----------|-------------|--------|
| 24122130 | Chicken breast, baked, broiled, or roasted, skin eaten, **from raw** | 生肉を購入して家庭調理 |
| 24122140 | Chicken breast, baked or broiled, skin eaten, **from pre-cooked** | 調理済みを購入して再加熱 |
| 24122150 | Chicken breast, baked or broiled, skin eaten, **from fast food / restaurant** | レストラン・ファストフード |

---

## 🍟 具体例：French Fries（フライドポテト）

### 入手先による分類

| Food Code | Description | 入手先/調理方法 |
|-----------|-------------|----------------|
| 71401010 | Potato, french fries, **from fresh, fried** | 生のジャガイモから揚げた |
| 71401020 | Potato, french fries, **from frozen, baked** | 冷凍フライドポテトをオーブンで調理 |
| 71401032 | Potato, french fries, **from frozen, fried** | 冷凍フライドポテトを揚げた |
| 71401030 | Potato, french fries, **fast food** | ファストフードで購入 |
| 71401031 | Potato, french fries, **restaurant** | レストランで購入 |

---

## 🔬 研究結果：入手先による栄養的な違い

### USDA/CDC の研究結果

#### **レストラン・ファストフード vs 家庭調理**

**レストラン・ファストフード食品の特徴**:
- ❌ **低い**: 食物繊維、カルシウム、鉄
- ❌ **高い**: 飽和脂肪、ナトリウム
- ❌ **少ない**: 果物、乳製品、全粒穀物、ナッツ、種子
- ❌ **多い**: 精製穀物

**ただし**:
- ✅ Added sugars（添加糖）は家庭調理より低い場合もある
- ✅ 野菜、肉、鶏肉、卵、シーフードは豊富

#### **冷凍食品 vs 生鮮食品**

**重要な発見**:
- 「**生鮮食品の方が栄養価が高い**」という一般的な信念は必ずしも正しくない
- 5日間冷蔵保存した生鮮食品よりも、**冷凍食品の方が栄養価が高い場合もある**
- 冷凍野菜は収穫直後に急速冷凍されるため、ビタミンやミネラルが保存される

---

## 🎯 なぜこの区別が重要なのか？

### 1. **公衆衛生政策の立案**
- アメリカ人の実際の食生活を正確に把握
- 食事の質（diet quality）の評価
- 栄養改善プログラムの効果測定

### 2. **栄養疫学研究**
- 疾病リスクと食事パターンの関連性を分析
- 特定の食品入手先と健康アウトカムの関係を調査

### 3. **個人の栄養管理**
- より正確なカロリー・栄養素摂取量の計算
- 外食が多い人と家庭調理中心の人では同じ食品でも栄養摂取量が異なる

### 4. **食品産業への示唆**
- レストラン業界：ナトリウム削減、栄養バランス改善の必要性
- 冷凍食品業界：栄養価の高さをアピール可能

---

## 📊 データ活用の実例

### WWEIA/NHANES 調査フロー

```
参加者の24時間食事記録
    ↓
「何を食べたか」→ FNDDS食品コード
    ↓
「どこで入手したか」→ Food Source
    ├─ Restaurant/Fast Food
    ├─ Store (Frozen/Fresh)
    ├─ School
    └─ Other
    ↓
正確な栄養摂取量の推定
    ↓
公衆衛生政策・研究に活用
```

### Individual Foods File の情報

NHANES の Individual Foods File には以下が含まれる：
- ✅ 食品コード（USDA food codes）
- ✅ グラム量
- ✅ エネルギー・栄養素摂取量
- ✅ **食品の入手先（source of food）**
- ✅ **家で食べたか否か（eaten at home）**
- ✅ 食事の時刻・機会

---

## 💡 プロジェクトでの活用方法

### 現在の状況
- **使用中**: `usda_data_processing/output/usda_raw_ingredients_split_cleaned.json`
- 食品コード（foodCode）ベースでマッチング

### 改善の提案

#### 1. **入手先を考慮した栄養分析**
```python
# 例：ユーザーが「ピザを食べた」と報告
# → 「どこで食べた？」を追加で質問
if pizza:
    if source == "restaurant":
        use_food_code("58106220")  # Restaurant版
    elif source == "frozen":
        use_food_code("58106200")  # Frozen版
```

#### 2. **ユーザーの食生活パターン分析**
- 外食頻度に基づいた栄養アドバイス
- 「外食が多い → ナトリウム摂取量に注意」

#### 3. **より正確なカロリー計算**
- 同じ「チキンブレスト」でも入手先で栄養素が異なる
- レストラン版は調理油が多い傾向

---

## 📌 重要なポイント

### ✅ 覚えておくべきこと

1. **"from restaurant" と "from frozen" は入手先（food source）を示す**
   - 同じ食品でも栄養成分が異なる

2. **レストラン食品の特徴**
   - ナトリウムが高い（塩分多め）
   - 飽和脂肪が多い
   - 食物繊維が少ない

3. **冷凍食品は悪くない**
   - 生鮮食品と栄養価はほぼ同等
   - 保存により栄養素が失われた生鮮食品より優れる場合も

4. **NHANES/WWEIA 調査の重要性**
   - 実際の食生活データに基づく
   - 食品の入手先情報が含まれる
   - 公衆衛生政策の基礎データ

---

## 🔗 参考資料

- **USDA FoodData Central**: https://fdc.nal.usda.gov/
- **NHANES**: https://www.cdc.gov/nchs/nhanes/
- **WWEIA Database**: https://agdatacommons.nal.usda.gov/articles/dataset/What_We_Eat_In_America_WWEIA_Database/
- **FNDDS Documentation**: https://www.ars.usda.gov/northeast-area/beltsville-md-bhnrc/beltsville-human-nutrition-research-center/food-surveys-research-group/docs/fndds-download-databases/
- **ERS - Dietary Quality by Food Source**: https://www.ers.usda.gov/publications/pub-details?pubid=105955

---

## 📝 まとめ

USDA FNDDS における "from restaurant" と "from frozen" の区別は、**食品の入手先による栄養成分の違いを正確に反映する**ための重要な分類です。

これにより：
- ✅ より正確な栄養摂取量の推定が可能
- ✅ 公衆衛生政策の立案に活用
- ✅ 栄養疫学研究に貢献
- ✅ 個人の栄養管理の精度向上

食事分析APIを開発する際は、この「入手先」の違いを考慮することで、より正確で有用な栄養情報を提供できます。
