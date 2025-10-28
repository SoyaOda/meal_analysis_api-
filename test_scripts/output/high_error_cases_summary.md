# 30%以上の栄養誤差がある画像の問題分析サマリー

## 📊 全体概要

- **対象画像数**: 12枚 / 50枚（24%）
- **誤差範囲**: 30.0% ～ 105.6%
- **平均誤差**: 48.4%

---

## 🔍 12枚の詳細リスト

| # | 画像名 | 誤差% | Label Cal | Pipeline Cal | 差分 | 主な問題 |
|---|--------|-------|-----------|--------------|------|----------|
| 1 | test_food44.jpg | 105.6% | 518 kcal | 1066 kcal | +547 | 重量過大評価(+69%), 低スコアマッチ(0.118) |
| 2 | test_food6.jpg | 77.5% | 504 kcal | 895 kcal | +391 | 重量過大評価, 食材認識ミス |
| 3 | test_food43.jpg | 46.0% | 564 kcal | 824 kcal | +260 | 食材認識ミス |
| 4 | test_food21.jpg | 41.5% | 725 kcal | 1026 kcal | +301 | 重量過大評価(+40%), 食材認識ミス |
| 5 | test_food48.jpg | 40.2% | 547 kcal | 767 kcal | +220 | 食材認識ミス |
| 6 | test_food30.jpg | 38.8% | 714 kcal | 990 kcal | +277 | 食材認識ミス |
| 7 | test_food27.jpg | 35.9% | 1069 kcal | 686 kcal | **-384** | 低スコアマッチ(0.481), **過小評価** |
| 8 | test_food41.jpg | 34.0% | 682 kcal | 914 kcal | +232 | 食材認識ミス |
| 9 | test_food29.jpg | 31.2% | 769 kcal | 529 kcal | **-240** | **過小評価**, 食材認識ミス |
| 10 | test_food20.jpg | 30.2% | 519 kcal | 676 kcal | +157 | 食材認識ミス |
| 11 | test_food49.jpg | 30.1% | 602 kcal | 784 kcal | +182 | 重量過大評価(+36%), 食材認識ミス |
| 12 | test_food31.jpg | 30.0% | 609 kcal | 426 kcal | **-183** | **過小評価**, 食材認識ミス |

---

## 🎯 問題の分類と件数

### 1. **カロリー評価の傾向**

- **過大評価**: 9件（75%）
  - 平均過大評価: +297 kcal
  - 最大: +547 kcal (test_food44.jpg)

- **過小評価**: 3件（25%）
  - 平均過小評価: -269 kcal
  - 最大: -384 kcal (test_food27.jpg)

### 2. **栄養素別の誤差**

最も誤差が大きい栄養素（各画像で最大誤差を記録）:

- **脂質が最大誤差**: 9件（75%）
  - 範囲: 56.5% ～ 168.0%
  - 原因: VLMの食材認識ミスや重量過大評価が脂質に大きく影響

- **炭水化物が最大誤差**: 3件（25%）
  - 範囲: 32.4% ～ 75.8%

### 3. **重量の過大/過小評価**

総重量の差が30%以上のケース: **4件**

| 画像名 | Label総重量 | Pipeline総重量 | 差分 | 誤差% |
|--------|-------------|----------------|------|-------|
| test_food44.jpg | 390g | 660g | +270g | +69.2% |
| test_food21.jpg | 325g | 455g | +130g | +40.0% |
| test_food49.jpg | 235g | 320g | +85g | +36.2% |

### 4. **低スコアマッチング（<0.5）**

Rerankerスコアが0.5未満のケース: **2件**

| 画像名 | 食材 | VLM出力 | スコア | 問題 |
|--------|------|---------|--------|------|
| test_food44.jpg | main_food | baked pasta with cheese and broccoli | 0.118 | VLMが余分に"and broccoli"を追加 |
| test_food27.jpg | main_food | pork and cabbage stir-fry | 0.481 | USDAマッチングが不適切 |

### 5. **VLMの食材認識ミス**

**全12枚で食材認識ミスが発生**

#### 典型的なミスのパターン:

**パターンA: 類似料理の混同**
- test_food6.jpg:
  - Label: `cream of chicken soup with vegetables`
  - VLM: `chicken stew with vegetables and cream sauce`

**パターンB: 複合料理の分解ミス**
- test_food21.jpg:
  - Label: 個別食材（lettuce, ground beef, flour tortilla, tomato, cheddar cheese）
  - VLM: 統合料理（taco with ground beef and lettuce）

**パターンC: 食材の見逃し**
- test_food44.jpg:
  - VLMが見逃した: cabbage, corn
  - VLMが余分に認識: broccoli florets

**パターンD: 食材の過剰認識**
- test_food30.jpg:
  - 6つの個別食材 → 4つの統合料理に変換
  - 詳細な食材情報が失われる

**パターンE: タンパク質源の誤認識**
- test_food31.jpg:
  - Label: `cod fillet`（魚）
  - VLM: `chicken breast`（鶏肉）
  - → タンパク質・脂質の大幅なズレ

---

## 📈 問題の重要度ランキング

### 最優先で対処すべき問題（Top 3）

#### 🥇 **1位: VLMの食材認識精度**
- **影響**: 全12枚（100%）
- **問題内容**:
  - 食材の見逃し
  - 余分な食材の認識
  - 類似料理の混同
  - タンパク質源の誤認識
- **対策案**:
  - VLMプロンプトの改善（より具体的な指示）
  - VLMモデルの変更（より高精度なモデル）
  - マルチステップ認識（複数回の確認）

#### 🥈 **2位: 重量の推定精度**
- **影響**: 4枚（33%）で30%以上の誤差
- **問題内容**:
  - 過大評価が多い（+36% ～ +69%）
  - 特にpasta, pizza等のボリューム感のある料理で過大評価
- **対策案**:
  - VLMプロンプトに重量推定の基準を追加
  - 料理カテゴリ別の重量補正係数の導入
  - 画像から皿のサイズを推定して補正

#### 🥉 **3位: 脂質の推定精度**
- **影響**: 9枚（75%）で最大誤差
- **問題内容**:
  - 誤差範囲: 56.5% ～ 168.0%
  - 食材認識ミス + 重量過大評価の複合効果
- **対策案**:
  - 調理法（揚げる、焼く等）の認識強化
  - ソース・ドレッシングの量の推定改善
  - 脂質含有量の高い食材の特定精度向上

---

## 🔬 各画像の詳細問題分析

### test_food44.jpg（誤差 105.6%、最悪ケース）

**Label（正解）:**
- baked pasta with cheese (250g, 475 kcal)
- cabbage (80g, 20 kcal)
- cucumber (30g, 4 kcal)
- red onion (15g, 6 kcal)
- corn (15g, 13 kcal)
- **合計: 518 kcal**

**Pipeline（予測）:**
- baked pasta with cheese **and broccoli** (450g, 1004 kcal) ← **重量+80%, 余分な食材**
- **shredded** cabbage (120g, 30 kcal) ← 形状の誤認識
- cucumber (30g, 5 kcal)
- red onion (20g, 9 kcal)
- corn **kernels** (15g, 10 kcal)
- **broccoli florets** (25g, 8 kcal) ← **存在しない食材**
- **合計: 1066 kcal (+547 kcal)**

**問題点:**
1. ❌ main_foodに"and broccoli"が余分に追加 → USDAマッチングスコア 0.118（極低）
2. ❌ main_foodの重量が250g → 450g（+80%）
3. ❌ 存在しないbroccoli floretsを認識
4. ❌ 総重量が390g → 660g（+69%）

**根本原因:**
- VLMが画像中の緑色の野菜（cabbage）をbroccoliと誤認識
- main_foodとextraの分離が不適切
- 重量推定が大幅に過大

---

### test_food6.jpg（誤差 77.5%）

**Label（正解）:**
- cream of chicken soup with vegetables (400g, 280 kcal)
- dinner roll (80g, 224 kcal)
- **合計: 504 kcal**

**Pipeline（予測）:**
- chicken stew with vegetables (450g, 567 kcal) ← **料理名の変更 + 重量増**
- dinner roll (120g, 328 kcal) ← **重量+50%**
- **合計: 895 kcal (+391 kcal)**

**問題点:**
1. ❌ "cream of chicken soup" → "chicken stew" （異なる料理として認識）
2. ❌ soup: 400g → 450g (+12.5%)
3. ❌ dinner roll: 80g → 120g (+50%)

**根本原因:**
- VLMがスープとシチューを混同
- パンの重量を大幅に過大評価

---

### test_food27.jpg（誤差 35.9%、過小評価ケース）

**Label（正解）:**
- beef with peppers and onions (300g, 450 kcal)
- pork with cabbage (200g, 360 kcal)
- mayonnaise salad (100g, 259 kcal)
- **合計: 1069 kcal**

**Pipeline（予測）:**
- shredded chicken with sauce (200g, 260 kcal) ← **beef/pork → chicken**
- beef stir-fry with vegetables (180g, 216 kcal)
- pork and cabbage stir-fry (150g, 210 kcal) ← **スコア 0.481**
- **合計: 686 kcal (-384 kcal)**

**問題点:**
1. ❌ beef → chicken への誤認識
2. ❌ mayonnaise saladを完全に見逃し（259 kcal損失）
3. ❌ pork and cabbageのUSDAマッチングが低スコア（0.481）
4. ❌ 全体的に重量を過小評価

**根本原因:**
- 複数のタンパク質源（beef, pork, chicken）の識別ミス
- 高カロリーのmayonnaise saladを認識できず
- 料理が複雑で視覚的に区別が困難

---

### test_food31.jpg（誤差 30.0%、過小評価ケース）

**Label（正解）:**
- sweet potatoes (150g, 129 kcal)
- cod fillet (120g, 105 kcal) ← **魚**
- vinaigrette dressing (20g, 90 kcal)
- strawberries, cucumber, mixed salad greens, pecans
- **合計: 609 kcal**

**Pipeline（予測）:**
- chicken breast (120g, 198 kcal) ← **cod → chicken（魚 → 鶏肉）**
- sweet potato (100g, 86 kcal)
- lemon (認識のみ)
- mixed greens salad (80g, 142 kcal)
- **合計: 426 kcal (-183 kcal)**

**問題点:**
1. ❌ cod fillet（魚） → chicken breast（鶏肉）への誤認識
2. ❌ vinaigrette dressing（90 kcal）を見逃し
3. ❌ strawberries, pecansを見逃し
4. ❌ 脂質の誤差 77.6%（最も大きい）

**根本原因:**
- 白身の魚と鶏肉の視覚的区別が困難
- ドレッシング・ナッツ等の小さな高カロリー食材を見逃し
- タンパク質源の誤認識が栄養素全体に影響

---

## 💡 改善施策の提案

### 短期的施策（即座に実施可能）

1. **VLMプロンプトの改善**
   - 食材リストを明示的に要求（"list all ingredients separately"）
   - 重量推定の基準を追加（"estimate weight based on standard portion sizes"）
   - 調理法の明示を要求（"specify cooking method: fried, grilled, baked, etc."）

2. **Post-processing補正**
   - 重量の異常値検出と補正（+50%以上は警告）
   - 脂質の異常値検出（100%以上の誤差時は再計算）
   - 低スコアマッチング（<0.5）の手動レビュー

3. **データベース拡充の検討**
   - Branded Foodデータベースの追加（test_food49のpizza等に有効）

### 中長期的施策（開発が必要）

1. **マルチステップVLM処理**
   - Step 1: 料理全体を認識
   - Step 2: 各料理の食材を分解
   - Step 3: 重量を推定
   - Step 4: クロスチェック

2. **料理カテゴリ別の補正係数**
   - Pasta: 重量 -15%
   - Pizza: 重量 -10%
   - Soup: 重量 +10%
   - Salad: 脂質 +20%（ドレッシング考慮）

3. **VLMモデルの変更/アンサンブル**
   - 複数のVLMモデルを使用してアンサンブル
   - 食材認識に特化したモデルの追加

---

## 📊 統計サマリー

### 問題発生頻度

| 問題カテゴリ | 件数 | 割合 |
|------------|------|------|
| VLM食材認識ミス | 12/12 | 100% |
| 脂質が最大誤差 | 9/12 | 75% |
| カロリー過大評価 | 9/12 | 75% |
| 重量過大評価（30%以上） | 4/12 | 33% |
| カロリー過小評価 | 3/12 | 25% |
| 炭水化物が最大誤差 | 3/12 | 25% |
| 低スコアマッチング（<0.5） | 2/12 | 17% |

### 誤差の内訳

- **平均カロリー誤差**: 48.4%
- **平均過大評価**: +297 kcal（9件）
- **平均過小評価**: -269 kcal（3件）
- **最大脂質誤差**: 168.0%（test_food44.jpg）
- **最大炭水化物誤差**: 75.8%（test_food21.jpg）
- **最大タンパク質誤差**: 92.2%（test_food44.jpg）

---

## 🎯 結論

30%以上の誤差がある12枚の画像では、**VLMの食材認識精度が最大の課題**であることが明確になりました。

**主な問題:**
1. ✅ 食材の見逃し・余分な認識（100%）
2. ✅ 重量の過大評価（75%）
3. ✅ 脂質の推定誤差（75%で最大誤差）
4. ✅ タンパク質源の誤認識（魚 → 鶏肉等）

**最優先の改善項目:**
1. **VLMプロンプトの改善** - 即座に実施可能、最も効果的
2. **重量推定の補正** - 過大評価傾向の修正
3. **脂質計算の見直し** - 調理法・ドレッシング等の考慮

これらの改善により、30%以上の誤差ケースを12枚 → 5枚程度に削減できる可能性があります。
