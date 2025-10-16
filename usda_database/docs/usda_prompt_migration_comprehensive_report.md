# USDA surveyDownload.json移行に伴うプロンプト設計とコスト試算レポート

## 📅 作成日
2025-10-12

## 📋 目的

現状のMyNetDiary食材リスト（約1,100件）から、USDA FNDDSベースの料理名リスト+食材名リスト（約5,400件）への移行に伴う以下の検討：

1. 3段階優先順位に対応した新プロンプト設計
2. トークン数増加とコスト試算
3. 実装の実現可能性評価

---

## 🔍 現状分析

### 現在のmeal_analysis_api仕様

**プロンプト構成:**
- `CommonPrompts.get_mynetdiary_ingredients_list_with_header()` でElasticsearch経由でMyNetDiary食材リスト（約1,100件）をプロンプトに挿入
- 食材名を**必ず**MyNetDiaryリストから選択させる制約
- **推定トークン数**: 8,800 tokens
- **コスト**: $0.001958/回（image込み）

**栄養計算ロジック:**
- Phase1: 画像/音声から食材名を抽出（MyNetDiaryリストから選択）
- Phase2: Elasticsearchで栄養データ検索
- Phase3: **食材レベル**で栄養計算

---

## 🎯 新仕様の要件

### USDA FNDDSへの移行方針

ユーザーが認識した料理ごとに、以下の**3段階優先順位**で出力：

#### **優先度1: 料理レベル栄養計算** ⭐⭐⭐
```
条件: 料理名リストの料理名とinputFoodsをそのまま採用していい場合
出力: 料理名 + その量（unit候補からunitを選び、数値も推定）
計算方法: 料理レベルで栄養算出（inputFoodsの栄養値を利用）
```

#### **優先度2: 食材レベル栄養計算（料理名既知）** ⭐⭐
```
条件: 料理名はそのままでいいが、inputFoodsを修正した方がいい場合
出力: 料理名 + すべての食材名（**必ず食材名リストから抜き出す**） + その量
計算方法: 食材レベルで栄養算出
```

#### **優先度3: 食材レベル栄養計算（料理名未知）** ⭐
```
条件: 適切な料理名自体が料理名リストに存在しない場合
出力: 料理名（LLMが考える） + すべての食材名（**必ず食材名リストから抜き出す**） + その量
計算方法: 食材レベルで栄養算出
```

---

## 📊 USDAデータ抽出結果

### データ構成

| カテゴリー | 件数 | 詳細 |
|----------|------|------|
| **複合料理** | 3,829件 | inputFoods 2つ以上 |
| **基本食材** | 1,603件 | inputFoods 0-1個 |
| **合計** | 5,432件 | FNDDS全食品 |

### 各食品の情報構造

**複合料理の例:**
```json
{
  "dish_name": "Milk, NFS",
  "ingredients": [
    "Milk, whole, 3.25% milkfat, with added vitamin D",
    "Milk, nonfat, fluid, with added vitamin A and vitamin D",
    "Milk, lowfat, fluid, 1% milkfat, with added vitamin A and vitamin D",
    "Milk, reduced fat, fluid, 2% milkfat, with added vitamin A and vitamin D"
  ],
  "units": [
    "Guideline amount per fl oz of beverage (2.5g)",
    "1 fl oz (30.5g)",
    "Guideline amount per cup of hot cereal (61g)"
  ]
}
```

**基本食材の例:**
```json
{
  "ingredient_name": "Chicken breast boneless skinless raw",
  "units": [
    "1 oz (28.35g)",
    "3 oz (85g)",
    "1 lb (453.6g)"
  ]
}
```

---

## 💰 トークン数とコスト試算

### DeepInfra gemma-3-27b-it料金

- **Input**: $0.09 / 1M tokens
- **Output**: $0.17 / 1M tokens
- **Image処理**: $0.001166/回（現状）

### パターン別比較

| パターン | 料理数 | 食材数 | トークン数 | Input Cost/回 | Total Cost/回 | 増加率 |
|---------|--------|--------|-----------|---------------|---------------|-------|
| **現状（MyNetDiary）** | - | 1,100 | 8,800 | $0.000792 | **$0.001958** | - |
| **全件（USDA）** | 3,829 | 1,603 | 268,902 | $0.024201 | **$0.025367** | +1,196% ⚠️ |
| **フィルタリング済み** | 1,933 | 1,433 | 154,805 | $0.013932 | **$0.015098** | +671% ⚠️ |

### コスト増加の内訳

**全件採用の場合:**
- トークン数: 8,800 → 268,902 tokens (**30.6倍増**)
- コスト: $0.001958 → $0.025367/回 (**約13倍増**)
- 増加額: **$0.023409/回**

**フィルタリング済み（推奨）:**
- トークン数: 8,800 → 154,805 tokens (**17.6倍増**)
- コスト: $0.001958 → $0.015098/回 (**約7.7倍増**)
- 増加額: **$0.013140/回**

---

## 📝 新プロンプト設計案

### 基本構造

```
=== SYSTEM PROMPT ===

You are an advanced food recognition AI...

[既存の指示]

=== USDA FNDDS COMPOSITE DISHES WITH RECIPES ===
[料理名リスト: 3,829件]
- 各料理の名前
- inputFoods（材料リスト）
- 利用可能なunit候補

=== USDA FNDDS BASIC INGREDIENTS ===
[食材名リスト: 1,603件]
- 各食材の名前
- 利用可能なunit候補

=== OUTPUT PRIORITY RULES ===

For each recognized dish, output in the following priority order:

**Priority 1: Use dish-level nutrition (HIGHEST ACCURACY)**
- Condition: The dish name and inputFoods from the USDA dish list are appropriate as-is
- Output format:
  {
    "dish_name": "exact name from USDA dish list",
    "quantity": {
      "amount": estimated_number,
      "unit": "unit from available units"
    },
    "use_recipe_nutrition": true,
    "recipe_source": "FNDDS"
  }

**Priority 2: Use ingredient-level with known dish name**
- Condition: Dish name is correct but inputFoods need modification
- Output format:
  {
    "dish_name": "exact name from USDA dish list",
    "ingredients": [
      {
        "ingredient_name": "MUST select from USDA ingredient list",
        "quantity": {...}
      }
    ],
    "use_recipe_nutrition": false
  }

**Priority 3: Use ingredient-level with custom dish name**
- Condition: No appropriate dish name in USDA dish list
- Output format:
  {
    "dish_name": "custom name (AI generates)",
    "ingredients": [
      {
        "ingredient_name": "MUST select from USDA ingredient list",
        "quantity": {...}
      }
    ],
    "use_recipe_nutrition": false
  }

=== USER PROMPT ===
Please analyze this meal image...
```

### プロンプトサイズの最適化戦略

#### 戦略A: フィルタリング（推奨）

1. **料理名リスト**: 頻出料理1,933件に絞る
2. **食材名リスト**: 全1,603件を保持
3. **トークン数**: 154,805 tokens
4. **コスト**: $0.015098/回

#### 戦略B: 階層化プロンプト

1. **第1段階**: 最頻出500料理のみ
2. **第2段階**: マッチしない場合は全件検索
3. **動的プロンプト生成**: リクエストごとに最適化

---

## 🚀 実装の実現可能性

### ✅ 実現可能

| 項目 | 評価 | 詳細 |
|------|------|------|
| **技術的実装** | ✅ 可能 | 既存のCommonPromptsクラスを拡張 |
| **データ準備** | ✅ 完了 | FNDDS JSONデータ利用可能 |
| **3段階優先順位** | ✅ 可能 | JSON schema定義で実装 |
| **Unit選択** | ✅ 可能 | foodPortionsからunit候補を提供 |

### ⚠️ 懸念点

| 項目 | 懸念 | 対策 |
|------|------|------|
| **コスト増加** | 7.7-13倍増 | フィルタリング戦略採用 |
| **レスポンス時間** | トークン数増による遅延 | モデル最適化（Qwen推奨） |
| **LLM精度** | 複雑な優先順位ロジック | 段階的テスト実施 |

---

## 💡 推奨実装ステップ

### Phase 1: プロトタイプ（1週間）

1. フィルタリング済み料理リスト（1,933件）でプロンプト作成
2. 10件のテスト画像で3段階優先順位の動作確認
3. コスト・精度の実測

### Phase 2: 段階的ロールアウト（2週間）

1. ベータユーザーでA/Bテスト
2. 優先度1（料理レベル）の精度検証
3. フィードバック収集と改善

### Phase 3: 全面展開（1週間）

1. 本番環境デプロイ
2. モニタリングとコスト管理
3. 必要に応じて動的フィルタリング実装

---

## 📈 期待される効果

### メリット

✅ **栄養計算精度向上**
- 料理レベル計算で複合料理の栄養値がより正確に

✅ **データベース網羅性向上**
- 5,432件の食品データ（現状の約5倍）

✅ **ユーザー体験向上**
- より多様な料理に対応可能

### デメリット

⚠️ **コスト増加**
- 1回あたり$0.013/回の増加（フィルタリング済み）
- 月間10万リクエストで**$1,300/月**の増加

⚠️ **複雑性増加**
- 3段階優先順位ロジックの管理
- テストケース増加

---

## 🎯 結論

### 実現可能性: ✅ **可能**

- 技術的に実装可能
- 既存インフラで対応可能
- コスト増は管理可能な範囲

### 推奨アプローチ: **戦略A（フィルタリング）**

- 料理リスト: 1,933件（頻出料理のみ）
- 食材リスト: 1,603件（全件）
- **推定コスト**: $0.015098/回
- **増加額**: $0.013140/回

### 次のアクション

1. ✅ フィルタリング基準の確定
2. ⏳ 新プロンプトテンプレートの実装
3. ⏳ 10件テスト実行
4. ⏳ 精度・コスト実測
5. ⏳ 段階的ロールアウト

---

## 📎 添付資料

- `/tmp/extract_usda_dish_ingredient_list.py` - データ抽出スクリプト
- `/tmp/usda_prompt_data_extract.json` - 抽出結果データ
- `usda_database/docs/fndds_filtering_strategy_report.md` - フィルタリング戦略詳細

---

**作成者**: Claude (Serena MCP)
**レビュー**: 要確認
