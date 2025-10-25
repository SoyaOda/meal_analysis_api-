# Role別カテゴリ分け表示の提案

## 現状の食品リスト形式

```
EXACT_FOOD_LIST (CORE) - 1,398 Unified Mappings
1. Apple
2. Bacon
3. Caesar salad
4. Caesar dressing
5. Chicken thigh
...
1398. Yogurt
```

**問題点**:
- すべての食品が平坦なリストとして表示
- is_base, ingredient_only, sauce_only, either の区別が不明
- VLMが各食品の「使い方」を判断できない

---

## 提案：Role別カテゴリ分け表示

### 提案A: セクション分割形式

```
EXACT_FOOD_LIST (CORE) - 1,398 Unified Mappings

[IS_BASE - Base Dishes for HYBRID_DECOMPOSITION] (332 items)
These items should be used as base_food in HYBRID_DECOMPOSITION method:
1. Caesar salad
2. Chicken curry
3. Mac and cheese
4. Pasta with Tomato Sauce
...

[INGREDIENT_ONLY - Ingredients Only] (130 items)
These items should ONLY be used in ingredients array, NEVER as base_food:
1. Alliums (onion/leek/shallot/scallion)
2. Cooking oil
3. Lettuce
4. Tomato
5. Wheat flour (refined)
...

[SAUCE_ONLY - Sauces and Condiments Only] (100 items)
These items should ONLY be used in ingredients array for sauces/condiments:
1. BBQ sauce
2. Caesar dressing
3. Gravy
4. Ketchup
5. Mayonnaise
6. Ranch dressing
7. Soy sauce
8. Tomato sauce
...

[EITHER - Flexible Usage] (836 items)
These items can be used either as base_food or in ingredients array:
1. Apple
2. Bacon
3. Chicken thigh
4. Egg
5. Mashed potatoes
6. Rice
...
```

### 提案B: インライン表記形式

```
EXACT_FOOD_LIST (CORE) - 1,398 Unified Mappings

1. [EITHER] Apple
2. [INGREDIENT_ONLY] Alliums (onion/leek/shallot/scallion)
3. [SAUCE_ONLY] BBQ sauce
4. [EITHER] Bacon
5. [IS_BASE] Caesar salad
6. [SAUCE_ONLY] Caesar dressing
7. [EITHER] Chicken thigh
8. [INGREDIENT_ONLY] Cooking oil
...
```

---

## メリット・デメリット比較

### 提案A: セクション分割形式

#### ✅ メリット

1. **VLMの理解向上**
   - 各roleの用途が明確に説明される
   - "should be used as base_food" などの明示的な指示
   - 混乱を大幅に削減

2. **found_in_list精度向上**
   - セクションごとに検索範囲が明確
   - "Tomato sauce"を探す際、SAUCE_ONLYセクションを優先的に検索可能

3. **analysis_method選択精度向上**
   - IS_BASEセクションの食品 → HYBRID_DECOMPOSITIONの候補
   - INGREDIENT_ONLYセクションの食品 → base_foodとして使用不可
   - VLMが正しいメソッドを選択しやすくなる

4. **プロンプト文章の簡潔化**
   - roleの説明をリスト内に含められる
   - 本文の繰り返し説明を削減可能

#### ❌ デメリット

1. **トークン数増加**
   - セクションヘッダー、説明文の追加
   - 現状: 34,420文字 → 推定: 38,000-40,000文字 (+10-15%)
   - コスト増加: 約$0.0007/画像 → $0.0008/画像 (+14%)

2. **検索時の複雑性**
   - VLMが複数セクションを横断して検索する必要
   - アルファベット順が崩れる

3. **プロンプト構造の複雑化**
   - 4つのセクションを管理
   - セクション間の整合性維持が必要

#### 📊 期待される精度向上

| 指標 | 現状 | 期待値 | 改善幅 |
|------|------|--------|--------|
| found_in_list精度 | 78.6% | **85-90%** | +6-11% |
| analysis_method精度 | 71% | **85-90%** | +14-19% |
| role理解度 | 不明 | **95%+** | - |

---

### 提案B: インライン表記形式

#### ✅ メリット

1. **アルファベット順維持**
   - 既存の検索ロジックを維持
   - VLMの検索効率が高い

2. **トークン数増加が最小**
   - 現状: 34,420文字 → 推定: 36,000文字 (+4.6%)
   - コスト増加: 約$0.0007/画像 → $0.00073/画像 (+4.3%)

3. **実装が簡単**
   - display_nameの前に [ROLE] を付けるだけ
   - 既存のソート順を維持

#### ❌ デメリット

1. **VLMの理解度向上が限定的**
   - タグのみでは用途が不明確
   - 別途プロンプト本文で説明が必要

2. **視覚的な分かりにくさ**
   - 1,398個のリストに [TAG] が散在
   - セクション化されていないため一覧性が低い

3. **found_in_list精度向上が限定的**
   - セクション分割ほどの精度向上は期待できない

#### 📊 期待される精度向上

| 指標 | 現状 | 期待値 | 改善幅 |
|------|------|--------|--------|
| found_in_list精度 | 78.6% | **80-85%** | +1-6% |
| analysis_method精度 | 71% | **75-80%** | +4-9% |
| role理解度 | 不明 | **70-80%** | - |

---

## プロンプト本文の修正提案

### 現状のプロンプト（関連部分）

```markdown
PRIMARY GOALS
- For every base_food and ingredient, check if the item exists in EXACT_FOOD_LIST (CORE).

ANALYSIS METHOD RULES (STRICT):
1) USE_AS_IS:
   - base_food: ONE item (required)
   - ingredients: MUST be empty array []

2) DECOMPOSE_TO_INGREDIENTS:
   - base_food: MUST be null
   - ingredients: ALL components listed

3) HYBRID_DECOMPOSITION:
   - base_food: ONE base item (required)
   - ingredients: ONLY additional/extra items
```

### 修正案（提案A採用時）

```markdown
PRIMARY GOALS
- For every base_food and ingredient, check if the item exists in EXACT_FOOD_LIST (CORE).
- Pay attention to the ROLE tags in the food list:
  - [IS_BASE]: Should be used as base_food in HYBRID_DECOMPOSITION
  - [INGREDIENT_ONLY]: Can ONLY be used in ingredients array, NEVER as base_food
  - [SAUCE_ONLY]: Can ONLY be used in ingredients array for sauces/condiments
  - [EITHER]: Can be used either as base_food or in ingredients array

ANALYSIS METHOD RULES (STRICT):
1) USE_AS_IS:
   - base_food: ONE item from [IS_BASE] or [EITHER] sections (required)
   - ingredients: MUST be empty array []

2) DECOMPOSE_TO_INGREDIENTS:
   - base_food: MUST be null
   - ingredients: Items from ANY section

3) HYBRID_DECOMPOSITION:
   - base_food: ONE item from [IS_BASE] or [EITHER] sections (required)
   - ingredients: Items from [INGREDIENT_ONLY], [SAUCE_ONLY], or [EITHER]
   - ⚠️ NEVER use [INGREDIENT_ONLY] or [SAUCE_ONLY] items as base_food

ROLE-SPECIFIC RULES:
- [IS_BASE] items are pre-defined dishes (e.g., "Caesar salad", "Mac and cheese")
  → Prefer HYBRID_DECOMPOSITION with these as base_food

- [INGREDIENT_ONLY] items are raw ingredients (e.g., "Lettuce", "Cooking oil")
  → Can ONLY appear in ingredients array

- [SAUCE_ONLY] items are condiments (e.g., "Caesar dressing", "Ketchup")
  → Can ONLY appear in ingredients array

- [EITHER] items are flexible (e.g., "Chicken thigh", "Mashed potatoes")
  → Can be base_food or ingredient depending on context
```

---

## コスト・パフォーマンス比較

### 提案A: セクション分割

| 項目 | 数値 |
|------|------|
| プロンプト長 | 38,000-40,000文字 (+10-15%) |
| 入力トークン | 約15,200 (+10%) |
| コスト/画像 | $0.0008 (+14%) |
| **期待精度向上** | **+6-19%** |
| **ROI** | **高い** ✅ |

**総コスト増加（5画像）**: $0.00035
**精度向上の価値**: found_in_list誤判定4件 → 1-2件に削減

### 提案B: インライン表記

| 項目 | 数値 |
|------|------|
| プロンプト長 | 36,000文字 (+4.6%) |
| 入力トークン | 約14,400 (+4%) |
| コスト/画像 | $0.00073 (+4.3%) |
| **期待精度向上** | **+1-9%** |
| **ROI** | **中程度** |

---

## 推奨案

### 🎯 **提案A（セクション分割形式）を推奨**

#### 理由:

1. **精度向上が最大**
   - found_in_list: 78.6% → 85-90% (+6-11%)
   - analysis_method: 71% → 85-90% (+14-19%)

2. **Food4の問題を解決**
   ```
   現状: "Mashed potatoes" found_in_list=false (誤り)
   改善後: [EITHER]セクションで明確に表示 → true

   現状: "Meatloaf" found_in_list=false (誤り)
   改善後: "Meat loaf"を[IS_BASE]セクションで発見 → true
   ```

3. **Food2/Food3の問題を解決**
   ```
   現状: プレート料理をHYBRIDと誤判定
   改善後: [IS_BASE]セクションに該当なし → DECOMPOSEを選択
   ```

4. **コスト増加が許容範囲**
   - +14%のコスト増加で +6-19%の精度向上
   - 1画像あたり$0.0001の追加コスト（約0.015円）

5. **長期的なメリット**
   - VLMの学習効果
   - プロンプト本文の簡潔化
   - 今後の拡張性

---

## 実装計画

### Phase 1: セクション分割実装

1. **generate_mapping_prompt.py修正**
   ```python
   def load_mapping_display_names_by_role():
       mappings = load_mappings()
       by_role = {
           'is_base': [],
           'ingredient_only': [],
           'sauce_only': [],
           'either': []
       }
       for key, mapping in mappings.items():
           role = mapping.get('role', 'either')
           by_role[role].append(mapping['display_name'])

       # 各セクションをソート
       for role in by_role:
           by_role[role].sort()

       return by_role
   ```

2. **プロンプトテンプレート修正**
   - セクションヘッダー追加
   - role説明文追加
   - analysis_method ルールに role 制約追加

3. **検証テスト**
   - 同じ5画像で再テスト
   - found_in_list精度測定
   - analysis_method精度測定

### Phase 2: 効果測定

- 精度が85%以上達成 → 採用
- 精度が80%未満 → 提案Bにフォールバック

---

## 結論

**提案A（セクション分割形式）を推奨**

- ✅ 最大の精度向上（+6-19%）
- ✅ Food4の誤判定を解決
- ✅ Food2/Food3の誤判定を解決
- ✅ コスト増加は許容範囲（+14%）
- ✅ 長期的なメリット大

**次のステップ**:
1. generate_mapping_prompt.py を修正
2. プロンプトテンプレートを修正
3. 5画像で再テスト
4. 精度85%達成を確認
