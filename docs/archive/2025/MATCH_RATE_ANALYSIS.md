# マッチ率の計算ロジック分析

## 📌 現在のマッチ率の意味

### 計算式
```python
exact_match_rate = (exact_matches / total_searches * 100) if total_searches > 0 else 0
```

`shared/components/advanced_nutrition_search_component.py:442`

### マッチの判定基準

**Exact Match**と判定される条件:
1. AIが食材名を出力
2. その食材名をWord Query APIに送信
3. Word Query APIが返す候補の`match_type`が **`"exact_match"`**

```python
# shared/components/advanced_nutrition_search_component.py:182-190
if match_list and term in input_data.ingredient_names:
    top_match = match_list[0]
    match_type = top_match.search_metadata.get("match_type", "unknown")

    if match_type == "exact_match":
        exact_matches += 1  # ✅ Exact matchとカウント
    elif match_type == "tier_1_exact":
        tier_1_exact_matches += 1  # △ High quality matchとカウント
```

---

## ❌ 問題点: なぜマッチ率が低いのか？

### 原因1: AIが食品名リストから選んでいない

**期待**: AIがUSDA FNDDS食品名リストから正確な名前を選択
**現実**: AIが自由形式で食材名を出力

#### 実際の例（Qwen3-VL-4B-Instruct）

| AIの出力 | USDA FNDDS内の正しい名前 | マッチ判定 |
|----------|--------------------------|------------|
| "Chicken Thigh, cooked, with sauce" | "Chicken, thigh, NS as to skin eaten" | ❌ No match |
| "Pasta with Tomato Sauce" | "Pasta, cooked, NFS" | ❌ No match |
| "Lettuce, romaine, raw" | "Lettuce, romaine, raw" | ✅ Exact match |

**問題**:
- AIは「コンテキストに基づいた詳細な説明」を含めてしまう
- ", cooked, with sauce" などの修飾語が余計
- USDA FNDDSの標準名と一致しない

### 原因2: Word Query APIがExact Matchを返せない

AIの出力がUSDA FNDDSの名前と**微妙に違う**場合:
- Word Query APIは候補を返す
- しかし`match_type`が`tier_1_exact`, `tier_2_fuzzy`など
- `exact_match`にならない → マッチ率にカウントされない

---

## 🎯 100%マッチを達成するには

### 解決策1: Promptを修正して食品名リストから選択させる ⭐ 推奨

**現状のPrompt問題**:
```json
{
  "ingredient_name": "自由形式の名前"
}
```

**改善案**:
```json
{
  "ingredient_name": "【必須】提供されたUSDA FNDDS食品名リストから完全一致する名前を選択"
}
```

#### Promptに追加すべき指示

1. **厳密な選択ルール**:
   ```
   - 食材名は必ずWord Query APIから返された候補リストから選択すること
   - 候補リストの"suggestion"フィールドの値をそのまま使用すること
   - 独自の修飾語や説明を追加しないこと
   ```

2. **2ステップ処理**:
   ```
   Step 1: 画像から食材を認識
   Step 2: 認識した食材をWord Query APIの候補から選択
   ```

3. **Exact Match優先**:
   ```
   - Word Query APIの候補の中で、confidence_scoreが最も高いものを選択
   - match_type="exact_match"の候補が存在する場合、必ずそれを選択
   ```

### 解決策2: Word Query API呼び出しを2回行う

**現在のフロー**:
```
AI出力 → Word Query API → 栄養計算
```

**改善フロー**:
```
画像 → AI（食材認識） → Word Query API（候補取得） → AI（候補選択） → 栄養計算
```

これにより:
1. AIは画像から「chicken」「potato」などの一般的な食材名を認識
2. Word Query APIが「Chicken, breast, NS as to skin eaten」などの候補を返す
3. AIが候補リストから最適なものを選択
4. **選択された名前は必ずUSDA FNDDSに存在する** = 100%マッチ

---

## 📈 現在のマッチ率の内訳

### Mistral-Small-3.2-24B-Instruct-2506（58.3%）

| 画像 | マッチ率 | 原因分析 |
|------|----------|----------|
| food1 | 75.0% | パスタ、サラダ：正確な名前を出力 |
| food2 | 50.0% | ミートローフ：修飾語が多い |
| food3 | **100.0%** | 全材料が正確にマッチ |
| food4 | 0.0% | 複雑な料理、全てミスマッチ |
| food5 | 66.7% | タコスの材料は比較的単純 |

### gemma-3-27b-it（51.8%）

- 詳細な材料分解が得意
- しかし修飾語が多く、完全一致しにくい

### Qwen/Qwen3-VL-4B-Instruct（39.3%）

- 最も低いマッチ率
- 自由形式の出力が多い
- food5で重複バグ

---

## 💡 推奨事項

### 優先度1: Prompt修正（即座に実装可能）

`shared/config/prompts/common_prompts.py`を修正:

```python
# 現在
"ingredient_name": "食材名"

# 修正後
"ingredient_name": "【重要】Word Query APIの候補リストから完全一致する食品名を選択すること。独自の修飾語や説明を追加しないこと。"
```

### 優先度2: 2段階AIパイプライン（より確実）

1. Phase 1: 画像 → AI → 一般的な食材名（chicken, potato, etc.）
2. Phase 2: 一般食材名 → Word Query API → 候補リスト
3. Phase 3: 候補リスト → AI → 最適な候補を選択
4. Phase 4: 選択された候補 → 栄養計算

---

## 🎯 期待される改善効果

| 改善策 | 期待マッチ率 | 実装難易度 |
|--------|--------------|------------|
| Prompt修正のみ | 70-80% | ⭐ 簡単 |
| 2段階パイプライン | 95-100% | ⭐⭐⭐ 複雑 |

---

**結論**: 現在のマッチ率58.3%は、「AIが自由形式で食材名を出力し、それがUSDA FNDDSの正確な名前と一致しない」ことが主な原因です。Promptを修正してWord Query APIの候補から選択させることで、大幅な改善が期待できます。


---

## 🔬 実例比較

### ✅ 100%マッチの例（Mistral food3）

```json
{
  "dish_name": "Mixed Salad",
  "ingredients": [
    {"ingredient_name": "Lettuce, for use on a sandwich"},  // ✅ USDA正式名
    {"ingredient_name": "Tomatoes, for use on a sandwich"}  // ✅ USDA正式名
  ]
}
```

**成功要因**:
- シンプルな食材名
- USDA FNDDSの正式名と完全一致
- 余計な修飾語なし

### ❌ 71%マッチの例（Qwen food3）

```json
{
  "dish_name": "Chicken Thigh, cooked, with sauce",  // ⚠️ 余計な詳細
  "ingredients": [
    {"ingredient_name": "Chicken thigh, baked or broiled, skin not eaten, from pre-cooked"}  // ✅ マッチ
  ]
},
{
  "dish_name": "Salad, mixed greens with corn and tomatoes",  // ⚠️ 余計な詳細
  "ingredients": [
    {"ingredient_name": "Lettuce, Boston, raw"},  // ❌ 微妙に違う
    {"ingredient_name": "Corn, cooked, as ingredient"},  // ✅ マッチ
    {"ingredient_name": "Tomatoes, for use on a sandwich"}  // ✅ マッチ
  ]
}
```

**問題点**:
- 料理名に", cooked, with sauce"など余計な説明を追加
- "Lettuce, Boston, raw" → Word Query APIが"exact_match"を返せない可能性

---

## 📝 現在のPromptの問題点を確認

