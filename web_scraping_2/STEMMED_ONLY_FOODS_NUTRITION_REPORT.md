# 📊 Stemmed Only Foods 栄養情報・Serving情報レポート

Stemmed DBにのみ存在する25件の食材の包括的な栄養情報とserving size変換情報

---

## 📋 概要

| 項目 | 値 |
|------|-----|
| **処理日時** | 2025-10-09 |
| **対象食材数** | 25件 |
| **生成Serving Options** | 181個 |
| **平均Serving Options/食材** | 7.2個 |
| **データソース** | 既存100g栄養情報 + 標準serving size換算 |

---

## 🎯 処理内容

### 実施したこと

1. **Web検索による情報収集**
   - MyNetDiary等の栄養データベースでserving size情報を調査
   - 標準的なserving sizeの重量換算を確認

2. **食材タイプの分類**
   - 25件の食材を11の食材タイプに分類
   - 各タイプに応じた適切なserving sizeを定義

3. **Serving Options の自動生成**
   - 既存の100g栄養情報を基に計算
   - 各serving sizeの栄養情報を自動算出

### 食材タイプ別内訳

| 食材タイプ | 件数 | 平均Serving Options |
|-----------|------|-------------------|
| **Oil/Fat（油脂類）** | 6件 | 8.0個 |
| **Nut Butter（ナッツバター）** | 6件 | 7.0個 |
| **Butter（バター・マーガリン）** | 3件 | 9.0個 |
| **Meat（肉類）** | 2件 | 6.0個 |
| **Sauce/Dressing（ソース・ドレッシング）** | 2件 | 9.0個 |
| **Beans（豆類）** | 1件 | 4.0個 |
| **Tofu（豆腐）** | 1件 | 6.0個 |
| **Pesto（ペスト）** | 1件 | 7.0個 |
| **Pie Crust（パイクラスト）** | 1件 | 4.0個 |
| **Salt（塩）** | 1件 | 6.0個 |
| **Honey（蜂蜜）** | 1件 | 7.0個 |

---

## 🍽️ 詳細データ

### 1. 肉類（Meat）- 2件

#### 1.1 Beef brisket flat cut trimmed to 1/8" fat raw
- **ID**: 10000000638
- **100gあたり**: 277 kcal, Protein 17.9g, Fat 22.2g, Carbs 0g
- **Serving Options（6個）**:
  - gram (1g): 2.77 kcal
  - oz (28.35g): 78.53 kcal
  - 3 oz (85g): 235.44 kcal
  - 4 oz (113g): 313.0 kcal
  - 6 oz (170g): 470.88 kcal
  - lb (453.6g): 1256.43 kcal

#### 1.2 Beef top sirloin steak lean and fat trimmed to 1/8" raw
- **ID**: 10000000661
- **100gあたり**: 201 kcal, Protein 20.2g, Fat 12.7g, Carbs 0g
- **Serving Options（6個）**:
  - gram (1g): 2.01 kcal
  - oz (28.35g): 56.98 kcal
  - 3 oz (85g): 170.84 kcal
  - 4 oz (113g): 227.12 kcal
  - 6 oz (170g): 341.68 kcal
  - lb (453.6g): 911.68 kcal

---

### 2. 油脂類（Oil/Fat）- 6件

#### 2.1 Lard or pig fat
- **ID**: 10000000356
- **100gあたり**: 902 kcal, Fat 100g
- **Serving Options（8個）**:
  - ml (0.92g): 8.3 kcal
  - gram (1g): 9.02 kcal
  - tsp (4.5g): 40.59 kcal
  - tbsp (13.6g): 122.67 kcal
  - fl oz (29.6g): 266.98 kcal
  - cup (218g): 1966.25 kcal

#### 2.2 Chicken fat
- **ID**: 10000000349
- **100gあたり**: 900 kcal, Fat 99.8g
- **Serving Options（8個）**: 同上

#### 2.3 Cod liver fish oil
- **ID**: 10000000352
- **100gあたり**: 902 kcal, Fat 100g
- **Serving Options（8個）**: tsp (40.58 kcal), tbsp (122.65 kcal)

#### 2.4 Flaxseed or flax oil
- **ID**: 10000000354
- **100gあたり**: 884 kcal, Fat 100g
- **Serving Options（8個）**: tsp (39.78 kcal), tbsp (120.22 kcal)

#### 2.5 Sunflower oil
- **ID**: 10000000367
- **100gあたり**: 884 kcal, Fat 100g
- **Serving Options（8個）**: tsp (39.78 kcal), tbsp (120.22 kcal)

#### 2.6 Walnut oil
- **ID**: 10000000370
- **100gあたり**: 884 kcal, Fat 100g
- **Serving Options（8個）**: tsp (39.78 kcal), tbsp (120.22 kcal)

---

### 3. ナッツバター（Nut Butter）- 6件

#### 3.1 Almond butter without salt
- **ID**: 10000000697
- **100gあたり**: 614 kcal, Protein 20.8g, Fat 55.5g, Carbs 18.8g
- **Serving Options（7個）**:
  - gram (1g): 6.14 kcal
  - tsp (5.3g): 32.54 kcal
  - tbsp (16g): 98.24 kcal
  - oz (28.35g): 174.07 kcal
  - cup (256g): 1571.84 kcal

#### 3.2 Almond butter with salt
- **ID**: 10000000696
- **100gあたり**: 614 kcal, Protein 20.8g, Fat 55.5g, Carbs 18.8g
- **Serving Options（7個）**: 同上

#### 3.3 Peanut butter chunky without salt
- **ID**: 10000000732
- **100gあたり**: 589 kcal, Protein 24.0g, Fat 49.9g, Carbs 21.7g
- **Serving Options（7個）**:
  - tsp (5.3g): 31.22 kcal
  - tbsp (16g): 94.26 kcal
  - cup (256g): 1508.22 kcal

#### 3.4 Peanut butter chunky with salt
- **ID**: 10000000731
- **100gあたり**: 589 kcal, Protein 24.0g, Fat 49.9g, Carbs 21.7g
- **Serving Options（7個）**: 同上

#### 3.5 Peanut butter smooth with salt
- **ID**: 10000000733
- **100gあたり**: 589 kcal, Protein 24.0g, Fat 49.4g, Carbs 22.9g
- **Serving Options（7個）**:
  - tsp (5.3g): 31.22 kcal
  - tbsp (16g): 94.26 kcal

#### 3.6 Peanut butter smooth without salt
- **ID**: 10000000734
- **100gあたり**: 598 kcal, Protein 22.1g, Fat 51.4g, Carbs 22.5g
- **Serving Options（7個）**:
  - tsp (5.3g): 31.7 kcal
  - tbsp (16g): 95.69 kcal

---

### 4. バター・マーガリン（Butter）- 3件

#### 4.1 Butter salted
- **ID**: 10000000287
- **100gあたり**: 717 kcal, Protein 0.9g, Fat 81.1g
- **Serving Options（9個）**:
  - gram (1g): 7.17 kcal
  - tsp (4.7g): 33.71 kcal
  - pat (5g): 35.86 kcal
  - tbsp (14.2g): 101.84 kcal
  - oz (28.35g): 203.32 kcal
  - stick (113g): 810.41 kcal
  - cup (227g): 1628.0 kcal

#### 4.2 Butter whipped salted
- **ID**: 10000000289
- **100gあたり**: 718 kcal, Protein 0.7g, Fat 78.3g, Carbs 2.6g
- **Serving Options（9個）**: 同上（カロリーは微妙に異なる）

#### 4.3 Margarine regular soft salted
- **ID**: 10000000357
- **100gあたり**: 713 kcal, Fat 80.2g, Carbs 0.9g
- **Serving Options（9個）**:
  - tsp (4.7g): 33.52 kcal
  - tbsp (14.2g): 101.28 kcal
  - stick (113g): 805.93 kcal

---

### 5. ソース・ドレッシング（Sauce/Dressing）- 2件

#### 5.1 Salad dressing thousand islands
- **ID**: 10000000261
- **100gあたり**: 413 kcal, Protein 0.8g, Fat 40g, Carbs 14g
- **Serving Options（9個）**:
  - ml (1g): 4.13 kcal
  - tsp (5g): 20.66 kcal
  - tbsp (15g): 61.98 kcal
  - oz (28.35g): 117.14 kcal
  - fl oz (30g): 123.96 kcal
  - cup (240g): 991.68 kcal

#### 5.2 Salad dressing coleslaw
- **ID**: 10000000248
- **100gあたり**: 404 kcal, Protein 0.8g, Fat 34.5g, Carbs 22.4g
- **Serving Options（9個）**:
  - tsp (5g): 20.2 kcal
  - tbsp (15g): 60.6 kcal
  - cup (240g): 969.6 kcal

---

### 6. その他の食材

#### 6.1 Kidney beans raw
- **ID**: 10000000023
- **100gあたり**: 56 kcal, Protein 2.9g, Fat 1.4g, Carbs 7.9g
- **Serving Options（4個）**:
  - gram (1g): 0.56 kcal
  - oz (28.35g): 15.83 kcal
  - half cup (88.5g): 49.41 kcal
  - cup (177g): 98.83 kcal

#### 6.2 Tofu crumbles
- **ID**: 10000000042
- **100gあたり**: 189 kcal, Protein 14.3g, Fat 4.6g, Carbs 3.6g
- **Serving Options（6個）**:
  - oz (28.35g): 53.66 kcal
  - 3 oz (85g): 160.89 kcal
  - half block (198g): 374.79 kcal
  - cup (252g): 477.0 kcal
  - block (396g): 749.57 kcal

#### 6.3 Pesto prepared refrigerated
- **ID**: 10000000237
- **100gあたり**: 418 kcal, Protein 9.9g, Fat 37.6g, Carbs 9.9g
- **Serving Options（7個）**:
  - tsp (5g): 20.89 kcal
  - tbsp (15g): 62.68 kcal
  - cup (240g): 1002.86 kcal

#### 6.4 Pie crust baked from refrigerated
- **ID**: 10000000938
- **100gあたり**: 507 kcal, Protein 3.5g, Fat 28.3g, Carbs 58.1g
- **Serving Options（4個）**:
  - gram (1g): 5.07 kcal
  - slice (28g): 141.84 kcal
  - oz (28.35g): 143.61 kcal
  - crust (120g): 607.88 kcal

#### 6.5 Sea salt non-iodized
- **ID**: 10000000857
- **100gあたり**: 0 kcal
- **Serving Options（6個）**:
  - pinch (0.36g): 0 kcal
  - tsp (6g): 0 kcal
  - tbsp (18g): 0 kcal

#### 6.6 Honey
- **ID**: 10000000918
- **100gあたり**: 304 kcal, Protein 0.3g, Carbs 82.3g
- **Serving Options（7個）**:
  - tsp (7g): 21.29 kcal
  - tbsp (21g): 63.87 kcal
  - oz (28.35g): 86.22 kcal
  - cup (339g): 1031.0 kcal

---

## 📁 出力ファイル

### 生成されたファイル

1. **`stemmed_only_foods_enriched.json`** (詳細データ)
   - パス: `web_scraping_2/output/stemmed_only_foods_enriched.json`
   - 内容: 25件の食材×平均7.2個のserving options
   - サイズ: 約150KB

2. **`collect_stemmed_only_nutrition.py`** (生成スクリプト)
   - パス: `web_scraping_2/collect_stemmed_only_nutrition.py`
   - 機能: 既存栄養情報からserving optionsを自動生成

3. **`STEMMED_ONLY_FOODS_NUTRITION_REPORT.md`** (このレポート)

---

## 📊 データ構造

### JSON構造例

```json
{
  "id": "10000000356",
  "original_name": "Lard or pig fat",
  "search_name": ["Lard", "pig fat"],
  "description": "None",
  "nutrition": {
    "calories": 901.95,
    "protein": 0.0,
    "fat": 100.0,
    "carbs": 0.0
  },
  "serving_options": [
    {
      "unit": "tbsp",
      "grams": 13.6,
      "calories": 122.67,
      "protein": 0.0,
      "fat": 13.6,
      "carbs": 0.0
    },
    ...
  ],
  "base_nutrition_per_100g": { ... },
  "total_serving_options": 8,
  "food_type": "oil_fat",
  "data_source": "calculated_from_100g_nutrition",
  "enriched_at": "2025-10-09T18:22:14.169847"
}
```

---

## 🎯 標準Serving Sizeリファレンス

### 食材タイプ別標準Serving Size

| 食材タイプ | 標準Units | グラム換算 |
|-----------|----------|----------|
| **Meat（肉類）** | oz, 3oz, 4oz, 6oz, lb | 28.35g, 85g, 113g, 170g, 453.6g |
| **Oil/Fat（油脂）** | tsp, tbsp, fl oz, cup | 4.5g, 13.6g, 29.6g, 218g |
| **Nut Butter** | tsp, tbsp, oz, cup | 5.3g, 16g, 28.35g, 256g |
| **Butter** | tsp, tbsp, pat, stick, cup | 4.7g, 14.2g, 5g, 113g, 227g |
| **Sauce/Dressing** | tsp, tbsp, fl oz, cup | 5g, 15g, 30g, 240g |
| **Beans** | cup, half cup | 177g, 88.5g |
| **Tofu** | 3oz, block, half block, cup | 85g, 396g, 198g, 252g |
| **Honey** | tsp, tbsp, cup | 7g, 21g, 339g |
| **Salt** | pinch, tsp, tbsp | 0.36g, 6g, 18g |
| **Pie Crust** | slice, crust | 28g, 120g |
| **Pesto** | tsp, tbsp, cup | 5g, 15g, 240g |

---

## ✅ 品質保証

### 計算方法

すべてのserving optionsの栄養情報は、既存の100gあたり栄養情報を基に以下の式で計算されています：

```
栄養素値 = (100gあたり栄養素値) × (serving size グラム数) / 100
```

### 検証済み項目

- ✅ 25件すべての食材にserving options生成
- ✅ 食材タイプの適切な分類
- ✅ 標準serving sizeの正確なグラム換算
- ✅ 栄養情報の計算精度（小数点第2位まで）
- ✅ JSONフォーマットの整合性

---

## 🔄 使用方法

### Python での利用例

```python
import json

# データ読み込み
with open('web_scraping_2/output/stemmed_only_foods_enriched.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 特定食材のserving情報を取得
for food in data['foods']:
    if food['original_name'] == 'Lard or pig fat':
        print(f"{food['original_name']}")
        print(f"100gあたり: {food['base_nutrition_per_100g']['calories']} kcal")
        print("\nServing Options:")
        for serving in food['serving_options']:
            print(f"  {serving['unit']}: {serving['grams']}g = {serving['calories']} kcal")
```

### 特定unitの栄養情報取得

```python
def get_nutrition_by_unit(food_data, unit_name):
    """指定unitの栄養情報を取得"""
    for serving in food_data['serving_options']:
        if serving['unit'] == unit_name:
            return serving
    return None

# 例: ラードの大さじ1の栄養情報
lard = next(f for f in data['foods'] if f['id'] == '10000000356')
tbsp_info = get_nutrition_by_unit(lard, 'tbsp')
print(f"ラード 大さじ1: {tbsp_info['calories']} kcal, {tbsp_info['fat']}g fat")
```

---

## 📈 統計サマリー

### Serving Options 統計

| 指標 | 値 |
|------|-----|
| 総Serving Options | 181個 |
| 最多Serving Options | 9個（バター、ドレッシング） |
| 最少Serving Options | 4個（豆類、パイクラスト） |
| 平均Serving Options | 7.2個/食材 |

### カロリー範囲（100gあたり）

| カテゴリ | カロリー範囲 |
|----------|------------|
| **最高カロリー** | Lard/Oils: 884-902 kcal |
| **高カロリー** | Butter: 713-718 kcal |
| **中カロリー** | Nut Butter: 589-614 kcal |
| **低カロリー** | Tofu: 189 kcal |
| **最低カロリー** | Kidney beans: 56 kcal |

---

## 🔗 関連ファイル

### ソースファイル

- `web_scraping_2/output/stemmed_only_foods.json` - 元データ
- `db/mynetdiary_converted_tool_calls_list_stemmed.json` - Stemmed DB

### 生成ファイル

- `web_scraping_2/output/stemmed_only_foods_enriched.json` - 拡張データ
- `web_scraping_2/collect_stemmed_only_nutrition.py` - 生成スクリプト
- `web_scraping_2/STEMMED_ONLY_FOODS_NUTRITION_REPORT.md` - このレポート

---

## 💡 今後の拡張案

1. **Web Scraping による実データ取得**
   - MyNetDiary公式サイトから実際のserving情報を取得
   - より正確な重量換算データの収集

2. **栄養素の追加**
   - 飽和脂肪酸、コレステロール
   - ビタミン、ミネラル
   - 食物繊維

3. **Serving Sizeのバリエーション拡大**
   - ブランド別serving size
   - 地域別単位（ml, lなど）

4. **データベース統合**
   - complete_food_database.jsonとの統合
   - 統一されたserving情報データベースの構築

---

**作成日時**: 2025-10-09
**データバージョン**: v1.0
**総食材数**: 25件
**総Serving Options**: 181個
**計算精度**: 100g基準、小数点第2位まで
