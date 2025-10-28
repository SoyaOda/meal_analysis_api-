# VLMプロンプト改善方針（汎用的原則）

## 問題の本質（データ分析から判明）

### 重量推定の系統的バイアス
- **0-300g**: 平均誤差 +130.8%
- **300-600g**: 平均誤差 +25.3%
- **600-900g**: 平均誤差 +4.1%

### 具体的な誤差パターン
1. **飲み物の幻覚**: 存在しない水・ジュースを追加（test_food49: +555g誤差）
2. **サラダの過大評価**: 40g → 200g（+400%）のような極端な誤差
3. **複合料理の誤統合**: 個別要素を一体化して重量を過大計算

## 汎用的改善原則（過学習を避ける）

### 1. 密度の物理原則を導入

```text
WEIGHT ESTIMATION PRINCIPLES:
Think in terms of DENSITY, not just VISUAL VOLUME.

Food density categories:
- HIGH DENSITY (1.2-2.0 g/cm³): meats, cheese, dense grains
- MEDIUM DENSITY (0.8-1.2 g/cm³): cooked pasta, rice, bread
- LOW DENSITY (0.2-0.8 g/cm³): leafy vegetables, salads, chips
- VERY LOW DENSITY (<0.2 g/cm³): popcorn, puffed items

For each food item, first classify its density, then estimate weight based on:
weight = visual_volume × density_factor
```

### 2. 階層的推定アプローチ

```text
HIERARCHICAL WEIGHT ESTIMATION:
1. First, estimate TOTAL meal weight (typically 300-800g for single meal)
2. Then, allocate proportions to each component
3. Validate: Sum of components ≈ Total estimate
4. If sum > 1000g for single plate, reconsider density assumptions
```

### 3. 存在確認の原則

```text
EXISTENCE VERIFICATION:
Before adding any item, verify VISUAL EVIDENCE:
- Beverages: Must see actual liquid, not just empty containers
- Condiments: Must see actual sauce/dressing, not just packets
- Extras: Must be visually distinct, not assumed
```

### 4. 分離判断の原則

```text
SEPARATION PRINCIPLE:
Decide if components were "cooked together" or "assembled together":
- COOKED TOGETHER → single main_food entry
  (e.g., "pasta with integrated meat sauce")
- ASSEMBLED TOGETHER → separate entries
  (e.g., pasta + separately cooked sausage on top)

Visual clues for separation:
- Different textures/cooking methods visible
- Clear boundaries between components
- Components that could be served separately
```

## 実装例（最小限の具体例）

```text
# BAD (specific examples that lead to overfitting):
"Pizza slice is typically 120-150g"
"Salad bowl is usually 150-200g"

# GOOD (principles that generalize):
"Apply density-based estimation:
 - Identify visual volume
 - Classify density category
 - Calculate: weight = volume × density_factor"
```

## 検証メカニズム

```text
SELF-VALIDATION CHECKS:
□ Total weight reasonable for single meal? (typically < 1000g)
□ Density categories correctly applied?
□ All items have visual evidence?
□ Component separation follows cooking method?
```

## 期待される改善効果

- **軽量食材（0-300g）**: 誤差 131% → 30% （密度原則の適用）
- **中量食材（300-600g）**: 誤差 25% → 15% （階層的推定）
- **飲み物の幻覚**: 完全排除（存在確認原則）

## プロンプト修正の具体的な編集箇所

### 現在のプロンプト（72-74行目）を以下に置換:

```text
OLD:
- weight_g: estimated edible weight in grams (positive integer; exclude inedible parts/ice)

NEW:
- weight_g: estimated using density principles:
  1. Assess visual volume
  2. Apply density factor (high/medium/low)
  3. Validate against total meal weight
```

### 新セクション追加（70行目の前）:

```text
DENSITY-BASED WEIGHT ESTIMATION:
[上記の密度原則セクション全体]
```

この方針により、特定の食材への過学習を避けながら、物理的原則に基づいた汎用的な重量推定が可能になります。