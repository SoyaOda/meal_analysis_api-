# USDA 複合料理の分類ロジックと問題点

## 現在の分類ロジック

ファイル: `apps/usda_meal_analysis_api/scripts/generate_usda_food_database.py`
関数: `extract_foods_by_three_types()` (行385-438)

### 分類基準

| カテゴリ | 条件 | 説明 |
|---------|------|------|
| 複合料理 | `len(inputFoods) >= 2` | 2つ以上の食材から構成 |
| 調理済み食材 | `len(inputFoods) == 1` + COOKING_KEYWORDS含む | 単一食材を調理 |
| 基本食材 | `len(inputFoods) == 1` + COOKING_KEYWORDS含まない | 単一食材で未調理 |

**COOKING_KEYWORDS** (行30-34):
```python
['cooked', 'toasted', 'baked', 'broiled', 'fried', 'roasted',
 'boiled', 'steamed', 'grilled', 'poached', 'sauteed', 'braised', 'stewed',
 'smoked', 'cured', 'dried', 'pickled']
```

## ピザとラーメンの分類実態

### ピザ
- **複合料理**: 68件 (例: "Pizza, extra cheese, thin crust" → inputFoods: 2)
- **基本食材**: 26件 (例: "Pizza, cheese, from frozen, thin crust" → inputFoods: 1)

### ラーメン
- **複合料理**: 7件 (例: "Ramen bowl with beef" → inputFoods: 7)
- **基本食材**: 1件 ("Ramen bowl, NFS" → inputFoods: 1)

## 問題点

### 1. 写真ベース栄養計算に不向き
- 複合料理の項目名が詳細すぎる（"Beef, potatoes, and vegetables; gravy"）
- ユーザーの写真と完全一致することは稀
- 基本食材にも料理名があり、重複している

### 2. USDA FNDDS の本来の目的
- 対面の食事調査用に設計
- 調査員が被験者の口頭説明から適切な項目を選ぶ
- 写真認識・自動マッチングは想定外

### 3. inputFoods 数の意味
- USDA側のレシピ記録方法で決まる
- 同じ「ピザ」でもレシピの記録方法で分類が変わる
- ユーザーの料理認識とは無関係

## 改善案

### オプション1: 基本食材のみ使用
- 複合料理を廃止
- メリット: シンプル、重複なし
- デメリット: 複雑な料理の栄養値が不正確

### オプション2: カスタム分類ルール
- WWEIA カテゴリ名を活用して再分類
- 写真認識に適した粒度で分類
- inputFoods 数ではなく料理の種類で判断

### オプション3: 統合ルールの拡張
- 現在の統合ルールを拡大
- 同じ料理名の複合料理と基本食材を1つに統合
- 例: すべての"Pizza, cheese"系を代表値に統合

## 参考スクリプト

分析用スクリプト:
- `/tmp/analyze_pizza_ramen_classification.py` - ピザとラーメンの分類詳細
- `/tmp/analyze_food_classification.py` - 全体的な分類分析
