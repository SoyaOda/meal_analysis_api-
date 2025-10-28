# 30%以上誤差ケースのパイプライン問題分析と改善提案

**生成日時**: 2025-10-26 22:30
**対象**: 11件の30%以上カロリー誤差ケース
**データソース**: nutrition_comparison_all_50_20251026_220152.json

---

## 📊 問題パターン統計

| 問題種類 | 発生件数 | 発生率 | 重大度 |
|---------|---------|--------|--------|
| **重量推定誤差** | 5件 | 45.5% | 🔴 高 |
| **低reranker score** | 3件 | 27.3% | 🟡 中 |
| **VLM認識不足** | 2件 | 18.2% | 🟡 中 |

---

## 🔍 問題パターン別詳細分析

### 1. 重量推定誤差（5件、45.5%）

#### 🎯 問題の本質

VLMによる重量推定が±20%以上の誤差を持つケース。パイプライン全体の精度に最も大きな影響を与える。

#### 📋 発生ケース

| 画像 | Label総重量 | VLM推定重量 | 誤差 | カロリー誤差 |
|------|------------|-------------|------|-------------|
| test_food4.jpg | 505g | 720g | +42.6% | +63.0% |
| test_food13.jpg | 470g | 590g | +25.5% | +61.4% |
| test_food27.jpg | 620g | 435g | -29.8% | -53.7% |
| test_food20.jpg | 590g | 712g | +20.7% | +47.7% |
| test_food8.jpg | 570g | 385g | -32.5% | -35.2% |

#### 🔬 根本原因

##### 1.1 主要料理の重量オーバー推定

**test_food4.jpg**:
```
Label: pork, loin, grilled 360g
VLM推定: chicken thigh 0g → pork loin 360g (認識ミス)
問題: 主料理を誤認識した上で、重量を大幅に多く推定
```

**test_food13.jpg**:
```
Label: beef fajita tacos 270g
VLM推定: beef fajitas 375g (+38.9%)
問題: 主料理の重量を約140g過大評価
```

##### 1.2 小食材の重量アンダー推定

**test_food27.jpg**:
```
Label総重量: 620g (4品)
VLM推定: 435g (4品)
問題: 全体的に控えめな重量推定（特にmain_foodの認識ミス）
```

**test_food8.jpg**:
```
Label: breaded fish fillet 150g
VLM推定: baked chicken fillet 120g
問題: 料理の種類を誤認識 + 重量アンダー推定
```

#### 💡 改善提案

##### 提案1-1: 重量推定のキャリブレーション

```python
# VLMプロンプトに追加
"""
**重量推定ガイドライン**:
- 主料理（main_food）: 一般的な提供量は150-250g
- 肉料理: 150-200g（手のひらサイズ）
- ご飯・パスタ: 150-200g（茶碗1杯）
- サラダ: 50-100g
- ソース・調味料: 10-30g

画像内の料理の大きさを皿や他の物体と比較して判断してください。
"""
```

##### 提案1-2: 重量推定の不確実性を考慮

```python
# パイプラインに重量推定の信頼区間を導入
def estimate_weight_with_confidence(dish: dict) -> tuple[float, float]:
    """
    重量推定に不確実性を導入

    Returns:
        (estimated_weight, confidence_level)
    """
    estimated = dish.get("weight_g", 0)
    confidence = dish.get("confidence", 0.8)

    # confidenceが低い場合は、重量にマージンを持たせる
    if confidence < 0.85:
        # ±15%の範囲を考慮
        lower_bound = estimated * 0.85
        upper_bound = estimated * 1.15
        return (estimated, lower_bound, upper_bound)

    return (estimated, estimated, estimated)
```

##### 提案1-3: 複数画像・複数視点からの推定

将来的には、複数角度の画像を使用して重量推定の精度を向上。

---

### 2. 低reranker score（3件、27.3%）

#### 🎯 問題の本質

USDA検索でマッチングは成功しているが、reranker scoreが0.8未満のケース。検索クエリとUSDAデータベースのギャップを示唆。

#### 📋 発生ケース

##### test_food27.jpg

| 検索クエリ | USDA Match | Rerank Score | 問題 |
|-----------|-----------|--------------|------|
| chicken, cooked, shredded | Chicken, NS as to part, baked, broiled, or roasted, NS as to skin eaten | 0.419 | 🔴 非常に低い |
| pork stir-fry with cabbage | Cabbage, cooked, as ingredient | 0.462 | 🔴 非常に低い |

**問題**: VLMが生成したクエリが曖昧すぎる、または調理方法の記述がUSDAデータと一致しない。

##### test_food20.jpg

| 検索クエリ | USDA Match | Rerank Score | 問題 |
|-----------|-----------|--------------|------|
| dried herbs | Spices, basil, dried | 0.409 | 🔴 非常に低い |
| figs | Fig, canned | 0.270 | 🔴 最低スコア |

**問題**:
- "dried herbs" → 特定のハーブ名が必要
- "figs" → 生のイチジク vs 缶詰イチジクの混同

##### test_food8.jpg

| 検索クエリ | USDA Match | Rerank Score | 問題 |
|-----------|-----------|--------------|------|
| baked chicken fillet with herb crust | Chicken breast, baked, broiled, or roasted, skin not eaten, from raw | 0.653 | 🟡 低い |

**問題**: "herb crust"という詳細な調理方法がUSDAデータにない。

#### 🔬 根本原因

##### 2.1 クエリの抽象度が高すぎる

VLMが生成するクエリが、USDAデータベースの記述粒度と一致しない。

##### 2.2 調理方法の記述の違い

VLM: "stir-fry with cabbage"
USDA: "cabbage, cooked, as ingredient"

→ 調理方法の記述方法が異なる

##### 2.3 食材の状態（生 vs 加工）の不一致

VLM: "figs"（生のイチジクを想定）
USDA: "fig, canned"（缶詰イチジクにマッチ）

→ 食材の状態を明示する必要がある

#### 💡 改善提案

##### 提案2-1: クエリ生成の改善

```python
# QueryExtractionService.pyに追加
def normalize_query_for_usda(search_name: str, description: str) -> str:
    """
    USDAデータベースに最適化されたクエリ生成
    """
    # 調理方法の標準化
    cooking_method_map = {
        "stir-fry": "cooked",
        "stir fry": "cooked",
        "sauteed": "cooked",
        "grilled": "broiled",
        "baked": "baked or broiled",
        "roasted": "baked or broiled or roasted",
    }

    # 食材状態の明示化
    # デフォルトは"fresh, raw"を追加
    if "dried" not in description and "canned" not in description:
        if "herb" in search_name or "spice" in search_name:
            pass  # ハーブ・スパイスはそのまま
        else:
            description = f"{description}, fresh"

    return f"{search_name}, {description}"
```

##### 提案2-2: Reranker scoreの閾値調整とフォールバック

```python
# 現在の閾値: なし（全てのマッチを受け入れ）
# 提案: 閾値を設定し、低スコアの場合は代替検索

def search_with_fallback(query: str, threshold: float = 0.7) -> Optional[dict]:
    """
    reranker scoreが閾値未満の場合、代替検索を実行
    """
    result = search_usda(query)

    if result and result.get("rerank_score", 0) >= threshold:
        return result

    # フォールバック: より一般的なクエリで再検索
    simplified_query = simplify_query(query)
    fallback_result = search_usda(simplified_query)

    return fallback_result if fallback_result else result

def simplify_query(query: str) -> str:
    """
    クエリを簡略化して再検索
    例: "pork stir-fry with cabbage" → "pork, cooked"
    """
    # 調理方法と修飾語を削除
    # ...
    return simplified_query
```

##### 提案2-3: USDA検索候補の拡張

```python
# 複数候補を返し、LLMで最適候補を選択
async def search_multiple_candidates(query: str, top_k: int = 3) -> List[dict]:
    """
    上位k件の候補を返す
    """
    candidates = await search_usda(query, top_k=top_k)

    # LLMで最適候補を選択
    best_match = await llm_select_best_match(
        query=query,
        candidates=candidates
    )

    return best_match
```

---

### 3. VLM認識不足（2件、18.2%）

#### 🎯 問題の本質

VLMが画像内の料理の一部を認識できていない、または誤認識しているケース。

#### 📋 発生ケース

##### test_food4.jpg

```
Label: 7品（chicken thigh, macaroni and cheese, salad + 4個の野菜）
VLM: 3品（salad, macaroni and cheese, pork loin）

問題:
1. chicken thighをpork loinと誤認識
2. サラダの個別野菜（cucumber, pepper, onion, carrots）を認識できず
3. 品数が7品 → 3品に減少
```

##### test_food13.jpg

```
Label: 4品（beef fajitas, sour cream, corn, grapes）
VLM: 3品（beef fajitas, corn, grapes）

問題:
1. sour cream（小さな付け合わせ）を認識できず
```

#### 🔬 根本原因

##### 3.1 小さな付け合わせの見落とし

- sour cream: 30g → VLMが認識できず
- サラダの個別野菜: 小さい野菜を個別に認識できない

##### 3.2 類似料理の誤認識

- chicken thigh → pork loin
  - 焼き色や形状が類似している場合に誤認識

#### 💡 改善提案

##### 提案3-1: VLMプロンプトの改善

```python
# プロンプトに追加
"""
**料理認識の重要ポイント**:

1. **小さな付け合わせも必ず認識してください**:
   - ソース（sour cream, salsa, dressing等）
   - 薬味（herbs, spices, garnish等）
   - 小さな野菜（cherry tomatoes, cucumber slices等）

2. **料理の種類を慎重に判断してください**:
   - 肉の種類: 色、脂身の分布、筋の入り方で判断
   - 鶏肉: 白っぽい、筋が細い
   - 豚肉: やや白っぽい、脂身が多い
   - 牛肉: 赤い、筋がしっかりしている

3. **不確実な場合は、より一般的な名称を使用**:
   - 例: "meat, grilled"（肉の種類が不明な場合）
   - confidenceスコアを適切に設定（0.7以下）
"""
```

##### 提案3-2: 2段階VLM認識

```python
# Phase 1: 主要料理の認識
vlm_response_main = await vlm_service.analyze_main_dishes(image)

# Phase 2: 付け合わせ・小物の認識（Phase 1で認識した主料理を除外）
vlm_response_extras = await vlm_service.analyze_side_items(
    image,
    exclude_main_dishes=vlm_response_main
)

# 統合
final_response = merge_vlm_responses(vlm_response_main, vlm_response_extras)
```

##### 提案3-3: Object Detection モデルの併用

```python
# YOLOやSAMなどのObject Detectionモデルで食材領域を検出
def detect_food_regions(image: bytes) -> List[BoundingBox]:
    """
    画像内の食材領域を検出
    """
    # Object Detectionモデルで食材を検出
    detections = yolo_detect(image)

    # VLMに各領域を個別に認識させる
    recognized_items = []
    for bbox in detections:
        cropped_image = crop_image(image, bbox)
        vlm_result = vlm_service.analyze_single_item(cropped_image)
        recognized_items.append(vlm_result)

    return recognized_items
```

---

## 🎯 重要な特殊ケース分析

### Case Study: test_food47.jpg（+57.9%誤差）

**Label**:
- cheeseburger: 200g, 520 kcal
- tomato: 20g, 4 kcal
- onion: 10g, 4 kcal
- potato wedges: 170g, **255 kcal**

**Pipeline**:
- cheeseburger: 170g, 524 kcal ✅ 良好
- tomato: 30g, 6 kcal ✅ 良好
- onion: 15g, 6 kcal ✅ 良好
- **potato wedges → potato chips, baked, flavored**: 150g, **700 kcal** 🔴 誤マッチング

**問題の根本原因**:

USDA検索で「potato wedges」を「potato chips, baked, flavored」と誤マッチング。

- Label: 255 kcal（揚げたwedges）
- Pipeline: 700 kcal（ベイクドポテトチップス）

→ **445 kcal差**（全体誤差の大部分）

**改善策**:

```python
# QueryExtractionServiceに調理方法のマッピング追加
COOKING_METHOD_DISAMBIGUATION = {
    "potato wedges": "potatoes, fried or baked, wedge-cut",
    "french fries": "potatoes, french fried",
    "potato chips": "potato chips, from bag",
    "mashed potatoes": "potatoes, mashed",
}

def disambiguate_query(search_name: str, description: str) -> str:
    """
    曖昧なクエリを明確化
    """
    if search_name in COOKING_METHOD_DISAMBIGUATION:
        return COOKING_METHOD_DISAMBIGUATION[search_name]

    return f"{search_name}, {description}"
```

---

## 📈 改善優先度と期待効果

### 優先度1（即実施）: 高

#### 1. 重量推定のキャリブレーション（提案1-1）

**期待効果**: 5件のケースで誤差30%改善 → 全体誤差15%改善

**実装難易度**: 低（プロンプト修正のみ）

**実装方法**:
```python
# shared/prompts/vlm_meal_analysis_prompt.py に追加
WEIGHT_ESTIMATION_GUIDELINES = """
【重量推定ガイドライン】
- 主料理（main_food）: 一般的な提供量は150-250g
- 肉料理: 150-200g（手のひらサイズ）
- ご飯・パスタ: 150-200g（茶碗1杯）
- サラダ: 50-100g
- ソース・調味料: 10-30g

画像内の料理の大きさを皿や他の物体と比較して判断してください。
不確実な場合は、confidenceスコアを下げてください（0.7以下）。
"""
```

#### 2. 調理方法のマッピング（Case Study解決策）

**期待効果**: 特殊ケース（test_food47等）の誤差50%改善

**実装難易度**: 低（辞書追加のみ）

**実装方法**:
```python
# apps/freeform_usda_meal_analysis_api/services/query_extraction.py に追加
COOKING_METHOD_DISAMBIGUATION = {
    "potato wedges": "potatoes, fried or baked, wedge-cut",
    "french fries": "potatoes, french fried",
    # ...
}
```

### 優先度2（短期実施）: 中

#### 3. Reranker scoreの閾値とフォールバック（提案2-2）

**期待効果**: 3件のケースで誤差20%改善

**実装難易度**: 中（ロジック追加）

#### 4. VLMプロンプトの改善（提案3-1）

**期待効果**: 2件のケースで誤差15%改善

**実装難易度**: 低（プロンプト修正）

### 優先度3（長期検討）: 低

#### 5. 2段階VLM認識（提案3-2）

**期待効果**: VLM認識精度10-20%向上

**実装難易度**: 高（アーキテクチャ変更）

#### 6. Object Detection併用（提案3-3）

**期待効果**: 小物認識率50%向上

**実装難易度**: 高（新規モデル導入）

---

## 📝 まとめ

### 現状の問題点

1. **重量推定誤差が最大の問題**（45.5%のケース）
   - VLMの重量推定が±20%以上の誤差
   - 主料理の過大評価が多い

2. **USDA検索の精度**（27.3%のケース）
   - 低reranker score（<0.8）
   - クエリとUSDAデータのギャップ

3. **VLM認識不足**（18.2%のケース）
   - 小さな付け合わせの見落とし
   - 類似料理の誤認識

### 即実施すべき改善策

1. ✅ **重量推定ガイドラインをVLMプロンプトに追加**
   - 実装難易度: 低
   - 期待効果: 高（誤差15%改善）

2. ✅ **調理方法の曖昧性解消マッピング**
   - 実装難易度: 低
   - 期待効果: 中（特殊ケースで誤差50%改善）

3. ✅ **Reranker score閾値とフォールバック**
   - 実装難易度: 中
   - 期待効果: 中（誤差20%改善）

### 期待される総合改善効果

- 30%以上誤差ケース: **11件 → 5件以下**（54%削減）
- 平均カロリー誤差: **+0.9% → +0.5%以下**（44%改善）

---

**次のアクション**: 優先度1の改善策を実装して、再度全50画像で比較テストを実行
