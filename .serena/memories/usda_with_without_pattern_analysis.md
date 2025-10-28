# USDA Database: With/Without Pattern Analysis

**Total USDA entries: 5,772**

## Summary Table

| Component   | WITH | WITHOUT | Ratio (WITH:WITHOUT) | Dominant Pattern |
|-------------|------|---------|---------------------|------------------|
| Dressing    |    2 |      28 |                2:28 | **WITHOUT** ✓    |
| Sauce       |   22 |      68 |               22:68 | **WITHOUT** ✓    |
| Cheese      |  158 |      11 |              158:11 | **WITH** ✓       |
| Meat        |  117 |       9 |               117:9 | **WITH** ✓       |
| Vegetables  |  128 |       1 |               128:1 | **WITH** ✓       |
| Butter      |   50 |       5 |                50:5 | **WITH** ✓       |
| Gravy       |   39 |       0 |                39:0 | **WITH** ✓       |

## Key Insights

### 1. DRESSING (WITHOUT dominant)
- **WITH dressing**: 2 entries (1.2% of salads)
  - Apple salad with dressing
  - Pineapple salad with dressing
- **NO dressing**: 28 entries (17.2% of salads)
  - Caesar salad, with romaine, no dressing
  - Chicken garden salads, no dressing
- **Unspecified**: 80 entries (49.1% of salads)
  - Chicken salad, made with mayonnaise (マヨネーズは明記、ドレッシングは不明)

**重要**: USDAサラダの**大多数はドレッシングについて明示的に記載していない**。「no dressing」が標準的な記述。

### 2. SAUCE (WITHOUT dominant)
- **WITH sauce**: 22 entries
  - Chicken grilled with sauce
- **WITHOUT sauce**: 68 entries
  - Chicken grilled without sauce

**パターン**: グリルチキンなどで、ソースの有無を明示的に区別。

### 3. CHEESE (WITH dominant)
- **WITH cheese**: 158 entries
  - Sandwiches, burgers, pasta dishes
- **NO cheese**: 11 entries
  - Tacos, specific variations

**重要**: チーズ入りが標準。「no cheese」は例外的。

### 4. MEAT (WITH dominant)
- **WITH meat**: 117 entries
  - Pasta with meat, chili with meat
- **NO meat**: 9 entries
  - Soup pho no meat, pot pie no meat

**重要**: 肉入りが標準。「no meat」はベジタリアン版など。

### 5. VEGETABLES (WITH dominant)
- **WITH vegetables**: 128 entries
  - Pasta with added vegetables
- **NO vegetables**: 1 entry
  - Sweet and sour chicken without vegetables

**重要**: 野菜入りが標準。「no vegetables」は極めて稀。

### 6. PASTA Special Case
- **Total pasta entries**: 107
- **Plain pasta**: 2 entries (1.9%)
  - Pasta, cooked
  - Pasta, whole grain, cooked
- **With sauce**: 103 entries (96.3%)
  - Pasta with tomato-based sauce (51 entries)
  - Pasta with cream sauce
  - Pasta with meat and vegetables

**重要**: **USDAではパスタ＝ソース込みが標準**。Plain pastaはほぼ存在しない。

## VLM Prompt への影響

### 現在のfreeform_usda_prompt の問題
VLMが「pasta with vegetables and meat」を検出した場合：
1. ❌ "Pasta, cooked"にマッチ → ソース・具材の栄養が欠落
2. ✅ "Pasta with tomato-based sauce, meat, and added vegetables"にマッチ → 正確

### Reranker改善の効果
- **Nutritional Components優先**により、具材・ソース含む候補を優先選択
- Pastaクエリで成功: Score 0.9893 → 0.5941（具材含む候補が1位）

### Caesar Salad の課題
- USDA DBには「Caesar salad with dressing」が**存在しない**
- VLMは「extras」として分離すべき：
  ```json
  {
    "main_food": {"search_name": "caesar salad", "description": "with romaine, no dressing"},
    "extras": [{"search_name": "caesar dressing", "weight_g": 30}]
  }
  ```

## 推奨事項

1. **VLM Promptの改善**
   - サラダ類: ドレッシングは`extras`として分離
   - パスタ類: ソース込みの料理名を使用（"Pasta with tomato sauce"など）

2. **Reranker設定（完了済み）**
   - ✅ Nutritional Components（具材・ソース）を最優先
   - ✅ Cooking Methodの優先度を下げる

3. **Post-processing**
   - Reranker score < 0.3の場合、警告表示
   - 特にサラダで「no dressing」マッチ時、ドレッシング追加を推奨

Date: 2025-10-26
