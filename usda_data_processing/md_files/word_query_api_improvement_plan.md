# Word Query API 改善実装プラン

## 📅 作成日: 2025-10-15

## 🎯 概要

Word Query APIをUSDAデータと統合し、ユーザーの検索体験を最適化するための包括的な改善プランです。
現在の問題点を解決し、Tier Systemを最大限に活用する実装方針を定義します。

---

## 📊 現状分析

### 現在のシステム構成

```
現在のWord Query API:
├── データソース: MyNetDiary (db/mynetdiary_converted_tool_calls_list_stemmed_with_nutrition.json)
├── Tier System: 7段階のマッチング優先度
├── Stemming処理: Porter Stemmerによる語幹化処理（実装済み）
│   ├── 単数/複数形の統一 (breads → bread)
│   ├── 動詞の時制統一 (toasted → toast)
│   └── 語尾変化の吸収
└── Boost Score: Tier 1 (15) から Tier 7 (1) まで

今後の統合予定:
├── USDAデータ (usda_raw_ingredients_split_cleaned.json)
├── USDAデータ (usda_prepared_ingredients_split_cleaned.json)
└── 合計: 1,542件の食材データ
```

### Stemming処理の詳細

```python
def stem_query(query: str) -> str:
    # 1. 小文字化: "Breads" → "breads"
    # 2. 特殊文字除去: "bread's" → "bread s"
    # 3. 語幹化: "breads" → "bread"
    return stemmed_query

# 実例：
"breads" → "bread"  ✅ 単複形統一
"toasted" → "toast"  ✅ 時制統一
"french" → "french"  (変化なし)
```

### 識別された問題点（Stemmingでも解決できない）

| 問題カテゴリ | 件数 | 影響度 | 詳細 | Stemming後も残る問題 |
|------------|------|--------|------|---------------------|
| **Bread関連** | 8件 | 🔴 高 | "bread"で検索できない | search_nameに"Bread"が含まれていない |
| **Topping関連** | 5件 | 🔴 高 | "topping"で検索できない | search_nameに"Topping"が含まれていない |
| **Icing関連** | 2件 | 🟡 中 | "icing"で検索できない | search_nameに"Icing"が含まれていない |
| **Cheese関連** | 1件 | 🟡 中 | "cheese"で一部検索できない | search_nameに"Cheese"が含まれていない |

#### 具体例：Stemmingがあっても問題が残る理由

```python
# 現在のデータ
search_name: ["French", "Vienna"]

# ユーザー入力とStemming処理
"bread" → stemmed: "bread"
"French" → stemmed: "french"  # ❌ bread ≠ french
"Vienna" → stemmed: "vienna"  # ❌ bread ≠ vienna

結果: マッチしない（基本カテゴリ名が欠落しているため）
```

---

## 🚀 改善プラン

### フェーズ1: データ構造の再設計（優先度: 最高）

#### 1.0 複合語の課題認識

**重要な発見**：一部の食材は複合語として扱う必要がある

```json
// 課題例1: "White beans"
// ❌ 現状
"search_name": ["White", "beans"]  // 分解してしまうと不適切

// ✅ 理想
"search_name": ["White beans", "Beans", "White"]  // 複合語を優先

// 課題例2: "Chicken breast"
// ❌ 現状
"search_name": ["Chicken", "Breast"]  // 別々だと検索精度低下

// ✅ 理想
"search_name": ["Chicken breast", "Chicken", "Breast"]  // 複合語優先
```

**識別すべき複合語カテゴリ**：
- 豆類: White beans, Black beans, Green beans（さやいんげんと黒豆は異なる）
- 鶏肉部位: Chicken breast, Chicken thigh, Chicken wing
- パン類: French bread, Wheat bread, White bread
- クリーム類: Ice cream, Sour cream, Cream cheese
- その他: French fries, Sweet potato, Green pepper

#### 1.1 search_name フィールドの拡張

**現状:**
```json
{
  "description": "Bread, French or Vienna, toasted",
  "search_name": ["French", "Vienna"],  // ❌ 問題あり
  "ai_description": "toasted"
}
```

**改善後（Stemming効果を最大化）:**
```json
{
  "description": "Bread, French or Vienna, toasted",
  "search_name": [
    "Bread",           // 基本カテゴリ → stem: "bread"
    "French bread",    // カテゴリ + タイプ → stem: "french bread"
    "Vienna bread",    // カテゴリ + タイプ → stem: "vienna bread"
    "Toasted bread",   // カテゴリ + 状態 → stem: "toast bread"
    "French",          // タイプ単体 → stem: "french"
    "Vienna"           // タイプ単体 → stem: "vienna"
  ],
  "ai_description": null
}
```

**Stemming + 改善の相乗効果:**
| ユーザー入力 | Stemmed | マッチする要素 | 結果 |
|-------------|---------|---------------|------|
| bread | bread | "Bread" → bread | ✅ Tier 1 |
| breads | bread | "Bread" → bread | ✅ Tier 1 |
| french breads | french bread | "French bread" → french bread | ✅ Tier 1 |
| toasted bread | toast bread | "Toasted bread" → toast bread | ✅ Tier 1 |

#### 1.2 新規フィールドの追加

```typescript
interface ImprovedFoodItem {
  // 既存フィールド
  foodCode: string;
  description: string;
  search_name: string[];  // 常に配列
  ai_description: string | null;

  // 新規フィールド
  category: string;              // 主要食品カテゴリ
  search_priority: number;        // デフォルト表示優先度
  common_misspellings?: string[]; // よくあるスペルミス
  alternative_names?: string[];   // 代替名・略称
  tags?: string[];                // 検索用タグ

  // 摂取頻度フィールド（新規追加）
  consumption_frequency: 'common' | 'moderate' | 'rare';  // 北米での摂取頻度
  frequency_score: 1 | 2 | 3;     // 頻度スコア（rare=1, moderate=2, common=3）

  // 栄養情報（既存）
  foodNutrients: NutrientInfo[];
}
```

### フェーズ2: Tier System の最適化（優先度: 高）

#### 2.1 現在のTier System

```python
# apps/word_query_api/endpoints/nutrition_search.py
Tier 1: stemmed_search_nameでの完全一致 (Boost: 15)
Tier 2: stemmed_descriptionでの完全一致 (Boost: 12)
Tier 3: search_nameでのプレフィックス一致 (Boost: 10)
Tier 4: descriptionでのプレフィックス一致 (Boost: 8)
Tier 5: search_nameでの部分一致 (Boost: 5)
Tier 6: descriptionでの部分一致 (Boost: 3)
Tier 7: ファジーマッチ (Boost: 1)
```

#### 2.2 改善提案

```python
# 新しいTier定義
Tier 1: search_name配列の要素で完全一致 (Boost: 15) # そのまま
Tier 1.5: categoryで完全一致 (Boost: 13) # 新規
Tier 2: ai_descriptionで完全一致 (Boost: 12) # そのまま
Tier 2.5: alternative_namesで完全一致 (Boost: 11) # 新規
# ... 以下既存のTierを調整
```

### フェーズ3: 摂取頻度による優先順位付け（優先度: 高）

#### 3.1 摂取頻度フィールドの活用

北米ユーザーの食事記録を支援するため、摂取頻度による優先順位付け機能を実装：

```python
# 摂取頻度の定義
FREQUENCY_DEFINITIONS = {
    'common': {
        'score': 3,
        'description': '日常的食材（週3回以上）',
        'examples': ['bread', 'milk', 'chicken', 'eggs', 'cheese', 'coffee'],
        'criteria': 'Walmart/Costcoで通年入手可能、70%以上が週複数回消費'
    },
    'moderate': {
        'score': 2,
        'description': '一般的食材（週1-2回）',
        'examples': ['salmon', 'avocado', 'quinoa', 'berries'],
        'criteria': '健康志向・グルメな選択肢'
    },
    'rare': {
        'score': 1,
        'description': '特別な機会（月1回以下）',
        'examples': ['lobster', 'caviar', 'truffle'],
        'criteria': '高価格帯（$20/lb以上）、エスニック食材'
    }
}
```

#### 3.2 スコアリング統合

```python
def calculate_combined_score(tier_score: float, frequency_score: int, use_frequency: bool = True) -> float:
    """
    Tierスコアと頻度スコアを組み合わせた最終スコアを計算

    Args:
        tier_score: Tier Systemによるスコア (1-15)
        frequency_score: 摂取頻度スコア (1-3)
        use_frequency: 頻度ブーストを使用するか

    Returns:
        最終スコア
    """
    if not use_frequency:
        return tier_score

    # 頻度による微調整（同一Tier内での順位付け）
    frequency_boost = frequency_score * 0.1  # 0.1, 0.2, or 0.3
    return tier_score + frequency_boost
```

### フェーズ4: 検索アルゴリズムの改善（優先度: 中）

#### 4.1 複数パターンマッチングの実装

```python
def enhanced_search(query: str, foods: List[Dict], use_frequency_boost: bool = True) -> List[Dict]:
    """
    改善された検索アルゴリズム

    Args:
        query: 検索クエリ
        foods: 食材データリスト
        use_frequency_boost: 摂取頻度による優先順位付けを使用するか（オプション）
    """
    stemmed_query = stem_query(query)
    results = []

    for food in foods:
        # search_name配列の各要素を個別にチェック
        best_tier = None
        best_score = 0

        for search_pattern in food['search_name']:
            tier = determine_match_tier(stemmed_query, search_pattern)
            score = get_tier_score(tier)
            if score > best_score:
                best_score = score
                best_tier = tier

        if best_tier:
            # 摂取頻度によるブーストを適用（オプション）
            frequency_boost = 0
            if use_frequency_boost and 'frequency_score' in food:
                # frequency_score (1-3) を 0.1-0.3 のブーストに変換
                # 同じTierでも頻度が高いものが上位に来るように微調整
                frequency_boost = food['frequency_score'] * 0.1

            results.append({
                'food': food,
                'tier': best_tier,
                'score': best_score,
                'final_score': best_score + frequency_boost,
                'frequency_score': food.get('frequency_score', 2)
            })

    # 最終スコアでソート（Tierが同じ場合は頻度順）
    return sorted(results, key=lambda x: (x['final_score'], x['frequency_score']), reverse=True)
```

#### 4.2 スペルミス対応

```python
def handle_misspellings(query: str, food: Dict) -> bool:
    """
    よくあるスペルミスをチェック
    """
    if 'common_misspellings' in food:
        for misspelling in food['common_misspellings']:
            if similar(query, misspelling) > 0.85:  # 類似度85%以上
                return True
    return False
```

---

## 📝 実装ステップ

### Step 1: データ再生成（1-2日）

1. **プロンプト修正（シンプルなアプローチ）**
   - split_ingredient_names_with_llm.py のプロンプトを更新
   - 検索パターンを網羅的に生成するよう変更
   - **重要**: 複雑な処理は後処理（clean_and_finalize_usda_split_data.py）に委ねる

   ```
   プロンプト側の責任範囲:
   - 基本的な検索パターン生成
   - 複合語の識別
   - 配列形式での出力

   後処理側の責任範囲（既に実装済み）:
   - NFS除去
   - 括弧内容の除去
   - "NS as to"を含む項目の削除
   - ブランド名の分離
   - "None"文字列のnull変換
   ```

2. **既存データの再処理**
   ```bash
   # バックアップ作成
   cp output/usda_*_split_cleaned.json output/backup/

   # 再処理実行
   python scripts/split_ingredient_names_with_llm.py

   # クリーニング
   python scripts/clean_and_finalize_usda_split_data.py
   ```

3. **品質検証**
   - 問題のあった16件を重点チェック
   - ランダムサンプリングで品質確認

### Step 2: API エンドポイント更新（1日）

1. **nutrition_search.py の修正**
   ```python
   # 新しいデータ形式に対応
   # Tier Systemの調整
   # 検索アルゴリズムの改善
   ```

2. **新規エンドポイント追加**
   ```python
   @router.post("/api/v1/word-query/enhanced-search")
   async def enhanced_search_endpoint(
       query: str,
       limit: int = 10,
       include_alternatives: bool = True
   ):
       """改善版検索エンドポイント"""
       pass
   ```

### Step 3: テストと検証（1日）

1. **ユニットテスト作成**
   ```python
   # tests/test_word_query_improvements.py
   test_cases = [
       ("bread", ["Bread, French or Vienna", "Bread, wheat", ...]),
       ("french bread", ["Bread, French or Vienna"]),
       ("cheese", ["Cheese, Gouda or Edam", ...]),
       ("topping", ["Topping, chocolate", ...])
   ]
   ```

2. **パフォーマンステスト**
   - 検索速度の測定
   - メモリ使用量の確認
   - 大量リクエスト処理の検証

### Step 4: 段階的移行（2-3日）

1. **A/Bテスト環境構築**
   - 既存APIと新APIの並行運用
   - メトリクス収集

2. **移行計画**
   ```
   Day 1: 10% のトラフィックを新APIへ
   Day 2: 50% のトラフィックを新APIへ
   Day 3: 100% 移行完了
   ```

---

## 🎯 成功指標（KPI）

| 指標 | 現在値 | 目標値 | 測定方法 |
|------|--------|--------|---------|
| **基本カテゴリヒット率** | 約90% | 99%以上 | "bread", "cheese"等の検索成功率 |
| **Tier 1マッチ率** | 約60% | 85%以上 | 全検索のうちTier 1でマッチする割合 |
| **平均検索時間** | 未測定 | <50ms | API応答時間 |
| **ユーザー満足度** | 未測定 | 90%以上 | クリック率、選択率から推定 |
| **頻度順の適切性** | 未測定 | 80%以上 | 上位3件中のcommon食材割合 |
| **予測精度** | 未測定 | 75%以上 | ユーザーが最初の5件から選択する率 |

---

## ⚠️ リスクと対策

### リスク1: データ量増加による性能劣化
**対策:**
- インデックス最適化
- キャッシュ戦略の実装
- 必要に応じてElasticsearch導入検討

### リスク2: 既存システムとの互換性
**対策:**
- 後方互換性の維持
- 段階的移行
- ロールバック計画の準備

### リスク3: LLM再処理のコスト
**対策:**
- バッチ処理の最適化
- チェックポイント機能の活用
- 部分的な再処理オプション

---

## 🔄 継続的改善

### 短期（1-2週間）
- [ ] 基本的な問題16件の修正
- [ ] プロンプト改善と再生成
- [ ] APIエンドポイントの更新

### 中期（1-2ヶ月）
- [ ] Elasticsearchの評価と導入
- [ ] 機械学習による検索順位最適化
- [ ] ユーザー行動分析の実装

### 長期（3-6ヶ月）
- [ ] 多言語対応（日本語、スペイン語等）
- [ ] 音声検索の最適化
- [ ] パーソナライゼーション機能

---

## 📚 参考資料

- [Word Query API 現在の実装](../apps/word_query_api/endpoints/nutrition_search.py)
- [USDAデータ分析レポート](./search_name_optimal_design_analysis.md)
- [問題点詳細リスト](./search_name_comprehensive_issues_report.md)
- [Tier System分析](./search_name_optimal_design_analysis.md)

---

## 👥 関係者

- **実装担当**: 開発チーム
- **レビュー**: テクニカルリード
- **承認**: プロダクトマネージャー

---

## 📅 更新履歴

| 日付 | バージョン | 更新内容 | 更新者 |
|------|-----------|---------|--------|
| 2025-10-15 | v1.0 | 初版作成 | Claude Code |
| 2025-10-15 | v1.1 | Stemming処理の詳細と相乗効果を追記 | Claude Code |
| 2025-10-15 | v1.2 | 摂取頻度によるスコアリングオプションを追加 | Claude Code |

---

## ✅ チェックリスト

### データ準備
- [ ] プロンプト改善案の最終確認
- [ ] 既存データのバックアップ
- [ ] テストデータセットの準備

### 実装
- [ ] split_ingredient_names_with_llm.py の修正
- [ ] clean_and_finalize_usda_split_data.py の更新
- [ ] nutrition_search.py の改善

### テスト
- [ ] ユニットテスト作成
- [ ] 統合テスト実施
- [ ] パフォーマンステスト

### デプロイ
- [ ] ステージング環境でのテスト
- [ ] A/Bテスト設定
- [ ] 本番環境への段階的展開
- [ ] モニタリング設定

---

## 📞 連絡先

技術的な質問や提案がある場合は、GitHubのIssueまたはプルリクエストでお知らせください。