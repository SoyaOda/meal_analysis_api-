# Pipeline 改善点詳細分析レポート

生成日時: 2025-10-26
分析対象: 50画像の比較結果（nutrition_comparison_all_50_20251026_163013.json）

## エグゼクティブサマリー

### 統計概要
- **高誤差ケース**: 41/50 (82%)が少なくとも1つの栄養素で30%以上の誤差
- **平均誤差**: カロリー +12.7%, タンパク質 +19.9%, 脂質 +10.0%, 炭水化物 +12.4%
- **最大誤差**: カロリー 66.5%, タンパク質 99.0%, 脂質 143.5%, 炭水化物 117.9%

### 主要な問題パターン（発生頻度順）
1. **VLM重量推定誤差** (25/41 = 61%)
2. **Rerankerが"with..."句を無視** (12/41 = 29%)
3. **VLM食材識別誤差** (4/41 = 10%)

## 詳細分析

### 1. VLMプロンプトの問題と改善点

#### 問題点1: 重量推定の過大評価

**具体例**:
- test_food11: lasagna 240g → 450g (+87%)
- test_food11: salad 40g → 200g (+400%)
- test_food13: tacos 270g → 380g (+40%)
- test_food22: pasta 180g → 380g (+111%)

**原因分析**:
- VLMは視覚的サイズを過大評価する傾向
- 特に密度の高い料理（ラザニア、パスタ）で顕著
- サラダなど体積の大きいものも過大評価

#### 問題点2: 複合料理の分離失敗

**具体例**:
- test_food48: "beef stew"をmain_food + extrasに分離すべきところを一体化
- test_food22: "pasta with shrimp and broccoli"を単純な"pasta"として処理

**改善提案**:
```text
# VLMプロンプト改善案（重量推定セクション）
WEIGHT ESTIMATION GUIDELINES:
- Standard portion references:
  * Pasta/rice main dish: 150-250g typical, 350g+ is very large
  * Side salad: 50-100g typical, 200g+ is a main salad
  * Tacos/wraps: 80-120g per piece typical
  * Lasagna slice: 200-300g typical
- Visual cues for weight:
  * Compare to plate size (standard dinner plate = 25cm)
  * Consider food density (dense foods weigh more than they appear)
  * Account for hidden depth in layered dishes
- When uncertain, prefer conservative estimates
```

### 2. USDA DBのエイリアス要件

#### 必要なエイリアス作成

**"with/without"パターン対応**:
USDAデータベース分析から判明した重要パターン：
- **Dressing**: WITHOUT dominant (2 WITH vs 28 WITHOUT)
- **Sauce**: WITHOUT dominant (22 WITH vs 68 WITHOUT)
- **Vegetables**: WITH dominant (128 WITH vs 1 WITHOUT)

**必要なエイリアス例**:
```json
{
  "user_query": "tacos with vegetables",
  "aliases": [
    "taco with lettuce and tomato",
    "taco with added vegetables",
    "taco, hard shell, with meat and vegetables"
  ]
}
```

**実装提案**:
- 前処理段階で"with"句を検出
- 対応するUSDAフォーマットに変換
- 複数の可能性がある場合は複数エイリアスを生成

### 3. Retriever（前処理・アルゴリズム）改善点

#### 問題点: "with"句の処理不適切

**現状の処理**:
```python
# query_main: "pasta"
# query_descriptors: "with shrimp and broccoli"
```

**改善案**:
```python
def preprocess_query(search_name: str, description: str):
    # "with"句を検出して主要食材に統合
    if "with" in search_name.lower():
        # 例: "pasta with shrimp" → query_main="pasta shrimp"
        components = search_name.split("with")
        main = components[0].strip()
        additions = components[1].strip() if len(components) > 1 else ""
        # 統合クエリを生成
        integrated_query = f"{main} {additions}"
        return integrated_query, description
    return search_name, description
```

### 4. Rerankerの問題と改善点

#### 現状の設定（良好だが改善余地あり）

**現在のinstruction**（優先順位）:
1. Food Identity
2. Nutritional Components
3. Other Details

**問題**: 低スコア時の処理が不十分

**改善提案**:
```python
class RerankerModel:
    def __init__(self):
        # スコア閾値を追加
        self.min_acceptable_score = 0.6
        self.very_low_score_threshold = 0.3

        # instructionに具体例を追加
        self.task_instruction = """
        ... 既存の内容 ...

        SPECIFIC PATTERNS TO PRIORITIZE:
        - "with vegetables" → MUST match entries containing vegetables
        - "with sauce/dressing" → MUST match entries with sauce/dressing
        - "no cheese/meat" → MUST NOT match entries with cheese/meat

        WARNING SCORES:
        - Score < 0.6: Match may be incomplete (missing components)
        - Score < 0.3: Match is likely incorrect
        """
```

### 5. その他の改善点

#### Post-processing層の追加

```python
def validate_and_adjust_results(vlm_output, usda_matches):
    warnings = []
    adjustments = []

    for dish, match in zip(vlm_output['dishes'], usda_matches):
        # 低スコア警告
        if match['rerank_score'] < 0.6:
            warnings.append(f"Low confidence match for {dish['search_name']}")

        # "with"句のバリデーション
        if "with" in dish['search_name'].lower():
            if match['rerank_score'] < 0.5:
                # 代替候補を検索
                adjustments.append({
                    "original": dish['search_name'],
                    "action": "search_alternatives"
                })

    return warnings, adjustments
```

## 実装優先順位

### Phase 1（即座に実装可能 - 1週間）
1. **VLMプロンプト改善**
   - 重量推定ガイドラインの追加
   - 標準ポーション参照の追加
   - 推定誤差: -30%期待

2. **Rerankerスコア閾値**
   - 低スコア警告の実装
   - 代替候補提示機能
   - 推定誤差: -10%期待

### Phase 2（中期 - 2週間）
3. **Retriever前処理改善**
   - "with"句の統合処理
   - クエリ拡張機能
   - 推定誤差: -20%期待

4. **Post-processing層**
   - 結果検証機能
   - 自動調整機能
   - 推定誤差: -15%期待

### Phase 3（長期 - 1ヶ月）
5. **USDAエイリアスDB構築**
   - 頻出パターンのマッピング
   - 動的エイリアス生成
   - 推定誤差: -25%期待

## 期待効果

全改善実装後の予測:
- **高誤差ケース**: 41/50 → 10/50 (20%)
- **平均誤差**: 全栄養素で10%以下
- **最大誤差**: 50%以下に抑制

## 次のアクション

1. VLMプロンプトファイル（`freeform_prompt_usda_format_ver.txt`）の更新
2. Rerankerに警告機能の追加
3. テストデータでの効果測定
4. 段階的な本番環境への適用